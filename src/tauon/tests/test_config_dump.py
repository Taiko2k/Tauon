"""Saving tauon.conf when it's a symlink or read-only (#1630)."""
from __future__ import annotations

import os
import stat
from typing import TYPE_CHECKING

import pytest

from tauon.t_modules.t_config import Config

if TYPE_CHECKING:
	from pathlib import Path


def make_config() -> Config:
	cf = Config()
	cf.add_text("[audio]")
	cf.live.append(["bool", "example", True, ""])
	return cf


def test_dump_writes_file(tmp_path: Path) -> None:
	path = tmp_path / "tauon.conf"
	make_config().dump(str(path))
	assert "example = true" in path.read_text(encoding="utf-8")


def test_dump_writes_through_symlink(tmp_path: Path) -> None:
	real = tmp_path / "dotfiles" / "tauon.conf"
	real.parent.mkdir()
	real.write_text("old", encoding="utf-8")
	link = tmp_path / "tauon.conf"
	link.symlink_to(real)

	make_config().dump(str(link))

	assert link.is_symlink()
	assert "example = true" in real.read_text(encoding="utf-8")


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0, reason="root can write read-only files")
def test_dump_leaves_read_only_file(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
	real = tmp_path / "store" / "tauon.conf"
	real.parent.mkdir()
	real.write_text("managed elsewhere", encoding="utf-8")
	real.chmod(stat.S_IRUSR)
	link = tmp_path / "tauon.conf"
	link.symlink_to(real)

	cf = make_config()
	try:
		cf.dump(str(link))
		cf.dump(str(link))
	finally:
		real.chmod(stat.S_IRUSR | stat.S_IWUSR)

	assert link.is_symlink()
	assert real.read_text(encoding="utf-8") == "managed elsewhere"
	assert not (tmp_path / "tauon.conf.tmp").exists()
	# Logged once, not on every save
	assert sum("read-only" in record.message for record in caplog.records) == 1
