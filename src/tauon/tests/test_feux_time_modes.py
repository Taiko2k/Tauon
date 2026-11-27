"""The Full panel's time readout follows the compact panel's display_time_mode (#2453)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from tauon.t_modules.t_custom import FeuxBar
from tauon.t_modules.t_enums import PlayingState


def bar(mode: int, state: PlayingState = PlayingState.PLAYING) -> SimpleNamespace:
	gui = SimpleNamespace(display_time_mode=mode, dtm3_cum=600, dtm3_total=2400)
	pctl = SimpleNamespace(playing_time=65, playing_length=245, playing_state=state)
	tauon = SimpleNamespace(bottom_bar1=SimpleNamespace(update_dtm3=lambda: None))
	return SimpleNamespace(gui=gui, pctl=pctl, tauon=tauon)


@pytest.mark.parametrize(("mode", "expected"), [
	(0, ("01:05", None)),
	(1, ("-03:00", None)),
	(2, ("01:05", "04:05")),
	(3, ("11:05", "40:00")),
])
def test_each_mode(mode: int, expected: tuple[str, str | None]) -> None:
	assert FeuxBar._time_texts(bar(mode)) == expected


def test_stopped_shows_zero_totals() -> None:
	assert FeuxBar._time_texts(bar(1, PlayingState.STOPPED)) == ("-00:00", None)
	assert FeuxBar._time_texts(bar(2, PlayingState.STOPPED))[1] == "00:00"


def test_stream_has_no_length() -> None:
	assert FeuxBar._time_texts(bar(2, PlayingState.URL_STREAM))[1] == "-- : --"
