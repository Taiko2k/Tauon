# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com
# ruff: noqa: ANN001, ARG004, ARG005, PLW0108, SLF001

from __future__ import annotations

import ctypes
import math
from types import SimpleNamespace

import pytest

from tauon.t_modules import t_custom
from tauon.t_modules.t_custom import (
	SPECTRAL_FLOW_PRESETS,
	SPECTRAL_FLOW_SENSITIVITY,
	SPECTRAL_FLOW_TURBULENCE,
	SPECTRO_PRESETS,
	SPECTROGRAM_BINS,
	SpectrogramWidget,
)
from tauon.t_modules.t_enums import Backend, PlayingState


def test_spectral_flow_presets_keep_prototype_settings() -> None:
	assert [SPECTRO_PRESETS[index][0] for index in sorted(SPECTRAL_FLOW_PRESETS)] == [
		"Flux",
		"Ion",
	]
	assert SPECTRAL_FLOW_SENSITIVITY == 1.75
	assert SPECTRAL_FLOW_TURBULENCE == 1.0
	assert t_custom.SPECTRAL_FLOW_AMPLITUDE[64] > 0.5
	assert SPECTROGRAM_BINS == 512


def test_spectral_flow_field_is_animated_and_non_uniform(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 64
	bins = 48
	values = bytearray(cols * bins)
	for row in range(bins):
		for column in range(cols):
			values[row * cols + column] = round(220 * abs(
				math.sin(column * 0.31 + row * 0.17)))
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", values)
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_filled", cols)
	monkeypatch.setattr(SpectrogramWidget, "_flow_w", 96)
	monkeypatch.setattr(SpectrogramWidget, "_flow_h", 48)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.4)
	monkeypatch.setattr(SpectrogramWidget, "_lut", t_custom.build_spectro_lut(2))
	monkeypatch.setattr(SpectrogramWidget, "_flow_phase", 1.2)
	first = SpectrogramWidget._build_flow_pixels(bins)
	monkeypatch.setattr(SpectrogramWidget, "_flow_phase", 2.2)
	second = SpectrogramWidget._build_flow_pixels(bins)

	assert len(first) == 96 * 48 * 4
	assert len({first[index:index + 4] for index in range(0, len(first), 4)}) > 60
	assert first != second


