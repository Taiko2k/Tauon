"""The Candy Factory skin's loading screen: a grey starfield.

The native launcher shows the splash before Python starts, so it can't draw
this itself. Instead it is painted here once, at the window's pixel size,
and saved as a BMP in the user data folder; window-state.json's
`aqua_splash` flag tells the launcher to show it. Everything is laid out on
a 1126x655 board (the design's frame): positions scale with the window, sizes
with the UI scale.
"""
from __future__ import annotations

import json
import logging
import math
import os
import threading
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageMath

SPLASH_FILENAME = "aqua-splash.bmp"
SPLASH_INFO_FILENAME = "aqua-splash.json"
# Bump when the design changes, so saved splashes are painted again
SPLASH_VERSION = 5

BOARD_W, BOARD_H = 1126, 655

_lock = threading.Lock()
_running = False


def splash_path(directory: Path) -> Path:
	return directory / SPLASH_FILENAME


def splash_ready(directory: Path) -> bool:
	return splash_path(directory).is_file()


def _needs_paint(directory: Path, size: tuple[int, int], scale: float) -> bool:
	if not splash_ready(directory):
		return True
	try:
		info = json.loads((directory / SPLASH_INFO_FILENAME).read_text(encoding="utf-8"))
	except (OSError, ValueError):
		return True
	return info != {"version": SPLASH_VERSION, "size": list(size), "scale": scale}


def refresh_splash(directory: Path, size: tuple[int, int], scale: float) -> None:
	"""Paint the splash on a worker thread if the saved one is missing, from
	an older design, or for another window size."""
	global _running
	size = (int(size[0]), int(size[1]))
	if size[0] < 100 or size[1] < 100 or not _needs_paint(directory, size, scale):
		return
	with _lock:
		if _running:
			return
		_running = True

	def work() -> None:
		global _running
		try:
			image = paint_splash(size, scale)
			path = splash_path(directory)
			temp = path.with_suffix(".tmp")
			image.save(temp, "BMP")
			os.replace(temp, path)
			info = {"version": SPLASH_VERSION, "size": list(size), "scale": scale}
			(directory / SPLASH_INFO_FILENAME).write_text(json.dumps(info), encoding="utf-8")
		except Exception:
			logging.exception("Candy Factory: painting the splash failed")
		finally:
			with _lock:
				_running = False

	threading.Thread(target=work, daemon=True).start()


# -- painting ------------------------------------------------------------------------------

# The sky is a few dozen levels of dark grey, so it is painted in float
# ("F" images) and rounded to 8 bits once, through a dither, at the end
_eval = getattr(ImageMath, "unsafe_eval", None) or ImageMath.eval


def _axis(size: tuple[int, int], origin: float, radius: float, vertical: bool = False) -> Image.Image:
	"""F image of (x - origin) / radius across the width, or of y down the height."""
	n = size[1] if vertical else size[0]
	line = Image.new("F", (1, n) if vertical else (n, 1))
	line.putdata([(i + 0.5 - origin) / radius for i in range(n)])
	return line.resize(size, Image.Resampling.NEAREST)


def _ramp(t: Image.Image, stops: list[tuple[float, float]]) -> Image.Image:
	"""Map an F image through piecewise-linear (t, value) stops, holding the
	end values beyond them."""
	(t0, v0), rest = stops[0], stops[1:]
	expr, args, slope = "max(t, 0.0) * 0.0 + v", {"t": t, "v": v0}, 0.0
	for i, (t1, v1) in enumerate(rest):
		new = (v1 - v0) / (t1 - t0) if t1 > t0 else 0.0
		expr += f" + k{i} * max(t - p{i}, 0.0)"
		args[f"k{i}"], args[f"p{i}"] = new - slope, t0
		slope, (t0, v0) = new, (t1, v1)
	expr += " - k * max(t - p, 0.0)"
	args["k"], args["p"] = slope, t0
	return _eval(expr, **args)


def _radial(size: tuple[int, int], cx: float, cy: float, rx: float, ry: float,
		stops: list[tuple[float, float]]) -> Image.Image:
	"""F image of an alpha following `stops` ((t, alpha), t from 0 at the
	centre to 1 at the (rx, ry) ellipse)."""
	x, y = _axis(size, cx, rx), _axis(size, cy, ry, vertical=True)
	return _ramp(_eval("(x * x + y * y) ** 0.5", x=x, y=y), stops)


def _over(channels: list[Image.Image], rgb, alpha: Image.Image) -> list[Image.Image]:
	"""Lay a colour (numbers, or F images) over float RGB channels at a float alpha."""
	return [_eval("c + (v - c) * a", c=c, v=v if isinstance(v, Image.Image) else float(v), a=alpha)
		for c, v in zip(channels, rgb)]


def _mask_circle(size: tuple[int, int], cx: float, cy: float, r: float, ss: int = 4) -> Image.Image:
	big = Image.new("L", (size[0] * ss, size[1] * ss), 0)
	ImageDraw.Draw(big).ellipse(((cx - r) * ss, (cy - r) * ss, (cx + r) * ss, (cy + r) * ss), fill=255)
	return big.reduce(ss)


def _fill(size: tuple[int, int], rgb: tuple[int, int, int], alpha: float, mask: Image.Image) -> Image.Image:
	layer = Image.new("RGBA", size, (*rgb, 0))
	layer.putalpha(mask.point(lambda v: round(v * alpha)))
	return layer


