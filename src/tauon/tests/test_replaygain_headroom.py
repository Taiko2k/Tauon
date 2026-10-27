"""ReplayGain peak limiting when compression is not allowed."""

from __future__ import annotations

import pytest

from tauon.t_modules.t_replaygain import PEAK_HEADROOM, replaygain_multiplier


def test_peak_limited_boost_stops_at_minus_one_dbfs() -> None:
	multiplier = replaygain_multiplier(12.0, 0.5, 0.0)
	assert multiplier == pytest.approx(PEAK_HEADROOM / 0.5)
	assert 0.5 * multiplier == pytest.approx(10 ** (-1 / 20))


def test_preamp_boost_without_tags_keeps_unity() -> None:
	# No peak tag means full scale, so the headroom must not cut the track
	assert replaygain_multiplier(None, None, 6.0) == pytest.approx(1.0)


def test_headroom_never_cuts_below_unity() -> None:
	assert replaygain_multiplier(3.0, 0.95, 0.0) == pytest.approx(1.0)
	assert replaygain_multiplier(0.0, 0.95, 0.0) == pytest.approx(1.0)


def test_peak_above_full_scale_still_attenuates() -> None:
	assert replaygain_multiplier(0.0, 1.25, 0.0) == pytest.approx(1 / 1.25)


def test_gain_below_ceiling_is_unchanged() -> None:
	assert replaygain_multiplier(-6.0, 0.9, 0.0) == pytest.approx(10 ** (-6 / 20))
	assert replaygain_multiplier(2.0, 0.5, 0.0) == pytest.approx(10 ** (2 / 20))


def test_compression_allowed_returns_full_gain() -> None:
	assert replaygain_multiplier(12.0, 0.5, 0.0, allow_compression=True) == pytest.approx(10 ** (12 / 20))
