"""ReplayGain calculations shared by the playback backend and tests."""

from __future__ import annotations

import math


def parse_replaygain_db(value: bytes | str) -> float:
	"""Parse a conventional ReplayGain value, including decimal-comma tags."""
	if isinstance(value, bytes):
		value = value.decode("utf-8")
	return float(value.lower().strip().removesuffix("db").strip().replace(",", "."))


def parse_r128_gain(value: bytes | str) -> float:
	"""Convert an R128 Q7.8 gain tag to ReplayGain's -18 LUFS reference."""
	if isinstance(value, bytes):
		value = value.decode("utf-8")
	return float(value.strip()) / 256 + 5


def replaygain_multiplier(gain_db: float | None, peak: float | None, preamp_db: float) -> float:
	"""Convert ReplayGain metadata to a clipping-safe linear multiplier.

	Preamp is global, so missing or malformed gain metadata uses the implicit
	0 dB fallback. Missing or invalid peak metadata is treated as full scale.
	"""
	if gain_db is None or not math.isfinite(gain_db):
		gain_db = 0.0

	multiplier = 10 ** ((gain_db + preamp_db) / 20)
	valid_peak = peak if peak is not None and math.isfinite(peak) and peak > 0 else 1.0
	return min(multiplier, 1 / valid_peak)
