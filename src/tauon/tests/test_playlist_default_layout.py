"""Per-playlist default layout: set from the tab menu, applied on entering the playlist (#1220).
Playlists without a default share one layout, restored on leaving the playlists that have one."""

from __future__ import annotations

import types
from unittest.mock import MagicMock

import pytest

from tauon.t_modules.t_custom import CustomLayout
from tauon.t_modules.t_extra import TauonPlaylist
from tauon.t_modules.t_main import Tauon


class FakeViewBox:
	"""Tracks which layout entry is showing, standing in for the real view switching."""

	def __init__(self) -> None:
		self.current: tuple[str, str | int] | None = ("preset", "tracks")
		self.applied: list[tuple[str, str | int]] = []

	def current_layout_index(self, items) -> int:
		return items.index(self.current) if self.current in items else -1

	def apply_layout(self, kind, ref) -> None:
		self.current = (kind, ref)
		self.applied.append((kind, ref))


def make_playlist(name: str, uid: int) -> TauonPlaylist:
	return TauonPlaylist(
		title=name, playing=0, playlist_ids=[], position=0, hide_title=False, selected=0, uuid_int=uid,
		last_folder=[], hidden=False, locked=False, parent_playlist_id=0, persist_time_positioning=False)


@pytest.fixture
def tauon(tmp_path):
	gui = types.SimpleNamespace(
		custom_edit=False, custom_mode=False, request_tracklist_redraw=lambda: None, request_frame=lambda: None,
		update_layout=False)
	host = types.SimpleNamespace(gui=gui, ddt=MagicMock(), renderer=MagicMock(), user_directory=tmp_path)
	custom = CustomLayout(tauon=host)
	custom.ensure_loaded()
	while len(custom.slots) < 2:
		custom.add_slot()
	custom.slot_names[0], custom.slot_names[1] = "Alpha", "Beta"

	stub = types.SimpleNamespace(
		custom=custom,
		view_box=FakeViewBox(),
		pctl=types.SimpleNamespace(
			multi_playlist=[make_playlist("A", 1), make_playlist("B", 2), make_playlist("C", 3), make_playlist("D", 4)],
			active_playlist_viewing=0),
		gui=gui,
		prefs=types.SimpleNamespace(shuffle_lock=False),
		colours=types.SimpleNamespace(menu_text=None, menu_background=None),
		show_message=MagicMock(),
		shared_layout=None,
		shared_layout_saved=False,
	)
	for name in (
		"current_layout_snapshot", "layout_snapshot_valid", "valid_default_layout", "show_layout_snapshot", "toggle_default_layout",
		"default_layout_deco", "apply_playlist_default_layout",
	):
		setattr(stub, name, types.MethodType(getattr(Tauon, name), stub))
	return stub


def enter(tauon, pl: int) -> None:
	tauon.pctl.active_playlist_viewing = pl
	tauon.apply_playlist_default_layout()


def test_toggle_sets_then_unsets(tauon):
	tauon.view_box.current = ("preset", "gallery1")
	assert tauon.default_layout_deco(0).text == "Use Current Layout as Default"
	tauon.toggle_default_layout(0)
	assert tauon.pctl.multi_playlist[0].default_layout["ref"] == "gallery1"
	assert tauon.default_layout_deco(0).text == "Unset Default Layout"
	tauon.toggle_default_layout(0)
	assert tauon.pctl.multi_playlist[0].default_layout is None
	assert tauon.default_layout_deco(0).text == "Use Current Layout as Default"


def test_default_applies_on_entry_and_override_is_temporary(tauon):
	tauon.view_box.current = ("preset", "gallery1")
	tauon.toggle_default_layout(0)
	enter(tauon, 1)
	tauon.view_box.current = ("preset", "tracks")
	enter(tauon, 0)
	assert tauon.view_box.current == ("preset", "gallery1")
	# Temporary override, then leave and come back
	tauon.view_box.current = ("preset", "lyrics")
	enter(tauon, 1)
	assert tauon.view_box.current == ("preset", "tracks")
	enter(tauon, 0)
	assert tauon.view_box.current == ("preset", "gallery1")


def set_default(tauon, pl: int, layout) -> None:
	tauon.view_box.current = layout
	tauon.toggle_default_layout(pl)


