"""Duotone palette generation and theme selection for album artwork.

The structural generator in :mod:`t_art_theme` measures colour with an absolute
chroma term, which collapses toward zero on dark colours, so deep navies and
rust reds are classified as neutral and rendered grey. It also builds its side
panel from an analogous hue a few lightness points from the background, leaving
the two large surfaces almost identical.

Duotone measures colour relative to each swatch's own brightness, takes its
tonal mode from a coverage-weighted median, and treats the gap between the two
surfaces as a target rather than a risk. :func:`select_art_theme` applies it
only where the routed generator returns a flat result.
"""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from tauon.t_modules.t_art_theme import (
	ArtTheme,
	_clamp,
	_colour_distance,
	_hls_to_colour,
	_hue_arc_distance,
	_quantized_palette,
	_readable_identity,
	_readable_tint,
	_rgb_to_hls,
	_rgb_tuple,
)

if TYPE_CHECKING:
	from PIL import Image

	from tauon.t_modules.t_extra import ColourRGBA

# Perceptual distance the two surfaces must reach on greyscale artwork, where
# tone is the only structure available. Coloured artwork uses 0.055.
MONOCHROME_SEPARATION = 0.14
# How far the legacy generator must beat the synthesized candidates to be used.
LEGACY_MARGIN = 0.05
# What counts as a flat theme: two surfaces of nearly the same tone with almost
# no colour in either.
FLAT_SEPARATION = 0.18
FLAT_CHROMA = 0.22
# A flat theme is corrected when it is this light, or when the artwork itself
# was too pale to have driven a better result.
LIGHT_THEME_LIGHTNESS = 0.55
PALE_ARTWORK = 0.35


@dataclass(frozen=True)
class Swatch:
	"""One quantized artwork colour."""

	coverage: float
	hue: float
	lightness: float
	saturation: float
	colourfulness: float


@dataclass(frozen=True)
class HueFamily:
	"""Neighbouring chromatic swatches merged into one hue."""

	coverage: float
	hue: float
	lightness: float
	saturation: float
	colourfulness: float


@dataclass(frozen=True)
class ArtSummary:
	"""Artwork measurements shared by the generator and the selector."""

	swatches: tuple[Swatch, ...]
	families: tuple[HueFamily, ...]
	chromatic_mass: float
	median_lightness: float


def relative_chroma(colour: tuple[int, int, int]) -> float:
	"""Return chroma as a fraction of the colour's own peak channel.

	Absolute chroma cannot separate a dark saturated colour from a dark grey:
	``(55, 41, 44)`` scores 0.055 on a 0-1 scale despite being visibly red.
	Dividing by the peak channel reports 0.255 instead.
	"""
	peak = max(colour)
	return (peak - min(colour)) / peak if peak else 0.0


def colourfulness(colour: tuple[int, int, int]) -> float:
	"""How coloured a swatch looks, at any lightness.

	Relative chroma rescues dark colours but understates pastels, whose floor
	channel is already high. Comparing the span against the widest span
	available at that lightness recovers those, and taking the better of the
	two measures covers the whole range. The headroom floor stops colours near
	white or black from exploding; the span gate rejects compression noise.
	"""
	span = (max(colour) - min(colour)) / 255
	if span < 0.035:
		return 0.0
	_hue, lightness, _saturation = _rgb_to_hls(colour)
	headroom = max(1 - abs(2 * lightness - 1), 0.25)
	return max(relative_chroma(colour), span / headroom)


def is_chromatic(swatch: Swatch) -> bool:
	"""Whether a swatch carries enough hue to be worth placing on a surface."""
	return swatch.colourfulness >= 0.30


def _swatches(image: Image.Image, count: int = 24) -> tuple[Swatch, ...]:
	palette = _quantized_palette(image, count)
	total = max(1, sum(population for population, _colour in palette))
	swatches = []
	for population, colour in palette:
		hue, lightness, saturation = _rgb_to_hls(colour)
		swatches.append(
			Swatch(
				coverage=population / total,
				hue=hue,
				lightness=lightness,
				saturation=saturation,
				colourfulness=colourfulness(colour),
			),
		)
	return tuple(swatches)