def _paste(base: Image.Image, layer: Image.Image, x: int, y: int) -> None:
	"""alpha_composite a layer at (x, y), clipped to the base."""
	left, top = max(0, -x), max(0, -y)
	right = min(layer.width, base.width - x)
	bottom = min(layer.height, base.height - y)
	if right <= left or bottom <= top:
		return
	base.alpha_composite(layer, (x + left, y + top), (left, top, right, bottom))


def _star_sprite(d: float, alpha: float) -> tuple[Image.Image, int]:
	size = math.ceil(d) + 4
	c = size / 2
	m = _mask_circle((size, size), c, c, d / 2)
	return _fill((size, size), (255, 255, 255), alpha, m), size


def _cross(length: float, thick: float, alpha: float, glow: tuple[int, int, int], dot: float = 0.0) -> Image.Image:
	"""A four-point glint: two thin lines fading out from the middle, an
	optional dot, and a soft glow."""
	size = math.ceil(length) + 8
	c = size / 2
	img = Image.new("RGBA", (size, size), (255, 255, 255, 0))
	line = Image.new("L", (size, size), 0)
	draw = ImageDraw.Draw(line)
	half = length / 2
	for i in range(size):
		k = max(0.0, 1 - abs(i + 0.5 - c) / half)
		v = round(255 * alpha * k)
		draw.line(((i, c - thick / 2), (i, c + thick / 2 - 1)), fill=v)
		draw.line(((c - thick / 2, i), (c + thick / 2 - 1, i)), fill=v)
	if dot:
		line = ImageChops.lighter(line, _mask_circle((size, size), c, c, dot))
	glow_mask = line.filter(ImageFilter.GaussianBlur(max(1.0, thick * 2)))
	img = Image.alpha_composite(_fill((size, size), glow, 0.8, glow_mask), img)
	img.alpha_composite(_fill((size, size), (255, 255, 255), 1.0, line))
	return img


def _stars() -> list[tuple[float, float, float, float]]:
	"""(x, y, diameter, alpha) on the board, the same field as the design."""
	seed = 7

	def rnd() -> float:
		nonlocal seed
		seed = (seed * 16807) % 2147483647
		return seed / 2147483647

	out = []
	for _i in range(90):
		x = rnd() * BOARD_W
		y = rnd() ** 1.25 * BOARD_H
		big = rnd() > 0.86
		d = 2.2 if big else 1 + rnd() * 0.8
		a = (0.7 if big else 0.22 + rnd() * 0.4) * (1 - y / 900)
		out.append((x, y, d, a))
	return out


def paint_splash(size: tuple[int, int], scale: float) -> Image.Image:
	"""The splash at a window size in pixels, for a UI scale."""
	W, H = size
	sx, sy = W / BOARD_W, H / BOARD_H
	u = max(0.5, scale)

	# Open sky: one broad wash of light from off the top-left corner, fading
	# diagonally, with no pool of light to frame the middle
	t = _axis(size, 0.0, H - 1, vertical=True)
	sky = [_ramp(t, [(0.0, a), (0.6, b), (1.0, c)]) for a, b, c in ((17, 12, 9), (18, 13, 9), (22, 16, 11))]
	sky = _over(sky, (140, 148, 166),
		_radial(size, -0.10 * W, -0.25 * H, 1.15 * W, 1.20 * H, [(0, 0.20), (0.35, 0.11), (0.75, 0.03), (1, 0)]))
	for (bx, by, rx, ry, rgb, a) in (
			(330, 210, 420, 170, (150, 156, 172), 0.05),
			(900, 470, 380, 150, (120, 130, 156), 0.04)):
		sky = _over(sky, rgb, _radial(size, bx * sx, by * sy, rx * sx, ry * sy, [(0, a), (0.5, a * 0.5), (1, 0)]))

	img = Image.new("RGBA", size, (0, 0, 0, 0))
	sprites: dict[tuple[float, float], tuple[Image.Image, int]] = {}
	for x, y, d, a in _stars():
		key = (round(d * u, 1), round(a, 2))
		if key not in sprites:
			sprites[key] = _star_sprite(*key)
		sprite, n = sprites[key]
		_paste(img, sprite, round(x * sx - n / 2), round(y * sy - n / 2))
	for bx, by, k, a in ((199, 105, 1.0, 1.0), (939, 149, 0.7, 1.0), (249, 509, 0.55, 0.7)):
		glint = _cross(18 * u * k, max(1.0, u), 0.85 * a, (220, 226, 240), dot=1.5 * u * k)
		_paste(img, glint, round(bx * sx - glint.width / 2), round(by * sy - glint.height / 2))

	# The stars over the sky, then a soft darkening at the corners
	stars = [band.convert("F") for band in img.split()]
	sky = _over(sky, stars[:3], _eval("a / 255.0", a=stars[3]))
	sky = _over(sky, (0, 0, 0), _radial(size, W * 0.5, H * 0.5, 0.95 * W, 1.0 * H, [(0, 0), (0.6, 0), (1, 0.35)]))

	# Round to 8 bits through one shared noise field, about half a level
	# wide, so the gradients' steps dissolve into grain instead of rings
	noise = Image.effect_noise(size, 64).convert("F")
	return Image.merge("RGB", [_eval("c + 0.5 + (n - 128.0) / 128.0", c=c, n=noise).convert("L") for c in sky])