def test_shared_layout_restored_on_leaving_to_playlist_without_default(tauon):
	set_default(tauon, 0, ("preset", "gallery1"))
	tauon.view_box.current = ("preset", "side_normal")
	enter(tauon, 1)
	enter(tauon, 0)
	assert tauon.view_box.current == ("preset", "gallery1")
	enter(tauon, 1)
	assert tauon.view_box.current == ("preset", "side_normal")


def test_shared_layout_kept_across_several_default_playlists(tauon):
	set_default(tauon, 0, ("preset", "gallery1"))
	set_default(tauon, 1, ("slot", 1))
	tauon.view_box.current = ("preset", "side_normal")
	enter(tauon, 2)
	enter(tauon, 0)
	enter(tauon, 1)
	assert tauon.view_box.current == ("slot", 1)
	enter(tauon, 0)
	enter(tauon, 3)
	assert tauon.view_box.current == ("preset", "side_normal")


def test_layout_changed_in_unset_playlists_is_what_gets_restored(tauon):
	set_default(tauon, 0, ("preset", "gallery1"))
	tauon.view_box.current = ("preset", "side_normal")
	enter(tauon, 1)
	enter(tauon, 0)
	enter(tauon, 1)
	tauon.view_box.current = ("preset", "lyrics")
	enter(tauon, 2)
	assert tauon.view_box.current == ("preset", "lyrics")
	enter(tauon, 0)
	enter(tauon, 2)
	assert tauon.view_box.current == ("preset", "lyrics")


def test_shared_layout_dropped_if_deleted(tauon):
	set_default(tauon, 0, ("preset", "gallery1"))
	tauon.view_box.current = ("slot", 0)
	enter(tauon, 1)
	enter(tauon, 0)
	tauon.custom.delete_slot(0)
	tauon.view_box.applied.clear()
	enter(tauon, 1)
	assert tauon.view_box.applied == []
	assert tauon.view_box.current == ("preset", "gallery1")
	assert tauon.shared_layout_saved is False


def test_custom_slot_default(tauon):
	tauon.view_box.current = ("slot", 1)
	tauon.toggle_default_layout(0)
	tauon.view_box.current = ("preset", "tracks")
	enter(tauon, 0)
	assert tauon.view_box.current == ("slot", 1)


def test_reordered_layout_unsets_default_and_stays(tauon):
	tauon.view_box.current = ("preset", "gallery1")
	tauon.toggle_default_layout(0)
	pos = tauon.pctl.multi_playlist[0].default_layout["pos"]
	tauon.custom.move_layout(pos, 1)
	tauon.view_box.current = ("preset", "tracks")
	enter(tauon, 0)
	assert tauon.view_box.current == ("preset", "tracks")
	assert tauon.view_box.applied == []
	assert tauon.pctl.multi_playlist[0].default_layout is None


def test_deleted_slot_unsets_default_and_stays(tauon):
	tauon.view_box.current = ("slot", 0)
	tauon.toggle_default_layout(0)
	tauon.custom.delete_slot(0)
	tauon.view_box.current = ("preset", "tracks")
	enter(tauon, 0)
	assert tauon.view_box.applied == []
	assert tauon.pctl.multi_playlist[0].default_layout is None


def test_renamed_slot_in_same_position_unsets_default(tauon):
	tauon.view_box.current = ("slot", 1)
	tauon.toggle_default_layout(0)
	tauon.custom.slot_names[1] = "Something else"
	tauon.view_box.current = ("preset", "tracks")
	enter(tauon, 0)
	assert tauon.view_box.applied == []
	assert tauon.pctl.multi_playlist[0].default_layout is None


def test_unrecognised_view_cannot_be_default(tauon):
	tauon.view_box.current = None
	tauon.toggle_default_layout(0)
	assert tauon.pctl.multi_playlist[0].default_layout is None
	tauon.show_message.assert_called_once()


def test_no_switch_while_editing_custom_layout(tauon):
	tauon.view_box.current = ("preset", "gallery1")
	tauon.toggle_default_layout(0)
	tauon.view_box.current = ("preset", "tracks")
	tauon.gui.custom_edit = True
	enter(tauon, 0)
	assert tauon.view_box.applied == []
	assert tauon.pctl.multi_playlist[0].default_layout is not None
