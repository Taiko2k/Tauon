"""Easter egg module, the other one: the Aero world ("Touch Grass")

**GO OUTSIDE**

The About icon in Settings opens this one while the Candy Factory skin is on,
and the Dream Room (t_room) otherwise; `Dreams` holds both behind the one
switch Tauon calls. (Not to be confused with t_aero, the skin itself.)

Same trick as t_room (the live UI rides on a screen inside a hand-projected
3D scene), but this screen floats over a mirror lake somewhere in 2007, at
night, under the skin's own dusk sky.

Implementation notes:

* Reuses DreamRoom's camera, clipping and batching. Draw order is painter's:
  sky -> mirrored world -> water tint -> world -> screen -> foreground ->
  lens effects. Loose objects (fish, bubbles, discs...) are depth sorted each
  frame and split by the screen's plane.
* The lake is a true planar mirror: the world is drawn a second time with y
  negated, then the water is laid over it as a translucent tint.
* The sky, water, light ribbons and glows take their colours from the skin
  (t_aero) every frame, so they follow the playing album and Obsidian. The
  sprites are painted once in fixed night colours and tinted toward it.
* All sprites are painted once with Pillow. Their transparent pixels are
  given the colour of whatever is nearby, so plain alpha blending filters
  cleanly at the edges on every renderer.
"""
from __future__ import annotations

import colorsys
import math
import random
from typing import TYPE_CHECKING

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps

from tauon.t_modules import t_native as sdl3
from tauon.t_modules.t_aero import Aero, _hue_lerp, hsl
from tauon.t_modules.t_room import FOV, NEAR, DreamRoom, _lerp, _smooth

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

TAU = math.tau
K255 = 1.0 / 255.0

# The floating screen (metres-ish). The lake surface is y=0, the camera looks toward -z.
SCR_CX, SCR_CY = 0.0, 0.92
SCR_H = 1.2
SCR_Z = 0.0

END_EYE = (1.25, 0.95, 4.0)
END_TGT = (0.3, 1.3, 0.0)

MOON = (-20.0, 182.0, -400.0)
MOON_R = 13.0

# Clouds: azimuth and elevation in degrees, distance, half-width, texture, drift
CLOUDS = [
	(-48, 9, 380, 60, 0, 0.9), (-30, 5, 390, 40, 1, 0.6), (-12, 24, 330, 55, 2, 1.2), (4, 14, 370, 42, 0, 0.8),
	(18, 6, 390, 36, 1, 0.5), (31, 19, 300, 50, 2, 1.1), (46, 11, 360, 58, 0, 0.7), (-58, 23, 340, 50, 1, 1.0),
	(60, 26, 300, 60, 2, 1.3), (-21, 36, 280, 40, 0, 1.4),
]

# Sky gradient: height on the far plane, then the skin's hue key (1: its top
# hue, 2: its floor hue), saturation and lightness, and lightness under Obsidian
SKY_Z = -420.0
SKY = [
	(0.0, 2, 0.50, 0.25, 0.16), (24.0, 2, 0.58, 0.17, 0.12), (90.0, 1, 0.65, 0.12, 0.085),
	(240.0, 1, 0.70, 0.07, 0.05), (560.0, 1, 0.72, 0.04, 0.03),
]

# Water: distance ahead of the eye, how far from the deep colour toward the
# horizon's, alpha. Thin at grazing angles so the far lake is nearly a pure mirror.
WATER = [
	(-6.0, 0.0, 214), (1.0, 0.0, 208), (2.5, 0.05, 196), (4.5, 0.10, 178), (8.0, 0.18, 150), (14.0, 0.28, 120),
	(26.0, 0.40, 92), (50.0, 0.55, 70), (110.0, 0.75, 54), (1000.0, 1.0, 46),
]

# The skin's light ribbons, as swooshes across the sky: y, amplitude,
# frequency, speed, phase, width, alpha. Hues as in t_aero's sky.
RIBBONS = [
	(150.0, 46.0, 1.15, 0.050, 0.0, 80.0, 92),
	(118.0, 34.0, 1.60, -0.037, 2.1, 52.0, 110),
	(196.0, 30.0, 0.90, 0.028, 4.0, 66.0, 64),
]

# Blooms on the sky, as in the skin: x, y, half-size, hue key (1, 2 or accent) + offset, strength
BLOOMS = [(-250.0, 175.0, 250.0, 1, 15.0, 0.30), (170.0, 45.0, 270.0, 2, 0.0, 0.34), (-50.0, 250.0, 210.0, 3, 25.0, 0.24)]

# Hill flats: x0, x1, height, z
HILL_L = (-230.0, -22.0, 50.0, -95.0)
HILL_R = (40.0, 300.0, 44.0, -95.0)

# Lens flare ghosts: position along the moon->centre axis, size, hue key + offset, alpha, texture
GHOSTS = [
	(0.38, 0.030, (3, 0.0), 44, "ring"),
	(0.60, 0.055, (1, 0.0), 26, "hex"),
	(0.86, 0.016, None, 60, "soft"),
	(1.14, 0.110, (3, 40.0), 18, "ring"),
	(1.42, 0.070, (2, 0.0), 22, "hex"),
	(1.80, 0.160, (1, 20.0), 14, "bokeh"),
]

ADDITIVE = {"soft", "ring", "bokeh", "hex", "city_lights"}

# Gel buttons take the skin's hues: the accent, its top hue, its floor hue
ORB_HUES = {"orb_play": 3, "orb_next": 1, "orb_note": 2}

CIRCLE = [(math.cos(TAU * i / 12), math.sin(TAU * i / 12)) for i in range(13)]


# ------------------------------------------------------------------ painting

def _lut(fn) -> list[int]:
	return [max(0, min(255, round(fn(i / 255.0) * 255.0))) for i in range(256)]


def _radial(size: int, fn) -> Image.Image:
	"""Radial L image of fn(r): r is 0 at the centre, 1 at the inscribed edge."""
	# Pillow's gradient only reaches white in the corners
	lut = _lut(lambda f: fn(min(1.0, f * 1.41421)))
	return Image.radial_gradient("L").point(lut).resize((size, size), Image.BILINEAR)


def _vgrad(size: tuple[int, int], top, bottom) -> Image.Image:
	g = Image.linear_gradient("L").resize(size, Image.BILINEAR)
	return Image.merge("RGB", [
		g.point(_lut(lambda f, a=top[i], b=bottom[i]: (a + (b - a) * f) / 255.0)) for i in range(3)])


def _hgrad(size: tuple[int, int], left, right) -> Image.Image:
	return _vgrad((size[1], size[0]), left, right).transpose(Image.Transpose.ROTATE_90)


def _flat(size: tuple[int, int], rgb) -> Image.Image:
	return Image.new("RGB", size, tuple(rgb))


def _layer(rgb, alpha: Image.Image) -> Image.Image:
	"""A solid colour with an L mask as its alpha."""
	im = Image.new("RGBA", alpha.size, (*rgb, 255))
	im.putalpha(alpha)
	return im


def _scale(mask: Image.Image, k: float) -> Image.Image:
	return mask.point(_lut(lambda f: f * k))


def _blur(im: Image.Image, r: float) -> Image.Image:
	return im.filter(ImageFilter.GaussianBlur(r))


def _noise(size, cells, rnd: random.Random, wrap: bool = False) -> Image.Image:
	cw, ch = cells
	grid = Image.frombytes("L", (cw, ch), rnd.randbytes(cw * ch))
	if not wrap:
		return grid.resize(size, Image.BICUBIC)
	# Tile the lattice before scaling so the result wraps horizontally
	wide = Image.new("L", (cw * 3, ch))
	for i in range(3):
		wide.paste(grid, (cw * i, 0))
	w, h = size
	return wide.resize((w * 3, h), Image.BICUBIC).crop((w, 0, w * 2, h))


def _fbm(size, rnd: random.Random, base=(4, 2), wrap: bool = False, octaves=((2, 0.40), (4, 0.25), (8, 0.14))) -> Image.Image:
	im = _noise(size, base, rnd, wrap)
	for k, wgt in octaves:
		im = Image.blend(im, _noise(size, (base[0] * k, base[1] * k), rnd, wrap), wgt)
	return ImageOps.autocontrast(im)


def _mix(a, b, f: float) -> tuple:
	return tuple(round(a[i] + (b[i] - a[i]) * f) for i in range(3))


def _make_hex() -> Image.Image:
	s = 192
	m = Image.new("L", (s, s), 0)
	d = ImageDraw.Draw(m)
	pts = [(s / 2 + s * 0.44 * math.cos(TAU * i / 6 + 0.3), s / 2 + s * 0.44 * math.sin(TAU * i / 6 + 0.3))
		for i in range(6)]
	d.polygon(pts, fill=150)
	d.line([*pts, pts[0]], fill=255, width=5)
	return _layer((255, 255, 255), _blur(m, 2.5).resize((96, 96), Image.BILINEAR))


def _make_bubble() -> Image.Image:
	s = 256
	rim = _radial(s, lambda r: (0.05 + 0.85 * r ** 7) if r < 0.93 else max(0.0, (1.0 - r) / 0.07) * 0.56)
	g = Image.linear_gradient("L")
	gh = g.transpose(Image.Transpose.ROTATE_90)
	col = Image.merge("RGB", [
		g.point(_lut(lambda f: (205 + 50 * math.sin(f * TAU)) / 255)),
		gh.point(_lut(lambda f: (225 + 30 * math.sin(f * TAU + 2.0)) / 255)),
		Image.new("L", (s, s), 255),
	])
	im = col.convert("RGBA")
	im.putalpha(rim)
	# Reflected light along the lower right of the rim
	cres = ImageChops.multiply(
		_radial(s, lambda r: math.exp(-((r - 0.78) / 0.07) ** 2)), g.rotate(45))
	im.alpha_composite(_layer((255, 255, 255), _scale(cres, 0.8)))
	# Specular highlights
	hl = Image.new("L", (s, s), 0)
	d = ImageDraw.Draw(hl)
	d.ellipse((s * 0.36, s * 0.13, s * 0.64, s * 0.31), fill=235)
	hl = hl.rotate(38, center=(s / 2, s / 2))
	ImageDraw.Draw(hl).ellipse((s * 0.67, s * 0.69, s * 0.74, s * 0.75), fill=200)
	im.alpha_composite(_layer((255, 255, 255), _blur(hl, 4)))
	return im


def _make_cloud(rnd: random.Random) -> Image.Image:
	w, h = 512, 256
	m = Image.new("L", (w, h), 0)
	d = ImageDraw.Draw(m)
	n = rnd.randint(6, 9)
	base = h * 0.76
	for i in range(n):
		f = i / (n - 1)
		r = h * (0.13 + 0.17 * math.sin(math.pi * f) ** 0.8 + rnd.uniform(-0.02, 0.05))
		x = w * (0.18 + 0.64 * f) + rnd.uniform(-10, 10)
		y = base - r * rnd.uniform(0.7, 1.0)
		d.ellipse((x - r, y - r, x + r, y + r), fill=255)
		if 0.2 < f < 0.8 and rnd.random() < 0.6:
			r2 = r * 0.72
			x2 = x + rnd.uniform(-22, 22)
			y2 = y - r * 0.8
			d.ellipse((x2 - r2, y2 - r2, x2 + r2, y2 + r2), fill=255)
	d.rounded_rectangle((w * 0.15, base - h * 0.16, w * 0.85, base), radius=h * 0.08, fill=255)
	# Moonlit from the upper right: a silver rim where the mask, sampled
	# toward the lower left, runs out
	rim = _blur(ImageChops.subtract(m, ImageChops.offset(m, -9, 13)), 7)
	col = Image.composite(_flat((w, h), (196, 214, 236)), _vgrad((w, h), (64, 74, 100), (30, 36, 56)), _scale(rim, 1.1))
	im = col.convert("RGBA")
	im.putalpha(_blur(m, 4))
	return im


