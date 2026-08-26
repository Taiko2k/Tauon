# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Upload album art to litterbox.catbox.moe for use as Discord rich presence art.

Discord has no client-side upload API, so local art has to live on a public URL
its media proxy can fetch. Litterbox is used over catbox proper because uploads
expire on their own, so nothing we publish outlives the cache tracking it.

Embedded art is always allowed. A file on disk is only published if its name
looks like cover art and it isn't loose in the user's home, Documents,
Downloads or Pictures folder. Anything rejected falls back to the MusicBrainz
lookup, which publishes nothing
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import os
import threading
import time
from collections import deque
from pathlib import Path
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon, TrackClass

API_URL = "https://litterbox.catbox.moe/resources/internals/api.php"

# Litterbox accepts 1h, 12h, 24h and 72h
RETENTION = "72h"
RETENTION_S = 72 * 60 * 60
# Expire links early so we never hand Discord one that dies mid-display
EXPIRY_MARGIN_S = 30 * 60

# Self-imposed limit, only checked when we actually need to upload
RATE_LIMIT_COUNT = 20
RATE_LIMIT_WINDOW_S = 10 * 60

# Discord renders the large image at a few hundred pixels
MAX_UPLOAD_DIM = 400
JPEG_QUALITY = 88
MAX_SOURCE_BYTES = 40 * 1024 * 1024

CACHE_FILENAME = "litterbox_cache.json"
CACHE_VERSION = 1
CACHE_MAX_ENTRIES = 2000

# Without this, a rejected track is re-read and re-hashed every 25s refresh
NEGATIVE_MEMO_S = 15 * 60

# Matched against the filename after _normalise()
COVER_NAME_HINTS = (
	"cover", "front", "folder", "albumart", "artwork", "jacket", "sleeve",
)


def _normalise(text: str | None) -> str:
	"""Lowercase and strip anything that is not alphanumeric."""
	if not text:
		return ""
	return "".join(c for c in text.lower() if c.isalnum())


def blocked_upload_dirs() -> set[Path]:
	"""Directories whose loose files must never be uploaded."""
	dirs: set[Path] = set()
	try:
		home = Path.home().resolve()
	except Exception:
		return dirs

	dirs.add(home)
	for env_key, default_name in (
		("XDG_DOCUMENTS_DIR", "Documents"),
		("XDG_DOWNLOAD_DIR", "Downloads"),
		("XDG_PICTURES_DIR", "Pictures"),
	):
		value = os.environ.get(env_key)
		if value:
			try:
				dirs.add(Path(os.path.expandvars(value)).expanduser().resolve())
			except Exception:
				logging.debug(f"Could not resolve {env_key} for upload safety check")
		try:
			dirs.add((home / default_name).resolve())
		except Exception:
			logging.debug(f"Could not resolve ~/{default_name} for upload safety check")

	return dirs


def file_is_safe_to_upload(path: str, tr: TrackClass) -> tuple[bool, str]:
	"""Check that an on-disk image is plausibly cover art and not a private file.

	Returns (allowed, reason). The reason is for logging only.
	"""
	try:
		resolved = Path(path).resolve()
	except Exception:
		return False, "path could not be resolved"

	parent = resolved.parent
	if parent in blocked_upload_dirs():
		return False, f"loose file in a protected folder ({parent})"

	name = _normalise(resolved.stem)
	if not name:
		return False, "filename has no usable characters"

	for hint in COVER_NAME_HINTS:
		if hint in name:
			return True, f"filename matches '{hint}'"

	for field in (tr.album, tr.album_artist, tr.artist):
		normalised = _normalise(field)
		# Very short names would match almost anything
		if len(normalised) >= 3 and normalised in name:
			return True, "filename contains the album or artist name"

	return False, "filename does not identify it as cover art"


