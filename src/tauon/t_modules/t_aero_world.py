"""Easter egg module, the other one: the Aero world ("Touch Grass")

**GO OUTSIDE**

The About icon in Settings opens this one while the Candy Factory skin is on,
and the Dream Room (t_room) otherwise; `Dreams` holds both behind the one
switch Tauon calls. (Not to be confused with t_aero, the skin itself.)

Same trick as t_room (the live UI rides on a screen inside a hand-projected
3D scene), but this screen hangs over a still lake at night, looking across
the water to a city under the skin's own dusk sky.

Implementation notes:

* Reuses DreamRoom's camera, clipping and batching. Draw order is painter's:
  sky -> mirrored world -> water -> world -> screen -> foreground -> lens.
  Loose objects (boats, fireflies) are depth sorted each frame and split by
  the screen's plane.
* The lake is a planar mirror: the world is drawn a second time with y
  negated, then the water is laid over it as a translucent tint. Lights are
  reflected from a copy smeared downward and cut into bands that sway, so
  they shimmer like light on moving water.
* The sky, water, light ribbons and glows take their colours from the skin
  (t_aero) every frame, so they follow the playing album and Obsidian. The
  land and the city are painted once in neutral night tones and tinted
  toward it.
* All sprites are painted once with Pillow, the detailed ones at twice their
  size and then reduced. Their transparent pixels are given the colour of
  whatever is nearby, so plain alpha blending filters cleanly at the edges
  on every renderer.
"""
from __future__ import annotations

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
MOON_R = 15.0

# Sky gradient: height on the far plane, then the skin's hue key (1: its top
# hue, 2: its floor hue), saturation and lightness, and lightness under Obsidian
SKY_Z = -420.0
SKY = [
	(0.0, 2, 0.50, 0.27, 0.17), (34.0, 2, 0.58, 0.20, 0.13), (100.0, 1, 0.65, 0.12, 0.085),
	(240.0, 1, 0.70, 0.07, 0.05), (560.0, 1, 0.72, 0.04, 0.03),
]