def _make_moon(rnd: random.Random) -> Image.Image:
	s = 256
	m = Image.new("L", (s, s), 0)
	ImageDraw.Draw(m).ellipse((8, 8, s - 8, s - 8), fill=255)
	maria = _fbm((s, s), rnd, (5, 5)).point(_lut(lambda f: 0.80 + 0.20 * _smooth(min(1.0, max(0.0, (f - 0.3) / 0.45)))))
	lum = ImageChops.multiply(maria, _radial(s, lambda r: 1.0 - 0.32 * r ** 3))
	im = Image.merge("RGB", [lum.point(_lut(lambda f, k=k: f * k)) for k in (0.93, 0.97, 1.0)]).convert("RGBA")
	im.putalpha(_blur(m, 1.2))
	return im.reduce(2)


def _make_city(rnd: random.Random) -> tuple[Image.Image, Image.Image]:
	"""The city at night: dark glass towers, and their lights on a layer of
	their own (drawn additively, so they also light up the reflection)."""
	w, h = 2048, 512
	im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	li = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)
	dl = ImageDraw.Draw(li)
	tints = [(28, 46, 66), (22, 38, 58), (38, 60, 82), (18, 30, 48), (32, 54, 74), (24, 44, 62)]
	lamps = [(255, 222, 168), (196, 234, 255), (255, 242, 218), (170, 226, 255)]
	tree = (12, 34, 40, 255)

	def lighter(c):
		return (*_mix(c, (150, 204, 232), 0.2), 255)

	def windows(x0, y0, x1, y1, lit: float) -> None:
		col = rnd.choice(lamps)
		y = y0 + 7
		while y < y1 - 5:
			if rnd.random() < 0.8:
				x = x0 + 5
				while x < x1 - 6:
					if rnd.random() < lit:
						dl.rectangle((x, y, x + 3, y + 4), fill=(*col, rnd.randint(110, 255)))
					x += 9
			y += 11

	def beacon(x, y) -> None:
		dl.ellipse((x - 4, y - 4, x + 4, y + 4), fill=(255, 70, 70, 255))

	g = h
	x = 20.0
	while x < w - 70:
		c = abs(x / w - 0.5) * 2
		top = h * (0.22 + 0.70 * (1 - c) ** 1.5)
		bw = rnd.uniform(36, 84)
		bh = top * rnd.uniform(0.42, 1.0)
		tint = rnd.choice(tints)
		style = rnd.choice(("slab", "slab", "sail", "needle", "eco", "twin"))
		lit = rnd.uniform(0.15, 0.5)
		y0 = g - bh
		if style == "slab":
			d.rounded_rectangle((x, y0, x + bw, g + 60), radius=bw * 0.3, fill=(*tint, 255))
			d.rounded_rectangle((x + bw * 0.62, y0 + bw * 0.1, x + bw, g + 60), radius=bw * 0.3, fill=lighter(tint))
			windows(x + bw * 0.1, y0 + bw * 0.3, x + bw * 0.9, g, lit)
			if rnd.random() < 0.45:
				d.ellipse((x + bw * 0.12, y0 - bw * 0.14, x + bw * 0.88, y0 + bw * 0.2), fill=tree)
			elif bh > h * 0.5:
				beacon(x + bw * 0.5, y0 + 3)
		elif style == "sail":
			d.pieslice((x - bw, g - bh, x + bw, g + bh), 270, 360, fill=(*tint, 255))
			d.pieslice((x - bw * 0.45, g - bh * 0.88, x + bw * 0.45, g + bh * 0.88), 270, 360, fill=lighter(tint))
			# A lit seam up the sail's curve
			dl.arc((x - bw * 0.72, g - bh * 0.94, x + bw * 0.72, g + bh * 0.94), 272, 358, fill=(*rnd.choice(lamps), 200), width=3)
		elif style == "needle":
			d.rectangle((x + bw * 0.42, y0, x + bw * 0.58, g), fill=(*tint, 255))
			d.polygon([(x + bw * 0.2, g), (x + bw * 0.8, g), (x + bw * 0.58, g - bh * 0.3), (x + bw * 0.42, g - bh * 0.3)],
				fill=(*tint, 255))
			sy = y0 + bh * 0.2
			r = bw * 0.36
			d.ellipse((x + bw * 0.5 - r, sy - r, x + bw * 0.5 + r, sy + r), fill=lighter(tint))
			dl.rectangle((x + bw * 0.5 - r * 0.9, sy - 2, x + bw * 0.5 + r * 0.9, sy + 2), fill=(*rnd.choice(lamps), 255))
			d.line((x + bw * 0.5, y0, x + bw * 0.5, y0 - bh * 0.16), fill=(*tint, 255), width=3)
			beacon(x + bw * 0.5, y0 - bh * 0.16)
		elif style == "eco":
			for k in range(3):
				tw = bw * (1 - 0.24 * k)
				ty = g - bh * (k + 1) / 3
				x0 = x + (bw - tw) / 2
				d.rectangle((x0, ty, x0 + tw, g), fill=(*tint, 255))
				d.rectangle((x0 + tw * 0.66, ty, x0 + tw, g), fill=lighter(tint))
				windows(x0, ty + 6, x0 + tw, ty + bh / 3, lit)
				d.ellipse((x0 - 5, ty - 9, x0 + tw * 0.4, ty + 7), fill=tree)
				d.ellipse((x0 + tw * 0.5, ty - 7, x0 + tw + 5, ty + 6), fill=tree)
		else:
			for k, hk in ((0.0, 1.0), (0.6, 0.84)):
				x0 = x + bw * k
				d.rounded_rectangle((x0, g - bh * hk, x0 + bw * 0.4, g + 60), radius=bw * 0.14, fill=(*tint, 255))
				d.rectangle((x0 + bw * 0.26, g - bh * hk + bw * 0.14, x0 + bw * 0.4, g), fill=lighter(tint))
				windows(x0, g - bh * hk + 8, x0 + bw * 0.4, g, lit)
			d.rectangle((x + bw * 0.3, g - bh * 0.62, x + bw * 0.7, g - bh * 0.56), fill=lighter(tint))
			dl.rectangle((x + bw * 0.3, g - bh * 0.6, x + bw * 0.7, g - bh * 0.58), fill=(*rnd.choice(lamps), 230))
		x += bw * rnd.uniform(0.8, 1.4)
	for i in range(7):	# biodomes, lit from inside
		cx = rnd.uniform(0.08, 0.92) * w
		r = rnd.uniform(40, 92)
		d.pieslice((cx - r, g - r * 0.8, cx + r, g + r * 0.8), 180, 360, fill=(34, 62, 80, 255))
		dl.pieslice((cx - r * 0.7, g - r * 0.42, cx + r * 0.7, g + r * 0.42), 180, 360, fill=(120, 230, 210, 26))
		d.arc((cx - r * 0.86, g - r * 0.68, cx + r * 0.86, g + r * 0.68), 205, 290, fill=(120, 170, 200, 255), width=5)
	for x in range(0, w, 13):	# parkland along the shore, and its lamps
		r = rnd.uniform(8, 19)
		d.ellipse((x - r, g - r * 1.5, x + r, g + r), fill=(*_mix((8, 26, 32), (18, 44, 50), rnd.random()), 255))
		if rnd.random() < 0.2:
			dl.ellipse((x - 3, g - 12, x + 3, g - 6), fill=(255, 226, 170, 220))
	im = im.reduce(2)
	rgb = Image.blend(im.convert("RGB"), _flat(im.size, (26, 44, 62)), 0.15)
	rgb.putalpha(im.getchannel("A"))
	li = li.reduce(2)
	glow = li.filter(ImageFilter.GaussianBlur(3))
	glow.putalpha(_scale(glow.getchannel("A"), 0.8))
	glow.alpha_composite(li)
	return rgb, glow


def _make_hills(rnd: random.Random, size, taper: str, far: bool) -> tuple[Image.Image, list[float]]:
	"""A range of rolling hills. Returns the image and its surface profile
	(0..1 of the image height, sampled every 8 px)."""
	w, h = size
	p1, p2, p3 = rnd.random(), rnd.random(), rnd.random()
	prof = []
	for x in range(0, w + 8, 8):
		u = x / w
		v = 0.50 + 0.26 * math.sin(TAU * (u * 1.1 + p1)) + 0.13 * math.sin(TAU * (u * 2.7 + p2)) \
			+ 0.05 * math.sin(TAU * (u * 6.1 + p3))
		env = 1.0
		if taper == "right":
			env = _smooth(min(1.0, (1.0 - u) / 0.4))
		elif taper == "left":
			env = _smooth(min(1.0, u / 0.4))
		prof.append(max(0.03, v) * env)
	top = max(prof)
	prof = [0.93 * v / top for v in prof]
	m = Image.new("L", size, 0)
	pts = [(i * 8, h - prof[i] * h) for i in range(len(prof))]
	ImageDraw.Draw(m).polygon([*pts, (w, h + 2), (0, h + 2)], fill=255)

	col = _vgrad(size, (34, 70, 74), (8, 24, 34))
	mot = _fbm(size, rnd, (12, 3))
	col = ImageChops.multiply(col, Image.merge("RGB", [mot.point(_lut(lambda f: 0.74 + 0.26 * f))] * 3))
	# Moonlit shoulders (facing up-right) and deeper shade on the far sides
	lit = _blur(ImageChops.subtract(m, ImageChops.offset(m, -12, 16)), 9)
	col = Image.composite(_flat(size, (96, 142, 156)), col, _scale(lit, 0.6))
	shade = _blur(ImageChops.subtract(m, ImageChops.offset(m, 14, 10)), 12)
	col = Image.composite(_flat(size, (4, 12, 22)), col, _scale(shade, 0.5))
	im = col.convert("RGBA")
	im.putalpha(_blur(m, 0.9))

	if not far:
		d = ImageDraw.Draw(im)
		for k in range(9):	# stands of round trees
			u0 = rnd.uniform(0.05, 0.95)
			for i in range(rnd.randint(4, 9)):
				u = u0 + rnd.uniform(-0.035, 0.035)
				j = int(u * w / 8)
				if not 0 <= j < len(prof) or prof[j] < 0.2:
					continue
				r = rnd.uniform(6, 12)
				x = u * w
				y = h - prof[j] * h + rnd.uniform(4, 70)
				d.ellipse((x - r, y - r * 1.9, x + r, y), fill=(20, 48, 54, 255))
				d.ellipse((x - r * 0.5, y - r * 1.8, x + r * 0.9, y - r * 0.5), fill=(38, 76, 82, 255))
		for k in range(160):	# glow-worms
			u = rnd.random()
			j = int(u * w / 8)
			y = h - prof[j] * h + rnd.uniform(10, prof[j] * h)
			if prof[j] > 0.1 and y < h:
				im.putpixel((int(u * w) % w, int(y)), rnd.choice(((150, 236, 220, 255), (200, 236, 255, 255))))
	else:
		rgb = Image.blend(im.convert("RGB"), _flat(size, (26, 46, 66)), 0.5)
		rgb.putalpha(im.getchannel("A"))
		im = rgb
	return im, prof


def _draw_tree(d: ImageDraw.ImageDraw, x: float, y: float, h: float, rnd: random.Random) -> None:
	d.polygon([(x - 0.06 * h, y), (x + 0.06 * h, y), (x + 0.035 * h, y - 0.55 * h), (x - 0.035 * h, y - 0.55 * h)],
		fill=(40, 34, 40, 255))
	blobs = [(rnd.uniform(-0.2, 0.2) * h, -(0.62 + rnd.uniform(0, 0.3)) * h, rnd.uniform(0.2, 0.3) * h) for i in range(7)]
	for (bx, by, r) in blobs:
		d.ellipse((x + bx - r, y + by - r, x + bx + r, y + by + r), fill=(10, 34, 40, 255))
	for (bx, by, r) in blobs:
		r2 = r * 0.78
		d.ellipse((x + bx + r * 0.16 - r2, y + by - r * 0.18 - r2, x + bx + r * 0.16 + r2, y + by - r * 0.18 + r2),
			fill=(20, 56, 60, 255))
	for (bx, by, r) in blobs[:5]:
		r2 = r * 0.36
		d.ellipse((x + bx + r * 0.4 - r2, y + by - r * 0.46 - r2, x + bx + r * 0.4 + r2, y + by - r * 0.46 + r2),
			fill=(52, 100, 110, 255))


