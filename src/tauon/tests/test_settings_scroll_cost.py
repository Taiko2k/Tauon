"""Settings scrolling stays cheap: the chart's album count is cached and the
skin culls drawing outside the visible page."""
from types import SimpleNamespace

from tauon.t_modules.t_aero import Aero
from tauon.t_modules.t_main import Over


class FakeTimer:
	def __init__(self) -> None:
		self.elapsed = 0.0

	def get(self) -> float:
		return self.elapsed

	def set(self) -> None:
		self.elapsed = 0.0


def make_over(playlist_ids: list[int]):
	calls = []

	def reload_albums(quiet: bool = False, return_playlist: int = -1) -> list[int]:
		calls.append(return_playlist)
		return list(range(len(playlist_ids) // 2))

	pl = SimpleNamespace(uuid_int=7, playlist_ids=playlist_ids)
	over = SimpleNamespace(
		pctl=SimpleNamespace(multi_playlist=[pl], active_playlist_viewing=0),
		prefs=SimpleNamespace(gallery_combine_disc=False),
		tauon=SimpleNamespace(reload_albums=reload_albums),
		chart_albums_key=None,
		chart_albums_timer=FakeTimer(),
		chart_albums=0,
		STATS_REFRESH=Over.STATS_REFRESH,
	)
	return over, calls


def test_chart_album_count_is_counted_once_per_playlist_change() -> None:
	ids = list(range(10))
	over, calls = make_over(ids)
	assert Over.settings_chart_albums(over) == 5
	for _frame in range(20):
		assert Over.settings_chart_albums(over) == 5
	assert len(calls) == 1
	ids.extend(range(10, 14))
	assert Over.settings_chart_albums(over) == 7
	assert len(calls) == 2
	over.chart_albums_timer.elapsed = Over.STATS_REFRESH + 1
	Over.settings_chart_albums(over)
	assert len(calls) == 3


def test_cull_skips_only_what_lies_outside() -> None:
	aero = SimpleNamespace(cull=None)
	assert not Aero.culled(aero, (0, -500, 10, 10))
	aero.cull = (100, 100, 200, 200)
	assert not Aero.culled(aero, (150, 150, 10, 10))
	# Straddling an edge still draws
	assert not Aero.culled(aero, (90, 95, 20, 20))
	assert Aero.culled(aero, (150, 320, 10, 10))
	assert Aero.culled(aero, (150, 80, 10, 10))
	# A glow's margin can bring it back in
	assert not Aero.culled(aero, (150, 80, 10, 10), margin=12)
	aero.cull = (0, 0, 0, 0)
	assert Aero.culled(aero, (150, 150, 10, 10))