# Water: distance ahead of the eye, how far from the deep colour toward the
# horizon's, alpha. Thin at grazing angles so the far lake is nearly a pure mirror.
WATER = [
	(-6.0, 0.0, 214), (1.0, 0.0, 208), (2.5, 0.05, 196), (4.5, 0.10, 178), (8.0, 0.18, 150), (14.0, 0.28, 120),
	(26.0, 0.40, 100), (50.0, 0.55, 84), (110.0, 0.75, 72), (1000.0, 1.0, 64),
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

# Wisps of cloud: azimuth and elevation in degrees, distance, half-width, texture, drift
CLOUDS = [
	(-50, 16, 380, 170, 0, 0.6), (-14, 27, 360, 150, 1, 0.9), (22, 12, 390, 190, 2, 0.5),
	(48, 22, 350, 140, 0, 0.8), (-34, 7, 395, 200, 1, 0.4), (8, 36, 330, 120, 2, 1.0),
]

# The far shore. Everything there is an upright flat standing on the water.
# The city: x0, x1, z; its height follows its texture's aspect.
CITY_W, CITY_H_PX = 4096, 720
CITY = (-330.0, 270.0, -240.0)
CITY_Y = (CITY[1] - CITY[0]) * CITY_H_PX / CITY_W
# Mountain ranges behind it: texture, x0, x1, height, z, palette key
RIDGES = [
	("ridge_far", -900.0, 900.0, 50.0, -385.0, "far"),
	("ridge_mid", -720.0, 720.0, 36.0, -330.0, "mid"),
]
# Low wooded shores either side, nearer: texture, x0, x1, height, z
SHORES = [("shore_l", -430.0, -150.0, 13.0, -175.0), ("shore_r", 190.0, 480.0, 9.0, -175.0)]

# Boats crossing the lake: z, x at T=0, speed, length
BOATS = [(-58.0, -30.0, 0.9, 3.6), (-118.0, 70.0, -0.6, 5.6), (-170.0, -160.0, 0.45, 7.0)]
BOAT_SPAN = (-230.0, 230.0)

# Window grids: cell size, and the pane inside each cell
WINDOWS = {
	"punched": ((8, 12), (2, 3, 5, 8)),
	"dense": ((6, 10), (1, 2, 4, 7)),
	"ribbon": ((5, 11), (0, 4, 4, 7)),
	"tall": ((10, 15), (2, 2, 7, 11)),
}

ADDITIVE = {"soft", "lights", "accent", "lights_streak", "accent_streak"}


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


def _flat(size: tuple[int, int], rgb) -> Image.Image:
	return Image.new("RGB", size, tuple(rgb))


def _layer(rgb, alpha: Image.Image) -> Image.Image:
	"""A solid colour with an L mask as its alpha."""
	im = Image.new("RGBA", alpha.size, (*rgb, 255))
	im.putalpha(alpha)
	return im


def _scale(mask: Image.Image, k: float) -> Image.Image:
	return mask.point(_lut(lambda f: f * k))


def _blur(im: Image.Image, r) -> Image.Image:
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


def _make_moon(rnd: random.Random) -> Image.Image:
	s = 256
	m = Image.new("L", (s, s), 0)
	ImageDraw.Draw(m).ellipse((8, 8, s - 8, s - 8), fill=255)
	maria = _fbm((s, s), rnd, (5, 5)).point(_lut(lambda f: 0.80 + 0.20 * _smooth(min(1.0, max(0.0, (f - 0.3) / 0.45)))))
	lum = ImageChops.multiply(maria, _radial(s, lambda r: 1.0 - 0.32 * r ** 3))
	im = Image.merge("RGB", [lum.point(_lut(lambda f, k=k: f * k)) for k in (0.93, 0.97, 1.0)]).convert("RGBA")
	im.putalpha(_blur(m, 1.2))
	return im.reduce(2)


def _make_wisp(rnd: random.Random) -> Image.Image:
	"""A thin band of cloud drawn out by the wind, its top edge silvered by the moon."""
	w, h = 1024, 192
	g = Image.linear_gradient("L")
	band = g.point(_lut(lambda f: math.exp(-((f - 0.55) / 0.2) ** 2))).resize((w, h))
	ends = g.transpose(Image.Transpose.ROTATE_90).point(_lut(lambda f: math.sin(math.pi * f) ** 0.8)).resize((w, h))
	n = _fbm((w, h), rnd, (6, 3), False, ((2, 0.45), (4, 0.30), (8, 0.18)))
	dens = ImageChops.multiply(n.point(_lut(lambda f: _smooth(min(1.0, max(0.0, (f - 0.36) / 0.42))))),
		ImageChops.multiply(band, ends))
	# Smear it sideways, as high wind does
	dens = dens.resize((w // 8, h), Image.BOX).resize((w, h), Image.BICUBIC)
	dens = _blur(dens, 1.5)
	rim = _blur(ImageChops.subtract(dens, ImageChops.offset(dens, 0, 6)), 2)
	col = Image.composite(_flat((w, h), (236, 240, 248)), _flat((w, h), (112, 120, 140)), _scale(rim, 2.2))
	im = col.convert("RGBA")
	im.putalpha(_scale(dens, 0.9))
	return im


def _ridge_profile(rnd: random.Random, n_pow: int, rough: float) -> list[float]:
	"""Midpoint displacement: a jagged 0..1 line of 2**n_pow + 1 points."""
	n = 2 ** n_pow
	pts = [0.0] * (n + 1)
	pts[0], pts[n] = rnd.random(), rnd.random()
	step, amp = n, 1.0
	while step > 1:
		half = step // 2
		for i in range(half, n, step):
			pts[i] = (pts[i - half] + pts[i + half]) / 2 + rnd.uniform(-amp, amp)
		amp *= rough
		step = half
	lo, hi = min(pts), max(pts)
	return [(p - lo) / (hi - lo) for p in pts]


def _make_ridge(rnd: random.Random, size: tuple[int, int], rough: float, floor: float, swell: float) -> Image.Image:
	"""A mountain range as a silhouette in greys, for tinting: its crests
	catch the moon. ``floor`` is the lowest the line goes (0..1 of the height)."""
	w, h = size
	ss = 2
	prof = _ridge_profile(rnd, 9, rough)
	n = len(prof) - 1
	p1, p2 = rnd.random(), rnd.random()
	vals = []
	for i, v in enumerate(prof):
		u = i / n
		# Group the peaks into massifs with a slow swell
		big = 0.5 + 0.3 * math.sin(TAU * (u * 1.3 + p1)) + 0.2 * math.sin(TAU * (u * 2.9 + p2))
		vals.append(v * (1.0 - swell + swell * big))
	top = max(vals)
	m = Image.new("L", (w * ss, h * ss), 0)
	pts = [(i * w * ss / n, h * ss * (1.0 - (floor + (1.0 - floor) * v / top))) for i, v in enumerate(vals)]
	ImageDraw.Draw(m).polygon([*pts, (w * ss, h * ss + 2), (0, h * ss + 2)], fill=255)
	m = m.reduce(ss)
	# Grey body, a little lighter up high, with faint gullies; a lit rim along the crests
	body = ImageChops.multiply(_vgrad((w, h), (214, 214, 214), (168, 168, 168)),
		Image.merge("RGB", [_fbm((w, h), rnd, (24, 3)).point(_lut(lambda f: 0.9 + 0.1 * f))] * 3))
	rim = _blur(ImageChops.subtract(m, ImageChops.offset(m, 0, 3)), 1.6)
	im = Image.composite(_flat((w, h), (255, 255, 255)), body, _scale(rim, 1.4)).convert("RGBA")
	im.putalpha(m)
	return im


def _make_shore(rnd: random.Random, size: tuple[int, int]) -> Image.Image:
	"""A low wooded shore: a gentle line roughened by treetops."""
	w, h = size
	ss = 2
	m = Image.new("L", (w * ss, h * ss), 0)
	d = ImageDraw.Draw(m)
	p1, p2 = rnd.random(), rnd.random()
	pts = []
	for i in range(0, w * ss + 8, 8):
		u = i / (w * ss)
		v = 0.45 + 0.2 * math.sin(TAU * (u * 1.4 + p1)) + 0.1 * math.sin(TAU * (u * 3.7 + p2))
		v *= _smooth(min(1.0, u / 0.15)) * _smooth(min(1.0, (1.0 - u) / 0.15))
		pts.append((i, h * ss * (1.0 - v * 0.8)))
	d.polygon([*pts, (w * ss, h * ss + 2), (0, h * ss + 2)], fill=255)
	for (x, y) in pts[::2]:	# treetops along the line
		if y < h * ss * 0.95:
			r = rnd.uniform(4, 11)
			d.ellipse((x - r, y - r * 1.3, x + r, y + r), fill=255)
	m = m.reduce(ss)
	im = _flat((w, h), (200, 200, 200)).convert("RGBA")
	im.putalpha(m)
	return im


def _window_grid(cell: tuple[int, int], pane: tuple[int, int, int, int], size=(256, 768)) -> Image.Image:
	"""L image of a facade's window grid: one pane in each cell."""
	cw, ch = cell
	tile = Image.new("L", cell, 0)
	ImageDraw.Draw(tile).rectangle(pane, fill=255)
	w, h = size
	row = Image.new("L", (w, ch), 0)
	for x in range(0, w, cw):
		row.paste(tile, (x, 0))
	out = Image.new("L", size, 0)
	for y in range(0, h, ch):
		out.paste(row, (0, y))
	return out


def _lit_cells(rnd: random.Random, cols: int, rows: int, density: float, cluster: tuple[int, int]) -> Image.Image:
	"""Which windows are lit, one pixel per window: offices light up in blocks."""
	r = Image.frombytes("L", (cols, rows), rnd.randbytes(cols * rows))
	cc, cr = -(-cols // cluster[0]), -(-rows // cluster[1])
	c = Image.frombytes("L", (cc, cr), rnd.randbytes(cc * cr)).resize(
		(cc * cluster[0], cr * cluster[1]), Image.NEAREST).crop((0, 0, cols, rows))
	thr = c.point(_lut(lambda f: density * (0.15 + 1.7 * f * f)))
	lit = ImageChops.subtract(thr, r).point(lambda v: 255 if v else 0)
	bright = Image.frombytes("L", (cols, rows), rnd.randbytes(cols * rows)).point(lambda v: 110 + v * 145 // 255)
	return ImageChops.multiply(lit, bright)


def _make_city(rnd: random.Random) -> tuple[Image.Image, Image.Image, Image.Image, list[tuple[float, float, float]]]:
	"""The far shore's skyline: two rows of towers in greys (tinted when
	drawn), their lit windows, the accent lights on their crowns, and where
	their aircraft warning lights are (u, v across the texture, blink phase;
	a negative phase is a steady light)."""
	W, H = CITY_W, CITY_H_PX
	body = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	lights = Image.new("RGBA", (W, H), (0, 0, 0, 0))
	accent = Image.new("L", (W, H), 0)
	bd, ld, ad = ImageDraw.Draw(body), ImageDraw.Draw(lights), ImageDraw.Draw(accent)
	grids = {k: (cell, _window_grid(cell, pane)) for k, (cell, pane) in WINDOWS.items()}
	kinds = ["punched"] * 7 + ["dense"] * 5 + ["ribbon"] * 5 + ["tall"] * 3
	lamps = [(255, 214, 150), (255, 230, 190), (210, 232, 255), (255, 196, 124), (236, 244, 255)]
	beacons: list[tuple[float, float, float]] = []
	base = H - 14	# the embankment's top

	def envelope(u: float) -> float:
		# Two downtowns, either side of where the screen hangs
		return 0.10 + 0.80 * math.exp(-((u - 0.72) / 0.10) ** 2) + 0.52 * math.exp(-((u - 0.16) / 0.07) ** 2)

	def windows(xa, ya, xb, yb, kind, density, lamp, dim, glass=True) -> None:
		(cw, ch), grid = grids[kind]
		cols = int((xb - xa - 6) // cw)
		rows = int((yb - ya - 4) // ch)
		if cols < 1 or rows < 1:
			return
		gw, gh = cols * cw, rows * ch
		ox, oy = int(xa + (xb - xa - gw) / 2), int(ya + 5)
		g = grid.crop((0, 0, gw, gh))
		box = (ox, oy, ox + gw, oy + gh)
		if glass:	# unlit panes, a shade off the facade
			body.paste((84, 92, 108, 255), box, _scale(g, 0.2))
		lit = _lit_cells(rnd, cols, rows, density, (8, 1) if kind == "ribbon" else (3, 2)).resize((gw, gh), Image.NEAREST)
		a = ImageChops.multiply(lit, g)
		if dim < 1.0:
			a = _scale(a, dim)
		lights.paste(Image.new("RGBA", (gw, gh), (*lamp, 255)), box, a)

	def tower(x0: float, bw: float, bh: float, back: bool) -> None:
		top = base - bh
		x1 = x0 + bw
		v = rnd.randint(-6, 6)
		c = (40 + v, 46 + v, 58 + v) if back else (24 + v, 28 + v, 36 + v)
		# A setback tower narrows as it rises: tiers, widest first
		tiers = [(x0, top, x1)]
		if bh > 250 and rnd.random() < 0.55:
			k = rnd.randint(1, 2)
			tiers = [(x0 + bw * 0.13 * i, top + bh * 0.2 * (k - i), x1 - bw * 0.13 * i) for i in range(k + 1)]
		if not back:	# hide what stands behind
			lights.paste((0, 0, 0, 0), (int(x0), int(top), int(x1) + 1, H))
			accent.paste(0, (int(x0), int(top), int(x1) + 1, H))
		kind = rnd.choice(kinds)
		lamp = rnd.choice(lamps)
		density = rnd.uniform(0.1, 0.42)
		dim = 0.7 if back else 1.0
		for i, (xa, ya, xb) in enumerate(tiers):
			# Lit from the upper left by the moon: a paler left face, a dark right edge
			bd.rectangle((xa, ya, xb, H), fill=(*c, 255))
			bd.rectangle((xa, ya, xa + (xb - xa) * 0.2, H), fill=(c[0] + 9, c[1] + 10, c[2] + 13, 255))
			bd.rectangle((xb - 3, ya, xb, H), fill=(c[0] - 8, c[1] - 8, c[2] - 8, 255))
			bd.line((xa, ya, xb, ya), fill=(c[0] + 22, c[1] + 26, c[2] + 32, 255), width=2)
			yb = tiers[i - 1][1] if i else base
			windows(xa, ya, xb, yb, kind, density, lamp, dim)
			windows(xa, ya, xb, yb, kind, density * 0.12, rnd.choice(lamps), dim, glass=False)
		xa, ya, xb = tiers[-1]
		cx = (xa + xb) / 2
		tw = xb - xa
		crown = rnd.random()
		if bh > 300 and crown < 0.3:	# spire
			h = bh * rnd.uniform(0.08, 0.16)
			bd.polygon([(cx - tw * 0.12, ya), (cx, ya - h), (cx + tw * 0.12, ya)], fill=(*c, 255))
			ad.line((cx, ya - h * 0.85, cx, ya), fill=120, width=2)
			beacons.append((cx / W, (ya - h) / H, rnd.uniform(0, 6)))
		elif bh > 200 and crown < 0.6:	# mast and plant room
			bd.rectangle((cx - tw * 0.25, ya - 12, cx + tw * 0.2, ya), fill=(*c, 255))
			h = rnd.uniform(30, 80)
			bd.line((cx, ya - 12, cx, ya - 12 - h), fill=(*c, 255), width=3)
			beacons.append((cx / W, (ya - 12 - h) / H, rnd.uniform(0, 6) if rnd.random() < 0.6 else -1.0))
		elif bh > 200 and crown < 0.8:	# a slanted top, lit along its edge
			h = tw * rnd.uniform(0.2, 0.5)
			pts = [(xa, ya), (xb, ya - h), (xb, ya)] if rnd.random() < 0.5 else [(xa, ya - h), (xb, ya), (xa, ya)]
			bd.polygon(pts, fill=(*c, 255))
			ad.line((pts[0], pts[1]), fill=210, width=3)
		elif bh > 120:
			bd.rectangle((cx - tw * 0.3, ya - 8, cx + tw * 0.1, ya), fill=(*c, 255))
		# Some of the tall ones are lit up: a crown band, or their corners
		if bh > 280 and rnd.random() < 0.55:
			if rnd.random() < 0.6:
				ad.rectangle((xa + 2, ya + 4, xb - 2, ya + 8), fill=230)
				ad.rectangle((xa + 2, ya + 14, xb - 2, ya + 16), fill=150)
			else:
				for xx in (xa + 1, xb - 2):
					ad.line((xx, ya, xx, ya + bh * 0.35), fill=170, width=2)

	for back in (True, False):
		x = rnd.uniform(-30.0, 0.0)
		while x < W:
			bw = rnd.uniform(44, 120) if back else rnd.uniform(56, 150)
			e = envelope((x + bw / 2) / W) * (1.0 if back else 0.55)
			bh = (base - 40) * e * rnd.uniform(0.5, 1.0) + rnd.uniform(16, 44)
			tower(x, bw, bh, back)
			x += bw + (rnd.uniform(-bw * 0.35, 4.0) if back else rnd.uniform(0.0, 10.0))

	# The embankment, and the promenade's lamps along it
	bd.rectangle((0, base, W, H), fill=(14, 16, 20, 255))
	lights.paste((0, 0, 0, 0), (0, base, W, H))
	accent.paste(0, (0, base, W, H))
	x = rnd.uniform(0, 20)
	while x < W:
		ld.ellipse((x - 2, base - 6, x + 2, base - 2), fill=(255, 206, 140, 255))
		x += rnd.uniform(22, 30)

	body = body.reduce(2)
	lights = lights.reduce(2)
	accent = _layer((255, 255, 255), accent.reduce(2))
	out = []
	for im in (lights, accent):	# a soft halo around each light
		glow = im.convert("RGBa").filter(ImageFilter.GaussianBlur(2.5)).convert("RGBA")
		glow.putalpha(_scale(glow.getchannel("A"), 0.7))
		glow.alpha_composite(im)
		out.append(glow)
	return body, out[0], out[1], beacons


def _streak(im: Image.Image, boost: float) -> Image.Image:
	"""Lights as rippled water reflects them: drawn out vertically into streaks."""
	w, h = im.size
	s = im.convert("RGBa").resize((w // 2, h // 2), Image.BOX).filter(ImageFilter.GaussianBlur((0.8, 12))).convert("RGBA")
	s.putalpha(s.getchannel("A").point(_lut(lambda f: min(1.0, f * boost))))
	return s


def _make_boat() -> Image.Image:
	"""A small motor cruiser side on, bow to the right, cabin lights on."""
	w, h = 384, 144
	im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
	d = ImageDraw.Draw(im)
	hull = (16, 18, 24, 255)
	d.polygon([(10, 92), (w - 8, 86), (w - 40, 118), (30, 120)], fill=hull)
	d.polygon([(110, 92), (130, 58), (270, 56), (300, 88)], fill=(22, 24, 32, 255))
	d.rectangle((150, 30, 230, 58), fill=(20, 22, 30, 255))
	d.line((190, 30, 190, 4), fill=hull, width=4)
	for x in range(142, 286, 22):	# cabin windows
		d.rectangle((x, 66, x + 14, 78), fill=(255, 214, 150, 255))
	d.line((30, 100, w - 30, 96), fill=(46, 52, 64, 255), width=3)	# sheer line, catching the moon
	return im.reduce(2)


def _make_vignette() -> Image.Image:
	a = _radial(256, lambda r: 0.62 * _smooth(min(1.0, max(0.0, (r - 0.45) / 0.95))))
	return _layer((0, 0, 0), a)


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


def build_images(seed: int = 2007) -> tuple[dict[str, Image.Image], list[tuple[float, float, float]]]:
	"""Paint every sprite. Pure Pillow, no renderer needed. Also returns the
	city's aircraft warning lights."""
	rnd = random.Random(seed)
	out: dict[str, Image.Image] = {
		"soft": _layer((255, 255, 255), _radial(128, lambda r: max(0.0, 1.0 - r) ** 2.0)),
		"moon": _make_moon(rnd),
		"boat": _make_boat(),
		"vignette": _make_vignette(),
	}
	out["city"], out["lights"], out["accent"], beacons = _make_city(rnd)
	out["lights_streak"] = _streak(out["lights"], 3.0)
	out["accent_streak"] = _streak(out["accent"], 2.5)
	# The towers' reflection: soft, as rippled water gives it back
	out["city_reflect"] = out["city"].convert("RGBa").filter(ImageFilter.GaussianBlur((1.5, 6))).convert("RGBA")
	out["ridge_far"] = _make_ridge(rnd, (2048, 160), 0.56, 0.25, 0.6)
	out["ridge_mid"] = _make_ridge(rnd, (2048, 128), 0.52, 0.15, 0.7)
	out["shore_l"] = _make_shore(rnd, (1024, 64))
	out["shore_r"] = _make_shore(rnd, (1024, 64))
	for i in range(3):
		out[f"wisp{i}"] = _make_wisp(rnd)
	return out, beacons


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
		self.beacons: list[tuple[float, float, float]] = []
		self._mirror = False
		self._fade = 1.0		# alpha scale for whatever is being drawn
		self._front = 0.0		# fade for things nearer than the screen (0 at t=0)
		self._e = 0.0
		self._w = 1
		self._h = 1
		self._scr_w = 1.0
		self._flare_vis = 0.0
		self._fb = ((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (0.0, 1.0, 0.0), (0.0, 0.0, -1.0), 1.0)
		self.pal: dict = {}

		rnd = random.Random(1999)
		u = rnd.uniform

		# Clouds: [x, y, z, half-width, texture, drift]
		self.clouds = []
		for (az, el, dist, hw, k, sp) in CLOUDS:
			a = math.radians(az)
			self.clouds.append([dist * math.sin(a), dist * math.tan(math.radians(el)), -dist * math.cos(a), hw, f"wisp{k}", sp])
		self.clouds.sort(key=lambda c: c[2])

		# Stars on the far plane, thinning toward the horizon: x, y, size, phase, twinkle, warm
		self.stars = [(u(-900.0, 900.0), 25.0 + 535.0 * rnd.random() ** 1.4, u(1.0, 2.8), u(0, 9), u(0.4, 1.8),
			rnd.random() < 0.2) for i in range(280)]
		# Fireflies along the near shore: [x, y, z, phase, size]
		self.motes = [[u(-2.5, 4.5), u(0.2, 3.0), u(-2.0, 4.0), u(0, 9), u(0.008, 0.022)] for i in range(24)]
		self.motes += [[u(-6.0, 7.0), u(0.15, 3.2), u(-9.0, 3.5), u(0, 9), u(0.008, 0.024)] for i in range(64)]
		# Moonlight glinting on the water: distance, lateral, phase, speed, size
		self.glitter = [(3.0 * 60.0 ** rnd.random(), u(-1, 1), u(0, 9), u(1.5, 5.0), u(0.5, 1.5)) for i in range(64)]
		self.sparkles = [(u(-26.0, 26.0), u(-60.0, 3.0), u(0, 9), u(0.8, 2.6)) for i in range(30)]
		# Reeds framing the settled shot: screen x (-1..1), distance, height, lean, phase, width
		self.blades = []
		for side in (-1, 1):
			for i in range(8):
				f = rnd.random()
				self.blades.append((
					side * (1.02 - 0.36 * f * f), u(0.95, 1.5), u(0.14, 0.32) + 0.3 * (1 - f) * rnd.random(),
					-side * u(0.04, 0.26), u(0, 9), u(0.009, 0.016)))
		self.blades.sort(key=lambda b: -b[1])

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
		images, self.beacons = build_images()
		for name, im in images.items():
			self.tex[name] = self._upload(im, name in ADDITIVE)

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

	def _flat_strip(self, x0, x1, y_top, z, tex, n, col=(255, 255, 255), additive=False) -> None:
		"""A textured upright flat standing on the water, cut into columns so
		the affine texture mapping stays straight."""
		q = self._quad
		cols = [(*col, 255)] * 4
		for i in range(n):
			f0, f1 = i / n, (i + 1) / n
			xa, xb = x0 + (x1 - x0) * f0, x0 + (x1 - x0) * f1
			q([(xa, y_top, z), (xb, y_top, z), (xb, 0.0, z), (xa, 0.0, z)], cols,
				uvs=[(f0, 0.0), (f1, 0.0), (f1, 1.0), (f0, 1.0)], texture=tex, additive=additive)

	def _shimmer_strip(self, x0, x1, y_top, z, tex, col, T, bands=18, n=6, additive=True) -> None:
		"""A flat as the lake reflects it (mirror pass): cut into bands that
		sway sideways, more the further they reach from the shore, like light
		on moving water."""
		q = self._quad
		cols = [(*col, 255)] * 4
		span = x1 - x0
		for b in range(bands):
			v0, v1 = b / bands, (b + 1) / bands
			ya, yb = y_top * (1.0 - v0), y_top * (1.0 - v1)
			reach = 1.0 - (v0 + v1) / 2
			dx = (0.2 + 1.6 * reach) * (math.sin(T * 0.9 + b * 1.7) + 0.5 * math.sin(T * 2.3 + b * 3.1))
			for i in range(n):
				f0, f1 = i / n, (i + 1) / n
				xa, xb = x0 + span * f0 + dx, x0 + span * f1 + dx
				q([(xa, ya, z), (xb, ya, z), (xb, yb, z), (xa, yb, z)], cols,
					uvs=[(f0, v0), (f1, v0), (f1, v1), (f0, v1)], texture=tex, additive=additive)

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
		p["lamp"] = _mix((255, 255, 255), glow, 0.15)
		p["haze"] = _mix((255, 196, 140), glow, 0.35)	# the city's light, on its own haze
		# The land in the sky's own hue: far ranges just darker than the
		# horizon behind them, nearer ones darker still
		p["far"] = _mix(deep, horizon, 0.3)
		p["mid"] = _mix(deep, horizon, 0.1)
		p["near"] = _mix(deep, (0, 0, 0), 0.4)
		p["city"] = _mix((255, 255, 255), tone(cool, 0.45, 0.75), 0.35)
		p["cloud"] = _mix((255, 255, 255), tone(cool, 0.5, 0.7), 0.45)

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
		warm = (255, 236, 214)
		for (x, y, s, ph, sp, w) in self.stars:
			a = 255.0 * (0.7 + 0.3 * math.sin(T * sp + ph)) * min(1.0, y / 140.0)
			self._spr((x, y, SKY_Z + 6.0), s, s, soft, warm if w else ice, a, add=True)

		self._spr(MOON, 220.0, 220.0, soft, pal["glow"], 24, add=True)
		self._spr(MOON, 70.0, 70.0, soft, ice, 54, add=True)
		self._spr(MOON, MOON_R * 1.8, MOON_R * 1.8, soft, (255, 255, 255), 90, add=True)
		self._spr(MOON, MOON_R, MOON_R, tex["moon"], (255, 255, 255), 255)
		if not mirror:
			self._aurora(T)

		cloud = pal["cloud"]
		for (x, y, z, hw, key, sp) in self.clouds:
			self._spr((x, y, z), hw, hw * 0.1875, tex[key], cloud, 170)

		if not mirror:
			# An airliner, very high up, crossing every so often
			k = (T / 80.0) % 1.0
			p = (-640.0 + 1280.0 * k, 132.0 + 36.0 * k, -372.0)
			self._spr(p, 1.0, 1.0, soft, (255, 255, 255), 150)
			self._spr(p, 1.6, 1.6, soft, (255, 60, 50), 140 * (0.5 + 0.5 * math.sin(T * 3.0)), add=True)
			self._spr(p, 3.2, 3.2, soft, (255, 255, 255), 255 * max(0.0, math.sin(T * 4.6)) ** 40, add=True)

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
		pal = self.pal
		mirror = self._mirror
		n = 6 if mirror else 10

		for (key, x0, x1, ht, z, colour) in RIDGES:
			g(x0, x1, ht, z, tex[key], 8, col=pal[colour])

		# The city's glow on the haze above it
		x0, x1, z = CITY
		haze = pal["haze"]
		hz = z - 6.0
		q([(x0 - 60.0, 70.0, hz), (x1 + 60.0, 70.0, hz), (x1 + 60.0, 0.0, hz), (x0 - 60.0, 0.0, hz)],
			[(*haze, 0), (*haze, 0), (*haze, 40), (*haze, 40)], additive=True)

		if mirror:
			self._shimmer_strip(x0, x1, CITY_Y, z, tex["city_reflect"], pal["city"], T, additive=False)
			self._shimmer_strip(x0, x1, CITY_Y, z + 0.5, tex["lights_streak"], pal["lamp"], T)
			self._shimmer_strip(x0, x1, CITY_Y, z + 0.5, tex["accent_streak"], pal["glow"], T)
		else:
			g(x0, x1, CITY_Y, z, tex["city"], n, col=pal["city"])
			g(x0, x1, CITY_Y, z + 0.5, tex["lights"], n, col=pal["lamp"], additive=True)
			g(x0, x1, CITY_Y, z + 0.5, tex["accent"], n, col=pal["glow"], additive=True)
		soft = tex["soft"]
		for (bu, bv, ph) in self.beacons:
			a = 1.0 if ph < 0 else max(0.0, math.sin(T * 1.4 + ph)) ** 4
			if a > 0.02:
				p = (x0 + (x1 - x0) * bu, CITY_Y * (1.0 - bv), z + 1.0)
				self._spr(p, 0.9, 0.9, soft, (255, 70, 56), 255.0 * a, add=True)
				self._spr(p, 3.0, 3.0, soft, (255, 50, 40), 60.0 * a, add=True)

		for (key, x0, x1, ht, z) in SHORES:
			g(x0, x1, ht, z, tex[key], 4, col=pal["near"])

		if not mirror:
			# Mist along the far shore softens the horizon
			mist = pal["mist"]
			for (ya, yb) in ((0.0, 7.0), (0.0, -3.0)):
				q([(-900.0, yb, -232.0), (900.0, yb, -232.0), (900.0, ya, -232.0), (-900.0, ya, -232.0)],
					[(*mist, 0), (*mist, 0), (*mist, 44), (*mist, 44)])

	# ------------------------------------------------------------------ water

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
			a = 170.0 * tw * tw
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
				self._spr((x, 0.02, z), s * 2.2, s * 0.5, soft, ice, 170 * (tw - 0.55) * 2.2, add=True)

		self._glow((SCR_CX, 0.008, SCR_Z + 0.1), self._scr_w * 0.9, 1.3, pal["glow"], 42.0 * self._e, axis="y")

	# --------------------------------------------------------- loose objects

	def _collect(self, T: float) -> list[tuple]:
		"""Everything adrift near the screen, sorted far to near:
		(view depth, world z, draw function, args)."""
		items: list[tuple] = []
		ex, ey, ez = self._eye
		fx, fy, fz = self._fwd
		sin = math.sin

		def put(p, fn, *args) -> None:
			items.append(((p[0] - ex) * fx + (p[1] - ey) * fy + (p[2] - ez) * fz, p[2], fn, args))

		lo, hi = BOAT_SPAN
		for (z, x0, sp, ln) in BOATS:
			x = lo + (x0 - lo + sp * T) % (hi - lo)
			put((x, 0.0, z), self._boat, x, z, ln, 1 if sp > 0 else -1, T)

		# Fireflies, glowing in and out: warm yellow-green, nudged toward the accent
		glow = _mix((200, 255, 96), self.pal["glow"], 0.15)
		for (x, y, z, ph, s) in self.motes:
			a = max(0.0, sin(T * 0.9 + ph)) ** 1.5
			if a > 0.01:
				put((x, y, z), self._firefly, (x, y, z), s, glow, a)

		items.sort(key=lambda it: -it[0])
		return items

	def _boat(self, x, z, ln, dirn, T) -> None:
		"""A boat under way: its hull and cabin lights, its navigation lights
		(and their long reflections), and a faint wake."""
		tex = self.tex
		hw = ln * 0.5
		hh = hw * 72 / 192
		bob = 0.03 * math.sin(T * 1.3 + z)
		self._spr((x, hh * 0.62 + bob, z), hw, hh, tex["boat"], (255, 255, 255), 255.0, 0.0, False, dirn < 0)
		soft = tex["soft"]
		mirror = self._mirror
		# Masthead (white), and the side light toward us: green to starboard
		stretch = 4.0 if mirror else 1.0
		mast = (x - dirn * hw * 0.01, hh * 1.92 + bob, z)
		side = (x + dirn * hw * 0.55, hh * 0.85 + bob, z)
		self._spr(mast, 0.34, 0.34 * stretch, soft, (255, 250, 236), 255.0, add=True)
		self._spr(side, 0.3, 0.3 * stretch, soft, (60, 255, 110) if dirn < 0 else (255, 60, 50), 255.0, add=True)
		self._spr((x, hh * 0.9 + bob, z), hw * 0.7, hh * 0.6 * stretch, soft, (255, 196, 120), 60.0, add=True)
		if mirror:
			return
		# Wake: two lines fanning out behind the stern
		q = self._quad
		ice = self.pal["ice"]
		sx = x - dirn * hw * 0.9
		for side_z in (-1.0, 1.0):
			for k in range(3):
				f0, f1 = k / 3, (k + 1) / 3
				xa, xb = sx - dirn * ln * 2.5 * f0, sx - dirn * ln * 2.5 * f1
				za, zb = z + side_z * ln * 0.35 * f0, z + side_z * ln * 0.35 * f1
				w = 0.05 * ln
				q([(xa, 0.01, za - w), (xb, 0.01, zb - w), (xb, 0.01, zb + w), (xa, 0.01, za + w)],
					[(*ice, 70 * (1 - f0)), (*ice, 70 * (1 - f1)), (*ice, 70 * (1 - f1)), (*ice, 70 * (1 - f0))], additive=True)

	def _firefly(self, p, s, col, a) -> None:
		soft = self.tex["soft"]
		self._spr(p, s * 7.0, s * 7.0, soft, col, 120.0 * a, add=True)
		self._spr(p, s * 1.4, s * 1.4, soft, _mix(col, (255, 255, 255), 0.6), 255.0 * a, add=True)

	# ----------------------------------------------------------------- screen

	def _panel(self) -> None:
		q = self._quad
		mirror = self._mirror
		sw = self._scr_w
		sx0, sx1 = SCR_CX - sw / 2, SCR_CX + sw / 2
		sy0, sy1 = SCR_CY - SCR_H / 2, SCR_CY + SCR_H / 2
		z = SCR_Z
		if not mirror:
			self._glow((SCR_CX, SCR_CY, z - 0.05), sw * 0.9, SCR_H * 1.05, self.pal["glow"], 48)
		# No frame of its own: the app window floats as it is
		if mirror:
			self._draw_app(sx0, sx1, sy0, sy1, z, 5, 3)
			return
		self._draw_app(sx0, sx1, sy0, sy1, z)
		a = 16.0 * self._front
		q([(sx0, sy1, z), (sx0 + sw * 0.56, sy1, z), (sx0 + sw * 0.30, sy0, z), (sx0, sy0, z)],
			[(255, 255, 255, a), (255, 255, 255, a * 0.4), (255, 255, 255, 0), (255, 255, 255, a * 0.5)], additive=True)

	# ------------------------------------------------------------- foreground

	def _foreground(self, T: float) -> None:
		f = self._front
		if f <= 0.01:
			return
		q = self._quad
		rx, ry, rz = self._right
		self._fade = f
		a = 255.0 * f
		tanh = math.tan(FOV / 2)
		fr = self._fb[1]
		for (xn, d, hn, lean, ph, wd) in self.blades:
			bx, by, bz = self._fview(xn, -1.0, d)
			ht = max(0.2, by + hn * tanh * d * 2.0)
			sway = math.sin(T * 0.9 + ph) * 0.03 + math.sin(T * 2.1 + ph * 2.0) * 0.01
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
				c = _mix((2, 8, 12), (14, 34, 40), s)
				cl = (min(255, c[0] + 14), min(255, c[1] + 22), min(255, c[2] + 30), a)
				cr = (*c, a)
				left = (px - rx * w, py, pz - rz * w)
				right = (px + rx * w, py, pz + rz * w)
				if pl is not None:
					q([pl, left, right, pr], [pcl, cl, cr, pcr])
				pl, pr, pcl, pcr = left, right, cl, cr
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
		if v > 0.01 and pr is not None:
			# A faint anamorphic streak through the moon
			self._fade = v
			soft = tex["soft"]
			s2(sx, sy, h * 0.8, h * 0.006, soft, pal["ice"], 90, add=True)
			s2(sx, sy, h * 0.3, h * 0.3, soft, pal["glow"], 14, add=True)
		self._fade = f
		if f > 0.01:
			s2(w * 0.5, h * 0.5, w * 0.5, h * 0.5, tex["vignette"], (255, 255, 255), 255.0)
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

		# Camera: straight back out of the screen, lifting a little, then
		# settling low over the water off to one side.
		d0 = (SCR_H / 2) / math.tan(FOV / 2)
		eye = (
			_lerp(SCR_CX, END_EYE[0], e) + math.sin(T * 0.23) * 0.08 * e,
			_lerp(SCR_CY, END_EYE[1], e) + 0.3 * math.sin(math.pi * e) + math.sin(T * 0.19 + 1.7) * 0.03 * e,
			_lerp(SCR_Z + d0, END_EYE[2], e) + math.sin(T * 0.15 + 0.6) * 0.06 * e,
		)
		tgt = (
			_lerp(SCR_CX, END_TGT[0], e) + math.sin(T * 0.17 + 4.0) * 0.02 * e,
			_lerp(SCR_CY, END_TGT[1], e) + math.sin(T * 0.21 + 2.2) * 0.015 * e,
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