class LitterboxCache:
	"""Record of uploaded art, persisted across restarts.

	Keyed by a hash of the original image bytes, so the same artwork uploads
	only once whether it was found embedded in a tag or as a file.
	"""

	def __init__(self, user_directory: Path) -> None:
		self.path: Path = Path(user_directory) / CACHE_FILENAME
		self.lock = threading.Lock()
		# image hash -> (url, upload time as epoch seconds)
		self.entries: dict[str, tuple[str, float]] = {}
		# Upload timestamps inside the rate limit window
		self.uploads: deque[float] = deque()
		# (track index, art cycle position) -> time we last refused to upload
		# for it. Keyed on the position too, so cycling the art re-evaluates
		# instead of inheriting the refusal of the image that was showing before
		self.negative: dict[tuple[int, int], float] = {}
		self.loaded: bool = False
		# Set by a failed upload; cached art still works, nothing new is sent
		self.upload_disabled: bool = False

	# --- persistence ---

	def load(self) -> None:
		with self.lock:
			self.loaded = True
			if not self.path.is_file():
				return
			try:
				with self.path.open() as file:
					data = json.load(file)
			except Exception:
				logging.exception("Unknown error loading litterbox_cache.json")
				return

			if not isinstance(data, dict) or data.get("version") != CACHE_VERSION:
				logging.warning("Ignoring litterbox cache with unexpected format")
				return

			entries = data.get("entries")
			if not isinstance(entries, dict):
				return

			for digest, record in entries.items():
				try:
					url = record["url"]
					uploaded_at = float(record["time"])
				except Exception:
					continue
				if isinstance(url, str) and url.startswith("https://"):
					self.entries[digest] = (url, uploaded_at)

			removed = self._prune_locked()
			logging.info(
				f"Loaded {len(self.entries)} litterbox art links ({removed} expired)")

	def save(self) -> None:
		with self.lock:
			if not self.loaded and not self.entries:
				# Don't truncate an existing file we never read
				return
			self._prune_locked()
			payload = {
				"version": CACHE_VERSION,
				"entries": {
					digest: {"url": url, "time": uploaded_at}
					for digest, (url, uploaded_at) in self.entries.items()
				},
			}
			try:
				tmp = self.path.with_suffix(".json.tmp")
				with tmp.open("w") as file:
					json.dump(payload, file)
				tmp.replace(self.path)
			except Exception:
				logging.exception("Failed to save litterbox_cache.json")

	# --- expiry ---

	def _prune_locked(self) -> int:
		"""Drop links that have expired. Caller holds the lock."""
		cutoff = time.time() - (RETENTION_S - EXPIRY_MARGIN_S)
		expired = [d for d, (_, at) in self.entries.items() if at <= cutoff]
		for digest in expired:
			del self.entries[digest]

		# Guard against unbounded growth if retention is ever lengthened
		if len(self.entries) > CACHE_MAX_ENTRIES:
			by_age = sorted(self.entries.items(), key=lambda kv: kv[1][1])
			for digest, _ in by_age[: len(self.entries) - CACHE_MAX_ENTRIES]:
				del self.entries[digest]

		return len(expired)

	def get(self, digest: str) -> str | None:
		with self.lock:
			record = self.entries.get(digest)
			if record is None:
				return None
			url, uploaded_at = record
			if uploaded_at <= time.time() - (RETENTION_S - EXPIRY_MARGIN_S):
				# Gone at litterbox's end, so let the caller upload again
				del self.entries[digest]
				return None
			return url

	def put(self, digest: str, url: str) -> None:
		with self.lock:
			self.entries[digest] = (url, time.time())

	# --- rate limiting ---

	def rate_limit_ok(self) -> bool:
		"""True if an upload is allowed right now. Does not consume budget."""
		now = time.time()
		with self.lock:
			while self.uploads and now - self.uploads[0] > RATE_LIMIT_WINDOW_S:
				self.uploads.popleft()
			return len(self.uploads) < RATE_LIMIT_COUNT

	def record_upload(self) -> None:
		with self.lock:
			self.uploads.append(time.time())

	# --- session kill switch ---

	def disable_uploads(self) -> None:
		"""Stop uploading for the rest of the session after a failure."""
		if not self.upload_disabled:
			self.upload_disabled = True
			logging.warning(
				"Litterbox: upload failed, no further art will be uploaded this "
				"session. Already uploaded art still works, and new art falls "
				"back to Cover Art Archive.")

	# --- per-track refusal memo ---

	def recently_refused(self, index: int, offset: int) -> bool:
		at = self.negative.get((index, offset))
		return at is not None and time.time() - at < NEGATIVE_MEMO_S

	def refuse(self, index: int, offset: int) -> None:
		self.negative[(index, offset)] = time.time()
		if len(self.negative) > 512:
			self.negative.clear()


def current_art_offset(tauon: Tauon, tr: TrackClass) -> int:
	"""The art cycle position the user has selected for this track's folder.

	Read straight out of the shared offsets rather than through
	AlbumArt.get_offset, which writes a clamped value back: a background upload
	has no business moving the position the UI is showing. The value is only
	clamped against the real source list once we have it, in _read_art_bytes.
	"""
	try:
		return int(tauon.folder_image_offsets.get(os.path.dirname(tr.fullpath), 0))
	except Exception:
		return 0


