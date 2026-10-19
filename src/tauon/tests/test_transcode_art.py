# Copyright © 2026, Tauon contributors
"""Transcoded files can carry the album cover in their tags."""

import os

os.environ["SDL_DISABLE_METADATA"] = "1"
os.environ["SDL_DOC_GENERATOR"] = "0"

import io
import shutil
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest
from PIL import Image

from tauon.t_modules.t_main import Tauon
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_tagedit import TagDocument


def cover() -> io.BytesIO:
	image = io.BytesIO()
	Image.new("RGB", (64, 64), (200, 40, 90)).save(image, "JPEG")
	image.seek(0)
	return image


def make_tauon(image: io.BytesIO | bool) -> Tauon:
	tauon = Tauon.__new__(Tauon)
	tauon.album_art_gen = SimpleNamespace(save_thumb=lambda track, size, save_path: image)
	return tauon


def test_defaults() -> None:
	fields = Prefs.__dataclass_fields__
	assert fields["transcode_embed_art"].default is False
	assert fields["transcode_copy_art"].default is True


@pytest.mark.parametrize("extension", ["mp3", "flac", "opus", "ogg"])
def test_embed_transcode_art(tmp_path: Path, extension: str) -> None:
	ffmpeg = shutil.which("ffmpeg")
	if ffmpeg is None:
		pytest.skip("ffmpeg is needed to generate real audio containers")
	path = tmp_path / f"track.{extension}"
	subprocess.run(
		[ffmpeg, "-v", "error", "-f", "lavfi", "-i", "anullsrc=r=48000:cl=stereo", "-t", "0.5", str(path)],
		check=True,
	)
	image = cover()

	make_tauon(image).embed_transcode_art(SimpleNamespace(), path)

	assert TagDocument(path).artwork() == [image.getvalue()]


def test_embed_without_art_leaves_file(tmp_path: Path) -> None:
	path = tmp_path / "track.flac"
	path.write_bytes(b"not audio")

	make_tauon(False).embed_transcode_art(SimpleNamespace(), path)

	assert path.read_bytes() == b"not audio"
