# Copyright © 2026, Tauon contributors

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest
import sdl3

from tauon.t_modules import t_main
from tauon.t_modules.t_draw import TDraw
from tauon.t_modules.t_extra import ColourRGBA

if TYPE_CHECKING:
	from collections.abc import Iterator


def make_box(text: str, index: int | None = None) -> t_main.TextBox:
	"""A bare TextBox with the cursor at index (counted from the start)."""
	box = t_main.TextBox.__new__(t_main.TextBox)
	box.text = text
	box.cursor_position = box.selection = len(text) - (len(text) if index is None else index)
	return box


def make_inp(**keys: object) -> t_main.Input:
	inp = t_main.Input(SimpleNamespace())
	for key, value in keys.items():
		setattr(inp, key, value)
	return inp


def cursor(box: t_main.TextBox) -> int:
	return len(box.text) - box.cursor_position


@pytest.fixture(autouse=True)
def not_macos(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(t_main, "macos", False)


@pytest.mark.parametrize(
	("text", "index", "expected"),
	[
		("foo bar", 7, 4),
		("foo bar  ", 9, 4),
		("foo.bar", 7, 4),
		("foo.bar", 4, 0),
		("don't stop", 5, 0),
		("a — b", 5, 4),
		("ab", 0, 0),
	],
)
def test_word_start_before(text: str, index: int, expected: int) -> None:
	assert t_main.word_start_before(text, index) == expected


@pytest.mark.parametrize(
	("text", "index", "expected"),
	[
		("foo bar", 0, 3),
		("foo bar", 3, 7),
		("foo.bar", 3, 7),
		("  foo", 0, 5),
		("ab", 2, 2),
	],
)
def test_word_end_after(text: str, index: int, expected: int) -> None:
	assert t_main.word_end_after(text, index) == expected


def test_ctrl_left_stops_at_word_start_after_punctuation() -> None:
	box = make_box("foo.bar")
	assert t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_left_press=True))
	assert cursor(box) == 4


def test_ctrl_right_moves_to_word_end() -> None:
	box = make_box("foo bar", 0)
	assert t_main.text_edit_shortcuts(box, make_inp(key_rctrl_down=True, key_right_press=True))
	assert cursor(box) == 3


def test_right_shift_extends_selection_by_word() -> None:
	box = make_box("foo bar")
	t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_shiftr_down=True, key_left_press=True))
	assert cursor(box) == 4
	assert box.get_selection() == "bar"


def test_ctrl_backspace_uses_same_word_boundary() -> None:
	box = make_box("foo.bar")
	assert t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, backspace_press=1))
	assert box.text == "foo."
	assert cursor(box) == 4


def test_ctrl_backspace_clears_selection_only() -> None:
	box = make_box("foo bar baz", 11)
	box.selection = 0
	box.cursor_position = 3
	t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, backspace_press=1))
	assert box.text == "foo bar "


def test_ctrl_delete_erases_next_word() -> None:
	box = make_box("foo bar baz", 3)
	assert t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_del=True))
	assert box.text == "foo baz"
	assert cursor(box) == 3


def test_ctrl_delete_can_be_left_to_the_caller() -> None:
	box = make_box("foo bar", 0)
	assert not t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_del=True), delete_key=False)
	assert box.text == "foo bar"


def test_plain_keys_are_not_used() -> None:
	box = make_box("foo bar")
	assert not t_main.text_edit_shortcuts(box, make_inp(key_left_press=True, backspace_press=1))
	assert not t_main.text_edit_shortcuts(box, make_inp(key_shift_down=True, key_left_press=True))


def test_alt_does_nothing_off_macos() -> None:
	box = make_box("foo bar")
	assert not t_main.text_edit_shortcuts(box, make_inp(key_lalt=True, key_left_press=True))


def test_macos_option_moves_by_word(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(t_main, "macos", True)
	box = make_box("foo bar")
	assert t_main.text_edit_shortcuts(box, make_inp(key_lalt=True, key_left_press=True))
	assert cursor(box) == 4
	assert t_main.text_edit_shortcuts(box, make_inp(key_ralt=True, backspace_press=1))
	assert box.text == "bar"


def test_macos_cmd_moves_to_line_ends(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(t_main, "macos", True)
	box = make_box("one\ntwo three\nfour", 9)
	t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_left_press=True))
	assert cursor(box) == 4
	t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_right_press=True))
	assert cursor(box) == 13
	t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, backspace_press=1))
	assert box.text == "one\n\nfour"


def test_stale_cursor_is_clamped() -> None:
	box = make_box("")
	box.cursor_position = box.selection = 9
	t_main.text_edit_shortcuts(box, make_inp(key_ctrl_down=True, key_left_press=True))
	assert box.cursor_position == box.selection == 0


@pytest.fixture
def quick_box(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple]:
	assert sdl3.SDL_Init(0)
	surface = sdl3.SDL_CreateSurface(400, 100, sdl3.SDL_PIXELFORMAT_RGBA32)
	renderer = sdl3.SDL_CreateSoftwareRenderer(surface)
	gui = SimpleNamespace(scale=1, window_size=[400, 100], editline="", cursor_want=0)
	inp = t_main.Input(gui)
	ddt = TDraw(renderer)
	ddt.prime_font("Sans", 10, 13)
	owner = SimpleNamespace(
		gui=gui, inp=inp, ddt=ddt, renderer=renderer, t_window=None, window_size=[400, 100],
		coll=lambda rect: False,
		fields=SimpleNamespace(add=Mock()),
		field_menu=SimpleNamespace(active=False, activate=Mock()),
		animate_monitor_timer=Mock(),
		set_text_input_area=lambda *args: None,
	)
	box = t_main.TextBox(owner)
	box.text = "foo bar"
	monkeypatch.setattr(sdl3, "SDL_SetTextInputArea", Mock())

	def press(**keys: object) -> None:
		for key, value in keys.items():
			setattr(inp, key, value)
		box.draw(10, 10, ColourRGBA(255, 255, 255, 255), font=13, width=300, arrow_keys_need_modifier=True)
		for key in keys:
			setattr(inp, key, type(getattr(inp, key))())

	yield box, press
	sdl3.SDL_DestroyRenderer(renderer)
	sdl3.SDL_DestroySurface(surface)


def test_quick_search_plain_arrows_leave_cursor(quick_box: tuple) -> None:
	box, press = quick_box
	press(key_left_press=True)
	press(key_home_press=True)
	assert box.cursor_position == 0


def test_quick_search_modified_arrows_move_cursor(quick_box: tuple) -> None:
	box, press = quick_box
	press(key_ctrl_down=True, key_left_press=True)
	assert cursor(box) == 4
	press(key_shift_down=True, key_left_press=True)
	assert cursor(box) == 3
	assert box.get_selection() == " "


def test_quick_search_inserts_at_cursor(quick_box: tuple) -> None:
	box, press = quick_box
	press(key_ctrl_down=True, key_left_press=True)
	press(input_text="x")
	assert box.text == "foo xbar"


def test_quick_search_leaves_delete_to_playlist(quick_box: tuple) -> None:
	box, press = quick_box
	press(key_ctrl_down=True, key_left_press=True)
	press(key_del=True)
	press(key_ctrl_down=True, key_del=True)
	assert box.text == "foo bar"