def _read_art_bytes(tauon: Tauon, tr: TrackClass, offset: int) -> tuple[bytes, int, str] | None:
	"""Return (raw image bytes, source type, source path) for a track's art.

	``offset`` is the cycle position to publish, so what Discord shows is the
	image the user cycled to rather than always the first one found. Source type
	is 0 for a file on disk, 1 for art embedded in the tag. Network art (2) is
	skipped, being remote already and usually only LAN reachable.
	"""
	art = tauon.album_art_gen
	try:
		sources = art.get_sources(tr)
	except Exception:
		logging.exception("Litterbox: failed to list art sources")
		return None
	if not sources:
		return None

	if offset < 0 or offset >= len(sources):
		offset = 0

	source_type, source_path = sources[offset][0], sources[offset][1]
	if source_type not in (0, 1):
		return None

	source_image = None
	try:
		source_image = art.get_source_raw(offset, sources, tr)
		if source_image is None:
			return None
		raw = source_image.read()
	except Exception:
		logging.exception("Litterbox: failed to read art source")
		return None
	finally:
		if source_image is not None:
			try:
				source_image.close()
			except Exception:
				pass

	if not raw or len(raw) > MAX_SOURCE_BYTES:
		return None

	return raw, source_type, source_path


def _prepare_upload(raw: bytes) -> bytes | None:
	"""Centre-crop art to a square and re-encode it at a size worth publishing."""
	try:
		from PIL import Image, ImageOps
	except Exception:
		logging.exception("Litterbox: Pillow unavailable")
		return None

	try:
		with Image.open(io.BytesIO(raw)) as im:
			im = im.convert("RGB")
			# ImageOps.fit would happily upscale, so cap the side at the
			# source's shortest edge
			side = min(MAX_UPLOAD_DIM, im.width, im.height)
			im = ImageOps.fit(im, (side, side), Image.Resampling.LANCZOS)
			out = io.BytesIO()
			im.save(out, format="JPEG", quality=JPEG_QUALITY)
	except Exception:
		logging.exception("Litterbox: could not decode art for upload")
		return None

	return out.getvalue()


def _upload(data: bytes, agent: str) -> str | None:
	"POST the art to litterbox, returning the public URL or None."
	try:
		response = requests.post(
			API_URL,
			data={"reqtype": "fileupload", "time": RETENTION},
			files={"fileToUpload": ("cover.jpg", data, "image/jpeg")},
			headers={"User-Agent": agent},
			timeout=30,
		)
	except Exception:
		logging.exception("Litterbox: upload request failed")
		return None

	body = (response.text or "").strip()
	if response.status_code != 200 or not body.startswith("https://"):
		# Litterbox answers every rejection with 412 and puts the reason in the
		# body, e.g. "No files given." or "Bad file type!", so the status alone
		# says nothing about what went wrong
		logging.warning(
			f"Litterbox: upload rejected (HTTP {response.status_code}): {body[:200]!r}")
		return None
	return body


def get_uploaded_art_url(tauon: Tauon, tr: TrackClass) -> str | None:
	"""Return a public URL for this track's art, uploading it if needed.

	The art published is whichever image the folder's cycle position currently
	selects, so the front/back/inlay the user picked is what Discord shows.

	None means the caller should fall back to the MusicBrainz lookup: no local
	art, art we won't publish, the rate limit hit, or an upload having failed
	earlier this session.
	"""
	cache: LitterboxCache = tauon.litterbox
	if not cache.loaded:
		cache.load()

	if getattr(tr, "is_network", False) or tr.file_ext == "RADIO":
		return None

	# Cheap dict read, so the refusal memo below can be per cycle position
	# without paying for a source list and a re-hash on every refresh
	offset = current_art_offset(tauon, tr)
	if cache.recently_refused(tr.index, offset):
		return None

	found = _read_art_bytes(tauon, tr, offset)
	if found is None:
		cache.refuse(tr.index, offset)
		return None
	raw, source_type, source_path = found

	# Hash first, so identical art already up is reused whichever source it came
	# from, without touching the network or the safety checks
	digest = hashlib.sha256(raw).hexdigest()
	cached_url = cache.get(digest)
	if cached_url:
		return cached_url

	# Checked after the cache lookup, so already published art keeps showing
	if cache.upload_disabled:
		cache.refuse(tr.index, offset)
		return None

	if source_type == 0:
		allowed, reason = file_is_safe_to_upload(source_path, tr)
		if not allowed:
			logging.info(f"Litterbox: not uploading {source_path!r} - {reason}")
			cache.refuse(tr.index, offset)
			return None

	if not cache.rate_limit_ok():
		logging.info(
			f"Litterbox: self rate limit reached "
			f"({RATE_LIMIT_COUNT} per {RATE_LIMIT_WINDOW_S // 60} minutes), "
			f"using MusicBrainz art for this track")
		return None

	data = _prepare_upload(raw)
	if data is None:
		cache.refuse(tr.index, offset)
		return None

	cache.record_upload()
	url = _upload(data, tauon.t_agent)
	if url is None:
		cache.disable_uploads()
		cache.refuse(tr.index, offset)
		return None

	cache.put(digest, url)
	logging.info(f"Litterbox: uploaded art for {tr.album or tr.title!r}")
	return url
