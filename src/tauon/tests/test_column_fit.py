# Copyright © 2026, Tauon contributors

from types import SimpleNamespace

from tauon.t_modules import t_main


def tauon_with(columns: list[list], plw: int) -> t_main.Tauon:
	owner = object.__new__(t_main.Tauon)
	owner.gui = SimpleNamespace(
		pl_st=columns, plw=plw, pl_st_left=16, scale=1, custom_mode=False, tracklist_center_mode=False)
	owner.column_fit = None
	return owner


def test_update_set_fills_width() -> None:
	owner = tauon_with([["Artist", 300, False], ["Title", 200, False], ["Time", 53, True]], 1069)
	owner.update_set()
	widths = [c[1] for c in owner.gui.pl_st]
	assert widths[2] == 53
	assert sum(widths) == 1053
	assert widths[0] / widths[1] == 1.5


def test_squeeze_and_restore_keeps_proportions() -> None:
	cols = [["A", 600, False], ["B", 390, False], ["C", 10, False], ["Time", 53, True]]
	owner = tauon_with(cols, 1069)
	owner.update_set()
	start = [c[1] for c in cols]
	for _cycle in range(20):
		owner.update_set(200)  # narrow: clamps to the 75px minimum
		assert cols[2][1] in (0, 1)
		owner.update_set(1069)
	assert [c[1] for c in cols] == start


def test_user_change_resets_proportions() -> None:
	cols = [["A", 500, False], ["B", 500, False]]
	owner = tauon_with(cols, 1016)
	owner.update_set()
	cols[0][1] = 700
	cols[1][1] = 300
	owner.update_set()
	assert [c[1] for c in cols] == [700, 300]


def test_explicit_width_overrides_custom_rect() -> None:
	cols = [["A", 100, False]]
	owner = tauon_with(cols, 1016)
	owner.gui.custom_mode = True
	owner.custom = SimpleNamespace(tracklist_rect=lambda: (0, 0, 516, 100))
	owner.update_set()
	assert cols[0][1] == 500
	owner.update_set(816)
	assert cols[0][1] == 800


def test_fill_last_column() -> None:
	cols = [["A", 400, False], ["B", 300, False], ["Time", 53, True]]
	owner = tauon_with(cols, 1016)
	owner.fill_last_column(1016)
	assert cols[2][1] == 300
