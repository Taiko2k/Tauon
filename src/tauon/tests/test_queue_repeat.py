# Copyright © 2026, Tauon contributors

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules.t_main import PlayerCtl, PlayingState, StopMode

PLAYING, QUEUED = 1, 2


def make_pctl(*, repeat: bool, overrides: bool, queued: bool = True, paused: bool = False) -> PlayerCtl:
	"""A PlayerCtl sitting at the end of track PLAYING, with QUEUED next in the queue."""
	pctl = PlayerCtl.__new__(PlayerCtl)
	track = SimpleNamespace(index=PLAYING, is_network=False, fullpath="/a.flac", start_time=0)
	pctl.prefs = SimpleNamespace(queue_overrides_repeat=overrides, playback_follow_cursor=False)
	pctl.tauon = SimpleNamespace(chrome_mode=False)
	pctl.lfm_scrobbler = SimpleNamespace(a_sc=False, start_queue=Mock())
	pctl.windows_progress = SimpleNamespace(update=Mock())
	pctl.master_library = {PLAYING: track}
	pctl.multi_playlist = [SimpleNamespace(persist_time_positioning=False, playlist_ids=[PLAYING])]
	pctl.active_playlist_playing = 0
	pctl.playlist_playing_position = 0
	pctl.track_queue = [PLAYING]
	pctl.queue_step = 0
	pctl.commit = None
	pctl.ab_repeat_a = pctl.ab_repeat_b = -1
	pctl.playing_state = PlayingState.PLAYING
	pctl.playing_length = 100
	pctl.decode_time = 99.5
	pctl.playing_time = 99.5
	pctl.a_time = 99.5
	pctl.stop_mode = StopMode.OFF
	pctl.repeat_mode = repeat
	pctl.album_repeat_mode = False
	pctl.random_mode = False
	pctl.force_queue = [SimpleNamespace(track_id=QUEUED)] if queued else []
	pctl.pause_queue = paused
	pctl.gui = SimpleNamespace(request_frame=Mock())
	pctl.advance = Mock(return_value=QUEUED)
	pctl.start_commit = Mock()
	return pctl


@pytest.mark.parametrize(("repeat", "overrides", "queued", "paused", "plays_queue"), [
	# Default: the queue beats repeat
	(True, True, True, False, True),
	# Setting off: repeat holds the queue
	(True, False, True, False, False),
	# Setting off, repeat off: the queue advances as normal
	(False, False, True, False, True),
	# A paused or empty queue never plays
	(True, True, True, True, False),
	(False, True, False, False, False),
])
def test_queue_plays_at_end(repeat: bool, overrides: bool, queued: bool, paused: bool, plays_queue: bool) -> None:
	pctl = make_pctl(repeat=repeat, overrides=overrides, queued=queued, paused=paused)
	assert pctl.queue_plays_at_end() is plays_queue


@pytest.mark.parametrize("overrides", [True, False])
def test_track_end_with_repeat_on(overrides: bool) -> None:
	pctl = make_pctl(repeat=True, overrides=overrides)
	pctl.test_progress()
	if overrides:
		pctl.start_commit.assert_called_once_with(QUEUED)
		assert pctl.commit is None
	else:
		# Repeats the playing track and leaves the queue alone
		pctl.start_commit.assert_not_called()
		assert pctl.commit == PLAYING
		assert pctl.playerSubCommand == "repeat"
		assert len(pctl.force_queue) == 1


def test_track_end_with_repeat_off_still_advances_queue() -> None:
	pctl = make_pctl(repeat=False, overrides=False)
	pctl.test_progress()
	pctl.start_commit.assert_called_once_with(QUEUED)