def _median_lightness(swatches: tuple[Swatch, ...]) -> float:
	"""Coverage-weighted median lightness.

	A mean is dragged around by one large black frame or white border, which is
	how a bright cover ends up as a dark theme. The median reports the tone the
	artwork actually spends most of its area near.
	"""
	ordered = sorted(swatches, key=lambda swatch: swatch.lightness)
	total = sum(swatch.coverage for swatch in ordered)
	if total <= 0:
		return 0.5
	seen = 0.0
	for swatch in ordered:
		seen += swatch.coverage
		if seen >= total / 2:
			return swatch.lightness
	return ordered[-1].lightness


def _hue_families(swatches: tuple[Swatch, ...]) -> tuple[HueFamily, ...]:
	"""Merge neighbouring chromatic swatches so fragmented colour still counts."""
	chromatic = [swatch for swatch in swatches if is_chromatic(swatch) and swatch.coverage >= 0.004]
	candidates = []
	for seed in chromatic:
		members = [swatch for swatch in chromatic if _hue_arc_distance(seed.hue, swatch.hue) <= 0.075]
		weights = [swatch.coverage * (0.30 + swatch.colourfulness) for swatch in members]
		weight_total = sum(weights)
		if weight_total <= 0:
			continue
		x_axis = sum(weight * math.cos(math.tau * member.hue) for weight, member in zip(weights, members, strict=True))
		y_axis = sum(weight * math.sin(math.tau * member.hue) for weight, member in zip(weights, members, strict=True))
		candidates.append(
			HueFamily(
				coverage=sum(member.coverage for member in members),
				hue=(math.atan2(y_axis, x_axis) / math.tau) % 1,
				lightness=sum(w * m.lightness for w, m in zip(weights, members, strict=True)) / weight_total,
				saturation=sum(w * m.saturation for w, m in zip(weights, members, strict=True)) / weight_total,
				colourfulness=sum(w * m.colourfulness for w, m in zip(weights, members, strict=True)) / weight_total,
			),
		)
	# Sliding hue windows produce near-identical candidates; keep one per family.
	candidates.sort(key=lambda family: family.coverage * (0.55 + family.colourfulness), reverse=True)
	families: list[HueFamily] = []
	for candidate in candidates:
		if all(_hue_arc_distance(candidate.hue, family.hue) >= 0.09 for family in families):
			families.append(candidate)
	return tuple(families)


def measure_artwork(image: Image.Image) -> ArtSummary:
	"""Measure an image once for both the generator and the selector."""
	swatches = _swatches(image)
	return ArtSummary(
		swatches=swatches,
		families=_hue_families(swatches),
		chromatic_mass=sum(swatch.coverage for swatch in swatches if is_chromatic(swatch)),
		median_lightness=_median_lightness(swatches),
	)


def _primary_family(summary: ArtSummary) -> HueFamily | None:
	"""The hue with the best combination of area and colour strength."""
	usable = [family for family in summary.families if family.coverage >= 0.055]
	if not usable:
		# Accept the broadest hue available rather than dropping to grey; the
		# saturation targets stay proportional to how little colour there is.
		usable = [family for family in summary.families if family.coverage >= 0.020]
	if not usable:
		return None
	return max(usable, key=lambda family: family.coverage**0.5 * (0.35 + family.colourfulness))


def _companion_family(summary: ArtSummary, primary: HueFamily) -> HueFamily | None:
	"""A second hue distinct enough from the primary to structure the side panel.

	A companion owns a whole panel, so it must hold a share of the artwork
	comparable to the primary; a distant hue needs a larger share still.
	Otherwise a small detail becomes half the interface and reads as a clash.
	"""
	usable = [
		family
		for family in summary.families
		if family is not primary and family.coverage >= 0.045 and _hue_arc_distance(family.hue, primary.hue) >= 0.09
	]
	usable = [
		family
		for family in usable
		if family.coverage >= primary.coverage * (0.35 if _hue_arc_distance(family.hue, primary.hue) <= 0.22 else 0.60)
	]
	if not usable:
		return None
	return max(
		usable,
		key=lambda family: family.coverage**0.4
		* (0.35 + family.colourfulness)
		# Prefer a neighbouring hue; distance is tolerated, not sought.
		* (1.0 - 0.8 * _hue_arc_distance(family.hue, primary.hue)),
	)


