"""Tooltips that would run off the window pop out into a tooltip window (#1697)."""

from types import SimpleNamespace
from unittest.mock import Mock

from tauon.t_modules import t_main, t_window
from tauon.t_modules.t_extra import ColourRGBA

FILL = ColourRGBA(30, 30, 30, 255)


class FakePopup:
	instances: list["FakePopup"] = []
	bounds: tuple[int, int, int, int] | None = (-200, -100, 1440, 900)
	show_ok = True

	def __init__(self, tauon, **kwargs) -> None:
		self.kwargs = kwargs
		self.ddt = Mock(name="popup_ddt")
		self.renderer = object()
		self.shown: tuple[int, int, int, int] | None = None
		FakePopup.instances.append(self)

	def usable_bounds(self):
		return self.bounds

	def show(self, w, h, x, y) -> bool:
		self.shown = (w, h, x, y)
		return self.show_ok

	def begin_frame(self) -> None:
		pass

	def end_frame(self) -> None:
		pass


def make_tauon(monkeypatch) -> SimpleNamespace:
	FakePopup.instances = []
	FakePopup.show_ok = True
	monkeypatch.setattr(t_window, "SecondaryWindow", FakePopup)
	tauon = SimpleNamespace(
		gui=SimpleNamespace(scale=1.0, mouse_in_window=True),
		inp=SimpleNamespace(view_window=None),
		window_size=[800, 600],
		ddt=Mock(name="main_ddt"),
		aero=SimpleNamespace(active=False),
		colours=SimpleNamespace(menu_text=ColourRGBA(255, 255, 255, 255)),
		tip_popup=None,
		tip_popup_used=False,
		tip_popup_failed=False,
		_destroy_secondary=Mock(),
	)
	for name in ("draw_tip", "_paint_tip", "close_tip_popup", "end_tip_frame"):
		setattr(tauon, name, getattr(t_main.Tauon, name).__get__(tauon))
	return tauon


def test_tip_inside_window_draws_inline(monkeypatch) -> None:
	tauon = make_tauon(monkeypatch)
	tauon.draw_tip((100, 100, 200, 24), "Hi", 13, FILL, text_y=4)
	assert FakePopup.instances == []
	tauon.ddt.rect.assert_called_once()
	tauon.ddt.text.assert_called_once()


def test_tip_past_right_edge_pops_out_inside_usable_bounds(monkeypatch) -> None:
	tauon = make_tauon(monkeypatch)
	# The display's usable area ends 1240px right of the window's left edge
	tauon.draw_tip((700, 100, 900, 24), "/a/very/long/path.flac", 312, FILL, text_y=3, border=FILL)
	popup = FakePopup.instances[0]
	assert popup.kwargs["tooltip"] is True
	assert popup.shown == (902, 26, 1240 - 902, 99)
	# Drawn at the popup's origin, inside its 1px border
	popup.ddt.rect.assert_any_call((1, 1, 900, 24), FILL)
	tauon.ddt.rect.assert_not_called()
	assert tauon.tip_popup_used


def test_unused_tip_popup_closes_at_end_of_frame(monkeypatch) -> None:
	tauon = make_tauon(monkeypatch)
	tauon.draw_tip((-50, 100, 200, 24), "Hi", 13, FILL, text_y=4)
	tauon.end_tip_frame()
	assert tauon.tip_popup is not None
	tauon.end_tip_frame()
	assert tauon.tip_popup is None
	tauon._destroy_secondary.assert_called_once()


def test_failed_popup_slides_tip_into_window(monkeypatch) -> None:
	tauon = make_tauon(monkeypatch)
	FakePopup.show_ok = False
	tauon.draw_tip((700, 100, 200, 24), "Hi", 13, FILL, text_y=4)
	assert tauon.tip_popup_failed
	tauon.ddt.rect.assert_called_once_with((600, 100, 200, 24), FILL)