def _make_island(rnd: random.Random, house: bool) -> Image.Image:
	s = 1024
	size = (s, s)
	cx = s * 0.5
	rim = s * 0.47
	rx = s * 0.42
	# Rocky underside, tapering to a point
	left, right = [], []
	n = 10
	for i in range(n + 1):
		f = i / n
		wd = rx * (1 - f) ** 0.62
		y = rim + s * 0.46 * f ** 0.9
		left.append((cx - wd * (1 + rnd.uniform(-0.1, 0.1)) + rnd.uniform(-20, 20) * f, y))
		right.append((cx + wd * (1 + rnd.uniform(-0.1, 0.1)) + rnd.uniform(-20, 20) * f, y))
	m = Image.new("L", size, 0)
	ImageDraw.Draw(m).polygon(left + right[::-1], fill=255)
	rock = _vgrad(size, (70, 66, 80), (18, 18, 28))
	rd = ImageDraw.Draw(rock)
	for i in range(34):	# strata
		x = cx + rnd.uniform(-1, 1) * rx
		y1 = rim + rnd.uniform(40, 420)
		c = rnd.choice(((46, 42, 54), (92, 90, 106), (34, 32, 44)))
		rd.line((x, rim - 10, x + rnd.uniform(-30, 30), y1), fill=c, width=rnd.randint(5, 16))
	rock = _blur(rock, 2.2)
	rock = ImageChops.multiply(rock, _hgrad(size, (130, 136, 160), (255, 255, 255)))
	rock = rock.convert("RGBA")
	rock.putalpha(m)
	im = Image.new("RGBA", size, (0, 0, 0, 0))
	im.alpha_composite(rock)
	d = ImageDraw.Draw(im)
	turf = (16, 48, 48, 255)
	for i in range(11):	# hanging vines
		x = cx + rnd.uniform(-0.95, 0.95) * rx
		ln = rnd.uniform(60, 230)
		d.line((x, rim, x + rnd.uniform(-12, 12), rim + ln * 0.5, x + rnd.uniform(-22, 22), rim + ln),
			fill=(14, 40, 44, 255), width=5)
	d.ellipse((cx - rx * 1.05, rim - s * 0.062, cx + rx * 1.05, rim + s * 0.062), fill=turf)
	for i in range(18):	# turf spilling over the rim
		x = cx + rnd.uniform(-1.0, 1.0) * rx
		d.ellipse((x - rnd.uniform(18, 34), rim, x + rnd.uniform(18, 34), rim + rnd.uniform(40, 96)), fill=turf)
	dome = (cx - rx * 1.03, rim - s * 0.19, cx + rx * 1.03, rim + s * 0.19)
	d.pieslice(dome, 180, 360, fill=(24, 62, 62, 255))
	dm = Image.new("L", size, 0)
	ImageDraw.Draw(dm).pieslice(dome, 180, 360, fill=255)
	hl = Image.new("L", size, 0)
	ImageDraw.Draw(hl).ellipse((cx - rx * 0.3, rim - s * 0.2, cx + rx * 0.95, rim - s * 0.05), fill=255)
	im.alpha_composite(_layer((88, 140, 150), ImageChops.multiply(_blur(hl, 26), dm)))
	d = ImageDraw.Draw(im)
	if house:
		hx, hy = cx + rx * 0.3, rim - s * 0.125
		d.rectangle((hx, hy - 78, hx + 150, hy), fill=(118, 130, 148, 255))
		# A lamp on inside (scene adds its glow)
		d.rectangle((hx + 14, hy - 62, hx + 96, hy - 16), fill=(255, 222, 160, 255))
		d.polygon([(hx + 14, hy - 62), (hx + 60, hy - 62), (hx + 30, hy - 16), (hx + 14, hy - 16)], fill=(255, 240, 206, 255))
		d.rectangle((hx - 12, hy - 90, hx + 164, hy - 78), fill=(146, 156, 172, 255))
		_draw_tree(d, cx - rx * 0.36, rim - s * 0.15, s * 0.26, rnd)
		_draw_tree(d, cx - rx * 0.72, rim - s * 0.085, s * 0.15, rnd)
	else:
		_draw_tree(d, cx - rx * 0.08, rim - s * 0.17, s * 0.32, rnd)
		_draw_tree(d, cx + rx * 0.56, rim - s * 0.105, s * 0.17, rnd)
	return im.reduce(2)


def _make_fish(kind: str, rnd: random.Random) -> Image.Image:
	"""A side-on fish, head at the left edge."""
	w, h = 768, 384
	size = (w, h)
	cy = h * 0.5
	body, belly, fin, tail = {
		"clown": ((255, 112, 16), (255, 176, 70), (250, 120, 24, 255), (250, 120, 24, 255)),
		"tang": ((22, 100, 236), (70, 160, 252), (30, 110, 240, 255), (255, 222, 44, 255)),
		"yellow": ((255, 218, 36), (255, 242, 130), (255, 208, 30, 255), (255, 208, 30, 255)),
		"koi": ((252, 252, 254), (236, 240, 248), (255, 214, 190, 255), (255, 196, 160, 255)),
		"tetra": ((176, 200, 226), (236, 244, 252), (200, 220, 240, 255), (255, 70, 60, 255)),
	}[kind]
	ry = h * (0.345 if kind == "yellow" else 0.22 if kind == "tetra" else 0.30)
	bx0, bx1 = w * 0.04, w * 0.72
	im = Image.new("RGBA", size, (0, 0, 0, 0))
	d = ImageDraw.Draw(im)
	tl = 0.99 if kind == "koi" else 0.95
	d.polygon([(w * 0.62, cy), (w * tl, cy - h * 0.36), (w * (tl - 0.09), cy), (w * tl, cy + h * 0.36)], fill=tail)
	d.polygon([(w * 0.24, cy - ry * 0.8), (w * 0.42, cy - ry * 1.42), (w * 0.62, cy - ry * 0.5)], fill=fin)
	d.polygon([(w * 0.36, cy + ry * 0.8), (w * 0.47, cy + ry * 1.36), (w * 0.58, cy + ry * 0.5)], fill=fin)
	m = Image.new("L", size, 0)
	ImageDraw.Draw(m).ellipse((bx0, cy - ry, bx1, cy + ry), fill=255)
	skin = _vgrad(size, body, belly)
	sd = ImageDraw.Draw(skin)
	if kind == "clown":
		for bx in (0.25, 0.44, 0.63):
			d0 = w * 0.012
			sd.rectangle((w * bx - d0, 0, w * (bx + 0.07) + d0, h), fill=(24, 20, 20))
			sd.rectangle((w * bx, 0, w * (bx + 0.07), h), fill=(255, 255, 255))
	elif kind == "tang":
		sd.arc((w * 0.2, cy - ry * 0.75, w * 0.86, cy + ry * 1.5), 175, 320, fill=(10, 16, 46), width=30)
		sd.ellipse((w * 0.34, cy - ry * 0.25, w * 0.5, cy + ry * 0.2), fill=(30, 110, 240))
	elif kind == "koi":
		for i in range(5):
			x = w * rnd.uniform(0.12, 0.6)
			y = cy + ry * rnd.uniform(-0.9, 0.3)
			r = w * rnd.uniform(0.04, 0.09)
			sd.ellipse((x - r * 1.5, y - r, x + r * 1.5, y + r), fill=rnd.choice(((244, 84, 28), (255, 130, 30), (30, 30, 36))))
		skin = _blur(skin, 3)
	elif kind == "tetra":
		sd.rectangle((w * 0.1, cy - h * 0.05, w * 0.7, cy + h * 0.02), fill=(0, 232, 255))
		sd.rectangle((w * 0.45, cy + h * 0.02, w * 0.72, cy + h * 0.1), fill=(255, 60, 60))
	skin = skin.convert("RGBA")
	skin.putalpha(m)
	im.alpha_composite(skin)
	gl = Image.new("L", size, 0)
	ImageDraw.Draw(gl).ellipse((bx0 + w * 0.08, cy - ry * 0.86, bx1 - w * 0.1, cy - ry * 0.3), fill=150)
	im.alpha_composite(_layer((255, 255, 255), ImageChops.multiply(_blur(gl, 9), m)))
	d = ImageDraw.Draw(im)
	d.polygon([(w * 0.30, cy + ry * 0.1), (w * 0.43, cy + ry * 0.34), (w * 0.32, cy + ry * 0.5)], fill=fin)
	ex, ey, er = w * 0.15, cy - ry * 0.22, min(ry * 0.22, h * 0.07)
	d.ellipse((ex - er, ey - er, ex + er, ey + er), fill=(255, 255, 255, 255))
	d.ellipse((ex - er * 0.55, ey - er * 0.55, ex + er * 0.55, ey + er * 0.55), fill=(12, 14, 24, 255))
	d.ellipse((ex - er * 0.42, ey - er * 0.5, ex - er * 0.02, ey - er * 0.1), fill=(255, 255, 255, 255))
	return im.reduce(3)


def _make_leaf() -> Image.Image:
	"""A dewy leaf hanging from its stem at the top edge."""
	w, h = 300, 600
	n = 30
	mid, left, right = [], [], []
	for i in range(n + 1):
		s = i / n
		y = _lerp(h * 0.05, h * 0.97, s)
		x = w * 0.5 + w * 0.05 * math.sin(math.pi * s)
		hw = w * 0.42 * math.sin(math.pi * s ** 0.78) ** 0.9
		mid.append((x, y))
		left.append((x - hw, y))
		right.append((x + hw, y))
	im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)
	d.polygon(left + mid[::-1], fill=(176, 238, 88, 255))
	d.polygon(mid + right[::-1], fill=(98, 204, 60, 255))
	m = im.getchannel("A")
	shade = _vgrad((w, h), (255, 255, 235), (150, 215, 170))
	rgb = ImageChops.multiply(im.convert("RGB"), shade)
	im = rgb.convert("RGBA")
	im.putalpha(m)
	d = ImageDraw.Draw(im)
	vein = (226, 250, 170, 255)
	for k in range(2, 26, 3):
		j = min(n, k + 4)
		d.line((*mid[k], *_mix3(mid[j], left[j], 0.86)), fill=vein, width=3)
		d.line((*mid[k], *_mix3(mid[j], right[j], 0.86)), fill=(170, 232, 120, 255), width=3)
	d.line(mid, fill=vein, width=6)
	d.line((mid[0][0], 0, *mid[1]), fill=(120, 170, 60, 255), width=9)
	for (fx, fy, r) in ((0.36, 0.34, 20), (0.62, 0.52, 15), (0.42, 0.68, 11), (0.6, 0.27, 8)):	# dew
		x, y = w * fx, h * fy
		d.ellipse((x - r, y - r, x + r, y + r), fill=(60, 150, 64, 255))
		d.ellipse((x - r * 0.84, y - r * 0.9, x + r * 0.84, y + r * 0.74), fill=(150, 226, 120, 255))
		d.ellipse((x - r * 0.2, y + r * 0.1, x + r * 0.7, y + r * 0.72), fill=(214, 250, 180, 255))
		d.ellipse((x - r * 0.6, y - r * 0.66, x - r * 0.05, y - r * 0.2), fill=(255, 255, 255, 255))
	return im.reduce(3)


def _mix3(a, b, f: float) -> tuple[float, float]:
	return (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)


