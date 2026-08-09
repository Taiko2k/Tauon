"""Album art, gallery, and image cache components."""

from __future__ import annotations

import base64
import copy
import hashlib
import io
import logging
import os
import random
import ssl
import subprocess
import threading
import time
import urllib.parse
import urllib.request
from ctypes import c_float, pointer
from io import BufferedReader, BytesIO
from pathlib import Path
from typing import Any, BinaryIO, Protocol

import musicbrainzngs
import mutagen
import requests
import sdl3
from PIL import Image, ImageChops, ImageEnhance, ImageFilter
from PIL.ImageFile import ImageFile

from tauon.t_modules.t_draw import QuickThumbnail, TDraw
from tauon.t_modules.t_enums import GuiMode, MiniModeMode
from tauon.t_modules.t_extra import (
	alpha_blend,
	check_equal,
	contrast_ratio,
	fit_box,
	get_artist_safe,
	hls_to_rgb,
	rgb_add_hls,
	rgb_to_hls,
	test_lumi,
)
from tauon.t_modules.t_models import ColourRGBA, TrackClass
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, GuiVar, Input
from tauon.t_modules.t_tagscan import Ape, Flac, M4a, Opus, parse_picture_block
from tauon.t_modules.t_templates import encode_folder_name

try:
	import gi
	gi.require_version("GdkPixbuf", "2.0")
	from gi.repository import GdkPixbuf
except (ImportError, ValueError):
	GdkPixbuf: Any = None


