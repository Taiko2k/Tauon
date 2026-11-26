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


def make_shuffle_pctl(*, history: list[int], album_repeat: bool, true_shuffle: bool) -> PlayerCtl:
	"""A shuffling PlayerCtl with the given playback history."""
	pctl = PlayerCtl.__new__(PlayerCtl)
	ids = [10, 11, 12]
	pctl.master_library = {i: SimpleNamespace(index=i, parent_folder_path="/album") for i in ids}
	pctl.multi_playlist = [SimpleNamespace(uuid_int=7, playlist_ids=ids)]
	pctl.prefs = SimpleNamespace(
		resume_on_jump=True, playback_follow_cursor=False, album_shuffle_lock_mode=False, auto_goto_playing=False,
		true_shuffle=true_shuffle, ban_skip_shuffle=False, banned_folders=set())
	pctl.tauon = SimpleNamespace(quick_d_timer=SimpleNamespace(set=Mock()))
	pctl.gui = SimpleNamespace(update_spec=0)
	pctl.active_playlist_playing = 0
	pctl.playlist_playing_position = 0
	pctl.track_queue = list(history)
	pctl.queue_step = 0
	pctl.playing_state = PlayingState.STOPPED
	pctl.playing_time = 0
	pctl.force_queue = []
	pctl.pause_queue = False
	pctl.random_mode = True
	pctl.album_shuffle_mode = False
	pctl.album_repeat_mode = album_repeat
	pctl.repeat_mode = album_repeat
	pctl.shuffle_pools = {}
	played: list[int] = []
	pctl.play_target = Mock(side_effect=lambda **_kwargs: played.append(pctl.track_queue[pctl.queue_step]))
	pctl.played = played
	# Tail of _advance: tracklist and now-playing refreshes
	pctl.active_playlist_viewing = 0
	pctl.show_current = Mock()
	pctl.render_playlist = Mock()
	pctl.refresh_now_playing = Mock()
	pctl.lfm_scrobbler = SimpleNamespace(start_queue=Mock())
	pctl.tauon.notify_song = Mock()
	return pctl


@pytest.mark.parametrize("album_repeat", [False, True])
@pytest.mark.parametrize("true_shuffle", [False, True])
def test_shuffle_with_empty_history_picks_a_track(album_repeat: bool, true_shuffle: bool) -> None:
	# A fresh profile, or every track in the history removed, leaves queue_step at 0
	pctl = make_shuffle_pctl(history=[], album_repeat=album_repeat, true_shuffle=true_shuffle)
	pctl._advance()
	assert len(pctl.played) == 1
	assert pctl.played[0] in pctl.multi_playlist[0].playlist_ids
	assert pctl.track_queue[pctl.queue_step] == pctl.played[0]


def test_shuffle_appends_after_current_track() -> None:
	pctl = make_shuffle_pctl(history=[10], album_repeat=False, true_shuffle=False)
	pctl._advance()
	assert len(pctl.track_queue) == 2
	assert pctl.queue_step == 1
	assert pctl.played == [pctl.track_queue[1]]
