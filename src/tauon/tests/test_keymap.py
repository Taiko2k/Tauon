# Copyright © 2026, Tauon contributors

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING
from unittest.mock import Mock

import pytest

from tauon.t_modules import t_main
from tauon.t_modules.t_db_migrate import database_migrate

if TYPE_CHECKING:
	from pathlib import Path


# Stand-in for SDL's key names; the native bridge is mocked in tests
KEYS = {"up": 1, "down": 2, "left": 3, "right": 4, "h": 5, "j": 6, "l": 7, "space": 8}


def key_code(name: str | bytes) -> int:
	name = name.decode() if isinstance(name, bytes) else name
	return KEYS.get(name.lower(), 100 + sum(map(ord, name.lower())))


def make_keymap(tmp_path: Path, text: str) -> t_main.KeyMap:
	(tmp_path / "input.txt").write_text(text, encoding="utf_8")
	bag = SimpleNamespace(prefs=SimpleNamespace(use_scancodes=False), dirs=SimpleNamespace(config_directory=tmp_path))
	keymap = t_main.KeyMap(bag=bag, inp=t_main.Input(SimpleNamespace()))
	keymap.load()
	return keymap


def press(keymap: t_main.KeyMap, name: str, *, shift: bool = False, ctrl: bool = False) -> None:
	keymap.new_frame()
	keymap.inp.key_shift_down = shift
	keymap.inp.key_ctrl_down = ctrl
	keymap.hits.append(key_code(name))


@pytest.fixture(autouse=True)
def setup(monkeypatch: pytest.MonkeyPatch) -> None:
	monkeypatch.setattr(t_main, "macos", False)
	monkeypatch.setattr(t_main.sdl3, "get_key_from_name", key_code)


def test_select_functions_default_to_arrows_when_missing(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "cycle-playlist-left Left\n")
	press(keymap, "Up")
	assert keymap.test("select-up")
	press(keymap, "Left")
	assert keymap.test("select-left")
	assert keymap.test("cycle-playlist-left")
	assert keymap.describe("select-down") == [["↓"]]


def test_bare_name_unbinds_a_default(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "select-up\nselect-down J\n")
	press(keymap, "Up")
	assert not keymap.test("select-up")
	assert keymap.describe("select-up") == []
	press(keymap, "Down")
	assert not keymap.test("select-down")
	press(keymap, "J")
	assert keymap.test("select-down")


def test_modifiers_must_match_exactly(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "shift-up Up Shift\n")
	press(keymap, "Up", shift=True)
	assert keymap.test("shift-up")
	assert not keymap.test("select-up")
	press(keymap, "Up")
	assert keymap.test("select-up")
	assert not keymap.test("shift-up")


def test_consume_lets_only_the_first_handler_fire(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "cycle-playlist-left Left\n")
	press(keymap, "Left")
	assert keymap.consume("select-left")
	assert not keymap.test("cycle-playlist-left")
	assert not keymap.consume("select-left")


def test_unconsumed_key_falls_through(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "cycle-playlist-left Left\n")
	press(keymap, "Left")
	assert not keymap.consume("select-up")
	assert keymap.test("cycle-playlist-left")


def test_typing_skips_keys_that_type(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "cycle-playlist-left H\ncycle-playlist-left Left\ncycle-playlist-right L Shift\n")
	press(keymap, "H")
	assert keymap.test("cycle-playlist-left")
	assert not keymap.test("cycle-playlist-left", typing=True)
	press(keymap, "L", shift=True)
	assert not keymap.test("cycle-playlist-right", typing=True)
	press(keymap, "Left")
	assert keymap.test("cycle-playlist-left", typing=True)


def test_typing_keeps_bindings_with_ctrl(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "cycle-playlist-left H Ctrl\n")
	press(keymap, "H", ctrl=True)
	assert keymap.test("cycle-playlist-left", typing=True)


def test_trigger_fires_without_a_key(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "select-up\n")
	keymap.new_frame()
	keymap.trigger("select-up")
	assert keymap.test("select-up")
	assert keymap.consume("select-up")
	assert not keymap.test("select-up")


