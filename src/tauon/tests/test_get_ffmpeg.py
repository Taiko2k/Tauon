# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com
"""Locating FFmpeg on Windows.

Windows builds bundle a static ffmpeg.exe in the install directory, so
test_ffmpeg() must find it there before offering to download a copy into the
user data directory. A copy the user already downloaded still wins.
"""

from __future__ import annotations

import os

os.environ["SDL_DISABLE_METADATA"] = "1"  # Disable metadata method
os.environ["SDL_DOC_GENERATOR"]    = "0"  # Disable doc generation

from pathlib import Path
from types import SimpleNamespace

import pytest

from tauon.t_modules import t_main


@pytest.fixture
def dirs(tmp_path: Path, monkeypatch) -> SimpleNamespace:
	monkeypatch.setattr(t_main.shutil, "which", lambda _name: None)
	user = tmp_path / "user"
	install = tmp_path / "install"
	user.mkdir()
	install.mkdir()
	return SimpleNamespace(user_directory=user, install_directory=install, windows=True, macos=False)


@pytest.mark.parametrize(("lookup", "exe"), [("get_ffmpeg", "ffmpeg.exe"), ("get_ffprobe", "ffprobe.exe")])
def test_bundled_copy_found(dirs: SimpleNamespace, lookup: str, exe: str) -> None:
	(dirs.install_directory / exe).touch()
	assert getattr(t_main.Tauon, lookup)(dirs) == dirs.install_directory / exe


@pytest.mark.parametrize(("lookup", "exe"), [("get_ffmpeg", "ffmpeg.exe"), ("get_ffprobe", "ffprobe.exe")])
def test_downloaded_copy_preferred(dirs: SimpleNamespace, lookup: str, exe: str) -> None:
	(dirs.install_directory / exe).touch()
	(dirs.user_directory / exe).touch()
	assert getattr(t_main.Tauon, lookup)(dirs) == dirs.user_directory / exe


def test_bundled_copy_skips_download_prompt(dirs: SimpleNamespace) -> None:
	(dirs.install_directory / "ffmpeg.exe").touch()
	prompts: list[str] = []
	dirs.get_ffmpeg = lambda: t_main.Tauon.get_ffmpeg(dirs)
	dirs.show_message = lambda text, **_kwargs: prompts.append(text)
	assert t_main.Tauon.test_ffmpeg(dirs) is True
	assert prompts == []


def test_nothing_found_prompts(dirs: SimpleNamespace) -> None:
	prompts: list[str] = []
	dirs.get_ffmpeg = lambda: t_main.Tauon.get_ffmpeg(dirs)
	dirs.show_message = lambda text, **_kwargs: prompts.append(text)
	dirs.gui = SimpleNamespace()
	dirs.download_ffmpeg = lambda _x: None
	assert t_main.Tauon.test_ffmpeg(dirs) is False
	assert len(prompts) == 1
