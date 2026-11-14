# Copyright © 2026, Tauon contributors
"""Album art helpers close the source stream they open."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

import io
from types import SimpleNamespace

import pytest
from PIL import Image

from tauon.t_modules.t_main import AlbumArt


def make_art(size: tuple[int, int]) -> tuple[SimpleNamespace, io.BytesIO]:
	source = io.BytesIO()
	Image.new("RGB", size, (200, 40, 90)).save(source, "JPEG")
	source.seek(0)
	art = SimpleNamespace(
		get_sources=lambda *_: [(0, "cover.jpg")],
		get_offset=lambda *_: 0,
		get_source_raw=lambda *_: source,
	)
	return art, source


# One image bigger than the thumbnail box and one already smaller
@pytest.mark.parametrize("size", [(64, 64), (16, 16)])
def test_save_thumb_closes_source(size: tuple[int, int]) -> None:
	art, source = make_art(size)

	thumb = AlbumArt.save_thumb(art, SimpleNamespace(fullpath="x"), (32, 32), "")

	assert source.closed
	assert Image.open(thumb).size == (min(size[0], 32), min(size[1], 32))


@pytest.mark.parametrize("size", [(64, 64), (16, 16)])
def test_get_base64_closes_source(size: tuple[int, int]) -> None:
	art, source = make_art(size)
	art.processing64on = None
	art.base64cache = (None, None, None)

	assert AlbumArt.get_base64(art, SimpleNamespace(fullpath="x"), (32, 32))
	assert source.closed