def _accent_family(summary: ArtSummary, background_hue: float) -> HueFamily | None:
	"""The most vivid hue present, even when it covers very little area.

	A small logo can be the cover's identity even though the sleeve owns the
	pixels, so coverage only weakly influences this choice.
	"""
	if not summary.families:
		return None
	away = [family for family in summary.families if _hue_arc_distance(family.hue, background_hue) >= 0.06]
	pool = away or list(summary.families)
	return max(pool, key=lambda family: family.colourfulness * (0.35 + family.coverage**0.30))


def _tinted(hue: float, lightness: float, saturation: float, target_chroma: float) -> ColourRGBA:
	"""Build a colour, raising saturation until the tint is actually visible.

	HLS saturation is not perceptual: near white, a moderate saturation lands
	within a couple of levels of grey. Surfaces are therefore specified by the
	chroma they must reach rather than by a saturation value.
	"""
	colour = _hls_to_colour(hue, lightness, saturation)
	while saturation < 0.98 and colourfulness(_rgb_tuple(colour)) < target_chroma:
		saturation += 0.03
		colour = _hls_to_colour(hue, lightness, saturation)
	return colour


def _neutral_hue(summary: ArtSummary) -> float:
	"""The artwork's faint colour bias, used to warm or cool a grey theme."""
	weights = [swatch.coverage * swatch.colourfulness for swatch in summary.swatches]
	total = sum(weights)
	if total <= 0:
		return 0.08
	x_axis = sum(w * math.cos(math.tau * s.hue) for w, s in zip(weights, summary.swatches, strict=True))
	y_axis = sum(w * math.sin(math.tau * s.hue) for w, s in zip(weights, summary.swatches, strict=True))
	return (math.atan2(y_axis, x_axis) / math.tau) % 1


def _monochrome_theme(summary: ArtSummary, *, light_mode: bool) -> tuple[ColourRGBA, ColourRGBA, float, float]:
	"""Surfaces for artwork with no usable hue.

	Tone is the only structure available, so it is spent freely: a pale track
	list against a deep side panel, stopping short of pure black.
	"""
	hue = _neutral_hue(summary)
	background_lightness = 0.90 if light_mode else 0.085
	side_lightness = 0.13 if light_mode else 0.255
	background = _hls_to_colour(hue, background_lightness, 0.020)
	side = _hls_to_colour(hue, side_lightness, 0.030)
	step = -0.02 if light_mode else 0.02
	for _iteration in range(8):
		if _colour_distance(_rgb_tuple(background), _rgb_tuple(side)) >= MONOCHROME_SEPARATION:
			break
		side_lightness = _clamp(side_lightness + step, 0.06, 0.94)
		side = _hls_to_colour(hue, side_lightness, 0.030)
	return background, side, hue, 0.10