def test_flow_history_age_zero_samples_the_newest_column(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(SpectrogramWidget, "_cols", 4)
	monkeypatch.setattr(SpectrogramWidget, "_filled", 4)
	monkeypatch.setattr(SpectrogramWidget, "_write", 2)
	monkeypatch.setattr(SpectrogramWidget, "_vals", bytearray((0, 255, 128, 0)))
	assert SpectrogramWidget._sample_flow_history(0.0, 0.0, 1) == pytest.approx(1.0)
	assert SpectrogramWidget._sample_flow_history(1.0, 0.0, 1) < 0.1
	assert SpectrogramWidget._sample_flow_history(99.0, 0.0, 1) == 0.0


def test_flow_source_broadens_sharp_harmonics(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 16
	bins = 32
	values = bytearray(cols * bins)
	for column in range(cols):
		values[24 * cols + column] = 255
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", values)
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_filled", cols)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.0)

	source = SpectrogramWidget._build_flow_source(bins, 16, 16)
	energized_rows = {
		row for row in range(16)
		if max(source[row * 16:(row + 1) * 16]) > 0.07
	}
	assert len(energized_rows) >= 3


def test_full_flow_history_extends_cleanly_to_both_edges(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 32
	bins = 16
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", bytearray((220,)) * (cols * bins))
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_filled", cols)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.65)

	source = SpectrogramWidget._build_flow_source(bins, 64, 12)
	middle_row = 6 * 64

	assert source[middle_row] > 0.5
	assert source[middle_row + 63] > 0.5


def test_first_flow_column_does_not_create_a_leading_wall(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 32
	bins = 16
	values = bytearray(cols * bins)
	for row in range(bins):
		values[row * cols] = 255
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", values)
	monkeypatch.setattr(SpectrogramWidget, "_write", 1)
	monkeypatch.setattr(SpectrogramWidget, "_filled", 1)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.0)

	source = SpectrogramWidget._build_flow_source(bins, 64, 12)

	assert max(source) == 0.0


def test_silent_flow_field_is_exactly_palette_floor(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 32
	bins = 16
	lut = t_custom.build_spectro_lut(2)
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", bytearray(cols * bins))
	monkeypatch.setattr(SpectrogramWidget, "_write", 1)
	monkeypatch.setattr(SpectrogramWidget, "_filled", 1)
	monkeypatch.setattr(SpectrogramWidget, "_flow_w", 48)
	monkeypatch.setattr(SpectrogramWidget, "_flow_h", 20)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.4)
	monkeypatch.setattr(SpectrogramWidget, "_flow_phase", 0.8)
	monkeypatch.setattr(SpectrogramWidget, "_lut", lut)

	pixels = SpectrogramWidget._build_flow_pixels(bins)

	assert {pixels[index:index + 4] for index in range(0, len(pixels), 4)} == {lut[0]}


def test_flow_field_extends_through_vertical_edges(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 64
	bins = 48
	width = 96
	height = 48
	lut = t_custom.build_spectro_lut(2)
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", bytearray((180,)) * (cols * bins))
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_filled", cols)
	monkeypatch.setattr(SpectrogramWidget, "_flow_w", width)
	monkeypatch.setattr(SpectrogramWidget, "_flow_h", height)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.4)
	monkeypatch.setattr(SpectrogramWidget, "_flow_phase", 1.2)
	monkeypatch.setattr(SpectrogramWidget, "_lut", lut)

	pixels = SpectrogramWidget._build_flow_pixels(bins)
	bottom = pixels[(height - 1) * width * 4:]

	assert all(bottom[index:index + 4] != lut[0] for index in range(0, len(bottom), 4))


def test_flow_field_does_not_create_a_hot_oldest_edge(monkeypatch: pytest.MonkeyPatch) -> None:
	cols = 512
	bins = 48
	width = 96
	height = 48
	lut = t_custom.build_spectro_lut(2)
	monkeypatch.setattr(SpectrogramWidget, "_cols", cols)
	monkeypatch.setattr(SpectrogramWidget, "_vals", bytearray((40,)) * (cols * bins))
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_filled", cols)
	monkeypatch.setattr(SpectrogramWidget, "_flow_w", width)
	monkeypatch.setattr(SpectrogramWidget, "_flow_h", height)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.4)
	monkeypatch.setattr(SpectrogramWidget, "_flow_phase", 1.2)
	monkeypatch.setattr(SpectrogramWidget, "_lut", lut)

	pixels = SpectrogramWidget._build_flow_pixels(bins)
	left_mean = sum(
		sum(pixels[(row * width) * 4:(row * width) * 4 + 3]) for row in range(height)
	) / height
	inside_mean = sum(
		sum(pixels[(row * width + 5) * 4:(row * width + 5) * 4 + 3]) for row in range(height)
	) / height

	assert left_mean <= inside_mean


def test_native_flow_texture_matches_prototype_resolution(monkeypatch: pytest.MonkeyPatch) -> None:
	def native_render(*_args: object) -> int:
		return 0

	widget = SpectrogramWidget()
	tauon = SimpleNamespace(
		aud=SimpleNamespace(render_spectral_flow=native_render),
		renderer=object(),
	)
	monkeypatch.setattr(SpectrogramWidget, "_flow_native", None)
	monkeypatch.setattr(SpectrogramWidget, "_flow_native_checked", False)
	monkeypatch.setattr(SpectrogramWidget, "_flow_tex", None)
	monkeypatch.setattr(t_custom.sdl3, "SDL_CreateTexture", lambda *args: object())
	monkeypatch.setattr(t_custom.sdl3, "SDL_SetTextureScaleMode", lambda *args: True)
	monkeypatch.setattr(t_custom.sdl3, "SDL_SetTextureBlendMode", lambda *args: True)

	widget._ensure_flow_texture(tauon, 256, 840, 196)

	assert (SpectrogramWidget._flow_w, SpectrogramWidget._flow_h) == (521, 180)


def test_native_flow_upload_passes_ctypes_buffer_to_sdl(monkeypatch: pytest.MonkeyPatch) -> None:
	uploaded: dict[str, object] = {}

	def native_render(*_args: object) -> int:
		return 0

	def update_texture(_texture, _rect, pixels, pitch) -> bool:
		uploaded["pixels"] = pixels
		uploaded["pitch"] = pitch
		return True

	monkeypatch.setattr(SpectrogramWidget, "_flow_native", native_render)
	monkeypatch.setattr(SpectrogramWidget, "_flow_tex", object())
	monkeypatch.setattr(SpectrogramWidget, "_flow_w", 8)
	monkeypatch.setattr(SpectrogramWidget, "_flow_h", 4)
	monkeypatch.setattr(SpectrogramWidget, "_flow_pixels", None)
	monkeypatch.setattr(SpectrogramWidget, "_flow_palette", None)
	monkeypatch.setattr(SpectrogramWidget, "_flow_palette_buffer", None)
	monkeypatch.setattr(SpectrogramWidget, "_lut", t_custom.build_spectro_lut(2))
	monkeypatch.setattr(SpectrogramWidget, "_vals", bytearray(16 * 8))
	monkeypatch.setattr(SpectrogramWidget, "_cols", 16)
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_filled", 16)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.0)
	monkeypatch.setattr(SpectrogramWidget, "_flow_phase", 0.0)
	monkeypatch.setattr(t_custom.sdl3, "SDL_UpdateTexture", update_texture)

	SpectrogramWidget()._render_flow_texture(8)

	assert isinstance(uploaded["pixels"], ctypes.Array)
	assert uploaded["pitch"] == 8 * 4


class _DrawHarness:
	def __init__(self, state: PlayingState) -> None:
		self.prefs = SimpleNamespace(backend=Backend.PHAZOR, spectrogram_colour=2)
		self.pctl = SimpleNamespace(playing_state=state)
		self.gui = SimpleNamespace(
			spectrogram_bins=8,
			spectrogram_buffers=[],
			scale=1.0,
			delay_frame_calls=0,
		)
		self.gui.delay_frame = lambda delay: setattr(
			self.gui, "delay_frame_calls", self.gui.delay_frame_calls + 1)
		self.gui.request_frame = lambda: None
		self.custom = SimpleNamespace(drag=None, widget_drag=None)
		self.ddt = SimpleNamespace(rect=lambda rect, colour: None)
		self.fields = set()
		self.renderer = None
		self.inp = SimpleNamespace(right_click=False)

	@staticmethod
	def coll(rect) -> bool:
		return False

	@staticmethod
	def is_level_zero(include_menus) -> bool:
		return True

	@staticmethod
	def frame_pace() -> float:
		return 0.01


def test_stopped_flow_drains_then_stops_requesting_frames(monkeypatch: pytest.MonkeyPatch) -> None:
	widget = SpectrogramWidget()
	harness = _DrawHarness(PlayingState.STOPPED)
	harness.gui.spectrogram_buffers = [[1.0] * 8, [2.0] * 8]
	blank_columns = []
	clock = iter((1.0, 1.1))
	monkeypatch.setattr(t_custom.time, "monotonic", lambda: next(clock))
	monkeypatch.setattr(widget, "_ensure", lambda tauon, bins, width, height: None)
	monkeypatch.setattr(widget, "_push_empty_column", lambda bins: blank_columns.append(bins))
	monkeypatch.setattr(widget, "_render_flow_texture", lambda bins: None)
	monkeypatch.setattr(t_custom.sdl3, "SDL_RenderTexture", lambda *args: True)
	monkeypatch.setattr(t_custom.sdl3, "SDL_SetRenderClipRect", lambda *args: True)
	monkeypatch.setattr(t_custom.sdl3, "SDL_SetTextureAlphaMod", lambda *args: True)
	monkeypatch.setattr(t_custom.sdl3, "SDL_SetTextureBlendMode", lambda *args: True)
	monkeypatch.setattr(SpectrogramWidget, "_lut_preset", 2)
	monkeypatch.setattr(SpectrogramWidget, "_lut", [bytes((7, 3, 1, 255))] * 256)
	monkeypatch.setattr(SpectrogramWidget, "_flow_tex", object())
	monkeypatch.setattr(SpectrogramWidget, "_flow_dirty", True)
	monkeypatch.setattr(SpectrogramWidget, "_filled", 3)
	monkeypatch.setattr(SpectrogramWidget, "_cols", 3)
	monkeypatch.setattr(SpectrogramWidget, "_write", 0)
	monkeypatch.setattr(SpectrogramWidget, "_last_playing_state", PlayingState.PLAYING)
	monkeypatch.setattr(SpectrogramWidget, "_last_frame", 0.9)
	monkeypatch.setattr(SpectrogramWidget, "_col_period", 0.02)
	monkeypatch.setattr(SpectrogramWidget, "_frac_accum", 0.0)
	monkeypatch.setattr(SpectrogramWidget, "_drain_remaining", 0)

	widget.draw(harness, 0, 0, 200, 100)
	assert SpectrogramWidget._drain_remaining == 3
	assert harness.gui.spectrogram_buffers == []
	assert harness.gui.delay_frame_calls == 1

	widget.draw(harness, 0, 0, 200, 100)
	assert len(blank_columns) == 3
	assert SpectrogramWidget._drain_remaining == 0
	assert SpectrogramWidget._filled == 0
	assert harness.gui.delay_frame_calls == 1


def test_paused_flow_holds_without_requesting_frames(monkeypatch: pytest.MonkeyPatch) -> None:
	widget = SpectrogramWidget()
	harness = _DrawHarness(PlayingState.PAUSED)
	monkeypatch.setattr(t_custom.time, "monotonic", lambda: 1.0)
	monkeypatch.setattr(widget, "_ensure", lambda tauon, bins, width, height: None)
	monkeypatch.setattr(SpectrogramWidget, "_lut_preset", 2)
	monkeypatch.setattr(SpectrogramWidget, "_lut", [bytes((7, 3, 1, 255))] * 256)
	monkeypatch.setattr(SpectrogramWidget, "_filled", 0)
	monkeypatch.setattr(SpectrogramWidget, "_last_playing_state", PlayingState.PLAYING)
	monkeypatch.setattr(SpectrogramWidget, "_last_frame", 0.9)
	monkeypatch.setattr(SpectrogramWidget, "_drain_remaining", 0)

	widget.draw(harness, 0, 0, 200, 100)
	assert SpectrogramWidget._drain_remaining == 0
	assert harness.gui.delay_frame_calls == 0