def _make_orb(rgb, glyph: str) -> Image.Image:
	"""A glossy gel button."""
	s = 384
	size = (s, s)
	m = Image.new("L", size, 0)
	ImageDraw.Draw(m).ellipse((8, 8, s - 8, s - 8), fill=255)
	shade = _radial(s, lambda r: 1.0 - 0.62 * r ** 2.4)
	base = ImageChops.multiply(_flat(size, rgb), Image.merge("RGB", [shade] * 3))
	# Light pooling in the lower half, as through coloured gel
	glow = Image.new("L", size, 0)
	glow.paste(_radial(256, lambda r: max(0.0, 1.0 - r) ** 1.4).resize((int(s * 0.8), int(s * 0.5))), (int(s * 0.1), int(s * 0.46)))
	base = Image.composite(_flat(size, _mix(rgb, (255, 255, 255), 0.72)), base, _scale(glow, 0.8))
	im = base.convert("RGBA")
	d = ImageDraw.Draw(im)
	white = (255, 255, 255, 255)
	if glyph == "play":
		d.polygon([(s * 0.41, s * 0.36), (s * 0.41, s * 0.72), (s * 0.71, s * 0.54)], fill=white)
	elif glyph == "next":
		d.polygon([(s * 0.30, s * 0.38), (s * 0.30, s * 0.70), (s * 0.51, s * 0.54)], fill=white)
		d.polygon([(s * 0.50, s * 0.38), (s * 0.50, s * 0.70), (s * 0.71, s * 0.54)], fill=white)
	else:	# beamed quavers
		for nx in (0.36, 0.60):
			d.ellipse((s * (nx - 0.075), s * 0.62, s * (nx + 0.04), s * 0.72), fill=white)
			d.rectangle((s * (nx + 0.015), s * 0.36, s * (nx + 0.04), s * 0.67), fill=white)
		d.polygon([(s * 0.375, s * 0.36), (s * 0.64, s * 0.33), (s * 0.64, s * 0.40), (s * 0.375, s * 0.43)], fill=white)
	d.ellipse((8, 8, s - 8, s - 8), outline=(*_mix(rgb, (0, 0, 0), 0.5), 255), width=5)
	gloss = Image.new("L", size, 0)
	ImageDraw.Draw(gloss).ellipse((s * 0.17, s * 0.05, s * 0.83, s * 0.50), fill=255)
	gloss = ImageChops.multiply(gloss, Image.linear_gradient("L").resize(size).point(_lut(lambda f: 0.88 - 1.7 * f)))
	im.alpha_composite(_layer((255, 255, 255), _blur(gloss, 1.5)))
	im.putalpha(_blur(m, 1.5))
	return im.reduce(2)