def _chromatic_theme(
	summary: ArtSummary,
	primary: HueFamily,
	*,
	light_mode: bool,
) -> tuple[ColourRGBA, ColourRGBA, float, float]:
	"""Surfaces and accent hue for artwork that carries a usable hue."""
	hue = primary.hue
	# A mostly white cover with a small colourful logo should stay near white
	# and spend its colour on the accent; a cover that is colour all over should
	# commit. Both scale with how much colour the artwork actually holds.
	commitment = min(1.0, 0.40 + summary.chromatic_mass / 0.40)
	presence = min(1.0, 0.55 + summary.chromatic_mass / 0.35)

	if light_mode:
		background_lightness = _clamp(0.89 - (1 - summary.median_lightness) * 0.14, 0.79, 0.90)
		background_saturation = _clamp(primary.saturation * 0.58 * commitment, 0.02, 0.44)
		background_target = 0.24 * presence
	else:
		# Follow the primary's own tone as well as the artwork's overall tone: a
		# cover whose colour lives at mid lightness turns to mud if the
		# background is dropped to near-black regardless.
		background_lightness = _clamp(0.075 + summary.median_lightness * 0.12 + primary.lightness * 0.16, 0.10, 0.21)
		background_saturation = _clamp(primary.saturation * 0.92, 0.10, 0.58)
		background_target = 0.30 * presence
	background = _tinted(hue, background_lightness, background_saturation, background_target)

	companion = _companion_family(summary, primary)
	side_hue = companion.hue if companion is not None else hue
	side_source = companion if companion is not None else primary
	if light_mode:
		side_lightness = _clamp(background_lightness - 0.13, 0.64, 0.83)
		side_saturation = _clamp(side_source.saturation * 0.72 * commitment, 0.03, 0.50)
		side_target = 0.34 * presence
	else:
		side_lightness = _clamp(background_lightness + 0.115, 0.17, 0.30)
		side_saturation = _clamp(side_source.saturation * 0.95, 0.12, 0.60)
		side_target = 0.40 * presence
	side = _tinted(side_hue, side_lightness, side_saturation, side_target)

	# Guarantee the panels read as two surfaces rather than one.
	step = -0.022 if light_mode else 0.022
	for _iteration in range(8):
		if _colour_distance(_rgb_tuple(background), _rgb_tuple(side)) >= 0.055:
			break
		side_lightness = _clamp(side_lightness + step, 0.06, 0.94)
		side = _tinted(side_hue, side_lightness, side_saturation, side_target)

	accent = _accent_family(summary, hue)
	accent_hue = accent.hue if accent is not None else hue
	accent_saturation = _clamp((accent.saturation if accent is not None else primary.saturation) * 1.05, 0.45, 0.85)
	return background, side, accent_hue, accent_saturation


def generate_duotone_art_theme(image: Image.Image, summary: ArtSummary | None = None) -> ArtTheme:
	"""Generate a theme with deliberate separation between the two surfaces."""
	if summary is None:
		summary = measure_artwork(image)
	light_mode = summary.median_lightness >= 0.62
	primary = _primary_family(summary)

	if primary is None:
		background, side, accent_hue, accent_saturation = _monochrome_theme(summary, light_mode=light_mode)
		hue = accent_hue
	else:
		background, side, accent_hue, accent_saturation = _chromatic_theme(summary, primary, light_mode=light_mode)
		hue = primary.hue

	prefer_light = not light_mode
	title = _readable_tint((background, side), hue, 0.06, prefer_light, 5.4)
	artist = _readable_tint((background, side), hue, 0.10, prefer_light, 4.5)
	if primary is None:
		# No hue to preserve, so a plain readable tint is enough.
		accent = _readable_tint((background, side), accent_hue, accent_saturation, prefer_light, 4.5)
	else:
		accent = _readable_identity((background, side), accent_hue, accent_saturation, prefer_light, 4.5)
	return ArtTheme(background, side, title, artist, accent, light_mode)


def _surface_support(summary: ArtSummary, colour: ColourRGBA) -> float:
	"""How much of the artwork sits near this surface's hue."""
	hue, _lightness, _saturation = _rgb_to_hls(colour)
	if colourfulness(_rgb_tuple(colour)) < 0.18:
		# A neutral surface makes no hue claim, so it cannot be unfaithful.
		return 1.0
	return min(
		1.0,
		sum(
			swatch.coverage
			for swatch in summary.swatches
			if is_chromatic(swatch) and _hue_arc_distance(swatch.hue, hue) <= 0.10
		)
		/ 0.12,
	)


