"""Generate a complete Tauon colour theme from album artwork."""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from PIL import Image

from tauon.t_modules.t_extra import ColourRGBA, contrast_ratio

if TYPE_CHECKING:
	from collections.abc import Iterable


@dataclass(frozen=True)
class ArtTheme:
	"""The five frozen Snapshot roles plus the artwork's tonal mode."""

	background: ColourRGBA
	side: ColourRGBA
	title: ColourRGBA
	artist: ColourRGBA
	accent: ColourRGBA
	light_mode: bool


@dataclass(frozen=True)
class _HueFamily:
	"""A chromatic hue with enough repeated palette support to be structural."""

	coverage: float
	hue: float
	lightness: float
	saturation: float
	chroma: float


def _clamp(value: float, low: float, high: float) -> float:
	return min(max(value, low), high)


def _rgb_tuple(colour: ColourRGBA) -> tuple[int, int, int]:
	return colour.r, colour.g, colour.b


def _rgb_to_hls(colour: tuple[int, int, int] | ColourRGBA) -> tuple[float, float, float]:
	if isinstance(colour, ColourRGBA):
		colour = _rgb_tuple(colour)
	return colorsys.rgb_to_hls(*(channel / 255 for channel in colour))


def _hls_to_colour(hue: float, lightness: float, saturation: float, alpha: int = 255) -> ColourRGBA:
	channels = colorsys.hls_to_rgb(hue % 1, _clamp(lightness, 0, 1), _clamp(saturation, 0, 1))
	return ColourRGBA(*(round(channel * 255) for channel in channels), alpha)


