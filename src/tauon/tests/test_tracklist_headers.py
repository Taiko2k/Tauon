# Copyright © 2026, Tauon contributors

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules.t_main import StandardPlaylist

ROW = 20


def make_view(tracks: list[tuple[str, str]], style: str = "compact") -> StandardPlaylist:
	"""tracks: (folder, disc_number) per playlist entry."""
	library = {
		i: SimpleNamespace(index=i, parent_folder_path=folder, album=folder, album_artist="", disc_number=disc)
		for i, (folder, disc) in enumerate(tracks)}
	view = object.__new__(StandardPlaylist)
	view.pctl = SimpleNamespace(
		default_playlist=list(library),
		multi_playlist=[SimpleNamespace(uuid_int=1, hide_title=False)],
		active_playlist_viewing=0,
		active_playlist_playing=1,
		playlist_playing_position=-1,
		selected_in_playlist=0,
		playlist_view_position=0,
		get_track=library.__getitem__,
		playing_object=lambda: None,
	)
	view.prefs = SimpleNamespace(
		tracklist_album_only=False, column_album_art_full_height=False, break_enable=True,
		tracklist_title_style=style)
	view.gui = SimpleNamespace(
		custom_mode=False, set_mode=False, pl_st=[], scale=1, playlist_row_height=ROW, playlist_scroll_pixels=0)
	view.smooth_scroll = Mock()
	view.album_only_owner = None
	view._tracklist_layout_key = None
	view._album_bounds_key = None
	view._album_bounds = None
	view._album_start_seen = None
	view._visible_rows = 0
	view._ensure_tracklist_layout()
	return view


TWO_DISCS = [("a", "1"), ("a", "1"), ("a", "2"), ("a", "2"), ("b", ""), ("b", "")]


def test_disc_rows_label_every_disc_of_multi_disc_albums() -> None:
	view = make_view(TWO_DISCS)
	sub = view.disc_row_height() / ROW
	assert view._tracklist_sub_rows == [sub, 0, sub, 0, 0, 0]
	assert view._tracklist_title_rows == [1, 0, 0, 0, 1, 0]
	# Title + disc row + track for the first entry
	assert view._tracklist_prefix_rows[1] == pytest.approx(2 + sub)
	assert view._tracklist_prefix_rows[-1] == pytest.approx(8 + 2 * sub)


def test_single_disc_album_has_no_disc_row() -> None:
	view = make_view([("a", "1"), ("a", "1"), ("b", "1")])
	assert view._tracklist_sub_rows == [0, 0, 0]


def test_full_titles_use_fixed_height() -> None:
	view = make_view(TWO_DISCS, style="full")
	assert view._tracklist_title_rows[0] == pytest.approx(view.title_row_height() / ROW)
	view.gui.playlist_row_height = 30
	view._ensure_tracklist_layout()
	# Same pixel height whatever the row height
	assert view._tracklist_title_rows[0] * 30 == pytest.approx(view.title_row_height())


def test_hidden_titles_drop_all_headers() -> None:
	view = make_view(TWO_DISCS)
	view.pctl.multi_playlist[0].hide_title = True
	view._ensure_tracklist_layout()
	assert view._tracklist_prefix_rows[-1] == len(TWO_DISCS)


def test_layout_rebuilds_after_middle_playlist_reorder() -> None:
	view = make_view([("a", "1"), ("b", "1"), ("a", "1"), ("b", "1"), ("c", "1")])
	view.pctl.default_playlist[1], view.pctl.default_playlist[2] = (
		view.pctl.default_playlist[2], view.pctl.default_playlist[1])

	view._ensure_tracklist_layout()

	assert view._tracklist_title_rows == [1, 0, 1, 0, 1]


def test_smooth_pixel_scroll_crosses_fractional_rows() -> None:
	view = make_view(TWO_DISCS, style="full")
	first_step = view._tracklist_step_height(0)
	view.gui.playlist_scroll_pixels = first_step + 5
	view._apply_tracklist_pixel_scroll()
	assert view.pctl.playlist_view_position == 1
	assert view.gui.playlist_scroll_pixels == pytest.approx(5)


def test_line_scroll_snaps_to_full_titles_only() -> None:
	view = make_view(TWO_DISCS, style="full")
	title = view._tracklist_title_rows[4]
	b_top = view._tracklist_prefix_rows[4]
	# Snapping hides 5 px of the title's top padding
	snap = b_top + 5 / ROW
	assert view.title_snap_trim() == pytest.approx(5 / ROW)
	# Down into b's title: stop at its top
	assert view.snap_line_scroll(b_top - 1, b_top + title / 2) == pytest.approx(snap)
	# Already snapped to it: skip past it rather than stick
	assert view.snap_line_scroll(snap, b_top + title / 2) == pytest.approx(b_top + title)
	# Up into it: land on its top
	assert view.snap_line_scroll(b_top + title + 2, b_top + title / 2) == pytest.approx(snap)
	# Disc rows don't snap
	disc_row_top = view._tracklist_prefix_rows[2]
	assert view.snap_line_scroll(0, disc_row_top + 0.1) == disc_row_top + 0.1


def test_compact_titles_never_snap() -> None:
	view = make_view(TWO_DISCS)
	assert view.snap_line_scroll(0, 4.5) == 4.5


def test_disc_label_prefers_subtitle() -> None:
	track = SimpleNamespace(disc_number="02", disc_subtitle="Twilight to Starlight")
	assert StandardPlaylist.disc_label(track) == "Twilight to Starlight"
	track.disc_subtitle = ""
	assert StandardPlaylist.disc_label(track) == "Disc 2"
	# Tracks saved before the field existed
	assert StandardPlaylist.disc_label(SimpleNamespace(disc_number="1")) == "Disc 1"


def test_integer_disc_numbers() -> None:
	# Subsonic and the M4A reader store disc numbers as ints
	view = make_view([("a", 1), ("a", 2), ("b", 0)])
	sub = view.disc_row_height() / ROW
	assert view._tracklist_sub_rows == [sub, sub, 0]
	assert StandardPlaylist.disc_label(SimpleNamespace(disc_number=2, disc_subtitle="")) == "Disc 2"


def test_settle_moves_partway_title_to_snap_position() -> None:
	view = make_view(TWO_DISCS, style="full")
	b_top = view._tracklist_prefix_rows[4]
	# Top edge left partway through b's title, as after a jump with leftover pixels
	view.pctl.playlist_view_position = 4
	view.gui.playlist_scroll_pixels = 12
	view.settle_on_full_title()
	assert view._tracklist_scroll_row() == pytest.approx(b_top + 5 / ROW)
	# Inside a track row: left alone
	view.pctl.playlist_view_position = 5
	view.gui.playlist_scroll_pixels = 5
	view.settle_on_full_title()
	assert view.pctl.playlist_view_position == 5
	assert view.gui.playlist_scroll_pixels == 5