def score_theme(theme: ArtTheme, summary: ArtSummary) -> float:
	"""Rate a candidate on visual interest less its safety failures."""
	background = _rgb_tuple(theme.background)
	side = _rgb_tuple(theme.side)
	background_chroma = colourfulness(background)
	side_chroma = colourfulness(side)
	_background_hue, background_lightness, _background_saturation = _rgb_to_hls(background)
	_side_hue, side_lightness, _side_saturation = _rgb_to_hls(side)

	# Reward panel structure up to a point; past that a pair is not structured,
	# it is merely violent.
	separation_score = min(_colour_distance(background, side), 0.26) / 0.26
	# Scale the colour terms by how much colour the artwork offers, with a floor
	# so a pale cover still earns credit for putting its one hue on a panel.
	# Whether that hue is really present is checked by the support penalty.
	available = min(1.0, 0.45 + summary.chromatic_mass / 0.30)
	colour_score = min(1.0, (0.60 * background_chroma + 0.40 * side_chroma) / 0.30) * available
	accent_score = min(1.0, colourfulness(_rgb_tuple(theme.accent)) / 0.55) * available
	interest = 0.42 * separation_score + 0.38 * colour_score + 0.20 * accent_score

	penalty = 0.0
	# A near-white or near-black panel is only mildly wrong on its own; several
	# good pairings put one beside a strongly coloured panel.
	extremes = sum(1 for value in (background_lightness, side_lightness) if value <= 0.045 or value >= 0.955)
	penalty += 0.12 * extremes
	# A near-white panel beside a near-black one carrying none of the cover's
	# colour, scaled so a merely high-contrast pair is not the same mistake.
	tonal_split = abs(background_lightness - side_lightness)
	if tonal_split >= 0.55 and max(background_chroma, side_chroma) < 0.30:
		# Only a fault when the artwork had colour that the pairing threw away.
		# On greyscale art a wide split is the correct answer, not a mistake.
		discarded = min(1.0, summary.chromatic_mass / 0.25)
		penalty += 0.55 * min(1.0, (tonal_split - 0.55) / 0.30) * discarded
	# A large surface at near-full saturation glares rather than reads.
	for lightness, saturation in (_rgb_to_hls(background)[1:], _rgb_to_hls(side)[1:]):
		if saturation >= 0.72 and 0.30 <= lightness <= 0.70:
			penalty += 0.45 * min(1.0, (saturation - 0.72) / 0.20)
	penalty += 0.35 * (1 - _surface_support(summary, theme.background))
	penalty += 0.20 * (1 - _surface_support(summary, theme.side))
	# Tonal-mode mistakes: a bright cover rendered dim, or a dark one rendered
	# pale. The first is the warm-to-mud failure.
	if not theme.light_mode and summary.median_lightness >= 0.70:
		penalty += 0.45
	if theme.light_mode and summary.median_lightness <= 0.30:
		penalty += 0.35
	return interest - penalty


def is_flat_theme(theme: ArtTheme, summary: ArtSummary) -> bool:
	"""Whether a theme is one of the pale, low-contrast results to be corrected.

	True for two surfaces of nearly the same tone with almost no colour in
	either, when the result is light or the artwork was too pale to have driven
	it well. Medium and dark artwork carrying real colour is left alone.
	"""
	background = _rgb_tuple(theme.background)
	side = _rgb_tuple(theme.side)
	flat = (
		_colour_distance(background, side) < FLAT_SEPARATION
		and max(colourfulness(background), colourfulness(side)) < FLAT_CHROMA
	)
	if not flat:
		return False
	return _rgb_to_hls(background)[1] >= LIGHT_THEME_LIGHTNESS or summary.chromatic_mass < PALE_ARTWORK


def select_art_theme(image: Image.Image) -> tuple[ArtTheme, str]:
	"""Correct a flat theme, otherwise keep the routed generator's result.

	The routed generator keeps every cover it already handles. Only when it
	returns a flat result are Duotone and the legacy generator considered.
	"""
	# Imported here because t_art_theme imports this module's selector.
	from tauon.t_modules.t_art_theme import (  # noqa: PLC0415
		generate_original_art_theme,
		generate_routed_art_theme,
	)

	routed = generate_routed_art_theme(image)
	summary = measure_artwork(image)
	if not is_flat_theme(routed, summary):
		return routed, "routed"

	candidates: list[tuple[str, ArtTheme]] = [
		("routed", routed),
		("duotone", generate_duotone_art_theme(image, summary)),
	]
	legacy = generate_original_art_theme(image)
	if legacy is not None:
		candidates.append(("legacy", legacy))

	scored = [(score_theme(theme, summary), name, theme) for name, theme in candidates]
	best_score, best_name, best_theme = max(scored, key=lambda entry: entry[0])
	if best_name == "legacy":
		# The legacy generator assigns raw artwork pixels to roles, so a narrow
		# win is usually a win on noise. Require a clear margin.
		synthesized = max(entry for entry in scored if entry[1] != "legacy")
		if best_score - synthesized[0] < LEGACY_MARGIN:
			return synthesized[2], synthesized[1]
	return best_theme, best_name
