# Copyright © 2026, Tauon contributors

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules.t_extra import ColourRGBA
from tauon.t_modules.t_main import TracklistLayoutPanel


def make_panel(set_mode: bool = False, scale: int = 1, coll: bool = False) -> TracklistLayoutPanel:
	panel = TracklistLayoutPanel.__new__(TracklistLayoutPanel)
	panel.gui = SimpleNamespace(scale=scale, set_mode=set_mode, set_bar=True)
	panel.prefs = SimpleNamespace(
		ui_scale=scale, playlist_font_size=15, playlist_row_height=22 * scale, tracklist_y_text_offset=0,
		row_title_genre=False, row_title_format=1, column_album_art_full_height=False, tracklist_scrollbar_left=False)
	panel.tauon = Mock()
	panel.ddt = Mock()
	panel.ddt.get_text_w.side_effect = lambda text, font: len(text) * 10
	panel.fields = Mock()
	panel.coll = lambda rect: coll
	panel.colours = SimpleNamespace(
		menu_highlight_background=ColourRGBA(40, 40, 40, 255),
		menu_text_disabled=ColourRGBA(100, 100, 100, 255))
	panel._bg = ColourRGBA(20, 20, 20, 255)
	panel._text = ColourRGBA(240, 240, 240, 255)
	panel._accent = ColourRGBA(40, 200, 120, 255)
	panel._line_px = 1
	panel.click = False
	return panel


@pytest.mark.parametrize("set_mode", [False, True])
def test_sections_apply_only_to_their_view_mode(set_mode: bool) -> None:
	panel = make_panel(set_mode=set_mode)
	assert panel.section_applies("")
	assert panel.section_applies("columns") is set_mode
	assert panel.section_applies("standard") is not set_mode


def test_track_row_toggles_are_standard_only_and_column_toggles_columns_only() -> None:
	panel = make_panel()
	sections = [section for row in panel.chip_rows() for section in row]
	modes = {title: mode for title, mode, _chips in sections}
	labels = {title: [chip[0] for chip in chips] for title, _mode, chips in sections}
	standard = next(title for title, mode in modes.items() if mode == "standard")
	columns = next(title for title, mode in modes.items() if mode == "columns")
	assert labels[standard] == ["Loves", "Track ratings", "Star hints", "Playcount lines"]
	assert labels[columns] == ["Header bar", "Full album art"]


@pytest.mark.parametrize("scale", [1, 2])
def test_density_matches_presets(scale: int) -> None:
	panel = make_panel(scale=scale)
	assert panel.density() == "thin"
	panel.prefs.playlist_row_height = round(27 * scale)
	assert panel.density() == "thick"
	panel.prefs.playlist_row_height = round(25 * scale)
	assert panel.density() == ""
	panel.prefs.playlist_row_height = round(27 * scale)
	panel.prefs.playlist_font_size = 14
	assert panel.density() == ""


def test_row_height_limits_follow_ui_scale() -> None:
	panel = make_panel(scale=2)
	limits = {attr: (low, high) for _label, attr, low, high in panel.steppers()}
	assert limits["playlist_row_height"] == (30, 90)


def test_flow_wraps_chips_onto_new_lines() -> None:
	panel = make_panel()
	positions, lines = panel.flow(["aaaa", "bbbb", "cc"], 150)
	# widths are text + 28; gaps of 6
	assert positions == [(0, 0, 68), (74, 0, 68), (0, 1, 48)]
	assert lines == 2


@pytest.mark.parametrize("disabled", [False, True])
def test_disabled_chip_ignores_clicks(disabled: bool) -> None:
	panel = make_panel(coll=True)
	panel.click = True
	assert panel._chip((0, 0, 80, 24), "Loves", True, disabled) is (not disabled)


def test_flow_width_is_single_line_width() -> None:
	panel = make_panel()
	assert panel.flow_width(["aaaa", "cc"]) == 68 + 6 + 48
	assert panel.flow_width([]) == 0