def _bleed(im: Image.Image) -> Image.Image:
	"""Give fully transparent pixels the colour of what is near them, so
	bilinear filtering doesn't pull a dark fringe in around the edges."""
	n = 24
	alpha = im.getchannel("A")
	small = Image.frombytes("RGBA", im.size, im.convert("RGBa").tobytes()).resize((n, n), Image.BOX).tobytes()
	cells: list = []
	for i in range(0, n * n * 4, 4):
		a = small[i + 3]
		cells.append((small[i] * 255 // a, small[i + 1] * 255 // a, small[i + 2] * 255 // a) if a else None)
	for k in range(n):	# spread outward into the empty cells
		if None not in cells:
			break
		nxt = list(cells)
		for i, c in enumerate(cells):
			if c is None:
				x, y = i % n, i // n
				near = [cells[yy * n + xx] for (xx, yy) in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
					if 0 <= xx < n and 0 <= yy < n and cells[yy * n + xx] is not None]
				if near:
					nxt[i] = tuple(sum(v[j] for v in near) // len(near) for j in range(3))
		cells = nxt
	matte = Image.new("RGB", (n, n))
	matte.putdata([c or (255, 255, 255) for c in cells])
	matte = matte.resize(im.size, Image.BILINEAR)
	out = Image.composite(im.convert("RGB"), matte, alpha.point([0] + [255] * 255))
	out.putalpha(alpha)
	return out


def build_images(seed: int = 2007) -> tuple[dict[str, Image.Image], dict[str, list[float]]]:
	"""Paint every sprite. Pure Pillow, no renderer needed."""
	rnd = random.Random(seed)
	white = (255, 255, 255)
	out: dict[str, Image.Image] = {
		"soft": _layer(white, _radial(128, lambda r: max(0.0, 1.0 - r) ** 2.0)),
		"ring": _layer(white, _radial(128, lambda r: math.exp(-((r - 0.78) / 0.05) ** 2))),
		"bokeh": _layer(white, _radial(128, lambda r: 0.0 if r > 0.95 else
			(0.5 + 0.5 * math.exp(-((r - 0.86) / 0.05) ** 2)) * min(1.0, (0.95 - r) / 0.05))),
		"hex": _make_hex(),
		"bubble": _make_bubble(),
		"moon": _make_moon(rnd),
		"leaf": _make_leaf(),
		# Neutral gel, tinted in the skin's hues when drawn (ORB_HUES)
		"orb_play": _make_orb((196, 200, 206), "play"),
		"orb_next": _make_orb((196, 200, 206), "next"),
		"orb_note": _make_orb((196, 200, 206), "note"),
	}
	out["city"], out["city_lights"] = _make_city(rnd)
	for i in range(3):
		out[f"cloud{i}"] = _make_cloud(rnd)
	for kind in ("clown", "tang", "yellow", "koi", "tetra"):
		out[kind] = _make_fish(kind, rnd)
	out["island0"] = _make_island(rnd, False)
	out["island1"] = _make_island(rnd, True)
	prof: dict[str, list[float]] = {}
	out["hills_far"], prof["far"] = _make_hills(rnd, (1024, 192), "none", True)
	out["hills_l"], prof["l"] = _make_hills(rnd, (1536, 384), "right", False)
	out["hills_r"], prof["r"] = _make_hills(rnd, (1536, 384), "left", False)
	return out, prof


# --------------------------------------------------------------------- scene

def _basis(eye, tgt) -> tuple[tuple, tuple, tuple]:
	fx, fy, fz = tgt[0] - eye[0], tgt[1] - eye[1], tgt[2] - eye[2]
	fl = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
	fx, fy, fz = fx / fl, fy / fl, fz / fl
	rx, rz = -fz, fx
	rl = math.sqrt(rx * rx + rz * rz) or 1.0
	rx, rz = rx / rl, rz / rl
	return (rx, 0.0, rz), (-rz * fy, rz * fx - rx * fz, rx * fy), (fx, fy, fz)


class AeroWorld(DreamRoom):

	zoom_out_time = 6.4
	zoom_in_time = 2.6

	def __init__(self, tauon: Tauon) -> None:
		super().__init__(tauon)
		self.tex: dict = {}
		self.hill_prof: dict[str, list[float]] = {}
		self._mirror = False
		self._fade = 1.0		# alpha scale for whatever is being drawn
		self._front = 0.0		# fade for things nearer than the screen (0 at t=0)
		self._e = 0.0
		self._w = 1
		self._h = 1
		self._scr_w = 1.0
		self._flare_vis = 0.0
		self._fb = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0), 1.0)

		rnd = random.Random(1999)
		u = rnd.uniform

		# Clouds: [x, y, z, half-width, texture, drift]
		self.clouds = []
		for (az, el, dist, hw, k, sp) in CLOUDS:
			a = math.radians(az)
			self.clouds.append([dist * math.sin(a), dist * math.tan(math.radians(el)), -dist * math.cos(a), hw, f"cloud{k}", sp])
		self.clouds.sort(key=lambda c: c[2])

		# Floating islands: x, y, z, half-size, texture, bob phase, waterfall
		self.islands_far = [(-58.0, 31.0, -150.0, 17.0, "island1", 1.0), (84.0, 58.0, -265.0, 24.0, "island0", 3.0)]
		self.islands = [(-8.8, 5.9, -16.0, 3.9, "island0", 0.0, True), (13.5, 8.6, -36.0, 6.8, "island1", 2.0, True)]

		# Bubbles: [x, y, z, radius, rise, phase]
		self.bubbles = [[u(-7.0, 8.0), u(0.0, 7.0), u(-13.0, 3.6), 0.03 + 0.4 * rnd.random() ** 3.2, u(0.05, 0.22), u(0, 9)]
			for i in range(30)]
		# Fireflies: [x, y, z, phase, size] (more are added below)
		self.motes = [[u(-2.5, 4.5), u(0.2, 3.0), u(-2.0, 4.0), u(0, 9), u(0.008, 0.022)] for i in range(24)]

		# Fish on elliptical circuits: cx, cz, rx, rz, y, bob, speed, theta0, length, texture.
		# They swim under the lake: only the mirror pass draws them, at depth y
		self.fish = [
			(0.3, -0.6, 4.6, 2.3, 1.72, 0.22, 0.22, 0.00, 0.56, "clown"),
			(0.3, -0.6, 4.6, 2.3, 1.95, 0.22, 0.22, 0.42, 0.44, "clown"),
			(0.3, -0.6, 4.6, 2.3, 1.60, 0.22, 0.22, 0.74, 0.36, "clown"),
			(1.0, -2.2, 7.5, 3.6, 3.05, 0.30, -0.13, 1.00, 0.86, "tang"),
			(1.0, -2.2, 7.5, 3.6, 2.70, 0.30, -0.13, 1.45, 0.66, "tang"),
			(-2.4, -3.0, 3.2, 1.7, 0.72, 0.14, 0.30, 2.00, 0.40, "yellow"),
			(-2.4, -3.0, 3.2, 1.7, 0.95, 0.14, 0.30, 2.60, 0.32, "yellow"),
			(10.0, -72.0, 62.0, 12.0, 23.0, 2.5, 0.034, 1.20, 13.0, "koi"),
		]
		# Neon tetra school: offsets from the school's centre + phase
		self.tetras = [(u(-0.7, 0.7), u(-0.3, 0.3), u(-0.5, 0.5), u(0, 9)) for i in range(16)]
		# Compact discs: centre, radius, phase
		self.discs = [((3.7, 3.2, -4.6), 0.62, 0.0), ((-5.6, 4.5, -10.0), 1.05, 2.0), ((10.5, 9.5, -30.0), 3.0, 4.0)]
		# Stray glass windows adrift: centre, width, height, phase
		self.panes = [
			((-4.3, 3.3, -7.0), 1.7, 1.05, 0.0), ((5.8, 5.4, -12.5), 2.3, 1.45, 1.7), ((-11.5, 8.2, -24.0), 3.2, 2.0, 3.1),
			((4.6, 1.9, -3.4), 0.95, 0.62, 4.6), ((1.8, 7.0, -18.0), 2.6, 1.6, 5.9),
		]
		# Glass stepping tiles back toward where the camera settles: x, z, size, phase
		self.tiles = [(0.05, 0.64, 0.34, 0.0), (0.20, 1.22, 0.36, 1.0), (0.42, 1.80, 0.38, 2.0), (0.68, 2.38, 0.40, 3.0),
			(0.96, 2.96, 0.42, 4.0)]
		# Gel buttons bobbing on the lake: x, z, radius, texture, phase
		self.orbs = [(-1.95, -1.3, 0.34, "orb_play", 0.0), (1.85, -2.7, 0.42, "orb_next", 2.2), (2.35, 0.7, 0.2, "orb_note", 4.1)]
		# Sun glitter on the water: distance, lateral, phase, speed, size
		self.glitter = [(3.0 * 60.0 ** rnd.random(), u(-1, 1), u(0, 9), u(1.5, 5.0), u(0.5, 1.5)) for i in range(64)]
		self.sparkles = [(u(-26.0, 26.0), u(-60.0, 3.0), u(0, 9), u(0.8, 2.6)) for i in range(40)]
		# Ripple sources: x, z, period, phase, max radius, strength
		self.ripples = [
			(SCR_CX, SCR_Z, 5.0, 0.0, 2.6, 96), (SCR_CX, SCR_Z, 5.0, 0.33, 2.6, 96), (SCR_CX, SCR_Z, 5.0, 0.66, 2.6, 96),
			(-6.3, -16.0, 2.4, 0.0, 2.4, 120), (-6.3, -16.0, 2.4, 0.5, 2.4, 120),
			(17.8, -36.0, 2.8, 0.2, 4.0, 120), (17.8, -36.0, 2.8, 0.7, 4.0, 120),
		]
		# Reeds framing the settled shot: screen x (-1..1), distance, height, lean, phase, width
		self.blades = []
		for side in (-1, 1):
			for i in range(11):
				f = rnd.random()
				self.blades.append((
					side * (1.02 - 0.42 * f * f), u(0.95, 1.5), u(0.16, 0.36) + 0.34 * (1 - f) * rnd.random(),
					-side * u(0.04, 0.30), u(0, 9), u(0.012, 0.022), rnd.random() < 0.45))
		self.blades.sort(key=lambda b: -b[1])
		# Leaves on a bough hanging in from the top right: along (0..1), angle, size, phase
		self.leaves = [(0.05 + 0.92 * i / 8 + u(-0.03, 0.03), u(-0.6, 0.6) + (0.5 if i % 2 else -0.4), u(0.07, 0.12), u(0, 9))
			for i in range(9)]
		# Bokeh drifting across the lens: x, y, radius, hue key (0 is the pale light), alpha, phase
		self.bokeh = [(rnd.choice((u(0.0, 0.25), u(0.75, 1.0))), u(0.0, 1.0), u(0.03, 0.09),
			rnd.choice((0, 1, 3)), u(10, 26), u(0, 9)) for i in range(10)]
		self.turbines: list[tuple] = []
		rnd = random.Random(2009)
		u = rnd.uniform
		# Stars on the far plane, thinning toward the horizon: x, y, size, phase, twinkle
		self.stars = [(u(-900.0, 900.0), 30.0 + 530.0 * rnd.random() ** 1.5, u(1.8, 3.6), u(0, 9), u(0.5, 2.0))
			for i in range(190)]
		# More fireflies, spread over the lake and the shore
		self.motes += [[u(-6.0, 7.0), u(0.15, 3.2), u(-9.0, 3.5), u(0, 9), u(0.008, 0.024)] for i in range(64)]
		self.pal: dict = {}

	# ----------------------------------------------------------------- assets

	def _upload(self, im: Image.Image, additive: bool):
		im = im.convert("RGBA")
		if not additive:
			im = _bleed(im)
		tex = sdl3.create_texture_from_rgba(self.renderer, im.width, im.height, im.tobytes())
		sdl3.set_texture_scale_mode(tex, sdl3.SDL_SCALEMODE_LINEAR)
		return tex

	def _ensure_assets(self) -> None:
		if self.tex:
			return
		images, self.hill_prof = build_images()
		for name, im in images.items():
			self.tex[name] = self._upload(im, name in ADDITIVE)
		# Wind turbines standing on the near hills: x, base y, z, height, phase, speed
		for (key, hill, spots) in (("l", HILL_L, (0.42, 0.60, 0.76)), ("r", HILL_R, (0.30, 0.50))):
			x0, x1, hh, z = hill
			prof = self.hill_prof[key]
			for i, f in enumerate(spots):
				base = prof[int(f * (len(prof) - 1))] * hh - 1.0
				self.turbines.append((_lerp(x0, x1, f), base, z + 1.0, 9.0 + 2.0 * (i % 2), f * 20.0, 0.7 + 0.25 * i))
		for i, (x, z) in enumerate(((-8.0, -150.0), (14.0, -172.0), (37.0, -196.0))):	# and a few offshore
			self.turbines.append((x, 0.0, z, 15.0, i * 2.0, 0.9 + 0.2 * i))
		self.turbines.sort(key=lambda t: t[2])

	# ------------------------------------------------------------- primitives

	def _quad(self, pts, cols, uvs=None, texture=None, additive=False) -> None:
		"""DreamRoom._quad with the mirror flip, and a fast path for polygons
		wholly in front of the camera (nearly all of them)."""
		ex, ey, ez = self._eye
		rx, ry, rz = self._right
		ux, uy, uz = self._up
		fx, fy, fz = self._fwd
		focal, cx, cy = self._focal, self._cx, self._cy
		sgn = -1.0 if self._mirror else 1.0
		out = []
		x0 = y0 = 1e9
		x1 = y1 = -1e9
		i = 0
		for (px, py, pz) in pts:
			dx = px - ex
			dy = py * sgn - ey
			dz = pz - ez
			zv = dx * fx + dy * fy + dz * fz
			if zv < NEAR:
				if sgn < 0:
					pts = [(p[0], -p[1], p[2]) for p in pts]
				super()._quad(pts, cols, uvs, texture, additive)
				return
			s = focal / zv
			x = cx + (dx * rx + dz * rz) * s
			y = cy - (dx * ux + dy * uy + dz * uz) * s
			if x < x0:
				x0 = x
			if x > x1:
				x1 = x
			if y < y0:
				y0 = y
			if y > y1:
				y1 = y
			r, g, b, a = cols[i]
			if uvs:
				u, v = uvs[i]
				out.append((x, y, u, v, r * K255, g * K255, b * K255, a * K255))
			else:
				out.append((x, y, 0.0, 0.0, r * K255, g * K255, b * K255, a * K255))
			i += 1
		if x1 < 0.0 or y1 < 0.0 or x0 > self._w or y0 > self._h:
			return
		batch = self.batch
		if texture is not batch.texture or additive != batch.additive:
			batch.set_state(texture, additive)
		base = len(batch.verts)
		batch.verts += out
		if i == 4:
			batch.idx += (base, base + 1, base + 2, base, base + 2, base + 3)
		else:
			batch.idx += (base, base + 1, base + 2)

	def _flat_strip(self, x0, x1, y_top, z, tex, n, flip=False, col=(255, 255, 255), additive=False) -> None:
		"""A textured upright flat standing on the water, cut into columns so
		the affine texture mapping stays straight."""
		q = self._quad
		cols = [(*col, 255)] * 4
		for i in range(n):
			f0, f1 = i / n, (i + 1) / n
			xa, xb = x0 + (x1 - x0) * f0, x0 + (x1 - x0) * f1
			if flip:
				f0, f1 = 1.0 - f0, 1.0 - f1
			q([(xa, y_top, z), (xb, y_top, z), (xb, 0.0, z), (xa, 0.0, z)], cols,
				uvs=[(f0, 0.0), (f1, 0.0), (f1, 1.0), (f0, 1.0)], texture=tex, additive=additive)

	def _proj(self, p) -> tuple[float, float] | None:
		ex, ey, ez = self._eye
		dx, dy, dz = p[0] - ex, p[1] - ey, p[2] - ez
		fx, fy, fz = self._fwd
		zv = dx * fx + dy * fy + dz * fz
		if zv < NEAR:
			return None
		rx, ry, rz = self._right
		ux, uy, uz = self._up
		s = self._focal / zv
		return (self._cx + (dx * rx + dy * ry + dz * rz) * s, self._cy - (dx * ux + dy * uy + dz * uz) * s)

	def _spr(self, c, hw, hh, tex, col=(255, 255, 255), a=255.0, rot=0.0, add=False, flip=False) -> None:
		"""A camera-facing sprite at a world position."""
		x, y, z = c
		mirror = self._mirror
		if mirror:
			y = -y
		ex, ey, ez = self._eye
		dx, dy, dz = x - ex, y - ey, z - ez
		fx, fy, fz = self._fwd
		zv = dx * fx + dy * fy + dz * fz
		if zv < NEAR:
			return
		rx, ry, rz = self._right
		ux, uy, uz = self._up
		s = self._focal / zv
		sx = self._cx + (dx * rx + dy * ry + dz * rz) * s
		sy = self._cy - (dx * ux + dy * uy + dz * uz) * s
		w = hw * s
		h = hh * s
		m = w + h
		if sx + m < 0 or sx - m > self._w or sy + m < 0 or sy - m > self._h:
			return
		self._spr2d(sx, sy, w, h, tex, col, a, rot, add, flip, mirror)

	def _spr2d(self, sx, sy, w, h, tex, col=(255, 255, 255), a=255.0, rot=0.0, add=False, flip=False, vflip=False) -> None:
		"""A screen-space sprite. ``rot`` turns it counter-clockwise."""
		al = a * self._fade * K255
		if al <= 0.004:
			return
		r, g, b = col[0] * K255, col[1] * K255, col[2] * K255
		u0, u1 = (1.0, 0.0) if flip else (0.0, 1.0)
		v0, v1 = (1.0, 0.0) if vflip else (0.0, 1.0)
		if rot:
			if vflip:
				rot = -rot
			c, s = math.cos(rot), math.sin(rot)
			wx, wy = w * c, -w * s
			ux, uy = -h * s, -h * c
		else:
			wx, wy, ux, uy = w, 0.0, 0.0, -h
		batch = self.batch
		batch.set_state(tex, add)
		batch.poly([
			(sx - wx + ux, sy - wy + uy, u0, v0, r, g, b, al),
			(sx + wx + ux, sy + wy + uy, u1, v0, r, g, b, al),
			(sx + wx - ux, sy + wy - uy, u1, v1, r, g, b, al),
			(sx - wx - ux, sy - wy - uy, u0, v1, r, g, b, al),
		])

	def _fview(self, xn: float, yn: float, d: float) -> tuple[float, float, float]:
		"""A point in the settled camera's view: xn/yn are -1..1 across the frame."""
		eye, r, u, f, aspect = self._fb
		hh = math.tan(FOV / 2) * d
		a = xn * hh * aspect
		b = yn * hh
		return (eye[0] + r[0] * a + u[0] * b + f[0] * d, eye[1] + r[1] * a + u[1] * b + f[1] * d,
			eye[2] + r[2] * a + u[2] * b + f[2] * d)

	# ---------------------------------------------------------------- animate

	def _advance(self, dt: float) -> None:
		T = self.T
		for c in self.clouds:
			c[0] += c[5] * dt
			if c[0] > -c[2] * 1.4:
				c[0] = c[2] * 1.4
		for b in self.bubbles:
			b[1] += b[4] * dt
			b[0] += math.sin(T * 0.7 + b[5]) * 0.05 * dt
			if b[1] > 7.5:
				b[1] = -b[3]
				b[0] = random.uniform(-7.0, 8.0)
				b[2] = random.uniform(-13.0, 3.6)
		for m in self.motes:
			m[0] += (0.03 + math.sin(T * 0.21 + m[3]) * 0.02) * dt
			m[1] += math.sin(T * 0.13 + m[3] * 2) * 0.02 * dt
			if m[0] > 7.0:
				m[0] = -6.0

	# ---------------------------------------------------------------- palette

	def _palette(self) -> None:
		"""This frame's colours, from the skin's sky as t_aero paints it: its
		hues follow the playing album, and Obsidian greys them out."""
		aero = getattr(self.tauon, "aero", None)
		if aero is None:
			h1, h2, acc = Aero.DEFAULT_PALETTE
			m, oacc = 0.0, Aero.ICE
		else:
			h1, h2, acc, m, oacc = aero.h1, aero.h2, aero.acc, aero.mono, aero.oacc
		cool = _hue_lerp(h1, 215, m)
		hues = {1: cool, 2: _hue_lerp(h2, 30, m), 3: _hue_lerp(acc, oacc, m)}

		def rgb(c) -> tuple[int, int, int]:
			return (round(c[0] * 255), round(c[1] * 255), round(c[2] * 255))

		def tone(h, s, li, ol=None, keep=False) -> tuple[int, int, int]:
			"""Under Obsidian, saturation eases out (unless keep) and lightness to ol."""
			return rgb(hsl(h, s if keep else _lerp(s, 0.10, m), li if ol is None else _lerp(li, ol, m)))

		p = self.pal
		p["sky"] = [(y, tone(hues[k], s, li, ol)) for (y, k, s, li, ol) in SKY]
		horizon = p["sky"][0][1]
		deep = tone(cool, 0.62, 0.045, 0.03)
		p["water"] = [(d, _mix(deep, horizon, f), a) for (d, f, a) in WATER]
		p["mist"] = _mix(horizon, (255, 255, 255), 0.2)
		glow = tone(hues[3], 0.85, 0.70, keep=True)
		p["glow"] = glow
		p["ice"] = _mix((214, 232, 250), glow, 0.25)
		p["lamp"] = _mix((255, 255, 255), glow, 0.3)
		p["tint"] = _mix((255, 255, 255), tone(cool, 0.45, 0.75), 0.35)
		p["cloud"] = _mix((255, 255, 255), tone(cool, 0.5, 0.7), 0.45)
		p["hue"] = {0: p["ice"], **{k: tone(h, 0.8, 0.7, keep=k == 3) for k, h in hues.items()}}

		# The skin's ribbons: its top hue, the accent, the top hue moved on;
		# silver under Obsidian, bar the accent's
		ribbons = []
		for k, hue in enumerate((h1, acc, h1 + 40)):
			c = hsl(hue, 0.90, 0.65)
			if m > 0:
				o = hsl(oacc, 0.75, 0.66, 0.8) if k == 1 else hsl(215, 0.10, 0.78, 0.5)
				c = tuple(_lerp(c[i], o[i] * o[3], m) for i in range(3))
			ribbons.append(rgb(c))
		p["ribbons"] = ribbons
		blooms = []
		for (x, y, hw, k, off, ba) in BLOOMS:
			bh = (h1, h2, acc)[k - 1] + off
			c = hsl(bh, 0.95, 0.55)
			a = ba
			if m > 0:
				if k == 3:
					o, oa = hsl(oacc, 0.70, 0.50), ba * 0.75
				else:
					o, oa = hsl(_hue_lerp(bh, 215, m), _lerp(0.95, 0.10, m), 0.46), ba * 0.45
				c = tuple(_lerp(c[i], o[i], m) for i in range(3))
				a = _lerp(ba, oa, m)
			blooms.append((x, y, hw, rgb(c), 255.0 * a))
		p["blooms"] = blooms

	# -------------------------------------------------------------------- sky

	def _sky(self, T: float) -> None:
		q = self._quad
		mirror = self._mirror
		tex = self.tex
		pal = self.pal
		sky = pal["sky"]
		for (y0, c0), (y1, c1) in zip(sky, sky[1:]):
			q([(-1100.0, y1, SKY_Z), (1100.0, y1, SKY_Z), (1100.0, y0, SKY_Z), (-1100.0, y0, SKY_Z)],
				[(*c1, 255), (*c1, 255), (*c0, 255), (*c0, 255)])

		soft = tex["soft"]
		for (x, y, hw, col, a) in pal["blooms"]:
			self._spr((x, y, SKY_Z + 8.0), hw, hw, soft, col, a, add=True)
		# Stars, fading out into the glow over the horizon
		ice = pal["ice"]
		for (x, y, s, ph, sp) in self.stars:
			a = 255.0 * (0.55 + 0.45 * math.sin(T * sp + ph)) * min(1.0, y / 130.0)
			self._spr((x, y, SKY_Z + 6.0), s, s, soft, ice, a, add=True)

		self._spr(MOON, 210.0, 210.0, soft, pal["glow"], 30, add=True)
		self._spr(MOON, 64.0, 64.0, soft, ice, 72, add=True)
		self._spr(MOON, MOON_R * 1.7, MOON_R * 1.7, soft, (255, 255, 255), 110, add=True)
		self._spr(MOON, MOON_R, MOON_R, tex["moon"], (255, 255, 255), 255)
		if not mirror:
			sx, sy, sz = MOON
			for i in range(12):	# faint moonbeams
				a = i * TAU / 12 + T * 0.016 + 0.3 * math.sin(i * 1.9)
				hw = 0.030 * (1.0 + 0.5 * math.sin(i * 1.7))
				ln = 300.0 + 100.0 * math.sin(i * 2.3)
				q([(sx, sy, sz), (sx + math.cos(a - hw) * ln, sy + math.sin(a - hw) * ln, sz),
					(sx + math.cos(a + hw) * ln, sy + math.sin(a + hw) * ln, sz)],
					[(*ice, 13), (*ice, 0), (*ice, 0)], additive=True)
			self._aurora(T)

		cloud = pal["cloud"]
		for (x, y, z, hw, key, sp) in self.clouds:
			self._spr((x, y, z), hw, hw * 0.5, tex[key], cloud, 226)

	def _aurora(self, T: float) -> None:
		q = self._quad
		n = 22
		z = SKY_Z + 14.0
		for (y0, amp, fr, sp, ph, wd, al), col in zip(RIBBONS, self.pal["ribbons"], strict=True):
			edge = _mix(col, (255, 255, 255), 0.5)
			px = py = pw = pa = 0.0
			for i in range(n + 1):
				s = i / n
				x = -560.0 + 1040.0 * s
				y = y0 + 90.0 * (s - 0.5) + amp * math.sin(TAU * (s * fr + T * sp) + ph) \
					+ amp * 0.35 * math.sin(TAU * (s * fr * 2.3 - T * sp * 1.7) + ph * 2.0)
				w = wd * (0.35 + 0.65 * math.sin(math.pi * s)) * (1.0 + 0.25 * math.sin(TAU * (s * 1.7 + T * sp * 2.0) + ph))
				a = al * math.sin(math.pi * s) ** 0.7
				if i:
					q([(px, py, z), (x, y, z), (x, y - w, z), (px, py - pw, z)],
						[(*col, pa), (*col, a), (*col, 0), (*col, 0)], additive=True)
					# crisp leading edge
					q([(px, py + 1.5, z), (x, y + 1.5, z), (x, y - 1.5, z), (px, py - 1.5, z)],
						[(*edge, pa), (*edge, a), (*edge, a), (*edge, pa)], additive=True)
				px, py, pw, pa = x, y, w, a

	# ------------------------------------------------------------------- land

	def _land(self, T: float) -> None:
		q = self._quad
		g = self._flat_strip
		tex = self.tex
		mirror = self._mirror
		n = 6 if mirror else 12
		tint = self.pal["tint"]

		# Hazy far range, the texture mirrored about the middle so it joins up
		g(-760.0, 0.0, 44.0, -330.0, tex["hills_far"], 8, col=tint)
		g(0.0, 760.0, 44.0, -330.0, tex["hills_far"], 8, True, col=tint)
		x, y, z, hw, key, ph = self.islands_far[1]
		self._spr((x, y + math.sin(T * 0.2 + ph) * 1.5, z), hw, hw, tex[key], _mix(tint, (90, 110, 130), 0.4), 235)

		# The city on the water, and its lights
		g(-80.0, 190.0, 64.0, -240.0, tex["city"], n, col=tint)
		g(-80.0, 190.0, 64.0, -240.0, tex["city_lights"], n, col=self.pal["lamp"], additive=True)
		x, y, z, hw, key, ph = self.islands_far[0]
		self._spr((x, y + math.sin(T * 0.25 + ph) * 1.0, z), hw, hw, tex[key], _mix(tint, (90, 110, 130), 0.25), 250)

		# Near hills either side of the gap
		for (key, (x0, x1, hh, z)) in (("hills_l", HILL_L), ("hills_r", HILL_R)):
			g(x0, x1, hh, z, tex[key], n, col=tint)

		soft = tex["soft"]
		for (x, y0, z, ht, ph, sp) in self.turbines:
			y1 = y0 + ht
			tw = ht * 0.028
			q([(x - tw * 0.45, y1, z), (x + tw * 0.45, y1, z), (x + tw, y0, z), (x - tw, y0, z)],
				[(58, 70, 88, 255), (92, 108, 126, 255), (64, 78, 96, 255), (36, 46, 60, 255)])
			ln = ht * 0.56
			for k in range(3):
				a = T * sp + ph + k * TAU / 3
				dx, dy = math.cos(a), math.sin(a)
				nx, ny = -dy, dx
				q([(x + nx * tw, y1 + ny * tw, z + 0.3), (x + dx * ln + nx * tw * 0.25, y1 + dy * ln + ny * tw * 0.25, z + 0.3),
					(x + dx * ln - nx * tw * 0.25, y1 - ny * tw * 0.25 + dy * ln, z + 0.3), (x - nx * tw, y1 - ny * tw, z + 0.3)],
					[(96, 112, 132, 250), (70, 84, 102, 250), (70, 84, 102, 250), (60, 72, 90, 250)])
			# Aircraft warning light on the nacelle
			blink = max(0.0, math.sin(T * 1.6 + ph)) ** 6
			if blink > 0.02:
				self._spr((x, y1 + tw, z + 0.4), ht * 0.09, ht * 0.09, soft, (255, 60, 50), 255.0 * blink, add=True)

		if not mirror:
			# Mist along the far shore softens the horizon
			mist = self.pal["mist"]
			for (ya, yb) in ((0.0, 9.0), (0.0, -3.0)):
				q([(-900.0, yb, -232.0), (900.0, yb, -232.0), (900.0, ya, -232.0), (-900.0, ya, -232.0)],
					[(*mist, 0), (*mist, 0), (*mist, 64), (*mist, 64)])

	# ------------------------------------------------------------------ water

	def _ring(self, x: float, z: float, r: float, th: float, a: float) -> None:
		if a < 2.0:
			return
		q = self._quad
		ice = self.pal["ice"]
		c1 = (*ice, a * 0.7)
		c0 = (*ice, 0)
		ro = r + th
		px, pz = CIRCLE[0]
		for (cx, cz) in CIRCLE[1:]:
			q([(x + px * r, 0.012, z + pz * r), (x + cx * r, 0.012, z + cz * r),
				(x + cx * ro, 0.012, z + cz * ro), (x + px * ro, 0.012, z + pz * ro)], [c1, c1, c0, c0], additive=True)
			px, pz = cx, cz

	def _water(self, T: float) -> None:
		q = self._quad
		ex, ey, ez = self._eye
		pal = self.pal
		pz, pc = 0.0, None
		for (d, col, a) in pal["water"]:
			z = max(SKY_Z, ez - d)
			c = (*col, a)
			if pc is not None:
				q([(-1100.0, 0.0, z), (1100.0, 0.0, z), (1100.0, 0.0, pz), (-1100.0, 0.0, pz)], [c, c, pc, pc])
			pz, pc = z, c

		# The moon's glitter path, running from the camera toward the moon
		ice = pal["ice"]
		dx, dz = MOON[0] - ex, MOON[2] - ez
		dl = math.sqrt(dx * dx + dz * dz)
		dx, dz = dx / dl, dz / dl
		nx, nz = -dz, dx
		for (d, lat, ph, sp, size) in self.glitter:
			tw = math.sin(T * sp + ph)
			if tw <= 0.0:
				continue
			a = 190.0 * tw * tw
			cx = ex + dx * d + nx * lat * d * 0.07
			cz = ez + dz * d + nz * lat * d * 0.07
			hw = 0.03 * d * size
			hd = 0.012 * d
			q([(cx - nx * hw, 0.01, cz - nz * hw), (cx + dx * hd, 0.01, cz + dz * hd),
				(cx + nx * hw, 0.01, cz + nz * hw), (cx - dx * hd, 0.01, cz - dz * hd)],
				[(*ice, 0), (*ice, a), (*ice, 0), (*ice, a)], additive=True)
		soft = self.tex["soft"]
		for (x, z, ph, sp) in self.sparkles:
			tw = math.sin(T * sp + ph)
			if tw > 0.55:
				s = 0.012 * (4.0 + ez - z) ** 0.9
				self._spr((x, 0.02, z), s * 2.2, s * 0.5, soft, ice, 200 * (tw - 0.55) * 2.2, add=True)

		# Ripples: under the screen, under the waterfalls, and where things land
		for (x, z, period, ph, rmax, strength) in self.ripples:
			age = (T / period + ph) % 1.0
			self._ring(x, z, rmax * age, rmax * (0.03 + 0.07 * age), strength * (1.0 - age) ** 1.5)
		for i in range(3):	# stray drops
			cyc = T / 3.7 + i * 0.37
			k = math.floor(cyc)
			age = cyc - k
			hx = math.sin(k * 12.9898 + i * 78.233) * 43758.5453
			hz = math.sin(k * 39.3468 + i * 11.135) * 24634.6345
			self._ring(-3.0 + 7.0 * (hx - math.floor(hx)), -5.0 + 8.0 * (hz - math.floor(hz)), 1.1 * age, 0.02 + 0.05 * age,
				150.0 * (1.0 - age) ** 2)
		self._glow((SCR_CX, 0.008, SCR_Z + 0.1), self._scr_w * 0.9, 1.3, pal["glow"], 50.0 * self._e, axis="y")

	# --------------------------------------------------------- loose objects

	def _collect(self, T: float) -> list[tuple]:
		"""Everything adrift near the screen, sorted far to near:
		(view depth, world z, draw function, args)."""
		items: list[tuple] = []
		tex = self.tex
		ex, ey, ez = self._eye
		fx, fy, fz = self._fwd
		sin, cos = math.sin, math.cos
		hues = self.pal["hue"]

		def put(p, fn, *args) -> None:
			items.append(((p[0] - ex) * fx + (p[1] - ey) * fy + (p[2] - ez) * fz, p[2], fn, args))

		for (x, y, z, hw, key, ph, fall) in self.islands:
			p = (x, y + sin(T * 0.4 + ph) * 0.22, z)
			put(p, self._island, p, hw, key, ph, T)
		for (c, r, ph) in self.discs:
			p = (c[0], c[1] + sin(T * 0.5 + ph) * 0.15 * r, c[2])
			put(p, self._disc, p, r, T * 0.35 + ph, 0.5 + 0.3 * sin(T * 0.23 + ph), T * 0.11 + ph)
		for (c, w, h, ph) in self.panes:
			p = (c[0] + sin(T * 0.13 + ph) * 0.3, c[1] + sin(T * 0.31 + ph) * 0.12, c[2])
			put(p, self._pane, p, w, h, 0.55 * sin(T * 0.21 + ph))
		for (x, z, s, ph) in self.tiles:
			put((x, 0.0, z), self._tile, x, 0.035 + 0.012 * sin(T * 0.9 + ph), z, s)
		for (x, z, r, key, ph) in self.orbs:
			p = (x, r * 0.5 + 0.03 * sin(T * 1.3 + ph), z)
			put(p, self._spr, p, r, r, tex[key], hues[ORB_HUES[key]], 255.0, 0.1 * sin(T * 0.9 + ph))
		bub = tex["bubble"]
		for (x, y, z, r, sp, ph) in self.bubbles:
			wob = 1.0 + 0.05 * sin(T * 2.1 + ph)
			put((x, y, z), self._spr, (x, y, z), r * wob, r / wob, bub, (196, 224, 246), 200.0)
		# Two big bubbles with something caught inside
		p = (5.3, 2.7 + 0.2 * sin(T * 0.37), -6.6)
		put(p, self._bubble_world, p, 1.25, tex["island0"], 0.8)
		p = (-3.3, 2.35 + 0.12 * sin(T * 0.5 + 2), -3.4)
		put(p, self._bubble_world, p, 0.52, tex["orb_note"], 0.26, hues[ORB_HUES["orb_note"]])
		# Fireflies, glowing in and out: warm yellow-green, nudged toward the accent
		glow = _mix((200, 255, 96), self.pal["glow"], 0.15)
		for (x, y, z, ph, s) in self.motes:
			a = max(0.0, sin(T * 0.9 + ph)) ** 1.5
			if a > 0.01:
				put((x, y, z), self._firefly, (x, y, z), s, glow, a)

		moonlit = (112, 126, 158)
		for (cx, cz, rx, rz, y, bob, sp, th0, ln, key) in self.fish:
			th = th0 * TAU + T * sp
			hx, hz = -rx * sin(th), rz * cos(th)
			if sp < 0:
				hx, hz = -hx, -hz
			hl = math.hypot(hx, hz)
			p = (cx + rx * cos(th), y + bob * sin(th * 2.0 + th0 * 9.0), cz + rz * sin(th))
			put(p, self._below, self._fish, p, hx / hl, hz / hl, ln, tex[key], T * (2.0 if ln > 5 else 7.0) + th0 * 20.0, moonlit)
		# The tetra school wanders as one
		sx = 2.2 + 2.6 * sin(T * 0.21)
		sy = 1.15 + 0.4 * sin(T * 0.33)
		sz = -1.0 + 2.4 * sin(T * 0.17 + 1.0)
		right = cos(T * 0.21) > 0
		tetra = tex["tetra"]
		for (ox, oy, oz, ph) in self.tetras:
			p = (sx + ox + 0.08 * sin(T * 1.7 + ph), sy + oy + 0.05 * sin(T * 2.3 + ph), sz + oz)
			put(p, self._below, self._spr, p, 0.075, 0.0375, tetra, (255, 255, 255), 255.0, 0.0, False, right)

		items.sort(key=lambda it: -it[0])
		return items

	def _island(self, p, hw, key, ph, T) -> None:
		tex = self.tex
		self._spr(p, hw, hw, tex[key], (255, 255, 255), 255.0)
		if key == "island1":	# lamplight from the house's window
			self._spr((p[0] + hw * 0.36, p[1] + hw * 0.39, p[2] + 0.05), hw * 0.3, hw * 0.24, tex["soft"],
				(255, 206, 140), 150.0, add=True)
		# A waterfall off the rim, all the way down to the lake
		q = self._quad
		x, top, z = p[0] + hw * 0.62, p[1] + hw * 0.02, p[2] + 0.05
		w = hw * 0.07
		f = self._fade
		ice = self.pal["ice"]
		q([(x - w, top, z), (x + w, top, z), (x + w * 1.7, 0.0, z), (x - w * 1.7, 0.0, z)],
			[(*ice, 120 * f), (*ice, 120 * f), (*ice, 60 * f), (*ice, 60 * f)])
		if self._mirror:
			return
		for i in range(9):
			k = (T * 0.5 + i / 9 + ph) % 1.0
			y = top * (1.0 - k * k)
			ln = 0.3 + top * 0.18 * k
			xo = x + w * 1.3 * math.sin(i * 7.3 + ph * 5.0) * (0.5 + 0.5 * k)
			sw = w * 0.22
			q([(xo - sw, y, z), (xo + sw, y, z), (xo + sw, y - ln, z), (xo - sw, y - ln, z)],
				[(*ice, 0), (*ice, 0), (*ice, 120 * f), (*ice, 120 * f)], additive=True)
		self._spr((x, w * 2.0, z), w * 9.0, w * 4.0, tex["soft"], ice, 90.0 + 25.0 * math.sin(T * 3.0), add=True)

	def _below(self, fn, *args) -> None:
		"""Draw only in the mirror pass, i.e. beneath the water's surface."""
		if self._mirror:
			fn(*args)

	def _bubble_world(self, p, r, inner, inner_r, col=(220, 228, 240)) -> None:
		self._spr(p, inner_r, inner_r, inner, col, 255.0)
		self._spr(p, r, r, self.tex["bubble"], (196, 224, 246), 220.0)

	def _firefly(self, p, s, col, a) -> None:
		soft = self.tex["soft"]
		self._spr(p, s * 7.0, s * 7.0, soft, col, 120.0 * a, add=True)
		self._spr(p, s * 1.4, s * 1.4, soft, _mix(col, (255, 255, 255), 0.6), 255.0 * a, add=True)

	def _fish(self, p, hx, hz, ln, tex, w, col=(255, 255, 255)) -> None:
		"""A fish as a ribbon along its heading, with a wave running down the body."""
		q = self._quad
		x, y, z = p
		px, pz = -hz, hx
		hh = ln * 0.25
		a = 255.0 * self._fade
		cols = [(*col, a)] * 4
		n = 4
		bx = bz = 0.0
		for k in range(n + 1):
			s = k / n
			lat = ln * 0.11 * (s * s + 0.1) * math.sin(w - s * 3.2)
			cx = x - hx * (s - 0.45) * ln + px * lat
			cz = z - hz * (s - 0.45) * ln + pz * lat
			if k:
				s0 = (k - 1) / n
				q([(bx, y + hh, bz), (cx, y + hh, cz), (cx, y - hh, cz), (bx, y - hh, bz)], cols,
					uvs=[(s0, 0.0), (s, 0.0), (s, 1.0), (s0, 1.0)], texture=tex)
			bx, bz = cx, cz

	def _disc(self, c, rad, yaw, tilt, spin) -> None:
		"""A compact disc, iridescent and slowly tumbling."""
		q = self._quad
		cx, cy, cz = c
		cyw, syw = math.cos(yaw), math.sin(yaw)
		ct, st = math.cos(tilt), math.sin(tilt)
		ax, ay, az = cyw, 0.0, -syw
		bx, by, bz = syw * st, ct, cyw * st
		f = self._fade
		r0, r1, r2 = rad * 0.14, rad * 0.34, rad
		n = 14
		mirror = self._mirror
		hsv = colorsys.hsv_to_rgb
		pd = pc_in = pc_out = None
		for i in range(n + 1):
			a = TAU * i / n
			ca, sa = math.cos(a), math.sin(a)
			d = (ax * ca + bx * sa, ay * ca + by * sa, az * ca + bz * sa)
			glint = max(0.0, math.cos(a * 2.0 - spin * 3.0)) ** 10
			sat = 0.5 * (1.0 - glint)
			r, g, b = hsv((i / n * 2.0 + spin) % 1.0, sat * 0.8, 0.46 + 0.54 * glint)
			c_out = (r * 255, g * 255, b * 255, 210 * f)
			r, g, b = hsv((i / n * 2.0 + spin + 0.22) % 1.0, sat * 0.6, 0.42 + 0.58 * glint)
			c_in = (r * 255, g * 255, b * 255, 210 * f)
			if pd is not None and not mirror:
				q([(cx + pd[0] * r0, cy + pd[1] * r0, cz + pd[2] * r0), (cx + d[0] * r0, cy + d[1] * r0, cz + d[2] * r0),
					(cx + d[0] * r1, cy + d[1] * r1, cz + d[2] * r1), (cx + pd[0] * r1, cy + pd[1] * r1, cz + pd[2] * r1)],
					[(120, 150, 180, 110 * f)] * 4)
			if pd is not None:
				q([(cx + pd[0] * r1, cy + pd[1] * r1, cz + pd[2] * r1), (cx + d[0] * r1, cy + d[1] * r1, cz + d[2] * r1),
					(cx + d[0] * r2, cy + d[1] * r2, cz + d[2] * r2), (cx + pd[0] * r2, cy + pd[1] * r2, cz + pd[2] * r2)],
					[pc_in, c_in, c_out, pc_out])
			pd, pc_in, pc_out = d, c_in, c_out

	def _pane(self, c, w, h, yaw) -> None:
		"""An empty glass window, drifting off on its own."""
		q = self._quad
		x, y, z = c
		rx, rz = math.cos(yaw) * w * 0.5, -math.sin(yaw) * w * 0.5
		hh = h * 0.5
		f = self._fade
		tl, tr = (x - rx, y + hh, z - rz), (x + rx, y + hh, z + rz)
		br, bl = (x + rx, y - hh, z + rz), (x - rx, y - hh, z - rz)
		# The skin's glass: a dark tint, a sheen over the top, cyan rims
		q([tl, tr, br, bl], [(14, 40, 62, 120 * f), (10, 32, 52, 104 * f), (6, 22, 40, 126 * f), (8, 26, 46, 136 * f)])
		tb = h * 0.3
		q([tl, tr, (tr[0], tr[1] - tb, tr[2]), (tl[0], tl[1] - tb, tl[2])],
			[(190, 235, 255, 60 * f), (190, 235, 255, 44 * f), (190, 235, 255, 6 * f), (190, 235, 255, 8 * f)])
		e = h * 0.018
		edge = [(180, 232, 255, 150 * f)] * 4
		dim = [(150, 215, 255, 54 * f)] * 4
		q([tl, tr, (tr[0], tr[1] - e, tr[2]), (tl[0], tl[1] - e, tl[2])], edge)
		q([bl, br, (br[0], br[1] + e, br[2]), (bl[0], bl[1] + e, bl[2])], dim)
		ex, ez = rx / w * e * 2.0, rz / w * e * 2.0
		q([tl, (tl[0] + ex, tl[1], tl[2] + ez), (bl[0] + ex, bl[1], bl[2] + ez), bl], edge)
		q([(tr[0] - ex, tr[1], tr[2] - ez), tr, br, (br[0] - ex, br[1], br[2] - ez)], dim)

	def _tile(self, x, y, z, s) -> None:
		if self._mirror:
			return
		q = self._quad
		f = self._fade
		h = s * 0.5
		q([(x - h, y, z - h), (x + h, y, z - h), (x + h, y, z + h), (x - h, y, z + h)],
			[(60, 110, 140, 110 * f), (24, 60, 88, 90 * f), (12, 36, 58, 120 * f), (30, 70, 100, 90 * f)])
		e = s * 0.045
		edge = [(180, 232, 255, 160 * f)] * 4
		q([(x - h, y, z - h), (x + h, y, z - h), (x + h, y, z - h + e), (x - h, y, z - h + e)], edge)
		q([(x - h, y, z - h), (x - h + e, y, z - h), (x - h + e, y, z + h), (x - h, y, z + h)], edge)
		q([(x - h, y, z + h - e), (x + h, y, z + h - e), (x + h, y, z + h), (x - h, y, z + h)], [(150, 215, 255, 70 * f)] * 4)
		q([(x - h, y - 0.025, z + h), (x + h, y - 0.025, z + h), (x + h, y, z + h), (x - h, y, z + h)],
			[(40, 90, 124, 110 * f)] * 4)

	# ----------------------------------------------------------------- screen

	def _panel(self) -> None:
		q = self._quad
		mirror = self._mirror
		sw = self._scr_w
		sx0, sx1 = SCR_CX - sw / 2, SCR_CX + sw / 2
		sy0, sy1 = SCR_CY - SCR_H / 2, SCR_CY + SCR_H / 2
		z = SCR_Z
		if not mirror:
			self._glow((SCR_CX, SCR_CY, z - 0.05), sw * 0.9, SCR_H * 1.05, self.pal["glow"], 64)
		# No frame of its own: the app window floats as it is
		if mirror:
			self._draw_app(sx0, sx1, sy0, sy1, z, 5, 3)
			return
		self._draw_app(sx0, sx1, sy0, sy1, z)
		a = 20.0 * self._front
		q([(sx0, sy1, z), (sx0 + sw * 0.56, sy1, z), (sx0 + sw * 0.30, sy0, z), (sx0, sy0, z)],
			[(255, 255, 255, a), (255, 255, 255, a * 0.4), (255, 255, 255, 0), (255, 255, 255, a * 0.5)], additive=True)

	# ------------------------------------------------------------- foreground

	def _foreground(self, T: float) -> None:
		f = self._front
		if f <= 0.01:
			return
		q = self._quad
		tex = self.tex
		rx, ry, rz = self._right
		bubble, soft = tex["bubble"], tex["soft"]
		ice = self.pal["ice"]
		self._fade = f
		a = 255.0 * f
		tanh = math.tan(FOV / 2)
		fr, fu = self._fb[1], self._fb[2]
		for (xn, d, hn, lean, ph, wd, dew) in self.blades:
			bx, by, bz = self._fview(xn, -1.0, d)
			ht = max(0.2, by + hn * tanh * d * 2.0)
			sway = math.sin(T * 1.1 + ph) * 0.035 + math.sin(T * 2.3 + ph * 2.0) * 0.012
			n = 4
			pl = pr = None
			pcl = pcr = None
			for k in range(n + 1):
				s = k / n
				off = (lean + sway) * s * s * ht
				px = bx + fr[0] * off
				py = ht * s * (1.0 - 0.1 * s * s)
				pz = bz + fr[2] * off
				w = wd * (1.0 - s ** 1.6) + 0.0015
				# Near-black silhouettes, the moon catching one edge
				if s < 0.5:
					c = _mix((2, 10, 14), (8, 28, 34), s * 2.0)
				else:
					c = _mix((8, 28, 34), (26, 60, 66), s * 2.0 - 1.0)
				cl = (min(255, c[0] + 16), min(255, c[1] + 26), min(255, c[2] + 34), a)
				cr = (*c, a)
				left = (px - rx * w, py, pz - rz * w)
				right = (px + rx * w, py, pz + rz * w)
				if pl is not None:
					q([pl, left, right, pr], [pcl, cl, cr, pcr])
				if dew and k == 2:
					self._spr((px, py, pz), 0.017, 0.019, bubble, (170, 210, 236), 230.0)
					self._spr((px - 0.004, py + 0.006, pz), 0.012, 0.012, soft, ice, 200.0, add=True)
				pl, pr, pcl, pcr = left, right, cl, cr

		# A leafy bough reaching in from the top right, against the moonlit sky
		d = 1.05
		p0 = self._fview(1.15, 1.10, d)
		p1 = self._fview(0.56, 0.86, d)
		bw = 0.009
		q([(p0[0], p0[1] + bw, p0[2]), (p1[0], p1[1] + bw * 0.3, p1[2]), (p1[0], p1[1] - bw * 0.3, p1[2]), (p0[0], p0[1] - bw, p0[2])],
			[(20, 18, 22, a), (30, 28, 32, a), (14, 12, 16, a), (10, 10, 14, a)])
		leaf = tex["leaf"]
		for (s, ang, size, ph) in self.leaves:
			th = ang + 0.09 * math.sin(T * 1.3 + ph) + 0.03 * math.sin(T * 2.9 + ph)
			hx, hy = math.sin(th) * size, -math.cos(th) * size
			sag = 0.02 * math.sin(math.pi * s)
			c = (_lerp(p0[0], p1[0], s) + fr[0] * hx + fu[0] * hy, _lerp(p0[1], p1[1], s) - sag + fr[1] * hx + fu[1] * hy,
				_lerp(p0[2], p1[2], s) + fr[2] * hx + fu[2] * hy)
			self._spr(c, size * 0.5, size, leaf, (46, 72, 80), 255.0, th)
		self._fade = 1.0

	# ------------------------------------------------------------------- lens

	def _lens(self, T: float) -> None:
		f = self._front
		w, h = self._w, self._h
		tex = self.tex
		s2 = self._spr2d
		target = 0.0
		pal = self.pal
		pr = self._proj(MOON)
		if pr is not None:
			sx, sy = pr
			if -0.2 * w < sx < 1.2 * w and -0.3 * h < sy < 1.2 * h:
				target = 1.0
				sw, sh = self._scr_w / 2 + 0.05, SCR_H / 2 + 0.05
				corners = [self._proj((SCR_CX + i * sw, SCR_CY + j * sh, SCR_Z)) for i in (-1, 1) for j in (-1, 1)]
				if None in corners:
					target = 0.0
				elif min(c[0] for c in corners) < sx < max(c[0] for c in corners) \
						and min(c[1] for c in corners) < sy < max(c[1] for c in corners):
					target = 0.0	# the moon is behind the screen
		self._flare_vis += (target - self._flare_vis) * 0.12
		v = self._flare_vis * f
		hues = pal["hue"]
		if v > 0.01 and pr is not None:
			self._fade = v
			soft = tex["soft"]
			# A cool anamorphic streak, and ghosts in the skin's hues
			s2(sx, sy, h * 0.45, h * 0.45, soft, pal["glow"], 22, add=True)
			s2(sx, sy, h * 0.95, h * 0.008, soft, pal["ice"], 130, add=True)
			s2(sx, sy, h * 0.008, h * 0.22, soft, pal["ice"], 50, add=True)
			dx, dy = self._cx - sx, self._cy - sy
			for (k, size, hue, a, key) in GHOSTS:
				col = (255, 255, 255) if hue is None else _mix(hues[hue[0]], (255, 255, 255), 0.2)
				s2(sx + dx * k, sy + dy * k, h * size, h * size, tex[key], col, a, add=True)
		self._fade = f
		if f > 0.01:
			bk = tex["bokeh"]
			for (bx, by, r, key, a, ph) in self.bokeh:
				s2((bx + 0.03 * math.sin(T * 0.11 + ph)) * w, (by + 0.05 * math.sin(T * 0.07 + ph * 2.0)) * h,
					r * h, r * h, bk, hues[key], a * (0.7 + 0.3 * math.sin(T * 0.5 + ph)), add=True)
		self._fade = 1.0
		self.batch.flush()

	# ----------------------------------------------------------------- render

	def render(self) -> None:
		renderer = self.renderer
		dt = self._step()
		self._ensure_assets()
		self._palette()
		self._advance(dt)

		w, h = self.window_size[0], self.window_size[1]
		self._w, self._h = w, h
		aspect = w / max(1, h)
		self._scr_w = SCR_H * aspect
		e = _smooth(self.t)
		T = self.T
		self._e = e
		self._front = min(1.0, e * 2.5)
		self._fb = (END_EYE, *_basis(END_EYE, END_TGT), aspect)

		# Camera: straight back out of the screen, lifting over the stepping
		# tiles, then settling low over the water off to one side.
		d0 = (SCR_H / 2) / math.tan(FOV / 2)
		eye = (
			_lerp(SCR_CX, END_EYE[0], e) + math.sin(T * 0.23) * 0.10 * e,
			_lerp(SCR_CY, END_EYE[1], e) + 0.38 * math.sin(math.pi * e) + math.sin(T * 0.19 + 1.7) * 0.04 * e,
			_lerp(SCR_Z + d0, END_EYE[2], e) + math.sin(T * 0.15 + 0.6) * 0.08 * e,
		)
		tgt = (
			_lerp(SCR_CX, END_TGT[0], e) + math.sin(T * 0.17 + 4.0) * 0.03 * e,
			_lerp(SCR_CY, END_TGT[1], e) + math.sin(T * 0.21 + 2.2) * 0.02 * e,
			SCR_Z,
		)
		self._camera(eye, tgt)

		sdl3.set_render_draw_blend_mode(renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.set_render_draw_color(renderer, *self.pal["sky"][0][1], 255)
		sdl3.render_clear(renderer)
		sdl3.set_render_draw_blend_mode(renderer, sdl3.SDL_BLENDMODE_BLEND)

		items = self._collect(T)
		behind = [it for it in items if it[1] < SCR_Z]
		front = [it for it in items if it[1] >= SCR_Z]
		ffade = self._front

		self._mirror = False
		self._sky(T)
		for mirror in (True, False):
			self._mirror = mirror
			if mirror:
				self._sky(T)
			else:
				self._water(T)
			self._land(T)
			for it in behind:
				it[2](*it[3])
			self._panel()
			self._fade = ffade
			if ffade > 0.01:
				for it in front:
					it[2](*it[3])
			self._fade = 1.0
		self._foreground(T)
		self._lens(T)
		self.batch.flush()
		self._finish()


class Dreams:
	"""The easter egg scenes behind one switch. At most one is out at a time."""

	def __init__(self, tauon: Tauon) -> None:
		self.room = DreamRoom(tauon)
		self.aero = AeroWorld(tauon)
		self.current: DreamRoom = self.room

	@property
	def active(self) -> bool:
		return self.current.active

	def _toggle(self, scene: DreamRoom) -> None:
		if self.current.active and self.current is not scene:
			return
		self.current = scene
		scene.toggle()

	def toggle(self) -> None:
		self._toggle(self.room)

	def toggle_aero(self) -> None:
		self._toggle(self.aero)

	def close_instant(self) -> None:
		self.current.close_instant()

	def handle_input(self) -> None:
		self.current.handle_input()

	def render(self) -> None:
		self.current.render()
