# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com
"""Volume commands queued for the player thread.

The player has a single command slot, and dragging the volume bar calls
set_volume() on every frame. When a command was already pending, set_volume()
used to fire off a thread that re-sent the volume command a second and two
seconds later — one thread per frame, so a drag left the player chewing
through volume commands long after the mouse was released. The command branch
in the player loop skips the playback branch, so nothing advanced
pctl.playing_time while that went on and the seek bar stopped moving
(issue #2332).

A pending "volume" command reads pctl.player_volume when the player runs it,
so it already carries the newest value and nothing needs deferring.
"""

from __future__ import annotations

import os

os.environ["SDL_DISABLE_METADATA"] = "1"  # Disable metadata method
os.environ["SDL_DOC_GENERATOR"]    = "0"  # Disable doc generation

import pytest

from tauon.t_modules import t_main


class FakePctl:
	"""Just the parts of PlayerCtl that set_volume() touches."""

	set_volume = t_main.PlayerCtl.set_volume

	def __init__(self) -> None:
		self.player_volume = 50
		self.playerCommand = ""
		self.playerCommandReady = False
		self.volume_update_timer = t_main.Timer()
		self.refreshed = 0

	def refresh_now_playing(self) -> None:
		self.refreshed += 1


@pytest.fixture
def shots(monkeypatch) -> list:
	fired: list = []
	monkeypatch.setattr(t_main, "shooter", lambda func, *a, **k: fired.append(func))
	return fired


def test_queues_command_when_player_is_free(shots: list) -> None:
	pctl = FakePctl()
	pctl.set_volume()

	assert (pctl.playerCommand, pctl.playerCommandReady) == ("volume", True)
	assert shots == []


def test_pending_volume_command_is_left_to_carry_the_new_value(shots: list) -> None:
	pctl = FakePctl()
	pctl.set_volume()

	# A drag moves the volume every frame, faster than the player consumes it
	for volume in range(50, 0, -1):
		pctl.player_volume = volume
		pctl.set_volume(notify=False)

	assert (pctl.playerCommand, pctl.playerCommandReady) == ("volume", True)
	assert shots == [], "no deferred re-send should be needed while volume is pending"


def test_other_pending_command_still_defers(shots: list) -> None:
	pctl = FakePctl()
	pctl.playerCommand = "open"
	pctl.playerCommandReady = True

	pctl.set_volume()

	# The open command must not be clobbered; the volume follows it later
	assert (pctl.playerCommand, pctl.playerCommandReady) == ("open", True)
	assert len(shots) == 1


def test_notify_refreshes_now_playing(shots: list) -> None:
	pctl = FakePctl()
	pctl.set_volume(notify=False)
	assert pctl.refreshed == 0
	pctl.set_volume(notify=True)
	assert pctl.refreshed == 1
