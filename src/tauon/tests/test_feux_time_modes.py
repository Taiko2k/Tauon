"""The bottom panels share one time readout for display_time_mode (#2453)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tauon.t_modules.t_enums import PlayingState
from tauon.t_modules.t_extra import get_clock_time
from tauon.t_modules.t_main import BottomBarType1


def bar(mode: int, state: PlayingState = PlayingState.PLAYING, time: float = 65, length: float = 245,
		dtm3_total: float = 2400) -> SimpleNamespace:
	gui = SimpleNamespace(display_time_mode=mode, dtm3_cum=600, dtm3_total=dtm3_total)
	pctl = SimpleNamespace(playing_time=time, playing_length=length, playing_state=state)
	return SimpleNamespace(gui=gui, pctl=pctl, update_dtm3=lambda: None)


def texts(*args, **kwargs) -> tuple[str, str | None]:
	return BottomBarType1.time_texts(bar(*args, **kwargs))


@pytest.mark.parametrize(("mode", "expected"), [
	(0, ("01:05", None)),
	(1, ("-03:00", None)),
	(2, ("01:05", "04:05")),
	(3, ("11:05", "40:00")),
	(4, ("01:05", "-03:00")),
])
def test_each_mode(mode: int, expected: tuple[str, str | None]) -> None:
	assert texts(mode) == expected


def test_stopped_shows_zero_totals() -> None:
	assert texts(1, PlayingState.STOPPED) == ("-00:00", None)
	assert texts(2, PlayingState.STOPPED)[1] == "00:00"
	assert texts(4, PlayingState.STOPPED)[1] == "-00:00"


def test_stream_has_no_length() -> None:
	assert texts(2, PlayingState.URL_STREAM)[1] == "-- : --"


def test_long_track_uses_hours_throughout() -> None:
	assert texts(0, time=65, length=6000) == ("0:01:05", None)
	assert texts(2, time=5999, length=6000) == ("1:39:59", "1:40:00")
	assert texts(4, time=65, length=6000) == ("0:01:05", "-1:38:55")
	assert texts(3, dtm3_total=7200) == ("0:11:05", "2:00:00")


def test_cycle_wraps() -> None:
	b = SimpleNamespace(gui=SimpleNamespace(display_time_mode=4), TIME_MODES=BottomBarType1.TIME_MODES)
	BottomBarType1.next_time_mode(b)
	assert b.gui.display_time_mode == 0


def test_clock_time() -> None:
	assert get_clock_time(5999) == "1:39:59"
	assert get_clock_time(3599.9) == "59:59"
	assert get_clock_time(59, hours=True) == "0:00:59"
	assert get_clock_time(-3) == "00:00"
