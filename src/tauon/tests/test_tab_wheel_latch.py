"""Wheel over the tabs cycles playlists once per event, and keeps cycling when a layout
change moves the panel out from under a still cursor"""

from __future__ import annotations

import types
from unittest.mock import MagicMock

import pytest

from tauon.t_modules import t_main
from tauon.t_modules.t_main import TopPanel


class FakeInput:
	def __init__(self) -> None:
		self.mouse_wheel = 0
		self.wheel_serial = 0
		self.mouse_position = [200, 20]
		self.view_offset = (0, 0)

	def to_screen(self, x, y):
		return (x + self.view_offset[0], y + self.view_offset[1])

	def wheel(self, amount: int) -> None:
		self.mouse_wheel += amount
		self.wheel_serial += 1


@pytest.fixture
def clock(monkeypatch):
	now = [100.0]
	monkeypatch.setattr(t_main.time, "monotonic", lambda: now[0])
	return now


@pytest.fixture
def panel(clock):
	top = TopPanel.__new__(TopPanel)
	top.inp = FakeInput()
	top.gui = types.SimpleNamespace(scale=1, request_tracklist_redraw=lambda: None)
	top.pctl = types.SimpleNamespace(
		multi_playlist=[object(), object(), object()], active_playlist_viewing=0, cycle_playlist_pinned=MagicMock())
	top.prefs = types.SimpleNamespace(tabs_on_top=True)
	top.tauon = MagicMock()
	top.wheel_serial_used = -1
	top.wheel_latch_until = 0.0
	top.wheel_latch_position = (0, 0)
	top.last_shown_tabs = []
	return top


def test_same_event_cycles_once(panel):
	panel.inp.wheel(1)
	panel.wheel_cycle_playlist()
	# Layout change re-renders the panel in the same frame
	panel.wheel_cycle_playlist()
	panel.pctl.cycle_playlist_pinned.assert_called_once_with(1)


def test_latch_keeps_cycling_when_panel_moves_away(panel, clock):
	panel.inp.wheel(1)
	panel.wheel_cycle_playlist()
	panel.inp.mouse_wheel = 0
	clock[0] += 0.1
	panel.inp.wheel(1)
	panel.latched_wheel()
	assert panel.pctl.cycle_playlist_pinned.call_count == 2
	assert panel.inp.mouse_wheel == 0


def test_latch_uses_screen_position_from_reframed_panel(panel, clock):
	panel.inp.view_offset = (0, 300)
	panel.inp.mouse_position = [200, 10]
	panel.inp.wheel(-1)
	panel.wheel_cycle_playlist()
	panel.inp.view_offset = (0, 0)
	panel.inp.mouse_position = [200, 310]
	panel.inp.mouse_wheel = 0
	panel.inp.wheel(-1)
	panel.latched_wheel()
	assert panel.pctl.cycle_playlist_pinned.call_count == 2


def test_latch_released_when_cursor_moves(panel, clock):
	panel.inp.wheel(1)
	panel.wheel_cycle_playlist()
	panel.inp.mouse_wheel = 0
	panel.inp.mouse_position = [200, 400]
	panel.inp.wheel(1)
	panel.latched_wheel()
	panel.pctl.cycle_playlist_pinned.assert_called_once()
	assert panel.inp.mouse_wheel == 1


def test_latch_expires(panel, clock):
	panel.inp.wheel(1)
	panel.wheel_cycle_playlist()
	panel.inp.mouse_wheel = 0
	clock[0] += TopPanel.WHEEL_LATCH_SECONDS + 0.1
	panel.inp.wheel(1)
	panel.latched_wheel()
	panel.pctl.cycle_playlist_pinned.assert_called_once()
	assert panel.inp.mouse_wheel == 1
