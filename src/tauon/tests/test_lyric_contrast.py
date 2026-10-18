# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import colorsys
from types import SimpleNamespace
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from tauon.t_modules.t_art_theme import apply_art_theme, apply_original_art_theme
from tauon.t_modules.t_extra import ColourRGBA, contrast_ratio, ensure_distinct

if TYPE_CHECKING:
	from collections.abc import Callable


def _hue(colour: ColourRGBA) -> float:
	return colorsys.rgb_to_hls(colour.r / 255, colour.g / 255, colour.b / 255)[0]


def test_near_black_active_is_pushed_away_from_near_black_inactive() -> None:
	background = ColourRGBA(236, 234, 230, 255)
	inactive = ColourRGBA(30, 30, 32, 255)
	active = ColourRGBA(40, 14, 14, 255)
	assert contrast_ratio(active, inactive) < 1.2

	adjusted, inactive_after = ensure_distinct(active, inactive, background)

	assert inactive_after == inactive
	assert contrast_ratio(adjusted, inactive) >= 1.5
	assert contrast_ratio(adjusted, background) >= 4.5
	assert _hue(adjusted) == pytest.approx(_hue(active), abs=0.02)
	assert adjusted.a == active.a


def test_palette_with_good_contrast_is_left_alone() -> None:
	background = ColourRGBA(236, 234, 230, 255)
	inactive = ColourRGBA(30, 30, 32, 255)
	active = ColourRGBA(200, 40, 40, 255)

	assert ensure_distinct(active, inactive, background) == (active, inactive)


def test_inactive_fades_when_it_already_sits_at_the_readable_limit() -> None:
	# On a mid-tone surface the dark inactive text leaves no readable room
	# darker than itself, so the inactive text gives way instead.
	background = ColourRGBA(192, 113, 59, 255)
	inactive = ColourRGBA(32, 29, 28, 255)
	active = ColourRGBA(30, 20, 14, 255)

	adjusted, inactive_after = ensure_distinct(active, inactive, background)

	assert contrast_ratio(adjusted, inactive_after) >= 1.5
	assert contrast_ratio(adjusted, background) >= 4.5
	assert contrast_ratio(inactive_after, background) >= 3.0


@pytest.mark.parametrize("apply", [apply_art_theme, apply_original_art_theme])
@pytest.mark.parametrize(
	("first", "second"),
	[
		((236, 232, 224), (214, 180, 120)),
		((18, 19, 21), (220, 24, 68)),
		((192, 113, 59), (90, 60, 40)),
		((121, 61, 162), (200, 190, 210)),
	],
)
def test_colourise_keeps_active_lyric_distinct(
	apply: Callable[[object, Image.Image], object],
	first: tuple[int, int, int],
	second: tuple[int, int, int],
) -> None:
	image = Image.new("RGB", (100, 100), first)
	image.paste(second, (0, 0, 40, 100))
	colours = SimpleNamespace(column_colours=[], column_colours_playing=[])
	apply(colours, image)

	assert contrast_ratio(colours.active_lyric, colours.lyrics) >= 1.5
	assert contrast_ratio(colours.active_lyric, colours.lyrics_panel_background) >= 4.5
