"""Renderer-independent image loading and pixel-buffer conversion."""

from __future__ import annotations

import io
import logging
from ctypes import string_at
from dataclasses import dataclass
from pathlib import Path

from PIL import Image


@dataclass(slots=True)
class ImageData:
	width: int
	height: int
	pixels: bytes


def from_buffer(width: int, height: int, pixels, pitch: int) -> ImageData:
	if isinstance(pixels, (bytes, bytearray, memoryview)):
		data = bytes(pixels)
	else:
		data = string_at(pixels, pitch * height)
	if pitch != width * 4:
		data = b"".join(data[row * pitch:row * pitch + width * 4] for row in range(height))
	return ImageData(width, height, data)


def load(path) -> ImageData:
	if hasattr(path, "value"):
		path = path.value
	if isinstance(path, bytes):
		path = path.decode("utf-8")
	path = Path(path)
	if not path.is_file() and path.parent.name == "scaled-icons":
		unscaled = Path(__file__).resolve().parent.parent / "assets" / path.name
		if unscaled.is_file():
			path = unscaled
	if not path.is_file():
		logging.warning("Image loader could not find %s; using a transparent placeholder", path)
		return ImageData(1, 1, bytes(4))
	if path.suffix.lower() == ".svg":
		import cairo
		from gi import require_version

		require_version("Rsvg", "2.0")
		from gi.repository import Rsvg

		svg = Rsvg.Handle.new_from_file(str(path))
		width = max(1, round(svg.props.width))
		height = max(1, round(svg.props.height))
		surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
		context = cairo.Context(surface)
		viewport = Rsvg.Rectangle()
		viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, width, height
		svg.render_document(context, viewport)
		encoded = io.BytesIO()
		surface.write_to_png(encoded)
		encoded.seek(0)
		with Image.open(encoded) as image:
			rgba = image.convert("RGBA")
			return ImageData(rgba.width, rgba.height, rgba.tobytes())
	with Image.open(path) as image:
		if image.mode != "RGBA":
			image = image.convert("RGBA")
		return ImageData(image.width, image.height, image.tobytes())
