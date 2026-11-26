# Copyright © 2026, Tauon contributors

import pytest

from tauon.t_modules.t_extra import ColourRGBA, contrast_ratio, neutral_ink, rgb_to_hls, split_title_brackets


@pytest.mark.parametrize(("title", "runs"), [
	("Stardust (Feat. Twin Shadow)", [("Stardust ", False), ("(Feat. Twin Shadow)", True)]),
	("Song (Live) [Remastered]", [("Song ", False), ("(Live)", True), (" ", False), ("[Remastered]", True)]),
	("Song (feat. X) Remix", [("Song ", False), ("(feat. X)", True), (" Remix", False)]),
	("A (b (c) d) e", [("A ", False), ("(b (c) d)", True), (" e", False)]),
	("Broken (feat", [("Broken ", False), ("(feat", True)]),
	("曲（Live）", [("曲", False), ("（Live）", True)]),
	("No brackets", [("No brackets", False)]),
	("", []),
])
def test_split_title_brackets(title: str, runs: list[tuple[str, bool]]) -> None:
	assert split_title_brackets(title) == runs


def test_leading_bracket_group_is_part_of_the_title() -> None:
	assert split_title_brackets("(I Can't Get No) Satisfaction") == [("(I Can't Get No) Satisfaction", False)]
	assert split_title_brackets(" (Intro) Song (Live)")[-1] == ("(Live)", True)


@pytest.mark.parametrize(("text", "background"), [
	(ColourRGBA(190, 190, 190, 255), ColourRGBA(21, 21, 21, 255)),
	(ColourRGBA(240, 70, 120, 255), ColourRGBA(21, 21, 21, 255)),
	(ColourRGBA(30, 30, 30, 255), ColourRGBA(255, 255, 255, 255)),
	(ColourRGBA(60, 60, 70, 255), ColourRGBA(235, 236, 240, 255)),
	(ColourRGBA(200, 200, 220, 255), ColourRGBA(20, 24, 40, 255)),
])
def test_neutral_ink_sits_between_background_and_text(text: ColourRGBA, background: ColourRGBA) -> None:
	ink = neutral_ink(text, background)
	assert 1.9 < contrast_ratio(ink, background) < contrast_ratio(text, background)
	_h, _l, s = rgb_to_hls(ink.r, ink.g, ink.b)
	assert s <= 0.16


def test_neutral_ink_takes_background_hue_and_text_alpha() -> None:
	ink = neutral_ink(ColourRGBA(200, 200, 220, 120), ColourRGBA(20, 24, 40, 255))
	assert ink.b > ink.r
	assert ink.a == 120
