import math
import shutil
import struct
import time
import wave
from types import SimpleNamespace

import pytest

from tauon.t_modules import t_waveform
from tauon.t_modules.t_waveform import (
	BLOCK_SAMPLES,
	UNZIP,
	Needles,
	Waveform,
	WaveformCache,
	block_rms,
	coverage_quads,
	normalise,
)


def tone(seconds: float, amplitude: float, rate: int = t_waveform.RATE) -> bytes:
	count = round(seconds * rate)
	return struct.pack(
		f"<{count}h",
		*(round(amplitude * 32767 * math.sin(2 * math.pi * 440 * i / rate)) for i in range(count)),
	)


def test_block_rms_ignores_trailing_partial_block():
	pcm = tone(2 * BLOCK_SAMPLES / t_waveform.RATE, 0.5) + b"\x00\x10" * 10
	rms = block_rms(pcm)
	assert len(rms) == 2
	assert rms[0] == pytest.approx(0.5 / math.sqrt(2), abs=0.005)


def test_normalise_is_linear_against_the_loudest_needle():
	assert normalise([0.1, None, 0.4, 0.2]) == [0.25, None, 1.0, 0.5]
	assert normalise([0.1, 0.4], contrast=2) == [pytest.approx(0.0625), 1.0]
	# Near silence isn't scaled up to full height.
	assert normalise([0.0003])[0] < 0.2
	assert normalise([None, None]) == [None, None]


def test_span_is_an_energy_mean_and_waits_for_its_blocks():
	waveform = Waveform(1.0)  # 20 blocks
	assert waveform.span(0, 0.5) is None
	waveform.rms.extend([0.3] * 5 + [0.4] * 5)
	assert waveform.span(0, 0.5) == pytest.approx(math.sqrt((0.09 + 0.16) / 2))
	assert waveform.span(0.5, 0.6) is None
	waveform.done = True
	assert waveform.span(0.9, 1.0) == 0.0


def test_spans_recompute_as_data_arrives():
	waveform = Waveform(1.0)
	waveform.rms.extend([0.5] * 10)
	assert waveform.spans(2) == [0.5, None]
	waveform.rms.extend([0.25] * 10)
	assert waveform.spans(2) == [0.5, 0.25]


def test_span_without_duration_waits_for_the_scan():
	waveform = Waveform(0)
	waveform.rms.extend([0.4, 0.8])
	assert waveform.span(0, 0.5) is None
	waveform.done = True
	assert waveform.span(0, 0.5) == 0.4
	assert waveform.span(0.5, 1.0) == 0.8


def test_needles_unzip_before_rising():
	needles = Needles(duration=1.0)
	needles.layout(1, 3.5, ("a",))
	needles.update([(10.0, 1.0)], now=0.0)
	half, gap = needles.value(0, UNZIP / 2)
	assert half == 3.5
	assert 0 < gap < 1
	half, gap = needles.value(0, UNZIP + 0.1)
	assert gap == 1.0
	assert 3.5 < half < 10
	assert needles.value(0, 1.0) == (10.0, 1.0)


def test_needles_settle_before_closing():
	needles = Needles(duration=1.0)
	needles.layout(1, 3.5, ("a",))
	needles.update([(10.0, 1.0)], now=0.0)
	needles.update([(3.5, 0.0)], now=2.0)
	half, gap = needles.value(0, 2.5)
	assert gap == 1.0
	assert 3.5 < half < 10
	half, gap = needles.value(0, 2.0 + 1 - UNZIP / 2)
	assert half == 3.5
	assert 0 < gap < 1


def test_needles_retarget_from_where_they_are():
	needles = Needles(duration=1.0)
	needles.layout(1, 3.5, ("a",))
	needles.update([(10.0, 1.0)], now=0.0)
	mid = needles.value(0, 0.6)
	assert needles.update([(6.0, 1.0)], now=0.6)
	assert needles.value(0, 0.6) == pytest.approx(mid)
	assert not needles.update([(6.0, 1.0)], now=1.7)


def test_needles_snap_on_geometry_change():
	needles = Needles(duration=1.0)
	needles.layout(2, 3.5, ("a",))
	needles.update([(10.0, 1.0)] * 2, now=0.0)
	needles.layout(3, 3.5, ("b",))
	assert not needles.update([(8.0, 1.0)] * 3, now=5.0)
	assert needles.value(2, 5.0) == (8.0, 1.0)


def test_coverage_quads_whole_pixels_are_one_quad():
	vertices, indices = [], []
	coverage_quads(2, 4, 5, 11, (1, 1, 1, 1), vertices, indices)
	assert len(vertices) == 4
	assert {v[7] for v in vertices} == {1}


def test_coverage_quads_fade_fractional_edges():
	vertices, indices = [], []
	coverage_quads(2, 3.75, 4, 6.5, (1, 1, 1, 0.8), vertices, indices)
	alphas = sorted({round(v[7], 3) for v in vertices})
	# top row 25% covered, middle rows whole, bottom row half
	assert alphas == [0.2, 0.4, 0.8]
	assert len(indices) == 18
	assert min(v[1] for v in vertices) == 3
	assert max(v[1] for v in vertices) == 7


@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="needs FFmpeg")
def test_cache_scans_a_file(tmp_path):
	path = tmp_path / "quiet-loud.wav"
	with wave.open(str(path), "wb") as out:
		out.setnchannels(1)
		out.setsampwidth(2)
		out.setframerate(t_waveform.RATE)
		out.writeframes(tone(1.0, 0.01) + tone(1.0, 0.9))

	frames = []
	tauon = SimpleNamespace(
		get_ffmpeg=lambda: shutil.which("ffmpeg"),
		gui=SimpleNamespace(request_frame=lambda: frames.append(1)),
		wake=lambda: None,
	)
	track = SimpleNamespace(fullpath=str(path), start_time=0, length=2.0, is_network=False, is_cue=False)
	cache = WaveformCache(tauon)
	waveform = cache.get(track)
	assert waveform is not None
	deadline = time.monotonic() + 10
	while not waveform.done and time.monotonic() < deadline:
		time.sleep(0.01)
	assert waveform.done and not waveform.failed
	assert len(waveform.rms) == 40
	quiet, loud = normalise(waveform.spans(2))
	assert loud == 1.0
	assert quiet < 0.05
	assert frames
	assert cache.get(track) is waveform


def test_cache_backs_off_when_source_is_missing(tmp_path):
	calls = []
	tauon = SimpleNamespace(get_ffmpeg=lambda: calls.append(1) or "ffmpeg")
	track = SimpleNamespace(
		fullpath=str(tmp_path / "gone.flac"), start_time=0, length=2.0, is_network=False, is_cue=False)
	cache = WaveformCache(tauon)
	assert cache.get(track) is None
	assert cache.get(track) is None
	assert not calls
	assert cache.thread is None
