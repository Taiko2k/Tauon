from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from tauon.t_modules import t_main


@pytest.mark.parametrize("title, tag_meta", [("", ""), ("", "Station metadata"), ("Radio song", "")])
def test_showcase_visualizer_renders_radio_without_music_queue(
	monkeypatch: pytest.MonkeyPatch, title: str, tag_meta: str
) -> None:
	track = SimpleNamespace(title=title, artist="Artist", album="", date="", lyrics="", filename="", index=-1)
	visualizer_rect = SimpleNamespace(x=0, y=0, w=322)
	gui = SimpleNamespace(
		scale=1, panelY=30, panelBY=51, vis_4_colour=None, draw_vis4_top=False,
		force_showcase_index=-1, spec4_rec=visualizer_rect, vis4_clip=None, message_box=False,
		timed_lyrics_edit_view=False,
	)
	colours = SimpleNamespace(
		lyrics_panel_background=t_main.ColourRGBA(30, 30, 30, 255),
		lm=False, grey=lambda value: t_main.ColourRGBA(value, value, value, 255),
		side_bar_line1=t_main.ColourRGBA(255, 255, 255, 255),
		side_bar_line2=t_main.ColourRGBA(255, 255, 255, 255),
	)
	showcase = object.__new__(t_main.Showcase)
	showcase.timed_lyrics_edit = SimpleNamespace(continuous=False)
	showcase.gui = gui
	showcase.pctl = SimpleNamespace(
		playing_state=t_main.PlayingState.URL_STREAM, track_queue=[], tag_meta=tag_meta, url="radio.example/stream",
	)
	showcase.prefs = SimpleNamespace(
		showcase_wide_art=False, showcase_vis=True, show_lyrics_showcase=False, guitar_chords=False,
	)
	showcase.colours = colours
	showcase.ddt = SimpleNamespace(rect=Mock(), text=Mock(), alpha_bg=False, force_gray=False)
	showcase.inp = SimpleNamespace(mouse_position=(0, 0))
	showcase.window_size = [1200, 700]
	showcase.tauon = SimpleNamespace(
		radiobox=SimpleNamespace(dummy_track=track), search_over=SimpleNamespace(active=False),
		is_level_zero=Mock(return_value=True), test_auto_lyrics=Mock(),
	)
	monkeypatch.setattr(t_main, "draw_showcase_art_box", Mock())

	showcase.render()

	assert gui.draw_vis4_top
	assert visualizer_rect.y > 0