class _ArtPlayer(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _StyleOverlay(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _SearchOverlay(Protocol):
	def __getattr__(self, name: str) -> Any: ...


class _ArtApp(Protocol):
	prefs: Prefs
	gui: GuiVar
	inp: Input
	ddt: TDraw
	pctl: _ArtPlayer
	colours: ColoursClass
	window_size: list[int]

	def __getattr__(self, name: str) -> Any: ...
class ImageObject:
	def __init__(self) -> None:
		self.index = 0
		self.texture = None
		self.rect = None
		self.request_size = (0, 0)
		self.original_size = (0, 0)
		self.actual_size = (0, 0)
		self.source = ""
		self.offset = 0
		self.stats = True
		self.format = ""
class AlbumArt:
	def __init__(self, tauon: _ArtApp, style_overlay: _StyleOverlay) -> None:
		self.tauon: _ArtApp                = tauon
		self.inp: Input                  = tauon.inp
		self.gui: GuiVar                  = tauon.gui
		self.ddt: TDraw                  = tauon.ddt
		self.pctl: _ArtPlayer                 = tauon.pctl
		self.windows: bool                 = tauon.windows
		self.macos: bool                = tauon.macos
		self.prefs: Prefs                = tauon.prefs
		self.temp_dest: sdl3.SDL_FRect            = tauon.temp_dest
		self.a_cache_directory: Path    = tauon.dirs.a_cache_directory
		self.b_cache_directory: Path    = tauon.dirs.b_cache_directory
		self.style_overlay: _StyleOverlay        = style_overlay
		self.colours: ColoursClass              = tauon.colours
		self.renderer             = tauon.renderer
		self.tls_context          = tauon.tls_context
		self.folder_image_offsets: dict[str, int] = tauon.folder_image_offsets
		self.install_directory: Path    = tauon.install_directory
		self.window_size: list[int]          = tauon.window_size
		self.cache_directory: Path      = tauon.cache_directory
		self.show_message = tauon.show_message
		self.image_types: set[str] = {"jpg", "JPG", "jpeg", "JPEG", "PNG", "png", "BMP", "bmp", "GIF", "gif", "jxl", "JXL"}
		self.art_folder_names: set[str] = {
			"art", "scans", "scan", "booklet", "images", "image", "cover",
			"covers", "coverart", "albumart", "gallery", "jacket", "artwork",
			"bonus", "bk", "cover artwork", "cover art"}
		self.source_cache: dict[int, list[tuple[int, str]]] = {}
		self.image_cache: list[ImageObject] = []

		self.blur_texture = None
		self.blur_rect = None

		# What get_blur_im last loaded: 0 = album art, 1 = artist background
		self.loaded_bg_type: int = 0

		self.download_in_progress: bool = False
		self.downloaded_image = None
		self.downloaded_track = None

		# State for display(async_hold=True), see display_async()
		self.async_lock: threading.LockType = threading.Lock()
		self.async_loads: dict[tuple, set] = {}      # (source, offset) -> requested boxes. One disk load per art
		self.async_results: dict[tuple, tuple] = {}  # (source, offset, box) -> (BytesIO, original size, format, time)
		self.async_failed: dict[tuple, float] = {}   # (source, offset, box) -> failure time (displays as blank)
		self.caller_history: dict[str, ImageObject] = {}  # caller_id -> unit it last displayed (held during loads)
		self.net_art_failed: dict[str, float] = {}  # art_url_key -> monotonic time of last failed network fetch

		self.base64cache = (0, 0, "")
		self.processing64on = None

		self.bin_cached = (None, None, None)  # track, subsource, bin

		self.embed_cached = (None, None)

	def async_download_image(self, track: TrackClass, subsource: list[tuple[int, str]]) -> None:
		self.downloaded_image = self.get_source_raw(0, 0, track, subsource=subsource)
		self.downloaded_track = track
		self.download_in_progress = False
		self.gui.request_frame()

	def get_info(self, track_object: TrackClass) -> list[tuple[int, int, int, int, str]] | None:
		sources = self.get_sources(track_object)
		if len(sources) == 0:
			return None

		offset = self.get_offset(track_object.fullpath, sources)

		o_size = (0, 0)
		format = "ERROR"

		for item in self.image_cache:
			if item.index == track_object.index and item.offset == offset:
				o_size = item.original_size
				format = item.format
				break

		else:
			# Hacky fix
			# A quirk is the index stays of the cached image
			# This workaround can be done since (currently) cache has max size of 1
			if self.image_cache:
				o_size = self.image_cache[0].original_size
				format = self.image_cache[0].format

		return [sources[offset][0], len(sources), offset, o_size, format]

	def get_sources(self, tr: TrackClass) -> list[tuple[int, str]]:
		filepath = tr.fullpath
		ext = tr.file_ext

		# Check if source list already exists, if not, make it
		if tr.index in self.source_cache:
			return self.source_cache[tr.index]

		source_list: list[tuple[int, str]] = []  # istag,

		# Source type the is first element in list
		# 0 = File
		# 1 = Embedded in tag
		# 2 = Network location

		if tr.is_network:
			# Add url if network target
			if tr.art_url_key:
				source_list.append([2, tr.art_url_key])
		else:
			# Check for local image files
			direc = os.path.dirname(filepath)
			try:
				items_in_dir = os.listdir(direc)
			except FileNotFoundError:
				logging.warning(f"Failed to find directory: {direc}")
				return []
			except Exception:
				logging.exception(f"Unknown error loading directory: {direc}")
				return []

		# Check for embedded image
		try:
			pic = self.get_embed(tr)
			if pic:
				source_list.append([1, filepath])
		except Exception:
			logging.exception("Failed to get embedded image")

		if not tr.is_network:

			dirs_in_dir = [
				subdirec for subdirec in items_in_dir if
				os.path.isdir(os.path.join(direc, subdirec)) and subdirec.lower() in self.art_folder_names]

			ins = len(source_list)
			for i in range(len(items_in_dir)):
				if os.path.splitext(items_in_dir[i])[1][1:] in self.image_types:
					dir_path = os.path.join(direc, items_in_dir[i]).replace("\\", "/")
					# The image name "Folder" is likely desired to be prioritised over other names
					if os.path.splitext(os.path.basename(dir_path))[0] in ("Folder", "folder", "Cover", "cover"):
						source_list.insert(ins, [0, dir_path])
					else:
						source_list.append([0, dir_path])

			for i in range(len(dirs_in_dir)):
				subdirec = os.path.join(direc, dirs_in_dir[i])
				items_in_dir2 = os.listdir(subdirec)

				for y in range(len(items_in_dir2)):
					if os.path.splitext(items_in_dir2[y])[1][1:] in self.image_types:
						dir_path = os.path.join(subdirec, items_in_dir2[y]).replace("\\", "/")
						source_list.append([0, dir_path])

		self.source_cache[tr.index] = source_list

		return source_list

	def get_error_img(self, size: float) -> ImageFile:
		im = Image.open(str(self.install_directory / "assets" / "load-error.png"))
		im.thumbnail((size, size), Image.Resampling.LANCZOS)
		return im

	def fast_display(self, index: int, location: list[int], box: tuple[int, int], source: list[tuple[int, str]], offset: int) -> int:
		"""Renders cached image only by given size for faster performance"""
		found_unit = None
		max_h = 0

		for unit in self.image_cache:
			if unit.source == source[offset][1] and unit.actual_size[1] > max_h:
				max_h = unit.actual_size[1]
				found_unit = unit

		if found_unit is None:
			return 1

		self.render_fit(found_unit, location, box)
		return 0

	def render_fit(self, unit: ImageObject, location: list[int], box: tuple[int, int]) -> None:
		"""Render a cached unit scaled to fit the given box.

		Unlike render(), this handles a unit that was made for a different box
		size, e.g. an async hold after a resize."""
		self.temp_dest.x = round(location[0])
		self.temp_dest.y = round(location[1])

		self.temp_dest.w = unit.original_size[0]  # round(box[0])
		self.temp_dest.h = unit.original_size[1]  # round(box[1])

		bh = round(box[1])
		bw = round(box[0])

		if self.prefs.zoom_art:
			self.temp_dest.w, self.temp_dest.h = fit_box((unit.original_size[0], unit.original_size[1]), box)
		else:
			# Constrain image to given box
			if self.temp_dest.w > bw:
				self.temp_dest.w = bw
				self.temp_dest.h = int(bw * (unit.original_size[1] / unit.original_size[0]))

			if self.temp_dest.h > bh:
				self.temp_dest.h = bh
				self.temp_dest.w = int(self.temp_dest.h * (unit.original_size[0] / unit.original_size[1]))

			# prevent scaling larger than original image size
			if self.temp_dest.w > unit.original_size[0] or self.temp_dest.h > unit.original_size[1]:
				self.temp_dest.w = unit.original_size[0]
				self.temp_dest.h = unit.original_size[1]

		# center the image
		self.temp_dest.x = int((box[0] - self.temp_dest.w) / 2) + self.temp_dest.x
		self.temp_dest.y = int((box[1] - self.temp_dest.h) / 2) + self.temp_dest.y

		# render the image
		sdl3.SDL_RenderTexture(self.renderer, unit.texture, None, self.temp_dest)
		self.style_overlay.hole_punches.append(self.temp_dest)

		self.gui.art_drawn_rect = (self.temp_dest.x, self.temp_dest.y, self.temp_dest.w, self.temp_dest.h)

	def open_external(self, track_object: TrackClass) -> int:
		index = track_object.index

		source = self.get_sources(track_object)
		if len(source) == 0:
			return 0

		offset = self.get_offset(track_object.fullpath, source)

		if track_object.is_network:
			self.show_message(_("Saving network images not implemented"))
			return 0
		if source[offset][0] > 0:
			pic = self.get_embed(track_object)
			if not pic:
				self.show_message(_("Image save error."), _("No embedded album art."), mode="warning")
				return 0

			source_image = io.BytesIO(pic)
			im = Image.open(source_image)
			source_image.close()

			ext = "." + im.format.lower()
			if im.format == "JPEG":
				ext = ".jpg"
			target = str(self.cache_directory / "open-image")
			if not os.path.exists(target):
				os.makedirs(target)
			target = os.path.join(target, "embed-" + str(im.height) + "px-" + str(track_object.index) + ext)

			if len(pic) > 30:
				with open(target, "wb") as w:
					w.write(pic)

		else:
			target = source[offset][1]

		if self.windows:
			os.startfile(target)
		elif self.macos:
			subprocess.call(["open", target])
		else:
			subprocess.call(["xdg-open", target])

		return 0

	def cycle_offset(self, track_object: TrackClass, reverse: bool = False) -> int:
		filepath = track_object.fullpath
		sources = self.get_sources(track_object)
		if len(sources) == 0:
			return 0
		parent_folder = os.path.dirname(filepath)
		# Find cached offset
		if parent_folder in self.folder_image_offsets:

			if reverse:
				self.folder_image_offsets[parent_folder] -= 1
			else:
				self.folder_image_offsets[parent_folder] += 1

			self.folder_image_offsets[parent_folder] %= len(sources)
		return 0

	def cycle_offset_reverse(self, track_object: TrackClass) -> None:
		self.cycle_offset(track_object, True)

	def get_offset(self, filepath: str, source: list[tuple[int, str]]) -> int:
		# Check if folder offset already exists, if not, make it
		parent_folder = os.path.dirname(filepath)

		if parent_folder in self.folder_image_offsets:
			# Reset the offset if greater than number of images available
			if self.folder_image_offsets[parent_folder] > len(source) - 1:
				self.folder_image_offsets[parent_folder] = 0
		else:
			self.folder_image_offsets[parent_folder] = 0

		return self.folder_image_offsets[parent_folder]

	def get_embed(self, track: TrackClass):
		# cached = self.embed_cached
		# if cached[0] == track:
		#	#logging.info("used cached")
		#	return cached[1]

		filepath = track.fullpath

		# Use cached file if present
		if self.prefs.precache and self.tauon.cachement:
			path = self.tauon.cachement.get_file_cached_only(track)
			if path:
				filepath = path

		pic = None

		if track.file_ext == "MP3":
			try:
				tag = mutagen.id3.ID3(filepath)
				frame = tag.getall("APIC")
				if frame:
					pic = frame[0].data
			except Exception:
				logging.exception(f"Failed to get tags on file: {filepath}")

			if pic is not None and len(pic) < 30:
				pic = None
		elif track.file_ext == "FLAC":
			with Flac(filepath) as tag:
				tag.read(True)
				if tag.has_picture and len(tag.picture) > 30:
					pic = tag.picture
		elif track.file_ext == "APE":
			with Ape(filepath) as tag:
				tag.read()
				if tag.has_picture and len(tag.picture) > 30:
					pic = tag.picture
		elif track.file_ext == "M4A":
			with M4a(filepath) as tag:
				tag.read(True)
				if tag.has_picture and len(tag.picture) > 30:
					pic = tag.picture
		elif track.file_ext in ("OPUS", "OGG", "OGA"):
			with Opus(filepath) as tag:
				tag.read()
				if tag.has_picture and len(tag.picture) > 30:
					with io.BytesIO(base64.b64decode(tag.picture)) as a:
						a.seek(0)
						image = parse_picture_block(a)
					pic = image

		# self.embed_cached = (track, pic)
		return pic

	def get_source_raw(self, offset: int, sources: list[tuple[int, str]] | int, track: TrackClass, subsource: list[tuple[int, str]] | None = None) -> BytesIO | BinaryIO | None:
		"""Caller has to call .close() on the returned object afterwards"""
		source_image = None

		if subsource is None:
			subsource = sources[offset]

		if subsource[0] == 1:
			# Target is a embedded image\\\
			pic = self.get_embed(track)
			assert pic
			source_image = io.BytesIO(pic)
		elif subsource[0] == 2:
			fetching = False
			try:
				if track.file_ext == "RADIO" and self.pctl.radio_image_bin:
					return self.pctl.radio_image_bin

				cached_path = os.path.join(self.tauon.n_cache_directory, hashlib.md5(track.art_url_key.encode()).hexdigest()[:12])
				if os.path.isfile(cached_path):
					source_image = open(cached_path, "rb")
				else:
					# Negative cache: many thumbnail sizes can queue up for the same
					# art, so a dead server would otherwise be hit once per size
					last_fail = self.net_art_failed.get(track.art_url_key)
					if last_fail is not None and time.monotonic() - last_fail < 120:
						return None
					fetching = True
					if track.file_ext == "SUB":
						source_image = self.tauon.subsonic.get_cover(track)
					elif track.file_ext == "JELY":
						source_image = self.tauon.jellyfin.get_cover(track)
					else:
						response = urllib.request.urlopen(self.tauon.get_network_thumbnail_url(track), context=self.tls_context)
						source_image = io.BytesIO(response.read())
					if source_image:
						with Path(cached_path).open("wb") as file:
							file.write(source_image.read())
						source_image.seek(0)
						self.net_art_failed.pop(track.art_url_key, None)
					else:
						self.net_art_failed[track.art_url_key] = time.monotonic()
			except Exception:
				if fetching:
					self.net_art_failed[track.art_url_key] = time.monotonic()
				logging.exception("Failed to get source")
		else:
			source_image = open(subsource[1], "rb")

		return source_image

	def get_base64(self, track: TrackClass, size):
		# Wait if an identical track is already being processed
		if self.processing64on == track:
			t = 0
			while True:
				if self.processing64on is None:
					break
				time.sleep(0.05)
				t += 1
				if t > 20:
					break

		cached = self.base64cache
		if track == cached[0] and size == cached[1]:
			return cached[2]

		self.processing64on = track

		filepath = track.fullpath
		sources = self.get_sources(track)

		if len(sources) == 0:
			self.processing64on = None
			return False

		offset = self.get_offset(filepath, sources)

		# Get source IO
		source_image = self.get_source_raw(offset, sources, track)

		if source_image is None:
			self.processing64on = None
			return ""

		im = Image.open(source_image)
		if im.mode != "RGB":
			im = im.convert("RGB")
		im.thumbnail(size, Image.Resampling.LANCZOS)
		buff = io.BytesIO()
		im.save(buff, format="JPEG")
		sss = base64.b64encode(buff.getvalue())

		self.base64cache = (track, size, sss)
		self.processing64on = None
		return sss

	def get_background(self, track: TrackClass) -> BytesIO | BufferedReader | None:
		#logging.info("Find background...")
		# Determine artist name to use
		artist = get_artist_safe(track)
		if not artist:
			return None

		# Check cache for existing image
		path = os.path.join(self.b_cache_directory, artist)
		if os.path.isfile(path):
			logging.info("Load cached background")
			return open(path, "rb")

		# Try last.fm background
		path = self.tauon.artist_info_box.get_data(artist, get_img_path=True)
		if os.path.isfile(path):
			logging.info("Load cached background lfm")
			return open(path, "rb")

		# Check we've not already attempted a search for this artist
		if artist in self.prefs.failed_background_artists:
			return None

		# Get artist MBID
		try:
			s = musicbrainzngs.search_artists(artist, limit=1)
			artist_id = s["artist-list"][0]["id"]
		except Exception:
			logging.exception(f"Failed to find artist MBID for: {artist}")
			self.prefs.failed_background_artists.append(artist)
			return None

		# Search fanart.tv for background
		try:
			r = requests.get(
				"https://webservice.fanart.tv/v3/music/" \
				+ artist_id + "?api_key=" + self.prefs.fatvap, timeout=(4, 10))

			artlink = r.json()["artistbackground"][0]["url"]

			response = urllib.request.urlopen(artlink, context=self.tls_context)
			info = response.info()

			assert info.get_content_maintype() == "image"

			t = io.BytesIO()
			t.seek(0)
			t.write(response.read())
			t.seek(0, 2)
			l = t.tell()
			t.seek(0)

			assert l > 1000

			# Cache image for future use
			path = os.path.join(self.a_cache_directory, artist + "-ftv-full.jpg")
			with open(path, "wb") as f:
				f.write(t.read())
			t.seek(0)
			return t

		except Exception:
			logging.exception(f"Failed to find fanart background for: {artist}")
			if not self.gui.artist_info_panel:
				self.tauon.artist_info_box.get_data(artist)
				path = self.tauon.artist_info_box.get_data(artist, get_img_path=True)
				if os.path.isfile(path):
					logging.debug("Downloaded background lfm")
					return open(path, "rb")


			self.prefs.failed_background_artists.append(artist)
			return None

	def get_blur_im(self, track: TrackClass) -> BytesIO | bool | None:
		source_image = None
		self.loaded_bg_type = 0
		if self.prefs.enable_fanart_bg:
			source_image = self.get_background(track)
			if source_image:
				self.loaded_bg_type = 1

		if source_image is None:
			filepath = track.fullpath
			sources = self.get_sources(track)

			if len(sources) == 0:
				return False

			offset = self.get_offset(filepath, sources)

			source_image = self.get_source_raw(offset, sources, track)

		if source_image is None:
			return None

		im = Image.open(source_image)

		ox_size = im.size[0]
		oy_size = im.size[1]

		format = im.format
		if im.format == "JPEG":
			format = "JPG"

		#logging.info(im.size)
		if im.mode != "RGB":
			im = im.convert("RGB")

		ratio = self.window_size[0] / ox_size
		ratio += 0.2

		if (oy_size * ratio) - ((oy_size * ratio) // 4) < self.window_size[1]:
			logging.info("Adjust bg vertical")
			ratio = self.window_size[1] / (oy_size - (oy_size // 4))
			ratio += 0.2

		new_x = round(ox_size * ratio)
		new_y = round(oy_size * ratio)

		im = im.resize((new_x, new_y))

		if self.loaded_bg_type == 1:
			artist = get_artist_safe(track)
			if artist and artist in self.prefs.bg_flips:
				im = im.transpose(Image.FLIP_LEFT_RIGHT)

		if self.gui.mode == GuiMode.MINI:
			blur = self.prefs.art_bg_blur
			if self.prefs.mini_mode_mode == MiniModeMode.SLATE:
				blur = 160
				pix = im.getpixel((new_x // 2, new_y // 4 * 3))
				pixel_sum = sum(pix) / (255 * 3)
				if pixel_sum > 0.6:
					enhancer = ImageEnhance.Brightness(im)
					deduct = 1 - ((pixel_sum - 0.6) * 1.5)
					im = enhancer.enhance(deduct)
					logging.info(deduct)

				self.gui.center_blur_pixel = im.getpixel((new_x // 2, new_y // 4 * 3))

			im = im.filter(ImageFilter.GaussianBlur(blur))
		elif self.prefs.art_bg_frosted:
			# Frosted glass / sandblasted: heavy blur, mute the colour, then
			# add fine monochrome grain (noise is mean-128, so adding with
			# -128 offset leaves brightness unchanged)
			im = im.filter(ImageFilter.GaussianBlur(max(self.prefs.art_bg_blur, 60)))
			im = ImageEnhance.Color(im).enhance(0.7)
			grain = Image.effect_noise(im.size, 10).convert("L")
			grain = Image.merge("RGB", (grain, grain, grain))
			im = ImageChops.add(im, grain, 1.0, -128)
		elif ox_size < 500:
			# Clear look; still soften low-res art to hide scaling artifacts
			im = im.filter(ImageFilter.GaussianBlur(self.prefs.art_bg_blur))


		self.gui.center_blur_pixel = im.getpixel((new_x // 2, new_y // 2))

		# Keep a small copy for sampling local colour under UI elements
		self.style_overlay.sample_source = im.resize((64, 40)).convert("RGB")

		g = io.BytesIO()
		g.seek(0)

		a_channel = Image.new("L", im.size, 255)  # 'L' 8-bit pixels, black and white
		im.putalpha(a_channel)

		im.save(g, "PNG")
		g.seek(0)

		# source_image.close()

		return g

	def save_thumb(self, track_object: TrackClass, size: tuple[int, int], save_path: str | None, png: bool = False, zoom: bool = False) -> BytesIO | bool | None:
		filepath = track_object.fullpath
		sources = self.get_sources(track_object)

		if len(sources) == 0:
			logging.error("Error thumbnailing; no source images found")
			return False

		offset = self.get_offset(filepath, sources)
		source_image = self.get_source_raw(offset, sources, track_object)

		im = Image.open(source_image)
		if im.mode != "RGB":
			im = im.convert("RGB")

		if not zoom:
			im.thumbnail(size, Image.Resampling.LANCZOS)
		else:
			w, h = im.size
			if w != h:
				m = min(w, h)
				im = im.crop((
					(w - m) / 2,
					(h - m) / 2,
					(w + m) / 2,
					(h + m) / 2,
				))

			im = im.resize(size, Image.Resampling.LANCZOS)

		if not save_path:
			g = io.BytesIO()
			g.seek(0)
			if png:
				im.save(g, "PNG")
			else:
				im.save(g, "JPEG")
			g.seek(0)
			return g

		if png:
			im.save(save_path + ".png", "PNG")
		else:
			im.save(save_path + ".jpg", "JPEG")
		return None

	def display(self, track: TrackClass, location: list[int], box: tuple[int, int], fast: bool = False, theme_only: bool = False, async_hold: bool = False, caller_id: str | None = None) -> int | None:
		"""Draw the art for the given track at location, sized to fit box.

		Without async_hold this always blocks to return the requested art.
		With async_hold, uncached images are loaded and resized on a worker
		thread while the art this caller last displayed is held on screen (no
		blank flash). Only use it for a live UI display box; thumbnailers etc.
		want the synchronous result. Callers passing async_hold should pass a
		unique caller_id so their previous art can be tracked for the hold.
		"""
		# A non-positive box (can happen for a very short/narrow Custom Layout
		# segment) would crash the PIL thumbnail/resize, so skip drawing.
		if box[0] <= 0 or box[1] <= 0:
			return None
		index = track.index
		filepath = track.fullpath

		if self.prefs.colour_from_image and track.album != self.gui.theme_temp_current and box[0] != 115:
			if track.album in self.gui.temp_themes:
				self.tauon.colours.__dict__.update(self.gui.temp_themes[track.album].__dict__)
				self.gui.theme_temp_current = track.album

		source = self.get_sources(track)

		if len(source) == 0:
			if caller_id:
				self.caller_history.pop(caller_id, None)  # No art means blank; don't hold this later
			return 1

		offset = self.get_offset(filepath, source)

		if not theme_only:
			# Check cache; any unit of the same source image at the same size will do
			for unit in self.image_cache:
				if unit.source == source[offset][1] and unit.request_size == box:
					self.touch_cache_unit(unit)
					self.render(unit, location)
					if caller_id:
						self.caller_history[caller_id] = unit
					return 0

			if fast:
				return self.fast_display(track.index, location, box, source, offset)

		if async_hold and not theme_only:
			return self.display_async(track, location, box, source, offset, index, caller_id)

		# Load and render, blocking
		r = self.load_art_image(track, source, offset, theme_only)
		if not isinstance(r, tuple):
			return r
		im, o_size, image_format = r

		try:
			if theme_only:
				self.extract_art_theme(im, track, box)
				return None

			g, o_size = self.resize_art_image(im, o_size, box)
			self.extract_art_theme(im, track, box)
			unit = self.create_unit_and_render(g, o_size, image_format, index, offset, box, source, location)
			if caller_id:
				self.caller_history[caller_id] = unit

			# temp fix
			self.inp.quick_drag = False
			self.gui.move_on_title = False
			self.gui.playlist_hold = False

		except Exception:
			logging.exception("Image display error")
			logging.error(f"-- Associated track: {track.fullpath}")  # noqa: TRY400
			return 1
		return 0

	def display_async(self, track: TrackClass, location: list[int], box: tuple[int, int], source: list[tuple[int, str]], offset: int, index: int, caller_id: str | None) -> int | None:
		"""Non-blocking version of the display() slow path.

		The source image is loaded and resized on a worker thread; one disk
		load is shared by every size requested of the same art. While that is
		in flight, the art this caller last displayed is held on screen so
		there is no blank flash. If the load fails we go straight to blank.
		"""
		load_key = (source[offset][1], offset)
		key = (source[offset][1], offset, box)
		now = time.monotonic()
		with self.async_lock:
			# Drop entries nothing came back for (e.g. sizes requested mid window-resize)
			for k, r in list(self.async_results.items()):
				if now - r[3] > 5:
					r[0].close()
					del self.async_results[k]
			for k, t in list(self.async_failed.items()):
				if now - t > 10:  # Allow an eventual retry
					del self.async_failed[k]

			if key in self.async_failed:
				if caller_id:
					self.caller_history.pop(caller_id, None)
				return 1  # The load failed; show blank

			pickup = self.async_results.pop(key, None)
			if pickup is None:
				boxes = self.async_loads.get(load_key)
				if boxes is not None:
					boxes.add(box)  # This art is already loading; have that load also make our size
				elif len(self.async_loads) < 3:
					self.async_loads[load_key] = {box}
					shoot = threading.Thread(
						target=self.async_prepare,
						args=(track, source, offset, load_key))
					shoot.daemon = True
					shoot.start()

				# Hold the art this caller last displayed while the new image loads
				if caller_id:
					held = self.caller_history.get(caller_id)
					if held is not None and held in self.image_cache:
						self.touch_cache_unit(held)
						if held.request_size == box:
							self.render(held, location)
						else:
							self.render_fit(held, location, box)
						return 0
				return None

		g, o_size, image_format, unused = pickup
		try:
			unit = self.create_unit_and_render(g, o_size, image_format, index, offset, box, source, location)
			if caller_id:
				self.caller_history[caller_id] = unit
		except Exception:
			logging.exception("Image display error")
			logging.error(f"-- Associated track: {track.fullpath}")  # noqa: TRY400
			return 1
		return 0

	def async_prepare(self, track: TrackClass, source: list[tuple[int, str]], offset: int, load_key: tuple) -> None:
		"""Load an art image once off the UI thread, then produce every size
		requested of it from that single load (see display_async)"""
		r = self.load_art_image(track, source, offset, in_worker=True)
		if not isinstance(r, tuple):
			# Load failed; mark every size that was waiting on it as failed
			now = time.monotonic()
			with self.async_lock:
				for b in self.async_loads.pop(load_key, ()):
					self.async_failed[(load_key[0], load_key[1], b)] = now
			self.gui.request_frame()
			return

		im, o_size, image_format = r
		themed = False
		try:
			while True:
				with self.async_lock:
					boxes = self.async_loads.get(load_key)
					if not boxes:
						self.async_loads.pop(load_key, None)
						break
					# Peek rather than pop, so a repeat request while we resize
					# sees the job still pending instead of starting another
					b = next(iter(boxes))
				g, sized_o_size = self.resize_art_image(im, o_size, b)
				if not themed:
					self.extract_art_theme(im, track, b)
					themed = True
				with self.async_lock:
					if load_key not in self.async_loads:  # clear_cache() happened; result is stale
						g.close()
						break
					self.async_results[(load_key[0], load_key[1], b)] = (g, sized_o_size, image_format, time.monotonic())
					self.async_loads[load_key].discard(b)
				self.gui.request_frame()
		except Exception:
			logging.exception("Error preparing image sizes")
			now = time.monotonic()
			with self.async_lock:
				for b in self.async_loads.pop(load_key, ()):
					self.async_failed[(load_key[0], load_key[1], b)] = now
		self.gui.request_frame()

	def load_art_image(self, track: TrackClass, source: list[tuple[int, str]], offset: int, theme_only: bool = False, in_worker: bool = False) -> tuple[ImageFile, tuple[int, int], str] | int | None:
		"""Fetch and decode the source image; this is the one disk (or network)
		load per art, which resize_art_image() can then be run against several
		times.

		Returns (image, original size, format) on success, or an int/None
		result code for display() to pass through. This is the slow part of
		display(); with in_worker it runs on a thread (see display_async).
		"""
		index = track.index
		try:
			# Get source IO
			if source[offset][0] == 1:
				# Target is a embedded image
				# source_image = io.BytesIO(self.get_embed(track))
				source_image = self.get_source_raw(0, 0, track, source[offset])

			elif source[offset][0] == 2:
				idea = self.prefs.encoder_output / encode_folder_name(track) / "cover.jpg"
				if idea.is_file():
					source_image = idea.open("rb")
				else:
					try:
						# We want to download the image asynchronously as to not block the UI
						if self.downloaded_image and self.downloaded_track == track:
							source_image = self.downloaded_image

						elif in_worker:
							# Already off the UI thread, just download here
							self.download_in_progress = True
							try:
								self.async_download_image(track, source[offset])
							finally:
								self.download_in_progress = False
							if self.downloaded_track != track:
								return None
							assert self.downloaded_image
							source_image = self.downloaded_image

						elif self.download_in_progress:
							return 0

						else:
							self.download_in_progress = True
							shoot_dl = threading.Thread(
								target=self.async_download_image,
								args=([track, source[offset]]))
							shoot_dl.daemon = True
							shoot_dl.start()

							# We'll block with a small timeout to avoid unwanted flashing between frames
							s = 0
							while self.download_in_progress:
								s += 1
								time.sleep(0.01)
								if s > 20:  # 200 ms
									break

							if self.downloaded_track != track:
								return None

							assert self.downloaded_image
							source_image = self.downloaded_image

					except Exception:
						logging.exception("IMAGE NETWORK LOAD ERROR")
						raise
			else:
				# source_image = open(source[offset][1], 'rb')
				source_image = self.get_source_raw(0, 0, track, source[offset])

			im = Image.open(source_image)
			o_size = im.size

			format = im.format

			try:
				if im.format == "JPEG":
					format = "JPG"

				if im.mode != "RGB":
					im = im.convert("RGB")
			except Exception:
				logging.exception("Failed to convert image")
				if theme_only:
					if not track.is_network:
						source_image.close()
					return None
				im = Image.open(str(self.install_directory / "assets" / "load-error.png"))
				o_size = im.size

			im.load()  # Force the full decode now so the source stream can be closed
			if not track.is_network:
				source_image.close()

		except Exception:
			logging.exception("Image load error")
			logging.error(f"-- Associated track: {track.fullpath}")  # noqa: TRY400

			try:
				del self.source_cache[index][offset]
			except Exception:
				logging.exception(" -- Error, no source cache?")
			return 1
		return im, o_size, format

	def resize_art_image(self, im: ImageFile, o_size: tuple[int, int], box: tuple[int, int]) -> tuple[BytesIO, tuple[int, int]]:
		"""Resize a loaded image to fit box and encode it ready for texture upload.

		Non-destructive, so several sizes can be made from a single load.
		Returns (BMP data, original size)."""
		try:
			if self.prefs.zoom_art:
				new_size = fit_box(o_size, box)
			else:
				# Fit within box, preserving aspect, never upscaling
				scale = min(box[0] / o_size[0], box[1] / o_size[1], 1)
				new_size = (max(1, round(o_size[0] * scale)), max(1, round(o_size[1] * scale)))
			im = im.resize(new_size, Image.Resampling.LANCZOS)
		except Exception:
			logging.exception("Failed to resize image")
			im = Image.open(str(self.install_directory / "assets" / "load-error.png"))
			o_size = im.size
			if self.prefs.zoom_art:
				im = im.resize(fit_box(o_size, box), Image.Resampling.LANCZOS)
			else:
				im.thumbnail((box[0], box[1]), Image.Resampling.LANCZOS)

		g = io.BytesIO()
		im.save(g, "BMP")
		g.seek(0)
		return g, o_size

	def extract_art_theme(self, im: ImageFile, track: TrackClass, box: tuple[int, int]) -> None:
		"""Set theme colours from the image (the "Carbon" theme and the
		"colour from image" setting).

		Pass the original full-size image (colours are sampled from an internal
		copy of it, so results don't vary with the display size). Best effort:
		on failure the theme is simply left unchanged.
		"""
		try:
			# Processing for "Carbon" theme
			if track == self.pctl.playing_object() and self.gui.theme_name == "Carbon" and track.parent_folder_path != self.colours.last_album:
				# Find main image colours
				_im_theme = im.copy()
				_im_theme.thumbnail((50, 50), Image.Resampling.LANCZOS)
				try:
					pixels = _im_theme.getcolors(maxcolors=2500)
				except Exception:
					logging.exception("theme gen error")
					return
				pixels = sorted(pixels, key=lambda x: x[0], reverse=True)[:]
				colour = pixels[0][1]

				# Try and find a colour that is not grayscale
				for c in pixels:
					cc = c[1]
					av = sum(cc) / 3
					if abs(cc[0] - av) > 10 or abs(cc[1] - av) > 10 or abs(cc[2] - av) > 10:
						colour = cc
						break

				h_colour = rgb_to_hls(colour[0], colour[1], colour[2])

				l = .51
				s = .44

				hh = h_colour[0]
				if 0.14 < hh < 0.3:  # Yellow and green are hard to read text on, so lower the luminance for those
					l = .45
				if check_equal(colour):  # Default to theme purple if source colour was grayscale
					hh = 0.72

				self.colours.bottom_panel_colour = hls_to_rgb(hh, l, s)
				self.colours.last_album = track.parent_folder_path

			# Processing for "Auto-theme" setting
			if self.prefs.colour_from_image and box[0] != 115 and track.album != self.gui.theme_temp_current \
					and track.album not in self.gui.temp_themes:  # and pctl.master_library[index].parent_folder_path != colours.last_album: #mark2233
				self.colours.last_album = track.parent_folder_path

				_im_theme = im.copy()
				_im_theme.thumbnail((50, 50), Image.Resampling.LANCZOS)

				colours = copy.deepcopy(self.colours)

				pixels = _im_theme.getcolors(maxcolors=2500)
				#logging.info(pixels)
				pixels = sorted(pixels, key=lambda x: x[0], reverse=True)[:]
				#logging.info(pixels)

				min_colour_varience = 75

				x_colours: list[ColourRGBA] = []
				for item in pixels:
					colour = item[1]
					for cc in x_colours:
						if abs(
							colour[0] - cc.r) < min_colour_varience and abs(
							colour[1] - cc.g) < min_colour_varience and abs(
							colour[2] - cc.b) < min_colour_varience:
							break
					else:
						x_colours.append(ColourRGBA(colour[0], colour[1], colour[2], 255))

				#logging.info(x_colours)
				colours.playlist_box_background = colours.side_panel_background

				colours.playlist_panel_background = x_colours[0]
				if len(x_colours) > 1:
					colours.side_panel_background = x_colours[1]
					colours.playlist_box_background = colours.side_panel_background
					if len(x_colours) > 2:
						colours.title_text = x_colours[2]
						colours.title_playing = x_colours[2]
						if len(x_colours) > 3:
							colours.artist_text = x_colours[3]
							colours.artist_playing = x_colours[3]
							if len(x_colours) > 4:
								colours.playlist_box_background = x_colours[4]

				colours.queue_background = colours.side_panel_background
				colours.lyrics_panel_background = colours.side_panel_background
				# Check artist text colour
				if contrast_ratio(colours.artist_text, colours.playlist_panel_background) < 1.9:
					black = ColourRGBA(25, 25, 25, 255)
					white = ColourRGBA(220, 220, 220, 255)

					con_b = contrast_ratio(black, colours.playlist_panel_background)
					con_w = contrast_ratio(white, colours.playlist_panel_background)

					choice = black
					if con_w > con_b:
						choice = white

					colours.artist_text = choice
					colours.artist_playing = choice

				# Check title text colour
				if contrast_ratio(colours.title_text, colours.playlist_panel_background) < 1.9:
					black = ColourRGBA(60, 60, 60, 255)
					white = ColourRGBA(180, 180, 180, 255)

					con_b = contrast_ratio(black, colours.playlist_panel_background)
					con_w = contrast_ratio(white, colours.playlist_panel_background)

					choice = black
					if con_w > con_b:
						choice = white

					colours.title_text = choice
					colours.title_playing = choice

				# Check lyrics text colour
				if contrast_ratio(colours.lyrics, colours.lyrics_panel_background) < 1.9:
					black = ColourRGBA(60, 60, 60, 255)
					white = ColourRGBA(180, 180, 180, 255)

					con_b = contrast_ratio(black, colours.lyrics_panel_background)
					con_w = contrast_ratio(white, colours.lyrics_panel_background)

					choice = black
					if con_w > con_b:
						choice = white

					colours.lyrics = choice

				# try to pick high-contrast active lyric color
				contrast = 0
				for i in x_colours:
					temp = contrast_ratio(i, colours.lyrics_panel_background)
					if temp > contrast:
						colours.active_lyric = i
						contrast = temp
				# if there isn't one, just do full black/white
				if contrast_ratio(colours.active_lyric, colours.lyrics_panel_background) < 2.9 or contrast_ratio(colours.active_lyric, colours.lyrics) < 1.9:
					lpb = colours.lyrics_panel_background
					lr  = colours.lyrics
					tc = rgb_to_hls(lpb.r, lpb.g, lpb.b)
					lc = rgb_to_hls(lr.r,  lr.g,  lr.b)

					colours.active_lyric = hls_to_rgb( tc[0]+0.3, lc[1], max(tc[2]*1.5, 0.5) )

				if test_lumi(colours.side_panel_background) < 0.50 and not self.prefs.transparent_mode:
					colours.side_bar_line1 = ColourRGBA(25, 25, 25, 255)
					colours.side_bar_line2 = ColourRGBA(35, 35, 35, 255)
				else:
					colours.side_bar_line1 = ColourRGBA(250, 250, 250, 255)
					colours.side_bar_line2 = ColourRGBA(235, 235, 235, 255)

				colours.album_text = colours.title_text
				colours.album_playing = colours.title_playing

				self.gui.request_tracklist_redraw()

				prcl = 100 - int(test_lumi(colours.playlist_panel_background) * 100)

				if prcl > 45:
					ce = alpha_blend(ColourRGBA(0, 0, 0, 180), colours.playlist_panel_background)  # [40, 40, 40, 255]
					colours.index_text = ce
					colours.index_playing = ce
					colours.time_text = ce
					colours.bar_time = ce
					colours.folder_title = ce
					colours.star_line = ColourRGBA(60, 60, 60, 255)
					colours.row_select_highlight = ColourRGBA(0, 0, 0, 30)
					colours.row_playing_highlight = ColourRGBA(0, 0, 0, 20)
					colours.gallery_background = rgb_add_hls(colours.playlist_panel_background, 0, -0.03, -0.03)
				else:
					ce = alpha_blend(ColourRGBA(255, 255, 255, 160), colours.playlist_panel_background)  # [165, 165, 165, 255]
					colours.index_text = ce
					colours.index_playing = ce
					colours.time_text = ce
					colours.bar_time = ce
					colours.folder_title = ce
					colours.star_line = ce  # ColourRGBA(150, 150, 150, 255)
					colours.row_select_highlight = ColourRGBA(255, 255, 255, 12)
					colours.row_playing_highlight = ColourRGBA(255, 255, 255, 8)
					colours.gallery_background = rgb_add_hls(colours.playlist_panel_background, 0, 0.03, 0.03)

				self.gui.temp_themes[track.album] = copy.deepcopy(colours)
				self.tauon.colours.__dict__.update(self.gui.temp_themes[track.album].__dict__)
				self.gui.theme_temp_current = track.album

				if self.prefs.transparent_mode:
					colours.apply_transparency(full=self.prefs.transparent_mode == 2)

		except Exception:
			logging.exception("Error extracting theme colours from image")

	def touch_cache_unit(self, unit: ImageObject) -> None:
		"""Move a cached unit to the back so eviction stays least-recently-used."""
		try:
			self.image_cache.remove(unit)
		except ValueError:
			return
		self.image_cache.append(unit)

	def create_unit_and_render(self, g: BytesIO, o_size: tuple[int, int], image_format: str, index: int, offset: int, box: tuple[int, int], source: list[tuple[int, str]], location: list[int]) -> ImageObject:
		"""Upload decoded image data as a texture, cache it and render it (main thread only)"""
		s_image = self.ddt.load_image(g)

		c = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)

		tex_w = pointer(c_float(0))
		tex_h = pointer(c_float(0))
		sdl3.SDL_GetTextureSize(c, tex_w, tex_h)

		dst = sdl3.SDL_FRect(round(location[0]), round(location[1]))
		dst.w = int(tex_w.contents.value)
		dst.h = int(tex_h.contents.value)

		# Clean up
		sdl3.SDL_DestroySurface(s_image)
		g.close()

		unit = ImageObject()
		unit.index = index
		unit.texture = c
		unit.rect = dst
		unit.request_size = box
		unit.original_size = o_size
		unit.actual_size = (dst.w, dst.h)
		unit.source = source[offset][1]
		unit.offset = offset
		unit.format = image_format

		self.image_cache.append(unit)

		self.render(unit, location)

		if len(self.image_cache) > 3:
			sdl3.SDL_DestroyTexture(self.image_cache[0].texture)
			del self.image_cache[0]

		return unit

	def render(self, unit, location) -> None:
		rect = unit.rect

		self.gui.art_aspect_ratio = unit.actual_size[0] / unit.actual_size[1]

		rect.x = round(int((unit.request_size[0] - unit.actual_size[0]) / 2) + location[0])
		rect.y = round(int((unit.request_size[1] - unit.actual_size[1]) / 2) + location[1])

		self.tauon.style_overlay.hole_punches.append(rect)

		sdl3.SDL_RenderTexture(self.renderer, unit.texture, None, rect)

		self.gui.art_drawn_rect = (rect.x, rect.y, rect.w, rect.h)

	def clear_cache(self) -> None:
		for unit in self.image_cache:
			sdl3.SDL_DestroyTexture(unit.texture)

		self.image_cache.clear()
		self.source_cache.clear()
		self.downloaded_track = None

		with self.async_lock:
			self.async_loads.clear()  # In-flight workers see their job vanish and stop
			for r in self.async_results.values():
				r[0].close()
			self.async_results.clear()
			self.async_failed.clear()
			self.caller_history.clear()

		self.base64cache = (0, 0, "")
		self.processing64on = None
		self.bin_cached = (None, None, None)
		self.loading_bin = (None, None)
		self.embed_cached = (None, None)

		self.gui.temp_themes.clear()
		self.gui.theme_temp_current = -1
		self.colours.last_album = ""
class GallClass:
	def __init__(self, tauon: _ArtApp, size: int = 250, save_out: bool = True) -> None:
		self.tauon: _ArtApp = tauon
		self.tls_context: ssl.SSLContext = tauon.tls_context
		self.renderer             = tauon.renderer
		self.ddt: TDraw = tauon.ddt
		self.quickthumbnail: QuickThumbnail = tauon.quickthumbnail
		self.folder_image_offsets: dict[str, int] = tauon.folder_image_offsets
		self.g_cache_directory: Path = tauon.g_cache_directory
		self.gui: GuiVar = tauon.gui
		self.prefs: Prefs = tauon.prefs
		self.search_over: _SearchOverlay = tauon.search_over
		self.album_art_gen: AlbumArt = tauon.album_art_gen
		self.size: int = size
		self.gall: dict[
			tuple[TrackClass, int, int],
			list[int | BytesIO | tuple[int, int, int] | None],
		] = {}
		self.queue:    list[tuple[TrackClass, int, int]] = []
		self.key_list: list[tuple[TrackClass, int, int]] = []
		self.save_out: bool = save_out
		self.i: int = 0
		self.lock: threading.LockType = threading.Lock()
		self.limit: int = 60
		self.frame: int = 0
		self.frame_stamp: dict[tuple[TrackClass, int, int], int] = {}

	def new_frame(self) -> None:
		"""Advance the wanted-stamp epoch. Called once at the start of each render pass.

		render() stamps every key it still wants but doesn't have; worker_render
		drops queued keys whose stamp has gone stale, so a resize or fast scroll
		doesn't leave hundreds of no-longer-visible sizes to thumbnail.
		"""
		self.frame += 1
		if not self.frame % 600 and self.frame_stamp:
			# Stamps for keys removed from the queue elsewhere (halt, cache
			# clear, scroll trim) would otherwise linger forever
			self.frame_stamp = {k: v for k, v in self.frame_stamp.items() if self.frame - v < 4}

	def album_art_column_is_shown(self) -> bool:
		return self.gui.set_mode and any(column[0] == "Album Art" for column in self.gui.pl_st)

	def get_file_source(self, track_object: TrackClass) -> tuple[bool, int] | tuple[tuple[int, str], int]:
		sources = self.album_art_gen.get_sources(track_object)

		if len(sources) == 0:
			return False, 0

		offset = self.album_art_gen.get_offset(track_object.fullpath, sources)
		return sources[offset], offset

	@staticmethod
	def border_dominant(image: Image.Image) -> tuple[int, int, int]:
		"""Return a representative dominant colour from an image's edge.

		Edge pixels are grouped into coarse colour buckets before selecting the
		most common one. A modest saturation weight prevents unrelated colours
		from averaging into grey while still allowing genuinely neutral artwork
		to produce a neutral spine.
		"""
		rgb = image if image.mode == "RGB" else image.convert("RGB")
		width, height = rgb.size
		if width < 1 or height < 1:
			return 48, 48, 48
		band = max(1, min(width, height) // 32)
		pixels = rgb.load()
		buckets: dict[tuple[int, int, int], list[int]] = {}

		def add_sample(red: int, green: int, blue: int) -> None:
			key = red // 32, green // 32, blue // 32
			stats = buckets.setdefault(key, [0, 0, 0, 0])
			stats[0] += 1
			stats[1] += red
			stats[2] += green
			stats[3] += blue

		for py in range(band):
			for px in range(width):
				for sample_y in (py, height - 1 - py):
					r, g, b = pixels[px, sample_y]
					add_sample(r, g, b)
		for py in range(band, max(band, height - band)):
			for px in range(band):
				for sample_x in (px, width - 1 - px):
					r, g, b = pixels[sample_x, py]
					add_sample(r, g, b)
		if not buckets:
			return 48, 48, 48

		def bucket_score(stats: list[int]) -> float:
			count, red, green, blue = stats
			average = red / count, green / count, blue / count
			highest = max(average)
			saturation = (highest - min(average)) / max(1.0, highest)
			return count * (0.75 + saturation)

		count, red, green, blue = max(buckets.values(), key=bucket_score)
		return round(red / count), round(green / count), round(blue / count)

	def worker_render(self) -> bool:
		self.lock.acquire()
		# time.sleep(0.1)

		if self.search_over.active:
			while self.quickthumbnail.queue:
				img = self.quickthumbnail.queue.pop(0)
				response = urllib.request.urlopen(img.url, context=self.tls_context)
				source_image = io.BytesIO(response.read())
				img.read_and_thumbnail(source_image, img.size, img.size)
				source_image.close()
				self.gui.request_frame()

		while len(self.queue) > 0:
			source_image = None

			if self.gui.halt_image_rendering:
				self.queue.clear()
				self.frame_stamp.clear()
				break

			self.i += 1

			try:
				# key = self.queue[0]
				key = self.queue.pop(0)
			except Exception:
				logging.exception("thumb queue empty")
				break

			# Flush entries no recent frame asked for (still-wanted keys are
			# re-stamped by render() every pass); if dropped in error the next
			# frame that wants the key just re-queues it
			if self.frame - self.frame_stamp.pop(key, self.frame) > 2:
				continue

			if key not in self.gall:
				order = [1, None, None, None, None]
				self.gall[key] = order
			else:
				order = self.gall[key]

			size = key[1]

			slow_load = False
			cache_load = False

			try:
				if True:
					offset = 0
					parent_folder = key[0].parent_folder_path
					if parent_folder in self.folder_image_offsets:
						offset = self.folder_image_offsets[parent_folder]
					img_name = str(key[2]) + "-" + str(size) + "-" + str(key[0].index) + "-" + str(offset)
					if self.prefs.cache_gallery and (self.g_cache_directory / f"{img_name}.jpg").is_file():
						source_image = (self.g_cache_directory / f"{img_name}.jpg").open("rb")
						# logging.info('load from cache')
						cache_load = True
					else:
						slow_load = True

				if slow_load:
					source, c_offset = self.get_file_source(key[0])

					if source is False:
						order[0] = 0
						self.gall[key] = order
						# del self.queue[0]
						continue

					img_name = str(key[2]) + "-" + str(size) + "-" + str(key[0].index) + "-" + str(c_offset)

					# gall_render_last_timer.set()

					if self.prefs.cache_gallery and (self.g_cache_directory / f"{img_name}.jpg").is_file():
						source_image = (self.g_cache_directory / f"{img_name}.jpg").open("rb")
						logging.info("slow load image")
						cache_load = True

					# elif source[0] == 1:
					#	 #logging.info('tag')
					#	 source_image = io.BytesIO(self.album_art_gen.get_embed(key[0]))
					#
					# elif source[0] == 2:
					#	 try:
					#		 url = tauon.get_network_thumbnail_url(key[0])
					#		 response = urllib.request.urlopen(url)
					#		 source_image = response
					#	 except Exception:
					#		 logging.exception("IMAGE NETWORK LOAD ERROR")
					# else:
					#	 source_image = open(source[1], 'rb')
					source_image = self.album_art_gen.get_source_raw(0, 0, key[0], subsource=source)
				if source_image is None:
					logging.debug(f"Image for {key[0].fullpath} not found")
					continue

				g = io.BytesIO()
				g.seek(0)
				edge_colour = (48, 48, 48)

				if cache_load:
					raw_image = source_image.read()
					g.write(raw_image)
					with Image.open(io.BytesIO(raw_image)) as cached_image:
						edge_colour = self.border_dominant(cached_image)

				else:
					error = False
					try:
						# Process image
						im = Image.open(source_image)
						if im.mode != "RGB":
							im = im.convert("RGB")
						im.thumbnail((size, size), Image.Resampling.LANCZOS)
					except Exception:
						logging.exception("Failed to work with thumbnail")
						im = self.album_art_gen.get_error_img(size)
						error = True

					edge_colour = self.border_dominant(im)
					im.save(g, "BMP")

					if not error and self.save_out and self.prefs.cache_gallery \
					and not (self.g_cache_directory / f"{img_name}.jpg").is_file():
						im.save(str(self.g_cache_directory / f"{img_name}.jpg"), "JPEG", quality=95)

				g.seek(0)

				# source_image.close()

				order = [2, g, None, None, edge_colour]
				self.gall[key] = order

				self.gui.request_frame()
				if self.album_art_column_is_shown():
					self.gui.request_tracklist_redraw()
				if source_image:
					source_image.close()
					source_image = None
				# del self.queue[0]

				time.sleep(0.001)

			except Exception:
				logging.exception(f"Image load failed on track: {key[0].fullpath}")
				order = [0, None, None, None]
				self.gall[key] = order
				self.gui.request_frame()
				# del self.queue[0]

			if size < 150:
				random.shuffle(self.queue)

		if self.i > 0:
			self.i = 0
			return True
		return False

	def render(
			self,
			track: TrackClass,
			location,
			size: int | None = None,
			force_offset: int | None = None,
			max_height: int | None = None,
			return_texture: bool = False,
	) -> bool | tuple[sdl3.LP_SDL_Texture, float, float, tuple[int, int, int]] | None:
		"""Draw an album thumbnail, or return its prepared SDL texture.

		``return_texture`` lets perspective renderers reuse the gallery cache
		without first flattening the image into another render target. It still
		runs the normal asynchronous request/texture-finalisation path; callers
		receive ``None``/``False`` until the thumbnail is ready, then the texture,
		its dimensions and the dominant colour of its outer pixel band.
		"""
		if self.tauon.gallery_load_delay.get() < 0.5:
			return None

		x = round(location[0])
		y = round(location[1])

		# time.sleep(0.1)
		if size is None:
			size = self.size

		size = round(size)

		# offset = self.get_offset(pctl.master_library[index].fullpath, self.get_sources(index))
		if track.parent_folder_path in self.folder_image_offsets:
			offset = self.folder_image_offsets[track.parent_folder_path]
		else:
			offset = 0

		if force_offset is not None:
			offset = force_offset

		key = (track, size, offset)

		if key in self.gall:
			#logging.info("old")

			order = self.gall[key]

			if order[0] == 0:
				# broken
				return False

			if order[0] == 1:
				# not done yet
				return False

			if order[0] == 2:
				# finish processing

				s_image = self.ddt.load_image(order[1])
				c = sdl3.SDL_CreateTextureFromSurface(self.renderer, s_image)
				sdl3.SDL_DestroySurface(s_image)
				sdl3.SDL_SetTextureBlendMode(c, sdl3.SDL_BLENDMODE_BLEND)
				sdl3.SDL_SetTextureScaleMode(c, sdl3.SDL_SCALEMODE_LINEAR)
				tex_w = pointer(c_float(0))
				tex_h = pointer(c_float(0))
				sdl3.SDL_GetTextureSize(c, tex_w, tex_h)
				dst = sdl3.SDL_FRect(x, y)
				dst.w = int(tex_w.contents.value)
				dst.h = int(tex_h.contents.value)


				order[0] = 3
				order[1].close()
				order[1] = None
				order[2] = c
				order[3] = dst
				self.gall[(track, size, offset)] = order

			if order[0] == 3:
				# ready
				order[3].x = x
				order[3].y = y
				order[3].x = int((size - order[3].w) / 2) + order[3].x
				order[3].y = int((size - order[3].h) / 2) + order[3].y

				if not return_texture:
					if max_height is None:
						sdl3.SDL_RenderTexture(self.renderer, order[2], None, order[3])
					else:
						max_height = round(max_height)
						clip_top = y
						clip_bottom = y + max_height
						dst_top = order[3].y
						dst_bottom = order[3].y + order[3].h
						render_top = max(dst_top, clip_top)
						render_bottom = min(dst_bottom, clip_bottom)
						if render_bottom > render_top and order[3].h > 0:
							source_y = ((render_top - dst_top) / order[3].h) * order[3].h
							source_h = ((render_bottom - render_top) / order[3].h) * order[3].h
							source_rect = sdl3.SDL_FRect(0, source_y, order[3].w, source_h)
							dest_rect = sdl3.SDL_FRect(
								order[3].x, render_top, order[3].w, render_bottom - render_top)
							sdl3.SDL_RenderTexture(self.renderer, order[2], source_rect, dest_rect)

				if (track, size, offset) in self.key_list:
					self.key_list.remove((track, size, offset))
				self.key_list.append((track, size, offset))

				# Remove old images to conserve RAM usage
				if len(self.key_list) > self.limit:
					self.gui.request_frame()
					key = self.key_list[0]
					# while key in self.queue:
					#	 self.queue.remove(key)
					if self.gall[key][2] is not None:
						sdl3.SDL_DestroyTexture(self.gall[key][2])
					del self.gall[key]
					del self.key_list[0]

				if return_texture:
					edge_colour = order[4] if len(order) > 4 and order[4] is not None else (48, 48, 48)
					if not isinstance(edge_colour, tuple):
						edge_colour = (48, 48, 48)
					return order[2], order[3].w, order[3].h, edge_colour
				return True
		else:
			self.frame_stamp[key] = self.frame
			if key not in self.queue:
				self.queue.append(key)
				if self.lock.locked():
					try:
						self.lock.release()
					except RuntimeError as e:
						if str(e) == "release unlocked lock":
							logging.error("RuntimeError: Attempted to release already unlocked lock")  # noqa: TRY400
						else:
							logging.exception("Unknown RuntimeError trying to release lock")
					except Exception:
						logging.exception("Unknown error trying to release lock")

		return False
class ThumbTracks:
	def __init__(self, tauon: _ArtApp) -> None:
		self.tauon         = tauon
		self.album_art_gen = tauon.album_art_gen

	def pixbuf(self, track: TrackClass) -> GdkPixbuf | None:
		try:
			source, _offset = self.tauon.gall_ren.get_file_source(track)
			if source is False:  # No art
				return None
			source_image = self.album_art_gen.get_source_raw(0, 0, track, subsource=source)
			with Image.open(source_image) as im:
				if im.mode != "RGB":
					im = im.convert("RGB")
				im.thumbnail((512, 512), Image.Resampling.LANCZOS)
				width, height = im.size
				data = im.tobytes()
			source_image.close()
			return GdkPixbuf.Pixbuf.new_from_data(data, GdkPixbuf.Colorspace.RGB, False, 8, width, height, width * 3)
		except Exception:
			logging.exception("Error create pixbuf of album art")
			return None

	def path(self, track: TrackClass) -> str | None:
		source, offset = self.tauon.gall_ren.get_file_source(track)

		if source is False:  # No art
			return None

		source_type, source_location = source
		source_mtime = ""
		if source_type in (0, 1):
			try:
				source_mtime = str(os.path.getmtime(source_location))
			except OSError:
				source_mtime = str(track.modified_time)

		image_name = f"{source_type}:{source_location}:{offset}:{source_mtime}"
		image_name = hashlib.md5(image_name.encode("utf-8", "replace")).hexdigest()  # noqa: S324 - not a security hash

		t_path = self.tauon.e_cache_directory / f"{image_name}.jpg"

		if t_path.is_file():
			return str(t_path)

		source_image = self.album_art_gen.get_source_raw(0, 0, track, subsource=source)
		with Image.open(source_image) as im:
			if im.mode != "RGB":
				im = im.convert("RGB")
			im.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
			im.save(str(t_path), "JPEG")
		source_image.close()

		return str(t_path)
