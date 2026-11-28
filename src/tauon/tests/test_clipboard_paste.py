"""Paste picks whichever clipboard changed last: Tauon's track cargo or the system clipboard"""

from __future__ import annotations

import types
from unittest.mock import MagicMock

import pytest

from tauon.t_modules import t_main
from tauon.t_modules.t_main import Tauon


class FakeClipboard:
	def __init__(self, text: str = "") -> None:
		self.text = text


@pytest.fixture
def clipboard(monkeypatch):
	board = FakeClipboard()
	monkeypatch.setattr(t_main, "copy_from_clipboard", lambda: board.text)
	return board


def make_tauon():
	tauon = types.SimpleNamespace(
		pctl=types.SimpleNamespace(
			cargo=[],
			default_playlist=[10, 11, 12],
			selected_in_playlist=0,
			active_playlist_viewing=0,
			multi_playlist=[types.SimpleNamespace(uuid_int=1)],
			pl_to_id=lambda n: n,
		),
		gui=types.SimpleNamespace(shift_selection=[1, 2], lightning_copy=False, request_tracklist_redraw=lambda: None),
		tidal=MagicMock(),
		load_orders=[],
		transfer=MagicMock(),
		append_playlist=MagicMock(),
		copied_track=None,
		cargo_clipboard_hash=None,
		clipboard_hash=Tauon.clipboard_hash,
	)
	tauon.mark_cargo_copied = types.MethodType(Tauon.mark_cargo_copied, tauon)
	return tauon


def test_internal_copy_after_system_clipboard_wins(clipboard):
	tauon = make_tauon()
	clipboard.text = "file:///music/a.flac"
	Tauon.s_copy(tauon)
	Tauon.paste(tauon)
	assert tauon.load_orders == []
	tauon.transfer.assert_called_once()
	assert clipboard.text == "file:///music/a.flac"


@pytest.mark.parametrize("text", ["/music/a.flac", "https://tidal.com/browse/track/123"])
def test_unchanged_path_or_tidal_link_does_not_override_cargo(clipboard, text):
	tauon = make_tauon()
	clipboard.text = text
	Tauon.s_copy(tauon)
	Tauon.paste(tauon)
	assert tauon.load_orders == []
	tauon.tidal.track.assert_not_called()
	tauon.transfer.assert_called_once()


def test_system_clipboard_changed_after_internal_copy_wins(clipboard):
	tauon = make_tauon()
	Tauon.s_copy(tauon)
	clipboard.text = "file:///music/b.flac"
	Tauon.paste(tauon)
	assert len(tauon.load_orders) == 1
	tauon.transfer.assert_not_called()


def test_tidal_link_does_not_also_paste_cargo(clipboard):
	tauon = make_tauon()
	Tauon.s_copy(tauon)
	clipboard.text = "https://tidal.com/browse/track/123"
	Tauon.paste(tauon)
	tauon.tidal.track.assert_called_once_with("123")
	tauon.transfer.assert_not_called()


def test_unimportable_clipboard_falls_back_to_cargo(clipboard):
	tauon = make_tauon()
	Tauon.s_copy(tauon)
	clipboard.text = "just some text"
	Tauon.paste(tauon)
	assert tauon.load_orders == []
	tauon.transfer.assert_called_once()