def _colour_distance(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
	red_mean = (first[0] + second[0]) / 2
	red_delta = first[0] - second[0]
	green_delta = first[1] - second[1]
	blue_delta = first[2] - second[2]
	return (
		math.sqrt(
			(2 + red_mean / 256) * red_delta**2 + 4 * green_delta**2 + (2 + (255 - red_mean) / 256) * blue_delta**2,
		)
		/ 765
	)


def _hue_distance(first: tuple[int, int, int], second: tuple[int, int, int]) -> float:
	first_hue, _first_lightness, first_saturation = _rgb_to_hls(first)
	second_hue, _second_lightness, second_saturation = _rgb_to_hls(second)
	if first_saturation < 0.08 or second_saturation < 0.08:
		return 0
	distance = abs(first_hue - second_hue)
	return min(distance, 1 - distance)


def _hue_arc_distance(first: float, second: float) -> float:
	distance = abs(first - second)
	return min(distance, 1 - distance)


def _quantized_palette(image: Image.Image, count: int = 12) -> list[tuple[int, tuple[int, int, int]]]:
	working = image.convert("RGB")
	working.thumbnail((160, 160), Image.Resampling.LANCZOS)
	quantized = working.quantize(colors=count, method=Image.Quantize.MEDIANCUT)
	palette_values = quantized.getpalette()
	if palette_values is None:
		return [(1, (127, 127, 127))]
	result = []
	for population, palette_index in sorted(quantized.getcolors() or [], reverse=True):
		offset = palette_index * 3
		colour = tuple(palette_values[offset : offset + 3])
		result.append((population, colour))
	return result or [(1, (127, 127, 127))]


def _edge_palette(image: Image.Image) -> list[tuple[int, tuple[int, int, int]]]:
	working = image.convert("RGB")
	working.thumbnail((96, 96), Image.Resampling.LANCZOS)
	border = max(2, round(min(working.size) * 0.08))
	pixels = [
		working.getpixel((x_pos, y_pos))
		for y_pos in range(working.height)
		for x_pos in range(working.width)
		if (x_pos < border or y_pos < border or x_pos >= working.width - border or y_pos >= working.height - border)
	]
	if not pixels:
		return _quantized_palette(working, 8)
	strip = Image.new("RGB", (len(pixels), 1))
	strip.putdata(pixels)
	return _quantized_palette(strip, 8)


def _minimum_contrast(colour: ColourRGBA, backgrounds: Iterable[ColourRGBA]) -> float:
	return min(contrast_ratio(colour, background) for background in backgrounds)


def _readable_tint(
	backgrounds: Iterable[ColourRGBA],
	hue: float,
	saturation: float,
	prefer_light: bool,
	minimum: float,
	*,
	soft: bool = True,
	alpha: int = 255,
) -> ColourRGBA:
	backgrounds = tuple(backgrounds)
	lightness = (0.88 if prefer_light else 0.14) if soft else (0.94 if prefer_light else 0.08)
	step = 0.012 if prefer_light else -0.012
	iterations = 10 if soft else 64
	for _iteration in range(iterations):
		candidate = _hls_to_colour(hue, lightness, saturation, alpha)
		if _minimum_contrast(candidate, backgrounds) >= minimum:
			return candidate
		lightness = _clamp(lightness + step, 0.01, 0.99)
	if soft:
		return _readable_tint(
			backgrounds,
			hue,
			saturation,
			prefer_light,
			minimum,
			soft=False,
			alpha=alpha,
		)
	fallbacks = (ColourRGBA(244, 244, 244, alpha), ColourRGBA(16, 16, 16, alpha))
	return max(fallbacks, key=lambda colour: _minimum_contrast(colour, backgrounds))


def _readable_identity(
	backgrounds: Iterable[ColourRGBA],
	hue: float,
	saturation: float,
	prefer_light: bool,
	minimum: float,
) -> ColourRGBA:
	"""Preserve a vivid identity colour while moving only as far as contrast needs."""
	backgrounds = tuple(backgrounds)
	lightness_options = (
		(0.55, 0.59, 0.63, 0.67, 0.71, 0.75, 0.79, 0.83, 0.87)
		if prefer_light
		else (0.42, 0.38, 0.34, 0.30, 0.26, 0.22, 0.18, 0.14, 0.10)
	)
	for lightness in lightness_options:
		candidate = _hls_to_colour(hue, lightness, saturation)
		if _minimum_contrast(candidate, backgrounds) >= minimum:
			return candidate
	return _readable_tint(backgrounds, hue, saturation, prefer_light, minimum)


def generate_art_theme(image: Image.Image) -> ArtTheme:
	"""Generate the frozen Guided V4 / WIP Snapshot palette."""
	palette = _quantized_palette(image, 16)
	total = max(1, sum(population for population, _colour in palette))
	mean_luminance = sum(contrast_luminance(colour) * population for population, colour in palette) / total
	mean_saturation = sum(_rgb_to_hls(colour)[2] * population for population, colour in palette) / total
	chromatic_mass = (
		sum(
			population
			for population, colour in palette
			if _rgb_to_hls(colour)[2] >= 0.28 and (max(colour) - min(colour)) / 255 >= 0.18
		)
		/ total
	)
	neutral_entries = [
		entry for entry in palette if _rgb_to_hls(entry[1])[2] < 0.18 or (max(entry[1]) - min(entry[1])) / 255 < 0.14
	]
	neutral_mass = sum(population for population, _colour in neutral_entries) / total
	neutral_profile = neutral_mass >= 0.48
	neutral_art = (mean_saturation < 0.16 and chromatic_mass < 0.20) or neutral_profile
	eligible = [entry for entry in palette if entry[0] / total >= 0.025] or palette

	def structural_score(entry: tuple[int, tuple[int, int, int]]) -> float:
		population, colour = entry
		coverage = population / total
		_hue, lightness, saturation = _rgb_to_hls(colour)
		chroma = (max(colour) - min(colour)) / 255
		tone = 0.55 + 0.45 * math.sin(math.pi * lightness) ** 0.55
		if neutral_art:
			expression = 0.72 + 0.28 * (1 - saturation)
		else:
			expression = 0.24 + 1.05 * chroma + 0.35 * saturation
			if chromatic_mass > 0.24 and chroma < 0.17:
				expression *= 0.48
			elif chromatic_mass > 0.24 and chroma < 0.25 and 0.22 < lightness < 0.70:
				expression *= 0.76
		return coverage**0.43 * expression * tone

	if neutral_profile:
		neutral_total = sum(population for population, _colour in neutral_entries)
		primary = tuple(
			round(sum(population * colour[channel] for population, colour in neutral_entries) / neutral_total)
			for channel in range(3)
		)
	else:
		primary = max(eligible, key=structural_score)[1]
	primary_hue, primary_lightness, primary_saturation = _rgb_to_hls(primary)
	light_mode = mean_luminance >= 0.47

	if not light_mode and primary_lightness > 0.62 and (primary_hue <= 0.19 or primary_hue >= 0.92):
		dark_role_candidates = [
			entry for entry in eligible if 0.10 <= _rgb_to_hls(entry[1])[1] <= 0.58 and _rgb_to_hls(entry[1])[2] >= 0.16
		]
		if dark_role_candidates:
			primary = max(dark_role_candidates, key=structural_score)[1]
			primary_hue, primary_lightness, primary_saturation = _rgb_to_hls(primary)

	if light_mode:
		background_lightness = _clamp(0.76 + (mean_luminance - 0.47) * 0.22, 0.76, 0.86)
	else:
		background_lightness = _clamp(0.18 + mean_luminance * 0.24, 0.18, 0.29)
	if neutral_art:
		background_saturation = _clamp(primary_saturation * 0.62, 0.025, 0.13)
	else:
		background_saturation = _clamp(primary_saturation * 0.88, 0.18, 0.64)
		if not light_mode:
			background_saturation = min(
				background_saturation,
				_clamp(0.30 + mean_luminance * 0.45, 0.32, 0.46),
			)
	background = _hls_to_colour(primary_hue, background_lightness, background_saturation)

	support_candidates = [
		entry
		for entry in eligible
		if entry[1] != primary
		and (_hue_distance(primary, entry[1]) <= 0.13 or (neutral_art and _rgb_to_hls(entry[1])[2] < 0.18))
	]
	if support_candidates:
		support = max(
			support_candidates,
			key=lambda entry: structural_score(entry) * (0.55 + _colour_distance(primary, entry[1])),
		)[1]
	else:
		support = primary
	support_hue, _support_lightness, support_saturation = _rgb_to_hls(support)
	if neutral_art:
		side_saturation = _clamp(support_saturation * 0.62, 0.02, 0.12)
	else:
		side_saturation = _clamp(support_saturation * 0.80, 0.15, 0.56)
		if not light_mode:
			side_saturation = min(
				side_saturation,
				_clamp(0.32 + mean_luminance * 0.48, 0.34, 0.49),
			)

	edges = _edge_palette(image)
	if light_mode:
		lightness_options = [_clamp(background_lightness + offset, 0.66, 0.91) for offset in (-0.11, -0.07, 0.07, 0.11)]
	else:
		lightness_options = [
			_clamp(background_lightness + offset, 0.10, 0.36) for offset in (-0.10, -0.065, 0.065, 0.10)
		]

	def side_score(lightness: float) -> float:
		candidate = _hls_to_colour(support_hue, lightness, side_saturation)
		edge_separation = sum(
			population * _colour_distance(_rgb_tuple(candidate), colour) for population, colour in edges
		) / max(1, sum(population for population, _colour in edges))
		return (
			edge_separation
			+ 0.30 * _colour_distance(_rgb_tuple(background), _rgb_tuple(candidate))
			- 0.20 * abs(lightness - background_lightness)
		)

	side = _hls_to_colour(support_hue, max(lightness_options, key=side_score), side_saturation)
	accent_candidates = [entry for entry in palette if entry[0] / total >= 0.012]
	accent_source = max(
		accent_candidates,
		key=lambda entry: (
			structural_score(entry) * (0.35 + _colour_distance(primary, entry[1])) * (0.30 + _rgb_to_hls(entry[1])[2])
		),
	)[1]
	accent_hue, _accent_lightness, accent_saturation = _rgb_to_hls(accent_source)
	prefer_light = not light_mode
	title = _readable_tint((background, side), primary_hue, 0.07, prefer_light, 5.4)
	artist = _readable_tint((background, side), support_hue, 0.09, prefer_light, 4.5)
	accent = _readable_tint(
		(background, side),
		accent_hue,
		_clamp(accent_saturation, 0.46, 0.78),
		prefer_light,
		4.5,
	)
	return ArtTheme(background, side, title, artist, accent, light_mode)


def _supported_hue_families(
	palette: list[tuple[int, tuple[int, int, int]]],
	total: int,
) -> list[_HueFamily]:
	"""Group neighbouring swatches so fragmented colour still counts as evidence."""
	chromatic_entries = []
	for population, colour in palette:
		hue, lightness, saturation = _rgb_to_hls(colour)
		chroma = (max(colour) - min(colour)) / 255
		if population / total >= 0.006 and saturation >= 0.22 and chroma >= 0.12:
			chromatic_entries.append((population, hue, lightness, saturation, chroma))

	candidates = []
	for _seed_population, seed_hue, _seed_lightness, _seed_saturation, _seed_chroma in chromatic_entries:
		members = [entry for entry in chromatic_entries if _hue_arc_distance(seed_hue, entry[1]) <= 0.085]
		coverage = sum(entry[0] for entry in members) / total
		weights = [entry[0] * (0.35 + entry[4]) for entry in members]
		weight_total = sum(weights)
		if weight_total <= 0:
			continue
		x_axis = sum(weight * math.cos(math.tau * entry[1]) for weight, entry in zip(weights, members, strict=True))
		y_axis = sum(weight * math.sin(math.tau * entry[1]) for weight, entry in zip(weights, members, strict=True))
		hue = (math.atan2(y_axis, x_axis) / math.tau) % 1
		lightness = sum(weight * entry[2] for weight, entry in zip(weights, members, strict=True)) / weight_total
		saturation = sum(weight * entry[3] for weight, entry in zip(weights, members, strict=True)) / weight_total
		chroma = sum(weight * entry[4] for weight, entry in zip(weights, members, strict=True)) / weight_total
		candidates.append(_HueFamily(coverage, hue, lightness, saturation, chroma))

	# Sliding hue windows produce several nearly identical candidates. Retain
	# only one representative per family, preferring broad and vivid support.
	candidates.sort(key=lambda family: family.coverage * (0.65 + family.chroma), reverse=True)
	families = []
	for candidate in candidates:
		if all(_hue_arc_distance(candidate.hue, family.hue) >= 0.105 for family in families):
			families.append(candidate)
	return families


def _dark_identity_theme(
	snapshot: ArtTheme,
	identity: _HueFamily,
	mean_luminance: float,
) -> ArtTheme:
	"""Pair a genuinely dark artwork structure with its vivid identity hue."""
	background_lightness = _clamp(0.085 + mean_luminance * 0.20, 0.09, 0.12)
	background = _hls_to_colour(identity.hue, background_lightness, 0.055)
	side = _hls_to_colour(
		identity.hue,
		_clamp(identity.lightness * 0.82, 0.30, 0.36),
		_clamp(identity.saturation * 1.06, 0.62, 0.78),
	)
	title = _readable_tint((background,), identity.hue, 0.045, True, 5.4)
	artist = _readable_tint((background,), identity.hue, 0.12, True, 4.5)
	accent = _readable_identity(
		(background,),
		identity.hue,
		_clamp(identity.saturation, 0.58, 0.82),
		True,
		4.5,
	)
	return ArtTheme(background, side, title, artist, accent, snapshot.light_mode)


def _colour_duet_theme(first: _HueFamily, second: _HueFamily) -> ArtTheme:
	"""Give two well-supported, tonally distinct artwork colours separate roles."""
	darker, lighter = sorted((first, second), key=lambda family: family.lightness)
	light_mode = lighter.lightness >= 0.58
	if light_mode:
		background = _hls_to_colour(
			lighter.hue,
			_clamp(0.75 + (lighter.lightness - 0.58) * 0.22, 0.75, 0.84),
			_clamp(lighter.saturation * 0.68, 0.20, 0.46),
		)
		side = _hls_to_colour(
			darker.hue,
			_clamp(darker.lightness, 0.36, 0.48),
			_clamp(darker.saturation * 0.88, 0.28, 0.58),
		)
		identity = darker
	else:
		background = _hls_to_colour(
			darker.hue,
			_clamp(darker.lightness * 0.68, 0.13, 0.20),
			_clamp(darker.saturation * 0.74, 0.24, 0.48),
		)
		side = _hls_to_colour(
			lighter.hue,
			_clamp(lighter.lightness * 0.82, 0.28, 0.37),
			_clamp(lighter.saturation * 0.96, 0.44, 0.70),
		)
		identity = lighter

	prefer_light = not light_mode
	title = _readable_tint((background,), darker.hue, 0.055, prefer_light, 5.4)
	artist = _readable_tint((background,), lighter.hue, 0.11, prefer_light, 4.5)
	accent = _readable_identity(
		(background,),
		identity.hue,
		_clamp(identity.saturation, 0.52, 0.80),
		prefer_light,
		4.5,
	)
	return ArtTheme(background, side, title, artist, accent, light_mode)


def generate_liberal_art_theme(image: Image.Image) -> ArtTheme:
	"""Route strong, repeatable colour opportunities around frozen Snapshot.

	Snapshot remains the default. A cover may take an expressive route when it
	either contains a substantial dark base plus a supported identity colour, or
	two supported hue families with clear tonal separation. Light artwork may
	also use corrected Original when it has a broad neutral field and Original
	finds a safe chromatic secondary surface. These conditions avoid promoting
	isolated pixels while permitting the high-contrast pairings that the
	conservative Snapshot intentionally suppresses.
	"""
	snapshot = generate_art_theme(image)
	palette = _quantized_palette(image, 24)
	total = max(1, sum(population for population, _colour in palette))
	mean_luminance = sum(contrast_luminance(colour) * population for population, colour in palette) / total
	dark_mass = sum(population for population, colour in palette if contrast_luminance(colour) <= 0.11) / total
	dark_neutral_mass = (
		sum(
			population
			for population, colour in palette
			if contrast_luminance(colour) <= 0.11
			and ((max(colour) - min(colour)) / 255 <= 0.18 or _rgb_to_hls(colour)[1] <= 0.09)
		)
		/ total
	)
	families = _supported_hue_families(palette, total)

	if families:
		identity = max(families, key=lambda family: family.coverage * (0.50 + family.chroma))
		if (
			mean_luminance <= 0.18
			and dark_mass >= 0.52
			and dark_neutral_mass >= 0.32
			and identity.coverage >= 0.16
			and identity.chroma >= 0.26
		):
			return _dark_identity_theme(snapshot, identity, mean_luminance)

	pairs = []
	for index, first in enumerate(families):
		for second in families[index + 1 :]:
			hue_separation = _hue_arc_distance(first.hue, second.hue)
			tone_separation = abs(first.lightness - second.lightness)
			if (
				min(first.coverage, second.coverage) >= 0.12
				and first.coverage + second.coverage >= 0.34
				and min(first.chroma, second.chroma) >= 0.18
				and hue_separation >= 0.18
				and tone_separation >= 0.16
			):
				score = (
					(first.coverage + second.coverage)
					* (0.55 + (first.chroma + second.chroma) / 2)
					* (0.65 + hue_separation)
					* (0.65 + tone_separation)
				)
				pairs.append((score, first, second))
	if pairs:
		_score, first, second = max(pairs, key=lambda pair: pair[0])
		if mean_luminance < 0.47:
			return _colour_duet_theme(first, second)

	# Snapshot tends to mute pale, largely neutral covers even when Original's
	# second frequent colour is a clean, usable source of personality. Route
	# only this narrow light-art case; near-black or effectively neutral second
	# surfaces remain with Snapshot, as does fully vivid light artwork.
	neutral_mass = (
		sum(
			population
			for population, colour in palette
			if _rgb_to_hls(colour)[2] < 0.18 or (max(colour) - min(colour)) / 255 < 0.14
		)
		/ total
	)
	if mean_luminance >= 0.50 and neutral_mass >= 0.45:
		original = generate_original_art_theme(image)
		if original is not None:
			_side_hue, side_lightness, side_saturation = _rgb_to_hls(original.side)
			if side_lightness >= 0.20 and side_saturation >= 0.25:
				return original
	return snapshot


def _original_readable_text(
	background: ColourRGBA,
	colour: ColourRGBA,
	minimum: float,
	fallback_saturation: float,
) -> ColourRGBA:
	"""Repair Original's extracted text without discarding its hue."""
	if contrast_ratio(colour, background) >= minimum:
		return colour
	background_hue, _background_lightness, _background_saturation = _rgb_to_hls(background)
	hue, _lightness, saturation = _rgb_to_hls(colour)
	if saturation < 0.06:
		hue = background_hue
	prefer_light = contrast_luminance(_rgb_tuple(background)) < 0.42
	lightness = 0.92 if prefer_light else 0.12
	step = -0.015 if prefer_light else 0.015
	for _iteration in range(42):
		candidate = _hls_to_colour(hue, lightness, _clamp(saturation, fallback_saturation, 0.28))
		if contrast_ratio(candidate, background) >= minimum:
			return candidate
		lightness = _clamp(lightness + step, 0.02, 0.98)
	fallbacks = (ColourRGBA(238, 238, 238, 255), ColourRGBA(24, 24, 24, 255))
	return max(fallbacks, key=lambda candidate: contrast_ratio(candidate, background))


def generate_original_art_theme(image: Image.Image) -> ArtTheme | None:
	"""Extract Original's five roles and repair its foreground contrast."""
	working = image.convert("RGB")
	working.thumbnail((50, 50), Image.Resampling.LANCZOS)
	pixels = sorted(working.getcolors(maxcolors=2500) or [], key=lambda item: item[0], reverse=True)
	extracted = []
	for _population, rgb_colour in pixels:
		if not any(
			all(abs(rgb_colour[channel] - _rgb_tuple(prior)[channel]) < 75 for channel in range(3))
			for prior in extracted
		):
			extracted.append(ColourRGBA(*rgb_colour, 255))
	if not extracted:
		return None

	background = extracted[0]
	side = extracted[1] if len(extracted) > 1 else background
	title = extracted[2] if len(extracted) > 2 else ColourRGBA(235, 235, 235, 255)
	artist = extracted[3] if len(extracted) > 3 else ColourRGBA(180, 180, 180, 255)
	accent = max(extracted, key=lambda candidate: contrast_ratio(candidate, background))
	# Preserve the old production algorithm's first-pass repairs before applying
	# the stronger correction adopted as the survey's new Original baseline.
	if contrast_ratio(artist, background) < 1.9:
		artist = max(
			(ColourRGBA(25, 25, 25, 255), ColourRGBA(220, 220, 220, 255)),
			key=lambda candidate: contrast_ratio(candidate, background),
		)
	if contrast_ratio(title, background) < 1.9:
		title = max(
			(ColourRGBA(60, 60, 60, 255), ColourRGBA(180, 180, 180, 255)),
			key=lambda candidate: contrast_ratio(candidate, background),
		)
	title = _original_readable_text(background, title, 4.5, 0.07)
	artist = _original_readable_text(background, artist, 4.0, 0.06)
	accent = _original_readable_text(background, accent, 3.5, 0.34)
	return ArtTheme(
		background,
		side,
		title,
		artist,
		accent,
		# Original can return an unmodified middle-valued surface. Choose the
		# polarity with the stronger black/white contrast rather than applying
		# Snapshot's overall-art luminance threshold to this one raw swatch.
		contrast_luminance(_rgb_tuple(background)) >= 0.18,
	)


def apply_original_art_theme(colours: object, image: Image.Image) -> ArtTheme | None:
	"""Expand Original's corrected five-role palette over the complete theme."""
	theme = generate_original_art_theme(image)
	if theme is None:
		return None
	_apply_complete_theme(colours, theme)
	post_config = getattr(colours, "post_config", None)
	if callable(post_config):
		post_config()
		# Match the liberal path: retain useful post_config bookkeeping without
		# allowing its legacy fallbacks to replace generated role colours.
		_apply_complete_theme(colours, theme)
	return theme


def contrast_luminance(colour: tuple[int, int, int]) -> float:
	"""Return WCAG relative luminance for an RGB tuple."""
	linear = []
	for channel in colour:
		value = channel / 255
		linear.append(value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4)
	return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _surface_variant(
	colour: ColourRGBA,
	*,
	lightness: float | None = None,
	lightness_delta: float = 0,
	saturation_factor: float = 1,
	saturation_delta: float = 0,
	hue_delta: float = 0,
	alpha: int = 255,
) -> ColourRGBA:
	hue, base_lightness, saturation = _rgb_to_hls(colour)
	if lightness is None:
		lightness = base_lightness + lightness_delta
	return _hls_to_colour(
		hue + hue_delta,
		lightness,
		_clamp(saturation * saturation_factor + saturation_delta, 0.01, 0.72),
		alpha,
	)


def _mix_hls(first: ColourRGBA, second: ColourRGBA, amount: float, alpha: int = 255) -> ColourRGBA:
	first_hue, first_lightness, first_saturation = _rgb_to_hls(first)
	second_hue, second_lightness, second_saturation = _rgb_to_hls(second)
	hue_delta = ((second_hue - first_hue + 0.5) % 1) - 0.5
	if first_saturation < 0.05:
		first_hue = second_hue
	if second_saturation < 0.05:
		hue_delta = 0
	return _hls_to_colour(
		first_hue + hue_delta * amount,
		first_lightness + (second_lightness - first_lightness) * amount,
		first_saturation + (second_saturation - first_saturation) * amount,
		alpha,
	)


def _alpha(colour: ColourRGBA, alpha: int) -> ColourRGBA:
	return ColourRGBA(colour.r, colour.g, colour.b, alpha)


def _apply_complete_theme(colours: object, theme: ArtTheme) -> None:
	"""Expand Snapshot's five roles over every colour-bearing Tauon role."""
	background = theme.background
	side = theme.side
	background_hue, background_lightness, background_saturation = _rgb_to_hls(background)
	side_hue, _side_lightness, _side_saturation = _rgb_to_hls(side)
	accent_hue, _accent_lightness, accent_saturation = _rgb_to_hls(theme.accent)
	prefer_light = not theme.light_mode

	if theme.light_mode:
		bar_lightness = _clamp(background_lightness - 0.13, 0.58, 0.76)
		top = _hls_to_colour(
			background_hue,
			bar_lightness,
			_clamp(background_saturation * 0.86, 0.02, 0.48),
		)
		surface_step = -1
	else:
		bar_lightness = _clamp(background_lightness - 0.075, 0.08, 0.23)
		top = _hls_to_colour(
			background_hue,
			bar_lightness,
			_clamp(background_saturation * 0.82, 0.02, 0.46),
		)
		surface_step = 1
	bottom = ColourRGBA(top.r, top.g, top.b, top.a)

	gallery = _surface_variant(background, lightness_delta=surface_step * 0.035, saturation_factor=0.90)
	queue = _surface_variant(side, lightness_delta=surface_step * 0.025, saturation_factor=0.94)
	lyrics_surface = _surface_variant(side, lightness_delta=-surface_step * 0.018, saturation_factor=0.88)
	menu_surface = _surface_variant(bottom, lightness_delta=-surface_step * 0.035, saturation_factor=0.90)
	box_surface = _surface_variant(top, lightness_delta=surface_step * 0.025, saturation_factor=0.82)
	mini_surface = _surface_variant(bottom, lightness_delta=-surface_step * 0.025, saturation_factor=0.92)
	column_surface = _surface_variant(background, lightness_delta=-surface_step * 0.045, saturation_factor=0.88)
	queue_card = _surface_variant(queue, lightness_delta=surface_step * 0.045, saturation_factor=0.92)

	# Use the full extracted identity colour throughout the tracklist. This is
	# deliberately the colour previously reserved for the playing artist; a
	# stronger variant below distinguishes the playing row.
	track_accent = theme.accent
	if contrast_ratio(track_accent, background) < 4.5:
		track_accent = _readable_identity(
			(background,),
			accent_hue,
			_clamp(accent_saturation, 0.46, 0.82),
			prefer_light,
			4.5,
		)
	track_secondary = theme.artist
	track_playing = _readable_identity(
		(background,),
		accent_hue,
		_clamp(accent_saturation * 1.08, 0.64, 0.88),
		prefer_light,
		5.4,
	)
	top_title = _readable_tint((top,), background_hue, 0.07, prefer_light, 5.4)
	top_secondary = _readable_tint((top,), side_hue, 0.09, prefer_light, 4.5)
	top_accent = _readable_tint((top,), accent_hue, _clamp(accent_saturation, 0.46, 0.78), prefer_light, 4.5)
	bottom_title = _readable_tint((bottom,), side_hue, 0.07, prefer_light, 5.4)
	bottom_secondary = _readable_tint((bottom,), background_hue, 0.09, prefer_light, 4.5)
	bottom_accent = _readable_tint(
		(bottom,),
		accent_hue,
		_clamp(accent_saturation, 0.46, 0.78),
		prefer_light,
		4.5,
	)
	# Tauon's bundled themes keep idle transport and mode controls close to
	# their panel (usually around 1.4-2.1:1), then make hover/active states
	# conspicuously brighter. Do not reuse secondary-text contrast here or the
	# controls look permanently active.
	bottom_button_off = _mix_hls(bottom, bottom_secondary, 0.24)
	top_button_off = _mix_hls(top, top_secondary, 0.24)
	# Original can put a light side panel beside a dark center panel or vice
	# versa. Side-panel labels therefore need their own polarity and must be
	# corrected against the surface they are actually rendered on.
	black = ColourRGBA(0, 0, 0, 255)
	white = ColourRGBA(255, 255, 255, 255)
	side_prefers_light = contrast_ratio(white, side) >= contrast_ratio(black, side)
	side_title = _readable_tint((side,), side_hue, 0.07, side_prefers_light, 5.2)
	side_secondary = _readable_tint((side,), background_hue, 0.09, side_prefers_light, 4.2)
	if contrast_ratio(side_title, side) < 5.2:
		side_title = max((black, white), key=lambda colour: contrast_ratio(colour, side))
	if contrast_ratio(side_secondary, side) < 4.2:
		side_secondary = max((black, white), key=lambda colour: contrast_ratio(colour, side))
	menu_title = _readable_tint((menu_surface,), side_hue, 0.06, prefer_light, 5.2)
	menu_secondary = _readable_tint((menu_surface,), background_hue, 0.07, prefer_light, 3.5)
	box_title = _readable_tint((box_surface,), background_hue, 0.06, prefer_light, 5.4)
	box_text = _readable_tint((box_surface,), side_hue, 0.07, prefer_light, 4.5)
	box_secondary = _readable_tint((box_surface,), side_hue, 0.06, prefer_light, 3.5)
	lyrics_text = _readable_tint((lyrics_surface,), side_hue, 0.07, prefer_light, 4.5)
	lyrics_accent = _readable_tint(
		(lyrics_surface,),
		accent_hue,
		_clamp(accent_saturation, 0.48, 0.80),
		prefer_light,
		4.5,
	)
	mini_title = _readable_tint((mini_surface,), background_hue, 0.06, prefer_light, 5.4)
	mini_secondary = _readable_tint((mini_surface,), side_hue, 0.07, prefer_light, 4.0)
	column_text = _readable_tint((column_surface,), background_hue, 0.06, prefer_light, 4.5)

	separator = _mix_hls(background, track_secondary, 0.28)
	border = _mix_hls(box_surface, box_text, 0.22)
	tab_background = _mix_hls(top, background, 0.24)
	tab_highlight = _mix_hls(tab_background, top_title, 0.13)
	tab_active = _mix_hls(tab_background, track_accent, 0.18)
	tab_text = _readable_tint((tab_background, tab_highlight), side_hue, 0.06, prefer_light, 4.5)
	tab_text_active = _readable_tint((tab_active,), accent_hue, 0.08, prefer_light, 4.5)
	seek_background = _mix_hls(bottom, bottom_title, 0.15)
	seek_fill = _readable_tint((seek_background,), accent_hue, _clamp(accent_saturation, 0.42, 0.72), prefer_light, 3.2)
	button_surface = _mix_hls(box_surface, box_text, 0.10)
	button_highlight = _mix_hls(box_surface, box_text, 0.18)
	menu_highlight = _mix_hls(menu_surface, track_accent, 0.18)

	values = {
		"window_frame": top,
		"gallery_highlight": _readable_tint((gallery,), accent_hue, accent_saturation, prefer_light, 3.5),
		"index_playing": track_playing,
		"time_text": track_playing,
		"artist_playing": track_playing,
		"album_text": track_accent,
		"album_playing": track_playing,
		"top_panel_background": top,
		"corner_button": top_button_off,
		"corner_button_active": top_accent,
		"corner_icon": top_secondary,
		"status_text_normal": top_secondary,
		"status_text_over": top_title,
		"status_info_text": top_accent,
		"queue_background": queue,
		"side_panel_background": side,
		"lyrics_panel_background": lyrics_surface,
		"gallery_background": gallery,
		"playlist_panel_background": background,
		"title_text": track_accent,
		"playlist_text_missing": _readable_tint((background,), side_hue, 0.05, prefer_light, 3.2),
		"row_playing_highlight": _alpha(track_accent, 24),
		"bar_time": track_accent,
		"star_line": track_secondary,
		"folder_title": track_secondary,
		"folder_line": separator,
		"media_buttons_off": bottom_button_off,
		"media_buttons_over": bottom_title,
		"media_buttons_active": bottom_accent,
		"time_playing": bottom_title,
		"index_text": track_accent,
		"title_playing": track_playing,
		"row_select_highlight": _alpha(track_accent, 32),
		"artist_text": track_accent,
		"tab_text_active": tab_text_active,
		"tab_text": tab_text,
		"tab_background": tab_background,
		"tab_highlight": tab_highlight,
		"tab_background_active": tab_active,
		"side_bar_line1": side_title,
		"side_bar_line2": side_secondary,
		"bar_title_text": bottom_title,
		"scroll_colour": _mix_hls(background, track_accent, 0.46),
		"seek_bar_fill": seek_fill,
		"seek_bar_background": seek_background,
		"volume_bar_fill": bottom_accent,
		"volume_bar_background": seek_background,
		"mode_button_off": bottom_button_off,
		"mode_button_over": bottom_title,
		"mode_button_active": bottom_accent,
		"art_box": _mix_hls(side, side_title, 0.18),
		"tb_line": _mix_hls(top, top_secondary, 0.24),
		"vis_colour": bottom_accent,
		"menu_background": menu_surface,
		"menu_text": menu_title,
		"menu_text_disabled": menu_secondary,
		"menu_icons": menu_secondary,
		"menu_highlight_background": menu_highlight,
		"menu_tab": _mix_hls(menu_surface, track_accent, 0.42),
		"lyrics": lyrics_text,
		"active_lyric": lyrics_accent,
		"bottom_panel_colour": bottom,
		"mini_mode_background": mini_surface,
		"mini_mode_border": _mix_hls(mini_surface, mini_title, 0.22),
		"mini_mode_text_1": mini_title,
		"mini_mode_text_2": mini_secondary,
		"playlist_box_background": side,
		"box_background": box_surface,
		"box_border": border,
		"box_text_border": _mix_hls(box_surface, box_text, 0.14),
		"box_text_label": box_secondary,
		"box_title_text": box_title,
		"box_text": box_text,
		"box_sub_text": box_secondary,
		"box_input_text": box_text,
		"box_button_text_highlight": box_title,
		"box_button_text": box_text,
		"box_button_background": button_surface,
		"box_button_background_highlight": button_highlight,
		"box_check_border": _alpha(box_text, 70),
		"window_buttons_bg": _alpha(top_title, 18),
		"window_buttons_bg_over": _alpha(top_title, 34),
		"window_button_icon_off": top_button_off,
		"window_buttons_icon_over": top_title,
		"window_button_x_on": top_accent,
		"window_button_x_off": top_button_off,
		"column_bar_background": column_surface,
		"artist_bio_background": side,
		"artist_bio_text": side_title,
		"vis_bg": top,
		"link_text": track_accent,
		"star_line_playing": track_playing,
		"message_box_bg": box_surface,
		"message_box_text": box_text,
		"queue_drag_indicator_colour": track_accent,
		"pulse_colour": track_accent,
		"queue_card_background": queue_card,
		"column_grip": _alpha(column_text, 54),
		"column_bar_text": column_text,
		"box_thumb_background": _alpha(button_highlight, 190),
		"level_1_bg": _mix_hls(box_surface, track_accent, 0.10),
		"level_2_bg": _mix_hls(box_surface, track_accent, 0.16),
		"level_3_bg": _mix_hls(box_surface, track_accent, 0.22),
		"level_green": _hls_to_colour(accent_hue + 0.08, 0.46 if prefer_light else 0.58, 0.58),
		"level_yellow": _hls_to_colour(accent_hue, 0.48 if prefer_light else 0.60, 0.62),
		"level_red": _hls_to_colour(accent_hue - 0.08, 0.46 if prefer_light else 0.58, 0.62),
		"time_sub": bottom_secondary,
		"gallery_artist_line": _alpha(side_secondary, 120),
		"sys_tab_bg": tab_background,
		"sys_tab_hl": tab_active,
		"toggle_box_on": track_accent,
	}
	for name, value in values.items():
		setattr(colours, name, value)
	# Snapshot still classifies the artwork tonally to build its palette, but
	# Tauon's legacy light-mode switch is intentionally left off. Components
	# must use their generated role colours rather than changing behaviour based
	# on this global flag.
	setattr(colours, "lm", False)  # noqa: B010 - ColoursClass is deliberately duck typed here.
	column_colours = getattr(colours, "column_colours", None)
	if column_colours is not None:
		column_colours.clear()
	column_colours_playing = getattr(colours, "column_colours_playing", None)
	if column_colours_playing is not None:
		column_colours_playing.clear()


def apply_art_theme(colours: object, image: Image.Image) -> ArtTheme:
	"""Apply the selected theme and complete role expansion to ColoursClass."""
	# Imported here rather than at module scope: the selector scores this
	# module's candidates, so a top-level import would be circular.
	from tauon.t_modules.t_art_theme_vivid import select_art_theme  # noqa: PLC0415

	theme, _route = select_art_theme(image)
	_apply_complete_theme(colours, theme)
	post_config = getattr(colours, "post_config", None)
	if callable(post_config):
		post_config()
		# post_config supplies useful non-colour bookkeeping, but also contains
		# legacy colour fallbacks. Reassert every generated role afterwards.
		_apply_complete_theme(colours, theme)
	return theme