@pytest.mark.parametrize(
	("text", "key", "shift", "ctrl", "expected"),
	[
		("cycle-playlist-left H\n", "H", False, False, True),
		("cycle-playlist-left H\n", "H", True, False, False),
		("cycle-playlist-left H Shift\n", "H", True, False, True),
		("cycle-playlist-left H Ctrl\n", "H", False, True, False),
		("cycle-playlist-left H Ctrl\n", "H", True, False, False),
		("", "Up", False, False, False),
		("playpause Space\n", "Space", False, False, True),
	],
)
def test_text_key_bound(tmp_path: Path, text: str, key: str, shift: bool, ctrl: bool, expected: bool) -> None:  # noqa: PLR0917
	keymap = make_keymap(tmp_path, text)
	press(keymap, key, shift=shift, ctrl=ctrl)
	assert keymap.text_key_bound() is expected


def test_text_key_bound_sees_consumed_keys(tmp_path: Path) -> None:
	keymap = make_keymap(tmp_path, "select-left H\n")
	press(keymap, "H")
	assert keymap.consume("select-left")
	assert keymap.text_key_bound()
	keymap.new_frame()
	assert not keymap.text_key_bound()


def test_template_keeps_the_arrow_defaults(tmp_path: Path) -> None:
	template = t_main.Path(t_main.__file__).parent.parent / "templates" / "input.txt"
	keymap = make_keymap(tmp_path, template.read_text(encoding="utf_8"))
	for function, key in (
		("select-up", "Up"), ("select-down", "Down"),
		("select-left", "Left"), ("select-right", "Right"),
		("cycle-playlist-left", "Left"), ("cycle-playlist-right", "Right"),
	):
		press(keymap, key)
		assert keymap.test(function), function
	# No default binding is a bare letter, so type-to-search is unchanged
	press(keymap, "H")
	assert not keymap.text_key_bound()


def migrate_v84(tmp_path: Path, text: str) -> tuple[str, Mock]:
	config = tmp_path / "config"
	config.mkdir()
	(config / "input.txt").write_text(text, encoding="utf_8")
	gui = SimpleNamespace(keymaps=Mock())
	database_migrate(
		tauon=SimpleNamespace(), db_version=83, master_library={}, legacy_track_misc={}, install_mode=False,
		multi_playlist=[], a_cache_dir="", cache_directory=tmp_path, config_directory=config,
		install_directory=tmp_path, user_directory=tmp_path, gui=gui, gen_codes={}, prefs=SimpleNamespace(),
		radio_playlists=[], theme=0, p_force_queue=[],
	)
	return (config / "input.txt").read_text(encoding="utf_8"), gui.keymaps


def test_v84_writes_select_bindings_into_old_input_txt(tmp_path: Path) -> None:
	text, keymaps = migrate_v84(tmp_path, "cycle-playlist-left Left\ncycle-playlist-right Right\n")
	assert text.startswith("cycle-playlist-left Left\ncycle-playlist-right Right\n")
	assert text.endswith("select-up Up\nselect-down Down\nselect-left Left\nselect-right Right\n")
	keymaps.load.assert_called_once()


def test_v84_keeps_select_bindings_the_user_has(tmp_path: Path) -> None:
	text, _keymaps = migrate_v84(tmp_path, "select-up K\nselect-left\n")
	assert "select-up Up" not in text
	assert "select-left Left" not in text
	assert text.endswith("select-down Down\nselect-right Right\n")


def test_v84_leaves_a_complete_file_alone(tmp_path: Path) -> None:
	original = "select-up K\nselect-down J\nselect-left H\nselect-right L\n"
	text, keymaps = migrate_v84(tmp_path, original)
	assert text == original
	keymaps.load.assert_not_called()


def test_v84_file_loads_the_same_as_defaults(tmp_path: Path) -> None:
	text, _keymaps = migrate_v84(tmp_path, "cycle-playlist-left Left\n")
	migrated = make_keymap(tmp_path, text)
	unmigrated = make_keymap(tmp_path, "cycle-playlist-left Left\n")
	for function in ("select-up", "select-down", "select-left", "select-right"):
		assert migrated.describe(function) == unmigrated.describe(function)
