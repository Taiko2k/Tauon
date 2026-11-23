# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Aqua: an optional glass-and-gel skin in the Frutiger Aero style.

Everything here draws on top of Tauon's normal UI. t_main and t_custom call in
at a handful of points while prefs.aero is on, and otherwise nothing in this
module runs.

The look is the dusk variant of the Aqua concept:

- a sky painted from the playing album's colours, at a fifth of the window's
  logical size so that scaling it up does the blurring, with drifting light
  ribbons, blooms and bokeh;
- glass panels floating over it, frosted by sampling a pre-blurred copy of
  that sky at the panel's own position (no live blur), then tinted, given a
  sheen over their top and one-pixel rims;
- gel controls (orbs, tubes, rows) lit in the album's accent hue.

Dark, colourless covers get the Obsidian variant instead: a graphite sky,
smoked glass, black lacquer orbs and mercury gel, with one accent hue taken
from the cover's small bright highlights. `Aero.mono` eases between the two
(0 is dusk, 1 Obsidian), so every colour below is a blend of both.

Shapes with gradients are built as meshes: a rounded-rect outline cut into
convex cells along every gradient stop, so vertex colour interpolation
reproduces the gradient exactly. Rings, orbs and other radial pieces are
rasterised once per size with Pillow and cached.
"""

from __future__ import annotations

import colorsys
import logging
import math
import random
import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from tauon.t_modules import t_native as sdl3
from tauon.t_modules.t_enums import GuiMode, PlayingState
from tauon.t_modules.t_extra import ColourRGBA

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

# Colour tuples are straight-alpha floats, 0-1
RGBA = tuple[float, float, float, float]


def hsl(h: float, s: float, l: float, a: float = 1.0) -> RGBA:
	"""CSS hsl(): hue in degrees, saturation and lightness 0-1."""
	r, g, b = colorsys.hls_to_rgb((h % 360) / 360, l, s)
	return (r, g, b, a)


def rgba8(r: int, g: int, b: int, a: float = 1.0) -> RGBA:
	return (r / 255, g / 255, b / 255, a)


def to_colour(c: RGBA) -> ColourRGBA:
	return ColourRGBA(round(c[0] * 255), round(c[1] * 255), round(c[2] * 255), round(c[3] * 255))


def _lerp(a: float, b: float, t: float) -> float:
	return a + (b - a) * t


def mix(a: RGBA, b: RGBA, t: float) -> RGBA:
	if t <= 0:
		return a
	if t >= 1:
		return b
	return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t,
		a[2] + (b[2] - a[2]) * t, a[3] + (b[3] - a[3]) * t)


def _hue_lerp(a: float, b: float, t: float) -> float:
	return (a + (((b - a + 540) % 360) - 180) * t) % 360


def _stop_at(stops: list[tuple[float, RGBA]], t: float) -> RGBA:
	"""Colour of a CSS gradient at t, interpolated premultiplied like CSS."""
	if t <= stops[0][0]:
		return stops[0][1]
	if t >= stops[-1][0]:
		return stops[-1][1]
	for (p0, c0), (p1, c1) in zip(stops, stops[1:]):
		if p0 <= t <= p1:
			k = 0.0 if p1 <= p0 else (t - p0) / (p1 - p0)
			a = _lerp(c0[3], c1[3], k)
			if a <= 0:
				return (c0[0], c0[1], c0[2], 0.0)
			r = _lerp(c0[0] * c0[3], c1[0] * c1[3], k) / a
			g = _lerp(c0[1] * c0[3], c1[1] * c1[3], k) / a
			b = _lerp(c0[2] * c0[3], c1[2] * c1[3], k) / a
			return (r, g, b, a)
	return stops[-1][1]


def _bezier(x1: float, y1: float, x2: float, y2: float, t: float) -> float:
	"""CSS cubic-bezier timing function, solved for x = t."""
	if t <= 0:
		return 0.0
	if t >= 1:
		return 1.0
	lo, hi = 0.0, 1.0
	u = t
	for _ in range(24):
		u = (lo + hi) / 2
		x = 3 * (1 - u) ** 2 * u * x1 + 3 * (1 - u) * u * u * x2 + u ** 3
		if x < t:
			lo = u
		else:
			hi = u
	return 3 * (1 - u) ** 2 * u * y1 + 3 * (1 - u) * u * u * y2 + u ** 3


# -- convex mesh helpers -------------------------------------------------------

def rounded_poly(x: float, y: float, w: float, h: float,
		radii: tuple[float, float, float, float], seg: int | None = None) -> list[tuple[float, float]]:
	"""Outline of a rounded rect, clockwise from the top-left. radii is
	(top-left, top-right, bottom-right, bottom-left); each corner may also be
	an (rx, ry) pair for an elliptical corner. `seg` fixes the segments per
	corner."""
	pts: list[tuple[float, float]] = []
	corners = (
		(x, y, 180, 270, 1, 1),            # top-left: centre is +r,+r from corner
		(x + w, y, 270, 360, -1, 1),
		(x + w, y + h, 0, 90, -1, -1),
		(x, y + h, 90, 180, 1, -1),
	)
	for (cx, cy, a0, a1, sx, sy), rad in zip(corners, radii):
		rx, ry = rad if isinstance(rad, tuple) else (rad, rad)
		rx = max(0.0, min(rx, w / 2))
		ry = max(0.0, min(ry, h / 2))
		if rx < 0.5 or ry < 0.5:
			pts.append((cx, cy))
			continue
		ox, oy = cx + sx * rx, cy + sy * ry
		# Enough segments that a small cap (a 7px tube end) reads as round
		n = seg or max(6, min(16, round(max(rx, ry) / 1.2)))
		for i in range(n + 1):
			ang = math.radians(a0 + (a1 - a0) * i / n)
			pts.append((ox + math.cos(ang) * rx, oy + math.sin(ang) * ry))
	return pts


def split_poly(poly: list[tuple[float, float]], a: float, b: float, c: float) -> tuple[list, list]:
	"""Split a convex polygon by the line a*x + b*y = c into (below, above)."""
	lo: list[tuple[float, float]] = []
	hi: list[tuple[float, float]] = []
	n = len(poly)
	for i in range(n):
		p = poly[i]
		q = poly[(i + 1) % n]
		dp = a * p[0] + b * p[1] - c
		dq = a * q[0] + b * q[1] - c
		if dp <= 0:
			lo.append(p)
		if dp >= 0:
			hi.append(p)
		if (dp < 0 < dq) or (dq < 0 < dp):
			t = dp / (dp - dq)
			m = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
			lo.append(m)
			hi.append(m)
	return (lo if len(lo) >= 3 else []), (hi if len(hi) >= 3 else [])


def cut_polys(polys: list[list], cuts: list[tuple[float, float, float]]) -> list[list]:
	for a, b, c in cuts:
		out = []
		for poly in polys:
			lo, hi = split_poly(poly, a, b, c)
			if lo:
				out.append(lo)
			if hi:
				out.append(hi)
		polys = out
	return polys


class Gradient:
	"""A CSS linear gradient over a box, as a colour function plus the lines
	its stops fall on (so a mesh can be cut there and stay exact)."""

	def __init__(self, box: tuple[float, float, float, float], angle: float,
			stops: list[tuple[float, RGBA]]) -> None:
		x, y, w, h = box
		rad = math.radians(angle)
		self.dx = math.sin(rad)
		self.dy = -math.cos(rad)
		length = abs(w * self.dx) + abs(h * self.dy)
		self.length = max(1e-6, length)
		cx, cy = x + w / 2, y + h / 2
		self.sx = cx - self.dx * length / 2
		self.sy = cy - self.dy * length / 2
		self.stops = stops

	def t(self, px: float, py: float) -> float:
		return ((px - self.sx) * self.dx + (py - self.sy) * self.dy) / self.length

	def __call__(self, px: float, py: float) -> RGBA:
		return _stop_at(self.stops, self.t(px, py))

	def cuts(self) -> list[tuple[float, float, float]]:
		out = []
		for p, _c in self.stops:
			# t = p  <=>  dx*x + dy*y = p*L + dx*sx + dy*sy
			out.append((self.dx, self.dy, p * self.length + self.dx * self.sx + self.dy * self.sy))
		return out


def vgrad(y: float, h: float, stops: list[tuple[float, RGBA]], x: float = 0.0, w: float = 1.0) -> Gradient:
	return Gradient((x, y, w, h), 180, stops)


# -- small raster helpers --------------------------------------------------------

_RADIAL_TEMPLATE: Image.Image | None = None


def _radial_l(size: tuple[int, int], cx: float, cy: float, rx: float, ry: float) -> Image.Image:
	"""'L' image of the normalised distance from (cx, cy): 0 at the centre,
	255 at the (rx, ry) ellipse and beyond."""
	global _RADIAL_TEMPLATE
	if _RADIAL_TEMPLATE is None:
		# Pillow's template reaches 255 at the corners (about 180 on the
		# inscribed circle); stretch it so the circle itself is 255
		_RADIAL_TEMPLATE = Image.radial_gradient("L").point(
			lambda v: min(255, round(v * 255 / 180.3)))
	out = Image.new("L", size, 255)
	bw, bh = max(1, round(rx * 2)), max(1, round(ry * 2))
	tpl = _RADIAL_TEMPLATE.resize((bw, bh), Image.Resampling.BILINEAR)
	out.paste(tpl, (round(cx - rx), round(cy - ry)))
	return out


def _map_stops(t_img: Image.Image, stops: list[tuple[float, RGBA]]) -> Image.Image:
	"""Colourise an 'L' parameter image through gradient stops."""
	luts = ([], [], [], [])
	for v in range(256):
		c = _stop_at(stops, v / 255)
		for i in range(4):
			luts[i].append(max(0, min(255, round(c[i] * 255))))
	return Image.merge("RGBA", [t_img.point(l) for l in luts])


def _stroke_outline(pts: list[tuple[float, float]], half: float) -> list[tuple[float, float]]:
	"""Outline of a polyline stroked `half` either side of it."""
	left: list[tuple[float, float]] = []
	right: list[tuple[float, float]] = []
	n = len(pts)
	for i in range(n):
		x0, y0 = pts[max(0, i - 1)]
		x1, y1 = pts[min(n - 1, i + 1)]
		dx, dy = x1 - x0, y1 - y0
		ln = math.hypot(dx, dy) or 1.0
		nx, ny = -dy / ln * half, dx / ln * half
		px, py = pts[i]
		left.append((px + nx, py + ny))
		right.append((px - nx, py - ny))
	return left + right[::-1]


_LUTS: dict[int, list[int]] = {}


def _lut(k: float) -> list[int]:
	"""A 256-entry table scaling a channel by k (for Image.point), cached
	at 1/1024 steps."""
	q = max(0, round(k * 1024))
	table = _LUTS.get(q)
	if table is None:
		k = q / 1024
		table = [min(255, round(v * k)) for v in range(256)]
		if len(_LUTS) > 4096:
			_LUTS.clear()
		_LUTS[q] = table
	return table


def _solid(size: tuple[int, int], c: RGBA, alpha: Image.Image) -> Image.Image:
	"""Colour c with alpha taken from an 'L' mask (scaled by c's own alpha)."""
	img = Image.new("RGBA", size, (round(c[0] * 255), round(c[1] * 255), round(c[2] * 255), 0))
	a = alpha.point(lambda v, k=c[3]: round(v * k))
	img.putalpha(a)
	return img


def _ellipse_mask(size: tuple[int, int], box: tuple[float, float, float, float], ss: int = 4) -> Image.Image:
	w, h = size
	big = Image.new("L", (w * ss, h * ss), 0)
	x0, y0, x1, y1 = box
	ImageDraw.Draw(big).ellipse([x0 * ss, y0 * ss, x1 * ss - 1, y1 * ss - 1], fill=255)
	return big.reduce(ss)


def _rr_mask(size: tuple[int, int], box: tuple[float, float, float, float], r: float, ss: int = 4) -> Image.Image:
	w, h = size
	big = Image.new("L", (w * ss, h * ss), 0)
	x0, y0, x1, y1 = box
	r = max(0.0, min(r, (x1 - x0) / 2, (y1 - y0) / 2))
	ImageDraw.Draw(big).rounded_rectangle(
		[x0 * ss, y0 * ss, x1 * ss - 1, y1 * ss - 1], radius=r * ss, fill=255)
	return big.reduce(ss)


def _shift(mask: Image.Image, dx: int, dy: int, fill: int = 0) -> Image.Image:
	out = Image.new("L", mask.size, fill)
	out.paste(mask, (dx, dy))
	return out


def _inset_shadow(mask: Image.Image, dx: float, dy: float, sigma: float) -> Image.Image:
	"""Coverage of a CSS inset box-shadow inside `mask`."""
	hole = _shift(mask, round(dx), round(dy))
	outside = ImageChops.invert(hole)
	if sigma > 0:
		outside = outside.filter(ImageFilter.GaussianBlur(sigma))
	return ImageChops.multiply(outside, mask)


def _outer_shadow(mask: Image.Image, dx: float, dy: float, sigma: float) -> Image.Image:
	sh = _shift(mask, round(dx), round(dy))
	if sigma > 0:
		sh = sh.filter(ImageFilter.GaussianBlur(sigma))
	return sh


def _mod(tex, r: int, g: int, b: int, a: int) -> None:
	"""Set a texture's colour and alpha mod. Never leaves both at their
	identity: SDL's software renderer takes a fast path for unmodulated
	blends that writes full alpha into a transparent render target, which
	turned every soft edge drawn into an offscreen widget into a black halo."""
	r, g, b, a = (max(0, min(255, v)) for v in (r, g, b, a))
	if r == 255 and g == 255 and b == 255 and a == 255:
		b = 254
	sdl3.set_texture_color_mod(tex, r, g, b)
	sdl3.set_texture_alpha_mod(tex, a)


class _Tex:
	__slots__ = ("tex", "w", "h", "cx", "cy", "pad")

	def __init__(self, tex, w: int, h: int, cx: int = 0, cy: int = 0, pad: int = 0) -> None:
		self.tex = tex
		self.w = w
		self.h = h
		self.cx = cx
		self.cy = cy
		self.pad = pad


class Aero:
	"""The Aqua skin. One instance lives on tauon.aero."""

	GUTTER = 8          # logical px between panels
	EDGE_GAP = 4        # logical px between the panels and the window edge
	RADIUS = 10         # panel corner radius
	TOP_H = 40          # top glass bar height (the panel's 30px row sits inside it)
	SKY_DIV = 5         # sky is painted at 1/SKY_DIV of the logical window size
	FROST_BLUR = 22     # backdrop-filter: blur(22px)
	FROST_SAT = 1.7     # backdrop-filter: saturate(1.7)
	FPS = 30            # the seek bar, bubbles, the spectrum
	FPS_AMBIENT = 60    # the sky's drift (it cross-fades between keyframes)
	SKY_KEY_RATE = 15   # sky keyframes per second while drifting
	SKY_KEY_RATE_FAST = 30  # and while the colours change
	FPS_FAST = 60       # colour transitions and the glint
	SHIMMER_SPEED = 170  # logical px per second along the seek tube

	# Dusk tokens from the concept
	TEXT = rgba8(232, 246, 255)
	# Secondary text: a neutral grey, tinted toward the accent by muted_for()
	MUTED = rgba8(160, 163, 168)
	MUTED_TINT = 0.12
	TINT = rgba8(6, 24, 42, 0.44)
	RIM = rgba8(180, 232, 255, 0.42)
	RIM_SOFT = rgba8(150, 215, 255, 0.12)
	EDGE = rgba8(0, 6, 14, 0.75)
	SHADOW = rgba8(0, 0, 0, 0.6)
	SHEEN_TOP = rgba8(190, 235, 255, 0.2)
	SHEEN_MID = rgba8(190, 235, 255, 0.03)
	SUNKEN = rgba8(0, 8, 18, 0.48)
	HOVER = rgba8(150, 220, 255, 0.08)
	SEL_TOP = rgba8(160, 225, 255, 0.22)
	SEL_BOT = rgba8(160, 225, 255, 0.07)
	SEL_EDGE = rgba8(160, 225, 255, 0.25)
	TAB = rgba8(160, 225, 255, 0.16)
	STAR = rgba8(170, 220, 255, 0.2)
	# Menus float over the panels, so their glass is deeper; a popup window
	# has no sky behind it and gets a solid pane instead
	MENU_TINT = rgba8(6, 20, 36, 0.66)
	MENU_SOLID = rgba8(20, 44, 66)

	# Obsidian tokens, the same roles in graphite and smoke
	OBSIDIAN = {
		"TEXT": rgba8(238, 241, 245),
		"MUTED": rgba8(152, 155, 160),
		"TINT": rgba8(12, 13, 16, 0.54),
		"RIM": rgba8(232, 238, 248, 0.34),
		"RIM_SOFT": rgba8(220, 228, 240, 0.10),
		"EDGE": rgba8(0, 0, 0, 0.82),
		"SHADOW": rgba8(0, 0, 0, 0.72),
		"SHEEN_TOP": rgba8(235, 240, 250, 0.15),
		"SHEEN_MID": rgba8(235, 240, 250, 0.02),
		"SUNKEN": rgba8(0, 0, 0, 0.55),
		"HOVER": rgba8(255, 255, 255, 0.06),
		"SEL_TOP": rgba8(235, 240, 250, 0.17),
		"SEL_BOT": rgba8(235, 240, 250, 0.05),
		"SEL_EDGE": rgba8(235, 240, 250, 0.20),
		"TAB": rgba8(235, 240, 250, 0.12),
		"STAR": rgba8(235, 240, 250, 0.18),
		"MENU_TINT": rgba8(10, 11, 14, 0.72),
		"MENU_SOLID": rgba8(30, 32, 37),
	}

	DEFAULT_PALETTE = (200.0, 186.0, 196.0)
	# Obsidian's accent when a dark cover has no highlights to take one from
	ICE = 205.0
	# A cover is "dark" (Obsidian on Auto) below these mean HSL values
	DARK_SAT = 0.16
	DARK_LIGHT = 0.24
	DARK_LIGHT_SAT = 0.30

	VARIANT_AUTO = 0
	VARIANT_DUSK = 1
	VARIANT_OBSIDIAN = 2

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.gui = tauon.gui
		self.prefs = tauon.prefs
		self.renderer = tauon.renderer
		self.inp = tauon.inp

		# Palette: hues in degrees, eased toward the target
		self.h1, self.h2, self.acc = self.DEFAULT_PALETTE
		self.target = self.DEFAULT_PALETTE
		# Obsidian: how far in (0-1), and its accent hue
		self.mono = 0.0
		self.oacc = self.ICE
		self.art_dark = False
		self.target_oacc = self.ICE
		self._mono_applied: int | None = None
		self._colours = None
		self._muted_applied: ColourRGBA | None = None
		# The class constants are the dusk tokens; the instance's own copies
		# are the blend that is drawn with
		self._dusk = {name: getattr(type(self), name) for name in self.OBSIDIAN}
		self._tokens_mono = -1.0
		self._update_tokens()
		self._palette_key = None
		self._palette_cache: dict = {}
		self._palette_lock = threading.Lock()
		self._palette_result: tuple | None = None

		# Sky
		self.sky_t = 0.0
		self._last = time.monotonic()
		# Two keyframes, each [sky texture, frost texture]: the sky shown is A
		# cross-faded into B, while the next keyframe paints on a thread
		self._key_a: list | None = None
		self._key_b: list | None = None
		self._blend_start = 0.0
		self._blend_len = 1.0
		self._sky_size = (0, 0)
		self._sky_dirty = True
		self._sky_gen = 0
		self._sky_job: threading.Thread | None = None
		self._sky_job_result: tuple | None = None
		self._sky_job_lock = threading.Lock()
		self._sprite: _Tex | None = None
		self._sky_drawn_key = None
		rnd = random.Random(7)
		self.parts = [
			{"x": rnd.random(), "y": rnd.random(), "r": 8 + rnd.random() ** 2 * 46,
			"vy": 6 + rnd.random() * 16, "ph": rnd.random() * 6.28, "a": 0.25 + rnd.random() * 0.6}
			for _ in range(30)]

		# Glint (a light sweep across every panel on track change)
		self.glint_start = -10.0
		self._glints: list = []
		self._due = 0.0
		self._raster_spent = 0.0
		self.palette_moving = False
		# The playing row's gel is drawn under the cached tracklist each frame
		# (so it follows a colour change without re-rendering the list)
		self.playing_rows: list[tuple[float, float, float, float]] = []
		# Off until the first palette is in, so start-up doesn't glint
		self._glint_armed = False
		self.panel_index = 0

		# Caches
		self._rings: dict = {}
		self._soft: OrderedDict = OrderedDict()
		self._orbs: OrderedDict = OrderedDict()
		self._misc: dict = {}

		# Seek tube furniture
		self.bubbles: list[dict] = []
		self._bubble_next = 0.0

		# Side-panel spectrum
		self.spec_vals = [0.0] * 24
		self.spec_peaks = [0.0] * 24

		# The play orb's liquid: 0 empty, 1 full; slosh is how much its
		# surface rocks (while the level moves)
		self.fill = 0.0
		self._fill_v = 0.0
		self._catching = False
		self._slosh = 0.0

		# Header rect for things drawn onto the top glass from outside it
		self.header_rect: tuple[int, int, int, int] | None = None
		# The compact playback panel's stand-in while the skin is on
		self.compact_bar = AquaBar(tauon)

	# -- state ------------------------------------------------------------------

	@property
	def enabled(self) -> bool:
		return bool(self.prefs.aero)

	@property
	def active(self) -> bool:
		return bool(self.prefs.aero) and self.gui.mode == GuiMode.MAIN

	def s(self, v: float) -> float:
		return v * self.gui.scale

	def si(self, v: float) -> int:
		return round(v * self.gui.scale)

	def reset(self) -> None:
		"""Drop every texture (render targets were reset, or the scale changed)."""
		for t in list(self._rings.values()):
			sdl3.destroy_texture(t.tex)
		self._rings.clear()
		for t in list(self._soft.values()):
			sdl3.destroy_texture(t.tex)
		self._soft.clear()
		for t in list(self._orbs.values()):
			sdl3.destroy_texture(t.tex)
		self._orbs.clear()
		for t in list(self._misc.values()):
			if isinstance(t, _Tex):
				sdl3.destroy_texture(t.tex)
		self._misc.clear()
		self._drop_sky_keys()
		self._sky_size = (0, 0)
		if self._sprite is not None:
			sdl3.destroy_texture(self._sprite.tex)
			self._sprite = None
		self._sky_dirty = True

	# -- colours applied to the theme -------------------------------------------

	PANEL_COLOURS = (
		"top_panel_background", "bottom_panel_colour", "side_panel_background",
		"playlist_panel_background", "gallery_background", "lyrics_panel_background",
		"queue_background", "playlist_box_background", "artist_bio_background",
		"column_bar_background", "tab_background", "tab_background_active",
		"tab_highlight", "art_box", "vis_bg",
	)

	def _update_tokens(self) -> None:
		m = self.mono
		if abs(m - self._tokens_mono) >= 1e-4:
			self._tokens_mono = m
			for name, obs in self.OBSIDIAN.items():
				setattr(self, name, mix(self._dusk[name], obs, m))
		self.MUTED = self.muted_for(self.acc, self.oacc, m)

	def muted_for(self, acc: float, oacc: float, m: float) -> RGBA:
		"""The secondary text grey with a little of the accent mixed in."""
		grey = mix(self._dusk["MUTED"], self.OBSIDIAN["MUTED"], m)
		tint = mix(hsl(acc, 0.7, 0.62), hsl(oacc, 0.7, 0.62), m)
		return mix(grey, tint, self.MUTED_TINT)

	def apply_colours(self, colours) -> None:
		"""Make the panels see-through and recolour text to the skin's
		palette. Called after every theme (re)load while the skin is on."""
		self._colours = colours
		self._mono_applied = round(self.mono)
		glass = ColourRGBA(10, 26, 42, 0)
		for name in self.PANEL_COLOURS:
			if getattr(colours, name, None) is None:
				continue
			# A fresh object per name: several names can alias one colour, and
			# every one of them has to stop pointing at the opaque original
			setattr(colours, name, ColourRGBA(glass.r, glass.g, glass.b, 0))
		colours.column_colours = {}
		colours.column_colours_playing = {}
		colours.lm = False
		self._apply_text_colours(colours)

	def _apply_text_colours(self, colours) -> None:
		"""Text and the theme-drawn bits, for the variant mostly showing."""
		obs = self._mono_applied == 1
		d = self._dusk
		text = to_colour(self.OBSIDIAN["TEXT"] if obs else d["TEXT"])
		muted_rgba = self.muted_for(self.target[2], self.target_oacc, 1.0 if obs else 0.0)
		muted = to_colour(muted_rgba)
		self._muted_applied = muted
		acc = to_colour(hsl(self.target_oacc, 0.85, 0.62)) if obs else ColourRGBA(90, 200, 240, 255)

		def put(name: str, c: ColourRGBA) -> None:
			if hasattr(colours, name):
				setattr(colours, name, ColourRGBA(c.r, c.g, c.b, c.a))

		for name in ("title_text", "title_playing", "album_text", "album_playing",
				"artist_playing", "index_playing", "time_playing", "bar_title_text",
				"side_bar_line1", "tab_text_active", "folder_title", "status_text_over",
				"menu_text"):
			put(name, text)
		for name in ("artist_text", "index_text", "time_text", "side_bar_line2", "tab_text",
				"status_text_normal", "playlist_text_missing"):
			put(name, muted)
		solid = self.OBSIDIAN["MENU_SOLID"] if obs else d["MENU_SOLID"]
		put("menu_icons", ColourRGBA(text.r, text.g, text.b, 62))
		put("menu_text_disabled", to_colour(mix(muted_rgba, solid, 0.45)))
		put("folder_line", ColourRGBA(225, 232, 242, 22) if obs else ColourRGBA(150, 215, 255, 26))
		put("row_playing_highlight", ColourRGBA(0, 0, 0, 0))
		put("row_select_highlight", ColourRGBA(0, 0, 0, 0))
		put("star_line", to_colour(self.OBSIDIAN["STAR"] if obs else rgba8(170, 220, 255, 0.2)))
		put("star_line_playing", ColourRGBA(255, 255, 255, 120))
		put("media_buttons_off", muted)
		put("media_buttons_over", text)
		put("media_buttons_active", text)
		put("mode_button_off", muted)
		put("mode_button_over", text)
		put("mode_button_active", text)
		put("corner_button", muted)
		put("corner_button_active", text)
		put("window_frame", to_colour(self.OBSIDIAN["EDGE"] if obs else d["EDGE"]))
		put("window_button_icon_off", muted)
		put("window_buttons_icon_over", text)
		# The close capsule is red gel: its cross stays white
		put("window_button_x_off", ColourRGBA(255, 255, 255, 230))
		put("window_button_x_on", ColourRGBA(255, 255, 255, 255))
		put("vis_colour", ColourRGBA(225, 232, 242, 255) if obs else ColourRGBA(120, 220, 255, 255))
		put("scroll_colour", ColourRGBA(225, 232, 242, 97) if obs else ColourRGBA(80, 170, 220, 140))
		sunken = to_colour(self.OBSIDIAN["SUNKEN"] if obs else d["SUNKEN"])
		put("seek_bar_background", sunken)
		put("volume_bar_background", sunken)
		put("seek_bar_fill", acc)
		put("volume_bar_fill", acc)
		put("bar_time", muted)

	def _sync_text_colours(self) -> None:
		"""Swap the theme's text colours as the blend crosses the middle (the
		tracklist is a cached texture, so it is redrawn once, not per step)."""
		side = round(self.mono)
		if side == self._mono_applied or self._colours is None:
			return
		self._mono_applied = side
		self._apply_text_colours(self._colours)
		self.gui.request_tracklist_redraw()

	# -- palette ------------------------------------------------------------------

	def _poll_palette(self) -> None:
		pctl = self.tauon.pctl
		track = pctl.playing_object()
		if track is None:
			track = pctl.show_object() if hasattr(pctl, "show_object") else None
		key = track.parent_folder_path if track is not None else None
		if key != self._palette_key:
			self._palette_key = key
			if key in self._palette_cache:
				self._set_target(self._palette_cache[key])
			elif track is None:
				self._set_target(self._default_entry())
			else:
				threading.Thread(target=self._palette_worker, args=(track, key), daemon=True).start()
		with self._palette_lock:
			if self._palette_result is not None:
				rkey, pal = self._palette_result
				self._palette_result = None
				self._palette_cache[rkey] = pal
				if rkey == self._palette_key:
					self._set_target(pal)
					self.gui.request_frame()

	def _default_entry(self) -> tuple:
		return (*self.DEFAULT_PALETTE, False, self.ICE)

	def _set_target(self, entry: tuple) -> None:
		"""entry: (sky hue, horizon hue, accent hue, dark art, Obsidian accent)."""
		# The glint marks a change of colours (not a new track from the same art)
		previous = (*self.target, self.art_dark, self.target_oacc)
		if self._glint_armed and tuple(entry) != previous:
			self.glint_start = time.monotonic()
		self._glint_armed = True
		self.target = entry[:3]
		self.art_dark = entry[3]
		self.target_oacc = entry[4]
		# The theme's secondary text follows the new accent (the tracklist is
		# cached, so only when it actually changes)
		if self._colours is not None and self.enabled:
			obs = 1.0 if self._mono_applied == 1 else 0.0
			if to_colour(self.muted_for(self.target[2], self.target_oacc, obs)) != self._muted_applied:
				self._apply_text_colours(self._colours)
				self.gui.request_tracklist_redraw()

	def target_mono(self) -> float:
		variant = self.prefs.aero_variant
		if variant == self.VARIANT_OBSIDIAN:
			return 1.0
		if variant == self.VARIANT_DUSK:
			return 0.0
		return 1.0 if self.art_dark else 0.0

	def _palette_worker(self, track, key) -> None:
		pal = self._default_entry()
		try:
			art = self.tauon.album_art_gen
			sources = art.get_sources(track)
			if sources:
				offset = art.get_offset(track.fullpath, sources)
				raw = art.get_source_raw(offset, sources, track)
				if raw is not None:
					im = Image.open(raw)
					im.draft("RGB", (100, 100))
					im = im.convert("RGB")
					im.thumbnail((100, 100))
					hues = self.palette_from_image(im)
					dark, highlight = self.art_stats(im)
					if highlight is not None:
						oacc = highlight
					else:
						# Forced Obsidian on colourful art keeps the album's accent
						oacc = self.ICE if dark else hues[2]
					pal = (*hues, dark, oacc)
					raw.close()
		except Exception:
			logging.exception("Aqua: could not read art colours")
		with self._palette_lock:
			self._palette_result = (key, pal)
		self.gui.request_frame()

	@classmethod
	def palette_from_image(cls, im: Image.Image) -> tuple[float, float, float]:
		"""(sky hue, horizon hue, accent hue) from album art."""
		im = im.convert("RGB")
		im.thumbnail((40, 40))
		bins = [0.0] * 36
		sat_bins = [0.0] * 36
		total = 0.0
		for r, g, b in im.getdata():
			h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
			v = max(r, g, b) / 255
			chroma = (max(r, g, b) - min(r, g, b)) / 255
			if v < 0.12 or chroma < 0.06:
				continue
			w = chroma * (0.4 + v)
			i = int(h * 36) % 36
			bins[i] += w
			sat_bins[i] += w * chroma * chroma
			total += w
		if total < 2:
			return cls.DEFAULT_PALETTE
		smooth = [bins[i - 1] * 0.25 + bins[i] * 0.5 + bins[(i + 1) % 36] * 0.25 for i in range(36)]

		def centre(i: int) -> float:
			# Weighted mean hue around bin i
			sx = sy = 0.0
			for j in (i - 1, i, i + 1):
				ang = math.radians((j % 36) * 10 + 5)
				wgt = bins[j % 36]
				sx += math.cos(ang) * wgt
				sy += math.sin(ang) * wgt
			return math.degrees(math.atan2(sy, sx)) % 360

		first = max(range(36), key=lambda i: smooth[i])
		h1 = centre(first)
		second = None
		best = 0.0
		for i in range(36):
			dist = min(abs(i - first), 36 - abs(i - first))
			if dist >= 3 and smooth[i] > best:
				best = smooth[i]
				second = i
		if second is not None and best > smooth[first] * 0.12:
			h2 = centre(second)
		else:
			h2 = (h1 - 18) % 360
		acc_bin = max(range(36), key=lambda i: sat_bins[i - 1] * 0.25 + sat_bins[i] * 0.5 + sat_bins[(i + 1) % 36] * 0.25)
		acc = centre(acc_bin)
		# A warm accent on a cool sky (or the reverse) reads as a clash in the
		# gel; keep the accent near the sky unless it dominates the art
		if min(abs(acc - h1), 360 - abs(acc - h1)) > 60 and smooth[acc_bin] < smooth[first] * 0.6:
			acc = h1
		return (h1, h2, acc)

	@classmethod
	def art_stats(cls, im: Image.Image) -> tuple[bool, float | None]:
		"""(dark, highlight hue) for album art.

		Dark: the 40px thumbnail's mean HSL saturation and lightness fall
		under the Obsidian rule. Highlight: the main hue among the bright,
		saturated pixels of a finer 100px sample (lit windows, a neon sign;
		at 40px they blur into grey), or None when there are too few."""
		im = im.convert("RGB")
		small = im.copy()
		small.thumbnail((40, 40))
		ss = ll = 0.0
		n = 0
		for r, g, b in small.getdata():
			mx = max(r, g, b)
			mn = min(r, g, b)
			l = (mx + mn) / 510
			n += 1
			ll += l
			# Under 6 levels of chroma is compression noise in the blacks,
			# where HSL saturation would read it as vivid
			if mx - mn >= 6:
				ss += (mx - mn) / 255 / max(1e-6, 1 - abs(2 * l - 1))
		if n == 0:
			return False, None
		sat = ss / n
		light = ll / n
		dark = sat < cls.DARK_SAT or (light < cls.DARK_LIGHT and sat < cls.DARK_LIGHT_SAT)

		fine = im.copy()
		fine.thumbnail((100, 100))
		bins = [0.0] * 36
		count = 0
		for r, g, b in fine.getdata():
			mx = max(r, g, b)
			mn = min(r, g, b)
			if mx == mn:
				continue
			l = (mx + mn) / 510
			s = (mx - mn) / 255 / max(1e-6, 1 - abs(2 * l - 1))
			if s > 0.4 and l > 0.12:
				h = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)[0]
				bins[int(h * 36) % 36] += s * l
				count += 1
		if count < 4:
			return dark, None
		# The strongest hue, not the mean: red and blue lights mustn't average
		# to magenta
		smooth = [bins[i - 1] * 0.25 + bins[i] * 0.5 + bins[(i + 1) % 36] * 0.25 for i in range(36)]
		peak = max(range(36), key=lambda i: smooth[i])
		sx = sy = 0.0
		for j in (peak - 1, peak, peak + 1):
			ang = math.radians((j % 36) * 10 + 5)
			sx += math.cos(ang) * bins[j % 36]
			sy += math.sin(ang) * bins[j % 36]
		return dark, math.degrees(math.atan2(sy, sx)) % 360

	def _step_palette(self, dt: float) -> bool:
		k = 1 - math.exp(-dt * 3.2)
		moving = False
		target = (*self.target, self.target_oacc)
		cur = [self.h1, self.h2, self.acc, self.oacc]
		for i in range(4):
			d = ((target[i] - cur[i] + 540) % 360) - 180
			if abs(d) > 0.3:
				cur[i] = (cur[i] + d * k) % 360
				moving = True
			else:
				cur[i] = target[i]
		self.h1, self.h2, self.acc, self.oacc = cur
		# Obsidian fades in over the same second the hues take
		tm = self.target_mono()
		dm = tm - self.mono
		if abs(dm) > 0.004:
			self.mono += dm * k
			moving = True
		else:
			self.mono = tm
		self._update_tokens()
		self._sync_text_colours()
		return moving

	# -- frame ----------------------------------------------------------------------

	@property
	def see_through(self) -> bool:
		"""The sky stays behind the glass only; the gaps show the desktop."""
		return self.active and bool(self.prefs.aero_see_through)

	def motion(self) -> bool:
		return bool(self.prefs.aero_motion) and not self.gui.lowered

	def begin_frame(self) -> None:
		"""Advance time, ease the palette and draw the sky. Call at the start
		of every main-mode frame while the skin is active."""
		now = time.monotonic()
		dt = min(0.1, max(0.0, now - self._last))
		self._last = now
		self._raster_spent = 0.0
		self._poll_palette()
		moving = self._step_palette(dt)
		filling = self._step_fill(dt)
		animate = self.motion()
		if animate:
			self.sky_t += dt
			for p in self.parts:
				p["y"] -= p["vy"] * dt / max(1, self.tauon.window_size[1] / self.gui.scale)
				if p["y"] < -0.1:
					p["y"] = 1.1
					p["x"] = random.random()
			self._sky_dirty = True
		if moving:
			self._sky_dirty = True
		glinting = now - self.glint_start < 1.6
		self.panel_index = 0
		self._glints = []
		self.palette_moving = moving
		self.draw_sky()
		# The sky keeps moving between keyframes (a cross-fade), so drift and
		# colour changes both run at the fast rate
		if moving or glinting or animate or filling or self.sky_settling():
			self.schedule(1 / self.FPS_AMBIENT)
		elif self.bubbles:
			self.schedule(1 / self.FPS)

	def schedule(self, interval: float) -> None:
		"""Ask for a frame `interval` from now, unless one is already due by then."""
		now = time.monotonic()
		due = now + interval
		if now < self._due <= due + 0.002:
			return
		self._due = due
		self.gui.delay_frame(interval)

	# -- sky -----------------------------------------------------------------------------

	def _sky_dims(self) -> tuple[int, int]:
		w = self.tauon.window_size[0] / self.gui.scale
		h = self.tauon.window_size[1] / self.gui.scale
		return max(16, round(w / self.SKY_DIV)), max(16, round(h / self.SKY_DIV))

	def _sky_snapshot(self) -> dict:
		"""Everything the sky painter reads, copied for its thread."""
		return {
			"h1": self.h1, "h2": self.h2, "acc": self.acc, "mono": self.mono, "oacc": self.oacc,
			"T": self.sky_t, "parts": [dict(p) for p in self.parts]}

	def _paint_sky(self, lw: int, lh: int, snap: dict) -> tuple[Image.Image, Image.Image]:
		"""The sky at low resolution, and its frosted copy, from a snapshot.

		Everything here is Pillow's C code; per-pixel work never runs in
		Python (lookup tables are 256 entries, and the bokeh sprites are
		cached by size and strength). Runs on a worker thread."""
		h1, h2, acc = snap["h1"], snap["h2"], snap["acc"]
		T = snap["T"]
		# Obsidian: the same sky with its colour eased out, a touch darker, its
		# light silver; one ribbon and the top bloom keep the accent
		m = snap["mono"]
		oacc = snap["oacc"]

		def sat(v: float) -> float:
			return _lerp(v, 0.10, m)

		def lit(v: float, o: float) -> float:
			return _lerp(v, o, m)

		# Base gradient: graphite, cool at the top and a hint warm at the floor
		cool = _hue_lerp(h1, 215, m)
		stops = [
			(0.0, hsl(cool, sat(0.70), lit(0.08, 0.05))),
			(0.55, hsl(cool, sat(0.65), lit(0.15, 0.10))),
			(1.0, hsl(_hue_lerp(h2, 30, m), sat(0.55), lit(0.20, 0.14)))]
		col = Image.new("RGB", (1, lh))
		px = col.load()
		for yy in range(lh):
			c = _stop_at(stops, (yy + 0.5) / lh)
			px[0, yy] = (round(c[0] * 255), round(c[1] * 255), round(c[2] * 255))
		img = col.resize((lw, lh), Image.Resampling.NEAREST)

		# Blooms, added ('lighter'): an inverted radial falloff, coloured
		blooms = (
			(0.2 + 0.08 * math.sin(T * 0.11), 0.25 + 0.06 * math.cos(T * 0.09), 0.6, h1 + 15, 0.26),
			(0.82 + 0.06 * math.cos(T * 0.07), 0.78 + 0.05 * math.sin(T * 0.12), 0.65, h2, 0.30),
			(0.55 + 0.1 * math.sin(T * 0.05 + 2), 0.08, 0.45, acc + 25, 0.20),
		)
		for i_b, (bx, by, br, bh, ba) in enumerate(blooms):
			R = br * lw
			falloff = self._falloff((lw, lh), bx * lw, by * lh, R)
			c = hsl(bh, 0.95, 0.55)
			c = (c[0] * ba, c[1] * ba, c[2] * ba)
			if m > 0:
				if i_b == 2:
					o = hsl(oacc, 0.70, 0.50)
					oa = ba * 0.75
				else:
					o = hsl(_hue_lerp(bh, 215, m), sat(0.95), 0.46)
					oa = ba * 0.45
				c = tuple(_lerp(c[i], o[i] * oa, m) for i in range(3))
			img = ImageChops.add(img, Image.merge("RGB", [falloff.point(_lut(c[i])) for i in range(3)]))

		# Light ribbons, added. Drawn at 2x for antialiasing
		ss = 2
		for k in range(3):
			amp = lh * (0.1 + 0.05 * k)
			base = lh * (0.42 + 0.17 * k)
			ph = T * (0.15 + 0.05 * k) + k * 2
			freq = (1.4 + k * 0.5) / lw * math.pi
			hue = acc if k == 1 else h1 + 20 * k
			pts = []
			xx = -10.0
			while xx <= lw + 10:
				yy = base + math.sin(xx * freq + ph) * amp + math.sin(xx * freq * 2.3 - ph * 1.3) * amp * 0.35 - xx * 0.14
				pts.append((xx * ss, yy * ss))
				xx += 2
			acc_l = Image.new("L", (lw, lh), 0)
			for width, alpha in ((14 - 3 * k, 0.10), (5, 0.17), (1.2, 0.45)):
				lay = Image.new("L", (lw * ss, lh * ss), 0)
				# Each stroke is one filled outline: a polyline leaves gaps at
				# its joints, and round joints cost a pie slice per point
				ImageDraw.Draw(lay).polygon(_stroke_outline(pts, max(1.0, width * ss) / 2), fill=round(255 * alpha))
				acc_l = ImageChops.add(acc_l, lay.reduce(ss))
			c = hsl(hue, 0.90, 0.65)
			if m > 0:
				if k == 1:
					o = hsl(oacc, 0.75, 0.66, 0.8)
				else:
					o = hsl(215, 0.10, 0.78, 0.5)
				c = tuple(_lerp(c[i], o[i] * o[3], m) for i in range(3))
			img = ImageChops.add(img, Image.merge("RGB", [acc_l.point(_lut(c[i])) for i in range(3)]))

		# Frost: the sky with its bokeh, blurred 22px and saturated 1.7
		bok = Image.new("L", (lw, lh), 0)
		for p in snap["parts"]:
			a = p["a"] * 0.42 * (1 - 0.35 * m) * (0.6 + 0.4 * math.sin(T * 0.6 + p["ph"]))
			r = p["r"] / self.SKY_DIV
			spr = self._bokeh_sprite(max(2, round(r * 2)), a)
			x = round(p["x"] * lw + math.sin(T * 0.3 + p["ph"]) * 14 / self.SKY_DIV - r)
			y = round(p["y"] * lh - r)
			box = (x, y, x + spr.width, y + spr.height)
			if box[2] <= 0 or box[3] <= 0 or box[0] >= lw or box[1] >= lh:
				continue
			region = bok.crop(box)
			bok.paste(ImageChops.add(region, spr), box)
		frost = ImageChops.add(img, Image.merge("RGB", (bok, bok, bok)))
		sigma = self.FROST_BLUR / self.SKY_DIV
		# Clamp-to-edge before blurring, like a backdrop filter at the window edge
		m = math.ceil(sigma * 3)
		padded = frost.resize((lw + m * 2, lh + m * 2), Image.Resampling.NEAREST)
		padded.paste(frost, (m, m))
		frost = padded.filter(ImageFilter.GaussianBlur(sigma)).crop((m, m, m + lw, m + lh))
		s = self.FROST_SAT
		matrix = (
			0.213 + 0.787 * s, 0.715 - 0.715 * s, 0.072 - 0.072 * s, 0,
			0.213 - 0.213 * s, 0.715 + 0.285 * s, 0.072 - 0.072 * s, 0,
			0.213 - 0.213 * s, 0.715 - 0.715 * s, 0.072 + 0.928 * s, 0,
		)
		frost = frost.convert("RGB", matrix)
		# A touch of softening so the 5x bilinear stretch reads as a smooth wash
		img = img.filter(ImageFilter.GaussianBlur(0.6))
		return img, frost

	def _falloff(self, size: tuple[int, int], cx: float, cy: float, R: float) -> Image.Image:
		"""'L' image, 255 at (cx, cy) falling linearly to 0 at radius R. The
		scaled template is cached per radius; only the paste moves."""
		key = ("falloff", round(R))
		tpl = self._misc.get(key)
		if tpl is None:
			d = max(1, round(R * 2))
			tpl = ImageChops.invert(_radial_l((d, d), d / 2, d / 2, d / 2, d / 2))
			self._misc[key] = tpl
		out = Image.new("L", size, 0)
		out.paste(tpl, (round(cx - tpl.width / 2), round(cy - tpl.height / 2)))
		return out

	def _bokeh_sprite(self, d: int, alpha: float) -> Image.Image:
		"""A bokeh disc at low resolution, scaled by `alpha` (cached in 32 steps)."""
		q = max(0, min(31, round(alpha * 31)))
		key = ("bokeh", d, q)
		spr = self._misc.get(key)
		if spr is None:
			spr = self._bokeh_profile().resize((d, d), Image.Resampling.BILINEAR).point(_lut(q / 31))
			self._misc[key] = spr
		return spr

	def _bokeh_profile(self) -> Image.Image:
		prof = self._misc.get("bokeh_profile")
		if prof is None:
			n = 96
			t = _radial_l((n, n), n / 2, n / 2, n / 2 - 1, n / 2 - 1)
			stops = [(0.0, (1, 1, 1, 0.26)), (0.72, (1, 1, 1, 0.15)), (0.9, (1, 1, 1, 0.55)), (1.0, (1, 1, 1, 0.0))]
			lut = [round(_stop_at(stops, v / 255)[3] * 255) for v in range(256)]
			prof = t.point(lut)
			self._misc["bokeh_profile"] = prof
		return prof

	def _upload(self, tex, img: Image.Image):
		w, h = img.size
		data = img.convert("RGBA").tobytes("raw", "BGRA")
		if tex is None:
			tex = sdl3.create_texture(self.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_STREAMING, w, h)
			sdl3.set_texture_scale_mode(tex, sdl3.SDL_SCALEMODE_LINEAR)
			sdl3.set_texture_blend_mode(tex, sdl3.SDL_BLENDMODE_NONE)
		sdl3.update_texture(tex, None, data, w * 4)
		return tex

	def _drop_sky_keys(self) -> None:
		for key in (self._key_a, self._key_b):
			if key is not None:
				for t in key:
					sdl3.destroy_texture(t)
		self._key_a = self._key_b = None
		# A paint still running was for the old textures or size
		self._sky_gen += 1

	def _sky_worker(self, lw: int, lh: int, snap: dict, gen: int) -> None:
		try:
			result = (gen, (lw, lh), self._paint_sky(lw, lh, snap))
		except Exception:
			logging.exception("Aqua: sky paint failed")
			result = (gen, None, None)
		with self._sky_job_lock:
			self._sky_job_result = result
		self.gui.request_frame()

	def sky_blend(self) -> float:
		"""How far the shown sky is from keyframe A to B (0-1)."""
		if self._key_a is None:
			return 1.0
		return min(1.0, max(0.0, (time.monotonic() - self._blend_start) / self._blend_len))

	def sky_settling(self) -> bool:
		"""A cross-fade or a keyframe paint is still under way."""
		return self._sky_job is not None or self.sky_blend() < 1.0

	def _update_sky_keys(self, lw: int, lh: int) -> None:
		"""Keyframes: paint the next one on a thread while the shown sky
		cross-fades from A to B; take it in once that fade has finished."""
		now = time.monotonic()
		if self._key_b is None:
			# First paint (or a resize): synchronous, nothing to fade from
			sky, frost = self._paint_sky(lw, lh, self._sky_snapshot())
			self._key_b = [self._upload(None, sky), self._upload(None, frost)]
			self._key_a = None
			self._sky_dirty = False
			return
		if self._sky_job is not None:
			with self._sky_job_lock:
				result = self._sky_job_result
			if result is not None and self.sky_blend() >= 1.0:
				self._sky_job = None
				self._sky_job_result = None
				gen, size, imgs = result
				if gen == self._sky_gen and size == (lw, lh) and imgs is not None:
					# Reuse the outgoing keyframe's textures for the new one
					old = self._key_a
					new = [self._upload(old[0] if old else None, imgs[0]),
						self._upload(old[1] if old else None, imgs[1])]
					self._key_a = self._key_b
					self._key_b = new
					self._blend_start = now
					rate = self.SKY_KEY_RATE_FAST if self.palette_moving else self.SKY_KEY_RATE
					self._blend_len = 1 / rate
		if self._sky_job is None and self._sky_dirty:
			self._sky_dirty = False
			self._sky_job_result = None
			self._sky_job = threading.Thread(
				target=self._sky_worker, args=(lw, lh, self._sky_snapshot(), self._sky_gen), daemon=True)
			self._sky_job.start()

	def frost_layers(self) -> list[tuple[object, float]]:
		"""(frost texture, alpha) to draw in order: A, then B faded over it."""
		if self._key_b is None:
			return []
		f = self.sky_blend()
		if self._key_a is None or f >= 1.0:
			return [(self._key_b[1], 1.0)]
		return [(self._key_a[1], 1.0), (self._key_b[1], f)]

	def draw_sky(self) -> None:
		"""Bring the sky keyframes up to date and paint the sky across the
		window, or, see-through, leave the window clear: the sky then only
		reaches the eye through the panels' frost."""
		ww, wh = self.tauon.window_size[0], self.tauon.window_size[1]
		lw, lh = self._sky_dims()
		if (lw, lh) != self._sky_size:
			self._drop_sky_keys()
			self._sky_job = None
			self._sky_size = (lw, lh)
			self._sky_dirty = True
		self._update_sky_keys(lw, lh)
		r = self.renderer
		if self.see_through:
			# Replace whatever is there with nothing (custom mode draws over
			# the standard layout's frame start)
			sdl3.set_render_draw_blend_mode(r, sdl3.SDL_BLENDMODE_NONE)
			sdl3.set_render_draw_color(r, 0, 0, 0, 0)
			sdl3.render_fill_rect(r, sdl3.FRect(0, 0, ww, wh))
			sdl3.set_render_draw_blend_mode(r, sdl3.SDL_BLENDMODE_BLEND)
			return
		dst = sdl3.FRect(0, 0, ww, wh)
		f = self.sky_blend()
		if self._key_a is not None and f < 1.0:
			# Opaque keyframes: A, then B blended over it at the fade's progress
			sdl3.set_texture_blend_mode(self._key_a[0], sdl3.SDL_BLENDMODE_NONE)
			_mod(self._key_a[0], 255, 255, 255, 255)
			sdl3.render_texture(r, self._key_a[0], None, dst)
			sdl3.set_texture_blend_mode(self._key_b[0], sdl3.SDL_BLENDMODE_BLEND)
			_mod(self._key_b[0], 255, 255, 255, round(f * 255))
			sdl3.render_texture(r, self._key_b[0], None, dst)
		else:
			sdl3.set_texture_blend_mode(self._key_b[0], sdl3.SDL_BLENDMODE_NONE)
			_mod(self._key_b[0], 255, 255, 255, 255)
			sdl3.render_texture(r, self._key_b[0], None, dst)
		# Bokeh over the sharp sky ('lighter')
		spr = self._sprite_tex()
		T = self.sky_t
		sc = self.gui.scale
		sdl3.set_texture_blend_mode(spr.tex, sdl3.SDL_BLENDMODE_ADD)
		for p in self.parts:
			a = p["a"] * 0.42 * (1 - 0.35 * self.mono) * (0.6 + 0.4 * math.sin(T * 0.6 + p["ph"]))
			rr = p["r"] * sc
			x = p["x"] * ww + math.sin(T * 0.3 + p["ph"]) * 14 * sc - rr
			y = p["y"] * wh - rr
			_mod(spr.tex, 255, 255, 255, round(a * 255))
			sdl3.render_texture(r, spr.tex, None, sdl3.FRect(x, y, rr * 2, rr * 2))

	def _sprite_tex(self) -> _Tex:
		if self._sprite is None:
			prof = self._bokeh_profile()
			img = Image.new("RGBA", prof.size, (255, 255, 255, 0))
			# Premultiplied-free: ADD blend multiplies by alpha itself
			img.putalpha(prof)
			tex = self._make_tex(img)
			self._sprite = _Tex(tex, img.width, img.height)
		return self._sprite

	def _make_tex(self, img: Image.Image, linear: bool = True):
		img = img.convert("RGBA")
		tex = sdl3.create_texture_from_rgba(self.renderer, img.width, img.height, img.tobytes())
		sdl3.set_texture_blend_mode(tex, sdl3.SDL_BLENDMODE_BLEND)
		if linear:
			sdl3.set_texture_scale_mode(tex, sdl3.SDL_SCALEMODE_LINEAR)
		_mod(tex, 255, 255, 255, 255)
		return tex

	# -- meshes ---------------------------------------------------------------------------

	def shape(self, rect: tuple[float, float, float, float], radii, colour=None, *,
			grad: Gradient | None = None, grads: tuple = (), texture=None, uv=None,
			cuts: list | None = None) -> None:
		"""Fill a rounded rect. `colour` is a flat RGBA, or `grad`/`grads` give
		gradients whose product is the vertex colour; `texture` with `uv`
		((x, y) -> (u, v)) samples a texture through it."""
		x, y, w, h = rect
		if w <= 0 or h <= 0:
			return
		if not isinstance(radii, tuple) or len(radii) != 4:
			radii = (radii, radii, radii, radii)
		polys = [rounded_poly(x, y, w, h, radii)]
		all_grads = ([grad] if grad is not None else []) + list(grads)
		allc = list(cuts or [])
		for g in all_grads:
			allc += g.cuts()
		if allc:
			polys = cut_polys(polys, allc)
		verts = []
		idx = []
		for poly in polys:
			base = len(verts)
			cx = sum(p[0] for p in poly) / len(poly)
			cy = sum(p[1] for p in poly) / len(poly)
			# Pull each sample a hair toward the cell centre so the colour
			# lookup can't land on the wrong side of a stop line
			for px, py in poly:
				qx = px + (cx - px) * 1e-4
				qy = py + (cy - py) * 1e-4
				if all_grads:
					r = g_ = b = a = 1.0
					for gr in all_grads:
						c = gr(qx, qy)
						r *= c[0]
						g_ *= c[1]
						b *= c[2]
						a *= c[3]
					col = (r, g_, b, a)
				elif colour is not None:
					col = colour
				else:
					col = (1.0, 1.0, 1.0, 1.0)
				if uv is not None:
					u, v = uv(px, py)
				else:
					u = v = 0.0
				verts.append((px, py, u, v, col[0], col[1], col[2], col[3]))
			for i in range(1, len(poly) - 1):
				idx += (base, base + i, base + i + 1)
		if not verts:
			return
		sdl3.set_render_draw_blend_mode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.render_geometry(self.renderer, texture, verts, idx)
		if texture is not None and not self._is_frost(texture):
			# SDL's software renderer applies vertex colours to a textured mesh
			# through the texture's own colour and alpha mod, and leaves them
			# there: album art drawn here (the reflection fades to alpha 0)
			# came out invisible the next time the rest of Tauon drew it
			sdl3.set_texture_color_mod(texture, 255, 255, 255)
			sdl3.set_texture_alpha_mod(texture, 255)

	def _is_frost(self, texture) -> bool:
		return any(key is not None and texture is key[1] for key in (self._key_a, self._key_b))

	# -- rings ------------------------------------------------------------------------------

	def _ring_tex(self, kind: str, r: float, h_exact: int | None) -> _Tex:
		key = (kind, round(r * 4), h_exact)
		t = self._rings.get(key)
		if t is not None:
			return t
		pad = 3
		C = math.ceil(r) + pad + 1
		W = 2 * C + 1
		H = W if h_exact is None else h_exact + 2 * pad
		size = (W, H)
		box = (pad, pad, W - pad, H - pad)

		def m(dx0: float = 0, dy0: float = 0, dx1: float = 0, dy1: float = 0, rad: float = r) -> Image.Image:
			return _rr_mask(size, (box[0] + dx0, box[1] + dy0, box[2] + dx1, box[3] + dy1), rad)

		base = m()
		if kind == "outer":
			a = ImageChops.subtract(m(-1, -1, 1, 1, r + 1), base)
		elif kind == "inner":
			a = ImageChops.subtract(base, m(1, 1, -1, -1, max(0.0, r - 1)))
		elif kind == "top":
			a = ImageChops.multiply(base, ImageChops.invert(m(0, 1, 0, 1)))
		elif kind == "bottom_in":
			a = ImageChops.multiply(base, ImageChops.invert(m(0, -1, 0, -1)))
		elif kind == "bottom_out":
			a = ImageChops.multiply(m(0, 1, 0, 1), ImageChops.invert(base))
		elif kind == "right_in":
			a = ImageChops.multiply(base, ImageChops.invert(m(-1, 0, -1, 0)))
		elif kind == "inset_top_shadow":
			# inset 0 2px 3px
			a = _inset_shadow(base, 0, 2, 1.5)
		elif kind == "fill":
			a = base
		else:
			raise ValueError(kind)
		img = Image.new("RGBA", size, (255, 255, 255, 0))
		img.putalpha(a)
		tex = self._make_tex(img, linear=False)
		t = _Tex(tex, W, H, C, 0 if h_exact is not None else C, pad)
		self._rings[key] = t
		return t

	def _nine(self, t: _Tex, x: float, y: float, w: float, h: float) -> None:
		"""Draw a sliced texture over the shape rect (x, y, w, h)."""
		p = t.pad
		dx, dy, dw, dh = x - p, y - p, w + 2 * p, h + 2 * p
		cx = min(t.cx, dw / 2)
		cy = min(t.cy, dh / 2)
		sxs = (0, t.cx, t.w - t.cx, t.w)
		dxs = (dx, dx + cx, dx + dw - cx, dx + dw)
		if t.cy:
			sys_ = (0, t.cy, t.h - t.cy, t.h)
			dys = (dy, dy + cy, dy + dh - cy, dy + dh)
		else:
			sys_ = (0, 0, t.h, t.h)
			dys = (dy, dy, dy + dh, dy + dh)
		r = self.renderer
		for j in range(3):
			sh = sys_[j + 1] - sys_[j]
			ddh = dys[j + 1] - dys[j]
			if sh <= 0 or ddh <= 0:
				continue
			for i in range(3):
				sw = sxs[i + 1] - sxs[i]
				ddw = dxs[i + 1] - dxs[i]
				if sw <= 0 or ddw <= 0:
					continue
				sdl3.render_texture(r, t.tex, sdl3.FRect(sxs[i], sys_[j], sw, sh), sdl3.FRect(dxs[i], dys[j], ddw, ddh))

	def ring(self, kind: str, rect: tuple[float, float, float, float], r: float, colour: RGBA) -> None:
		x, y, w, h = rect
		if w <= 0 or h <= 0 or colour[3] <= 0:
			return
		pad = 3
		C = math.ceil(r) + pad + 1
		h_exact = round(h) if h + 2 * pad < 2 * C + 1 else None
		t = self._ring_tex(kind, r, h_exact)
		_mod(t.tex, round(colour[0] * 255), round(colour[1] * 255), round(colour[2] * 255), round(colour[3] * 255))
		self._nine(t, x, y, w, h)

	# -- soft shadows and glows ---------------------------------------------------------------

	def _soft_tex(self, w: int, h: int, r: float, sigma: float, spread: float) -> _Tex:
		key = (w, h, round(r * 2), round(sigma * 2), round(spread * 2))
		t = self._soft.get(key)
		if t is not None:
			self._soft.move_to_end(key)
			return t
		# Large shadows are rendered at half size; they're all blur anyway
		f = 2 if sigma >= 6 else 1
		m = math.ceil(sigma * 3 + max(0.0, spread)) + 2
		W = math.ceil((w + 2 * m) / f)
		H = math.ceil((h + 2 * m) / f)
		box = ((m - spread) / f, (m - spread) / f, (m + w + spread) / f, (m + h + spread) / f)
		mask = _rr_mask((W, H), box, max(0.0, r + spread) / f, ss=2)
		if sigma > 0:
			mask = mask.filter(ImageFilter.GaussianBlur(sigma / f))
		img = Image.new("RGBA", (W, H), (255, 255, 255, 0))
		img.putalpha(mask)
		tex = self._make_tex(img)
		t = _Tex(tex, W, H, 0, 0, m)
		self._soft[key] = t
		while len(self._soft) > 48:
			_k, old = self._soft.popitem(last=False)
			sdl3.destroy_texture(old.tex)
		return t

	def soft(self, rect, r: float, sigma: float, spread: float, colour: RGBA, dx: float = 0, dy: float = 0) -> None:
		"""A CSS box-shadow drawn under (around) a shape."""
		x, y, w, h = rect
		w, h = round(w), round(h)
		if w <= 0 or h <= 0 or colour[3] <= 0:
			return
		t = self._soft_tex(w, h, r, sigma, spread)
		_mod(t.tex, round(colour[0] * 255), round(colour[1] * 255), round(colour[2] * 255), round(colour[3] * 255))
		m = t.pad
		sdl3.render_texture(self.renderer, t.tex, None, sdl3.FRect(round(x) - m + dx, round(y) - m + dy, w + 2 * m, h + 2 * m))

	# -- glass panels -------------------------------------------------------------------------------

	def frost_uv(self):
		ww, wh = max(1, self.tauon.window_size[0]), max(1, self.tauon.window_size[1])
		return lambda px, py: (px / ww, py / wh)

	def panel(self, rect: tuple[float, float, float, float], tall: bool = False,
			sheen_h: float | None = None) -> None:
		"""One floating glass panel: shadow, frost, tint, sheen, rims, glint."""
		x, y, w, h = (round(v) for v in rect)
		if w < 4 or h < 4:
			return
		R = min(self.s(self.RADIUS), w / 2, h / 2)
		sc = self.gui.scale
		index = self.panel_index
		self.panel_index += 1

		# 0 10px 26px -12px shadow
		self.soft((x, y, w, h), R, 13 * sc, -12 * sc, self.SHADOW, 0, 10 * sc)
		# Frost
		uv = self.frost_uv()
		for tex, alpha in self.frost_layers():
			# The first layer replaces what is under it; a fading second one blends
			sdl3.set_texture_blend_mode(tex, sdl3.SDL_BLENDMODE_NONE if alpha >= 1.0 else sdl3.SDL_BLENDMODE_BLEND)
			self.shape((x, y, w, h), R, (1.0, 1.0, 1.0, alpha), texture=tex, uv=uv)
		# Tint
		self.shape((x, y, w, h), R, self.TINT)
		# Sheen: ::before, inset 1px, rounded top corners only
		ri = max(0.0, R - 1)
		if tall:
			sh = min(h - 2, self.s(sheen_h or 110))
			top = self.SHEEN_TOP
			g = vgrad(y + 1, sh, [(0.0, (top[0], top[1], top[2], top[3] * 0.8)), (1.0, (top[0], top[1], top[2], 0.0))])
		else:
			sh = (h - 2) * 0.48 if sheen_h is None else min(h - 2, self.s(sheen_h))
			g = vgrad(y + 1, sh, [(0.0, self.SHEEN_TOP), (1.0, self.SHEEN_MID)])
		self.shape((x + 1, y + 1, w - 2, sh), (ri, ri, 0, 0), grad=g)
		# Rims: inner ring, top highlight over it, then the dark outer edge
		self.ring("inner", (x, y, w, h), R, self.RIM_SOFT)
		self.ring("top", (x, y, w, h), R, self.RIM)
		self.ring("outer", (x, y, w, h), R, self.EDGE)
		# The glint crosses the panel's content too, so it waits for flush_glints()
		self._glints.append(((x, y, w, h), R, index))

	# -- context menus --------------------------------------------------------------------------

	MENU_RADIUS = 8
	# A popup window shows the desktop behind it unfrosted, so it stays mostly solid
	MENU_POPUP_ALPHA = 0.9
	DIALOG_RADIUS = 12

	def colour(self, name: str) -> ColourRGBA:
		"""A token (TEXT, MUTED, ...) as a theme colour."""
		return to_colour(getattr(self, name))

	def badge(self, rect, colour: ColourRGBA) -> None:
		"""A small coloured gel tag (the track box's format badges)."""
		x, y, w, h = rect
		r = self.s(3)
		c = (colour.r / 255, colour.g / 255, colour.b / 255, colour.a / 255)
		self.shape(rect, r, grad=vgrad(y, h, [(0.0, mix(c, (1.0, 1.0, 1.0, c[3]), 0.18)), (1.0, c)]))
		self.ring("top", rect, r, (1.0, 1.0, 1.0, 0.45))
		self.ring("outer", rect, r, (0.0, 0.0, 0.0, 0.35))

	def button(self, rect, hover: bool) -> None:
		"""A glass push button."""
		r = rect[3] / 2
		self.selection(rect, r)
		if hover:
			self.shape(rect, r, self.HOVER)

	@contextmanager
	def _on(self, renderer):
		"""Draw meshes on another renderer (a popup window's) for a while."""
		if renderer is None:
			yield
			return
		old = self.renderer
		self.renderer = renderer
		try:
			yield
		finally:
			self.renderer = old

	def menu_bg(self) -> ColourRGBA:
		"""The colour menu text and glyphs are worked out against."""
		c = to_colour(self.MENU_SOLID)
		return ColourRGBA(c.r, c.g, c.b, 200)

	def menu_glass(self, rect, renderer=None, *, dialog: bool = False) -> None:
		"""A context menu's glass: frosted sky in the main window, or a solid
		pane of the same glass in a popup window (textures belong to the main
		renderer, so the popup's is meshes only). A dialog is rounder and
		floats higher."""
		x, y, w, h = (round(v) for v in rect)
		if w < 4 or h < 4:
			return
		R = min(self.s(self.DIALOG_RADIUS if dialog else self.MENU_RADIUS), w / 2, h / 2)
		ri = max(0.0, R - 1)
		sh = min(h - 2, self.s(28))
		top = self.SHEEN_TOP
		sheen = vgrad(y + 1, sh, [(0.0, top), (1.0, (top[0], top[1], top[2], 0.0))])
		if renderer is None:
			sc = self.gui.scale
			if dialog:
				# 0 18px 40px -8px
				self.soft((x, y, w, h), R, 20 * sc, -8 * sc, self.SHADOW, 0, 18 * sc)
			else:
				self.soft((x, y, w, h), R, 12 * sc, -4 * sc, self.SHADOW, 0, 9 * sc)
			uv = self.frost_uv()
			for tex, alpha in self.frost_layers():
				sdl3.set_texture_blend_mode(tex, sdl3.SDL_BLENDMODE_NONE if alpha >= 1.0 else sdl3.SDL_BLENDMODE_BLEND)
				self.shape((x, y, w, h), R, (1.0, 1.0, 1.0, alpha), texture=tex, uv=uv)
			self.shape((x, y, w, h), R, self.MENU_TINT)
			self.shape((x + 1, y + 1, w - 2, sh), (ri, ri, 0, 0), grad=sheen)
			self.ring("inner", (x, y, w, h), R, self.RIM_SOFT)
			self.ring("top", (x, y, w, h), R, self.RIM)
			self.ring("outer", (x, y, w, h), R, self.EDGE)
			return
		base = self.MENU_SOLID
		a = self.MENU_POPUP_ALPHA
		top_c = mix(base, (1.0, 1.0, 1.0, 1.0), 0.07)
		with self._on(renderer):
			self.band((x, y, w, h), R, 1.0, mix(base, (0.0, 0.0, 0.0, 1.0), 0.55)[:3] + (0.92,))
			self.shape((x + 1, y + 1, w - 2, h - 2), ri, grad=vgrad(y, h, [
				(0.0, top_c[:3] + (a,)), (1.0, base[:3] + (a,))]))
			self.shape((x + 1, y + 1, w - 2, sh), (ri, ri, 0, 0), grad=sheen)
			self.shape((x + R, y + 1, w - 2 * R, max(1.0, self.s(1))), 0, self.RIM)

	def band(self, rect, R: float, t: float, colour: RGBA) -> None:
		"""A rounded rect's border, t px wide, as one mesh: unlike a filled
		shape under an inset one, nothing shows through a translucent fill."""
		x, y, w, h = rect
		seg = max(6, min(16, round(R / 1.2)))
		outer = rounded_poly(x, y, w, h, (R, R, R, R), seg)
		ri = max(0.0, R - t)
		inner = rounded_poly(x + t, y + t, w - 2 * t, h - 2 * t, (ri, ri, ri, ri), seg)
		if len(outer) != len(inner):
			return
		n = len(outer)
		verts = []
		for (ox, oy), (ix, iy) in zip(outer, inner):
			verts.append((ox, oy, 0.0, 0.0, *colour))
			verts.append((ix, iy, 0.0, 0.0, *colour))
		idx = []
		for i in range(n):
			j = (i + 1) % n
			idx += (2 * i, 2 * j, 2 * i + 1, 2 * i + 1, 2 * j, 2 * j + 1)
		sdl3.set_render_draw_blend_mode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.render_geometry(self.renderer, None, verts, idx)

	def accent_colour(self) -> ColourRGBA:
		"""The accent as a theme colour (Obsidian's highlight accent there)."""
		return to_colour(mix(hsl(self.acc, 0.85, 0.6), hsl(self.oacc, 0.85, 0.62), self.mono))

	def tile(self, rect, r: float, hover: bool) -> None:
		"""A glass button face: the selection pill, fainter at rest."""
		x, y, w, h = rect
		k = 1.0 if hover else 0.55
		top, bot = self.SEL_TOP, self.SEL_BOT
		self.shape(rect, r, grad=vgrad(y, h, [
			(0.0, (top[0], top[1], top[2], top[3] * k)), (1.0, (bot[0], bot[1], bot[2], bot[3] * k))]))
		self.ring("top", rect, r, self.RIM if hover else self.RIM_SOFT)
		self.ring("outer", rect, r, self.SEL_EDGE)

	GLOW_RADIUS = 3.5   # logical px of blur in the text halo on the playing gel
	GLOW_ALPHA = 0.6

	def text_glow(self) -> tuple[ColourRGBA, float]:
		"""(colour, radius) for ddt.text_glow on the playing row: a deep shade
		of the gel's own hue, so bright gels darken just around the letters."""
		obs = 1.0 if self._mono_applied == 1 else 0.0
		c = mix(hsl(self.target[2], 0.8, 0.12, self.GLOW_ALPHA), (0.0, 0.0, 0.0, self.GLOW_ALPHA * 0.7), obs)
		return to_colour(c), self.s(self.GLOW_RADIUS)

	def menu_hover(self, rect, renderer=None) -> None:
		"""The hovered item: the tracklist's selection pill."""
		r = self.s(5)
		if renderer is None:
			self.selection(rect, r)
			return
		y, h = rect[1], rect[3]
		with self._on(renderer):
			self.shape(rect, r, grad=vgrad(y, h, [(0.0, self.SEL_TOP), (1.0, self.SEL_BOT)]))

	def menu_rule(self, x: float, y: float, w: float, renderer=None) -> None:
		"""A menu break's hairline."""
		with self._on(renderer):
			self.shape((x + self.s(10), y, w - self.s(20), max(1.0, self.s(1))), 0, self.STAR)

	def flush_glints(self) -> None:
		"""Draw the queued glints over everything drawn since the panels."""
		glints = self._glints
		self._glints = []
		for rect, R, index in glints:
			self._glint(rect, R, index)

	GLINT_ALPHA = 0.3   # peak of the light sweep on a colour change (the concept had .5)

	def _glint(self, rect, R: float, index: int) -> None:
		"""linear-gradient(105deg, transparent 38%, white .5 50%, transparent
		62%) at 260% width, swept from 140% to -40% in 1s, staggered 80ms per
		panel, eased cubic-bezier(.35,.6,.2,1)."""
		el = time.monotonic() - self.glint_start - index * 0.08
		if el < 0 or el > 1.0:
			return
		k = _bezier(0.35, 0.6, 0.2, 1.0, el)
		x, y, w, h = rect
		bw = w * 2.6
		pos = 1.4 + (-0.4 - 1.4) * k
		ox = (w - bw) * pos
		box = (x + ox, y, bw, h)
		g = Gradient(box, 105, [
			(0.0, (1, 1, 1, 0)), (0.38, (1, 1, 1, 0)), (0.5, (1, 1, 1, self.GLINT_ALPHA)),
			(0.62, (1, 1, 1, 0)), (1.0, (1, 1, 1, 0))])
		self.shape(rect, R, grad=g)

	# -- elements -------------------------------------------------------------------------------

	def hover_row(self, rect, r: float | None = None) -> None:
		self.shape(rect, self.s(6) if r is None else r, self.HOVER)

	def selection(self, rect, r: float | None = None) -> None:
		"""Glass pill: the selected row, mode toggles, active tabs."""
		r = self.s(6) if r is None else r
		x, y, w, h = rect
		self.shape(rect, r, grad=vgrad(y, h, [(0.0, self.SEL_TOP), (1.0, self.SEL_BOT)]))
		self.ring("top", rect, r, self.RIM)
		self.ring("outer", rect, r, self.SEL_EDGE)

	def gel(self, rect, r: float | None = None, hue: float | None = None, glow: bool = True) -> None:
		"""The playing row's gel: a hard step at the midline."""
		r = self.s(6) if r is None else r
		H = self.acc if hue is None else hue
		m = self.mono if hue is None else 0.0
		A = self.oacc
		x, y, w, h = rect
		sc = self.gui.scale
		if glow:
			# 0 3px 12px -3px glow; Obsidian's in the accent
			self.soft(rect, r, 6 * sc, -3 * sc, mix(hsl(H, 0.95, 0.45, 0.7), hsl(A, 0.9, 0.55, 0.6), m), 0, 3 * sc)
		# Obsidian: a graphite gel, with the same hard step
		obs = (rgba8(107, 114, 125), rgba8(71, 77, 86), rgba8(42, 46, 52), rgba8(59, 64, 71))
		dusk = (hsl(H, 0.85, 0.64), hsl(H, 0.82, 0.52), hsl(H, 0.90, 0.41), hsl(H, 0.85, 0.50))
		stops = [(p, mix(dusk[i], obs[i], m)) for i, p in enumerate((0.0, 0.5, 0.51, 1.0))]
		self.shape(rect, r, grad=vgrad(y, h, stops))
		self.ring("top", rect, r, (1, 1, 1, 0.65 - 0.1 * m))
		if m > 0:
			# An accent lip along the bottom
			self.ring("bottom_in", rect, r, hsl(A, 0.9, 0.62, 0.7 * m))
		self.ring("outer", rect, r, mix(hsl(H, 0.80, 0.28, 0.7), rgba8(0, 0, 0, 0.72), m))

	def tab(self, rect, active: bool, hover: bool) -> None:
		r = self.s(7)
		x, y, w, h = rect
		if active:
			self.shape(rect, r, self.TAB)
			self.ring("top", rect, r, self.RIM)
			self.ring("outer", rect, r, self.SEL_EDGE)
			# Accent underline with its glow
			ux = x + self.s(12)
			uw = w - self.s(24)
			uh = max(1.0, self.s(2))
			uy = y + h + self.s(1) - uh
			col = mix(hsl(self.acc, 0.95, 0.55), hsl(self.oacc, 0.9, 0.64), self.mono)
			glow = mix(col, hsl(self.oacc, 0.9, 0.58), self.mono)
			self.soft((ux, uy, uw, uh), uh / 2, 4 * self.gui.scale, 0, glow)
			self.shape((ux, uy, uw, uh), uh / 2, col)
		elif hover:
			self.shape(rect, r, self.HOVER)

	def tab_rect(self, rect) -> tuple[float, float, float, float]:
		"""Tabs are pills with a little space around them."""
		x, y, w, h = rect
		return (x + self.s(1), y + self.s(1), w - self.s(2), h - self.s(2))

	def tab_playing_mark(self, rect) -> None:
		"""A small lit dot in the tab that playback comes from."""
		x, y, w, h = rect
		d = self.s(4)
		H = _hue_lerp(self.acc, self.oacc, self.mono)
		self.soft((x + w - self.s(7) - d, y + self.s(5), d, d), d / 2, 2 * self.gui.scale, 0, hsl(H, 1.0, 0.6, 0.8))
		self.shape((x + w - self.s(7) - d, y + self.s(5), d, d), d / 2, hsl(H, 0.9, 0.75))

	def sunken(self, rect, r: float) -> None:
		"""A recessed track: sunken fill, inner shadow, ring and lower lip."""
		self.shape(rect, r, self.SUNKEN)
		m = self.mono
		self.ring("inset_top_shadow", rect, r, mix(rgba8(0, 20, 40, 0.35), rgba8(0, 0, 0, 0.45), m))
		self.ring("inner", rect, r, mix(rgba8(0, 20, 40, 0.18), rgba8(0, 0, 0, 0.25), m))
		self.ring("bottom_out", rect, r, self.RIM_SOFT)

	def tube(self, rect, frac: float, *, playing: bool = False, shimmer: bool = True,
			bead: bool = True, bubbles: bool = False, hover: bool = False) -> None:
		"""A glass tube filled with gel to `frac`, with the bead at the fill's end."""
		x, y, w, h = rect
		r = h / 2
		sc = self.gui.scale
		H = self.acc
		self.sunken(rect, r)
		fw = max(0.0, min(w, w * frac))
		r_ = self.renderer
		if fw >= 1:
			clip = sdl3.Rect(round(x), round(y), round(w), round(h))
			old_clip = sdl3.get_render_clip_rect(r_)
			fr = (x, y, fw, h)
			sdl3.set_render_clip_rect(r_, clip)
			m = self.mono
			A = self.oacc
			# 0 0 10px glow, clipped by the tube
			self.soft(fr, min(r, fw / 2), 5 * sc, 0, mix(hsl(H, 0.95, 0.55, 0.65), hsl(A, 0.9, 0.60, 0.45), m))
			# Obsidian: mercury, lit by the accent at its end
			obs = (rgba8(245, 247, 250), rgba8(188, 196, 206), rgba8(133, 142, 153), rgba8(206, 212, 219))
			dusk = (hsl(H, 0.92, 0.74), hsl(H, 0.85, 0.56), hsl(H, 0.90, 0.44), hsl(H, 0.85, 0.58))
			stops = [(p, mix(dusk[i], obs[i], m)) for i, p in enumerate((0.0, 0.5, 0.51, 1.0))]
			rr = min(r, fw / 2)
			self.shape(fr, rr, grad=vgrad(y, h, stops))
			self.ring("top", fr, rr, (1, 1, 1, 0.75 + 0.25 * m))
			self.ring("right_in", fr, rr, mix((1, 1, 1, 0.4), hsl(A, 0.9, 0.75, 0.8), m))
			now = time.monotonic()
			if shimmer and playing and self.motion():
				# A 70px band travelling the whole tube at a constant speed,
				# lit only where the gel is: its pace and position don't
				# depend on how full the tube is
				bw = 70 * sc
				span = w + 150 * sc
				bx = x - 80 * sc + (now * self.SHIMMER_SPEED * sc) % span
				band = Gradient((bx, y, bw, h), 90, [
					(0.0, (1, 1, 1, 0)), (0.5, (1, 1, 1, 0.6)), (1.0, (1, 1, 1, 0))])
				self.shape(fr, rr, grad=band, cuts=[(1, 0, bx), (1, 0, bx + bw)])
			if bubbles:
				self._bubbles(fr, now, playing)
			sdl3.set_render_clip_rect(r_, old_clip)
		if playing:
			# Keep frames coming so the fill advances smoothly (with or
			# without ambient motion)
			self.schedule(1 / self.FPS)
		if bead:
			self.bead(x + fw, y + h / 2)

	def _bubbles(self, fr, now: float, playing: bool) -> None:
		x, y, fw, h = fr
		sc = self.gui.scale
		if playing and self.motion() and fw > 24 * sc and now >= self._bubble_next:
			self._bubble_next = now + 0.26
			# Born at a fixed distance along the tube, so they stay put as
			# the gel grows or shrinks around them
			self.bubbles.append({
				"t": now, "off": random.random() * max(0.0, fw - 22 * sc),
				"size": (2 + random.random() * 2.5) * sc,
				"top": (5 + random.random() * 4) * sc})
		keep = []
		spr = self._bubble_tex()
		for b in self.bubbles:
			k = (now - b["t"]) / 1.8
			if k >= 1:
				continue
			keep.append(b)
			e = 1 - (1 - k) ** 2   # ease-out
			a = (k / 0.25) * 0.95 if k < 0.25 else 0.95 * (1 - (k - 0.25) / 0.75)
			bx = x + b["off"] + 18 * sc * e
			if bx > x + fw:
				# A seek back left it outside the gel
				continue
			by = y + b["top"] + (6 - 15 * e) * sc
			_mod(spr.tex, 255, 255, 255, round(a * 255))
			sz = b["size"]
			sdl3.render_texture(self.renderer, spr.tex, None, sdl3.FRect(bx, by - sz / 2, sz, sz))
		self.bubbles = keep
		if keep:
			self.schedule(1 / self.FPS)

	def _bubble_tex(self) -> _Tex:
		t = self._misc.get("bubble")
		if t is None:
			n = 24
			tt = _radial_l((n, n), n * 0.35, n * 0.3, n * 0.95, n * 0.95)
			stops = [(0.0, (1, 1, 1, 1)), (0.6, (1, 1, 1, 0.35)), (1.0, (1, 1, 1, 0.1))]
			img = _map_stops(tt, stops)
			img.putalpha(ImageChops.multiply(img.getchannel("A"), _ellipse_mask((n, n), (0, 0, n, n))))
			t = _Tex(self._make_tex(img), n, n)
			self._misc["bubble"] = t
		return t

	# -- rasterised pieces: orbs, bead, LED --------------------------------------------------------

	RASTER_BUDGET = 0.004   # seconds of hue-driven re-rasterising per frame

	def _cached(self, key, build, hue_slot: int | None = None) -> _Tex:
		"""A cached raster. Keys whose `hue_slot` entry is a hue are rebuilt as
		the palette moves; past the per-frame budget the nearest hue already
		built stands in, so a colour change never stalls a frame."""
		t = self._orbs.get(key)
		if t is not None:
			self._orbs.move_to_end(key)
			return t
		if hue_slot is not None and self._raster_spent > self.RASTER_BUDGET:
			best = None
			for k, cand in self._orbs.items():
				if len(k) == len(key) and all(k[i] == key[i] for i in range(len(key)) if i != hue_slot):
					dist = abs(((k[hue_slot] - key[hue_slot] + 540) % 360) - 180)
					if best is None or dist < best[0]:
						best = (dist, cand)
			# Only a near hue: the traffic lights share sizes but not colours
			if best is not None and best[0] <= 40:
				# Come back for the exact one next frame
				self.schedule(1 / self.FPS_FAST)
				return best[1]
		started = time.perf_counter()
		img, pad = build()
		if hue_slot is not None:
			self._raster_spent += time.perf_counter() - started
		t = _Tex(self._make_tex(img), img.width, img.height, 0, 0, pad)
		self._orbs[key] = t
		while len(self._orbs) > 96:
			_k, old = self._orbs.popitem(last=False)
			sdl3.destroy_texture(old.tex)
		return t

	def _orb_image(self, d: int, H: float, hover: bool, obs: bool = False) -> tuple[Image.Image, int]:
		"""A gel orb in hue H, or with `obs`, Obsidian's black lacquer whose
		caustic and inner glow take H."""
		sc = self.gui.scale
		pad = math.ceil(30 * sc) + 2
		N = d + pad * 2
		size = (N, N)
		c0 = pad
		circle = _ellipse_mask(size, (c0, c0, c0 + d, c0 + d))
		canvas = Image.new("RGBA", size, (0, 0, 0, 0))
		# Hover lights the orb from inside (body, caustic, inner glow and rim
		# all brighter) rather than throwing a halo around it
		drop = _outer_shadow(circle, 0, 3 * sc, 4 * sc)
		canvas = Image.alpha_composite(canvas, _solid(size, rgba8(0, 0, 0, 0.6) if obs else rgba8(0, 25, 50, 0.45), drop))
		outer = ImageChops.subtract(_ellipse_mask(size, (c0 - 1, c0 - 1, c0 + d + 1, c0 + d + 1)), circle)
		canvas = Image.alpha_composite(canvas, _solid(size, rgba8(0, 0, 0, 0.78) if obs else rgba8(0, 25, 50, 0.55), outer))
		# Body: radial-gradient(circle at 50% 35%, ...) to the farthest corner
		R = d * math.hypot(0.5, 0.65)
		t = _radial_l(size, c0 + d * 0.5, c0 + d * 0.35, R, R)
		if obs:
			body_stops = [(0.0, rgba8(75, 81, 91)), (0.62, rgba8(29, 32, 38)), (1.0, rgba8(8, 9, 11))]
		else:
			body_stops = [(0.0, hsl(H, 0.75, 0.48)), (0.62, hsl(H, 0.85, 0.30)), (1.0, hsl(H, 0.90, 0.16))]
		body = _map_stops(t, body_stops)
		# Caustic over it: ellipse 60% 45% at 50% 92%
		reach = 0.82 if hover else 0.7
		t2 = _radial_l(size, c0 + d * 0.5, c0 + d * 0.92, d * 0.6, d * 0.45)
		if obs:
			cs, cl, ca = 0.85, 0.66, (0.7 if hover else 0.55)
		else:
			cs, cl, ca = 1.0, (0.80 if hover else 0.78), (1.0 if hover else 0.9)
		caustic = _map_stops(t2, [
			(0.0, hsl(H, cs, cl, ca)), (reach, hsl(H, cs, cl, 0.0)), (1.0, hsl(H, cs, cl, 0.0))])
		body = Image.alpha_composite(body, caustic)
		body.putalpha(ImageChops.multiply(body.getchannel("A"), circle))
		canvas = Image.alpha_composite(canvas, body)
		# inset 0 -2px 4px glow, then the 1px inner ring
		ig = _inset_shadow(circle, 0, -2 * sc, (3 if hover else 2) * sc)
		if obs:
			glow_c = hsl(H, 0.9, 0.70, 0.45 if hover else 0.3)
			ring_c = rgba8(240, 245, 252, 0.5) if hover else rgba8(230, 236, 245, 0.36)
		else:
			glow_c = hsl(H, 1.0, 0.80, 0.6 if hover else 0.35)
			ring_c = hsl(H, 0.90, 0.88, 0.7 if hover else 0.45)
		canvas = Image.alpha_composite(canvas, _solid(size, glow_c, ig))
		inner = ImageChops.subtract(circle, _ellipse_mask(size, (c0 + 1, c0 + 1, c0 + d - 1, c0 + d - 1)))
		canvas = Image.alpha_composite(canvas, _solid(size, ring_c, inner))
		if hover:
			# Brighten the glass itself, not the shadow under it
			r, g, b, a = canvas.split()
			lift = _lut(1.12)
			bright = Image.merge("RGBA", (r.point(lift), g.point(lift), b.point(lift), a))
			canvas = Image.composite(bright, canvas, circle)
		return canvas, pad

	def _cap_image(self, d: int, pressed: bool) -> tuple[Image.Image, int]:
		"""The specular cap: left/right 15%, top 4% (8% pressed), height 48%
		(40%), radius 50% 50% 45% 45% / 60% 60% 40% 40%, white .92 -> .16."""
		ss = 4
		bw = d * 0.70
		top = d * (0.08 if pressed else 0.04)
		bh = d * (0.40 if pressed else 0.48)
		big = Image.new("L", (d * ss, d * ss), 0)
		x0 = d * 0.15 * ss
		y0 = top * ss
		W = bw * ss
		Hh = bh * ss
		# Upper: half an ellipse spanning the full width, 60% of the height deep
		upper = Image.new("L", big.size, 0)
		ImageDraw.Draw(upper).ellipse([x0, y0, x0 + W, y0 + 1.2 * Hh], fill=255)
		upper.paste(0, (0, round(y0 + 0.6 * Hh), big.width, big.height))
		big = ImageChops.lighter(big, upper)
		# Lower: two 45%x40% corners and a flat 10% between them
		lower = Image.new("L", big.size, 0)
		ld = ImageDraw.Draw(lower)
		ld.ellipse([x0, y0 + 0.2 * Hh, x0 + 0.9 * W, y0 + Hh], fill=255)
		ld.ellipse([x0 + 0.1 * W, y0 + 0.2 * Hh, x0 + W, y0 + Hh], fill=255)
		ld.rectangle([x0 + 0.45 * W, y0 + 0.6 * Hh, x0 + 0.55 * W, y0 + Hh], fill=255)
		lower.paste(0, (0, 0, big.width, round(y0 + 0.6 * Hh)))
		big = ImageChops.lighter(big, lower)
		mask = big.reduce(ss)
		grad = Image.new("L", (1, d))
		px = grad.load()
		for yy in range(d):
			k = min(1.0, max(0.0, (yy + 0.5 - top) / max(1.0, bh)))
			px[0, yy] = round(255 * (0.92 + (0.16 - 0.92) * k) * (0.75 if pressed else 1.0))
		alpha = ImageChops.multiply(mask, grad.resize((d, d)))
		img = Image.new("RGBA", (d, d), (255, 255, 255, 0))
		img.putalpha(alpha)
		return img, 0

	def _blit(self, t: _Tex, x: float, y: float, alpha: float = 1.0) -> None:
		"""Draw a cached raster with its top-left (less its pad) at (x, y)."""
		_mod(t.tex, 255, 255, 255, round(alpha * 255))
		sdl3.render_texture(self.renderer, t.tex, None, sdl3.FRect(x - t.pad, y - t.pad, t.w, t.h))

	def _orb_body(self, x: int, y: int, d: int, hover: bool, hue: float | None) -> None:
		"""The orb under its glyph: the gel, or Obsidian's lacquer faded in
		over it. An explicit hue (the traffic lights) is never Obsidian."""
		m = self.mono if hue is None else 0.0
		if m < 1:
			hq = round((self.acc if hue is None else hue) / 2) * 2
			self._blit(self._cached(("orb", d, hq, hover), lambda: self._orb_image(d, hq, hover), 2), x, y)
		if m > 0:
			oq = round(self.oacc / 2) * 2
			t = self._cached(("orb_obs", d, oq, hover), lambda: self._orb_image(d, oq, hover, obs=True), 2)
			self._blit(t, x, y, min(1.0, m))

	def _glyph_shadow(self, hue: float | None) -> ColourRGBA:
		return to_colour(mix(rgba8(0, 30, 60, 0.6), rgba8(0, 0, 0, 0.6), self.mono if hue is None else 0.0))

	def _orb_glow(self, x: int, y: int, d: int, strength: float = 1.0) -> None:
		"""0 0 14px of the accent around the transport's hero orb."""
		c = mix(hsl(self.acc, 0.9, 0.55, 0.45 * strength), hsl(self.oacc, 0.9, 0.6, 0.4 * strength), self.mono)
		self.soft((x, y, d, d), d / 2, 7 * self.gui.scale, 0, c)

	def orb(self, cx: float, cy: float, d: float, glyph=None, *, hover: bool = False,
			pressed: bool = False, hue: float | None = None, glow: bool = False) -> None:
		"""A gel orb centred on (cx, cy). `glyph` is an icon asset drawn white
		under the cap, with the concept's 1px drop shadow. `glow` adds the
		hero orb's accent glow."""
		d = max(6, round(d))
		x = round(cx - d / 2)
		y = round(cy - d / 2)
		if glow:
			self._orb_glow(x, y, d)
		self._orb_body(x, y, d, hover, hue)
		if glyph is not None:
			gx = round(cx - glyph.w / 2)
			gy = round(cy - glyph.h / 2)
			sh = max(1, round(self.gui.scale))
			glyph.render(gx, gy + sh, self._glyph_shadow(hue))
			glyph.render(gx, gy, ColourRGBA(255, 255, 255, 255))
		cap = self._cached(("cap", d, pressed), lambda: self._cap_image(d, pressed))
		sdl3.render_texture(self.renderer, cap.tex, None, sdl3.FRect(x, y, d, d))

	def orb_glyph(self, cx: float, cy: float, d: float, draw_glyph, *, hover: bool = False,
			pressed: bool = False, hue: float | None = None, glow: bool = False) -> None:
		"""Like orb(), but the glyph is drawn by a callback (colour) -> None."""
		d = max(6, round(d))
		x = round(cx - d / 2)
		y = round(cy - d / 2)
		if glow:
			self._orb_glow(x, y, d)
		self._orb_body(x, y, d, hover, hue)
		draw_glyph(max(1, round(self.gui.scale)), self._glyph_shadow(hue))
		draw_glyph(0, ColourRGBA(255, 255, 255, 255))
		cap = self._cached(("cap", d, pressed), lambda: self._cap_image(d, pressed))
		sdl3.render_texture(self.renderer, cap.tex, None, sdl3.FRect(x, y, d, d))

	# -- the liquid play orb ------------------------------------------------------------

	PLAYTIME_FULL = 180.0  # a track's total play time (seconds) that fills the orb
	CATCH_UP = 0.5     # orbs per second the level moves after a track change
	DRAIN_TIME = 1.5   # seconds to drain a full orb when playback stops
	EASE_ZONE = 0.15   # within this of its target the level slows down
	FILL_LEVEL = 1.0   # full is this much of the orb's height

	def _fill_target(self) -> float:
		pctl = self.tauon.pctl
		if pctl.playing_state == PlayingState.STOPPED:
			return 0.0
		track = pctl.playing_object()
		if track is None:
			return 0.0
		return min(1.0, self.tauon.star_store.get(track.index) / self.PLAYTIME_FULL)

	def _step_fill(self, dt: float) -> bool:
		"""Move the liquid toward the playing track's total play time (a
		pause holds it; a stop drains it). Small gaps, like the play time
		growing as it plays, are taken at once without asking for frames; a
		new track's level is reached quickly. True while animating."""
		target = self._fill_target()
		gap = target - self.fill
		# Starts past a visible gap, then runs until it has all but arrived
		animating = abs(gap) > (0.003 if self._catching else 0.02)
		self._catching = animating
		if animating:
			if self.tauon.pctl.playing_state == PlayingState.STOPPED:
				top = 1 / self.DRAIN_TIME
			else:
				top = self.CATCH_UP
			# Eased: the speed builds up, and tapers off near the target
			speed = top * max(0.08, min(1.0, abs(gap) / self.EASE_ZONE))
			want = math.copysign(speed, gap)
			self._fill_v += (want - self._fill_v) * min(1.0, dt * 6)
			step = self._fill_v * dt
			self.fill = min(target, self.fill + step) if gap > 0 else max(target, self.fill + step)
		else:
			self.fill = target
			self._fill_v = 0.0
		self._slosh += ((1.0 if animating else 0.0) - self._slosh) * min(1.0, dt * 3)
		return animating or self._slosh > 0.01

	def liquid_orb(self, cx: float, cy: float, d: float, glyph=None, *, hover: bool = False,
			pressed: bool = False, draw_glyph=None) -> None:
		"""The play button: the menu marble's clear glass, part filled with
		the accent as playback runs. `glyph` is an icon asset, or
		`draw_glyph(offset, colour)` draws it."""
		d = max(8, round(d))
		ox = round(cx - d / 2)
		oy = round(cy - d / 2)
		level = self.fill
		if level > 0.02:
			self._orb_glow(ox, oy, d, 0.3 + 0.7 * level)
		for part, index in (("under", 0), ("liquid", -1), ("glyph", -1), ("over", 2)):
			if part == "liquid":
				self._liquid(cx, cy, d, level, hover)
			elif part == "glyph":
				shadow = self._glyph_shadow(None)
				sh = max(1, round(self.gui.scale))
				if draw_glyph is not None:
					draw_glyph(sh, shadow)
					draw_glyph(0, ColourRGBA(255, 255, 255, 255))
				elif glyph is not None:
					gx = round(cx - glyph.w / 2)
					gy = round(cy - glyph.h / 2)
					glyph.render(gx, gy + sh, shadow)
					glyph.render(gx, gy, ColourRGBA(255, 255, 255, 255))
			else:
				t = self._cached(("menu_icon", part, d, hover, pressed),
					lambda i=index: self._menu_icon_part(d, hover, pressed, i))
				sdl3.render_texture(self.renderer, t.tex, None, sdl3.FRect(ox - t.pad, oy - t.pad, t.w, t.h))

	def _liquid(self, cx: float, cy: float, d: int, level: float, hover: bool) -> None:
		"""The accent liquid inside the orb: a circle cut by its (rocking)
		surface, a bright meniscus and, while playing, rising bubbles."""
		if level <= 0.005:
			return
		sc = self.gui.scale
		R = d / 2 - max(1.0, 1.2 * sc)
		h = level * self.FILL_LEVEL * 2 * R
		y0 = cy + R - h
		now = time.monotonic()
		tilt = 0.12 * self._slosh * math.sin(now * 6.5)

		def depth(px: float, py: float) -> float:
			return py - (y0 + tilt * (px - cx))

		n = 48
		ring = [(cx + R * math.cos(math.tau * i / n), cy + R * math.sin(math.tau * i / n)) for i in range(n)]
		poly: list[tuple[float, float]] = []
		chord: list[tuple[float, float]] = []
		for i in range(n):
			p, q = ring[i], ring[(i + 1) % n]
			fp, fq = depth(*p), depth(*q)
			if fp >= 0:
				poly.append(p)
			if (fp >= 0) != (fq >= 0):
				t = fp / (fp - fq)
				pt = (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)
				poly.append(pt)
				chord.append(pt)
		if len(poly) < 3:
			return
		m = self.mono
		H, A = self.acc, self.oacc
		stops = [
			(0.0, mix(hsl(H, 0.80, 0.70), hsl(A, 0.75, 0.68), m)),
			(0.3, mix(hsl(H, 0.85, 0.50), hsl(A, 0.85, 0.52), m)),
			(1.0, mix(hsl(H, 0.90, 0.28), hsl(A, 0.80, 0.30), m)),
		]
		if hover:
			stops = [(t, mix(c, (1.0, 1.0, 1.0, 1.0), 0.12)) for t, c in stops]
		top = min(p[1] for p in poly)
		span = max(1.0, cy + R - top)

		def colour(py: float) -> tuple:
			c = _stop_at(stops, (py - top) / span)
			return (c[0], c[1], c[2], 0.94)

		mx = sum(p[0] for p in poly) / len(poly)
		my = sum(p[1] for p in poly) / len(poly)
		verts = [(mx, my, 0.0, 0.0, *colour(my))]
		verts += [(px, py, 0.0, 0.0, *colour(py)) for px, py in poly]
		idx = []
		for i in range(len(poly)):
			idx += (0, 1 + i, 1 + (i + 1) % len(poly))
		sdl3.set_render_draw_blend_mode(self.renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.render_geometry(self.renderer, None, verts, idx)

		# Meniscus: a bright band just under the surface, short of the walls
		if len(chord) == 2:
			(ax, ay), (bx, by) = sorted(chord)
			ix, iy = (bx - ax) * 0.08, (by - ay) * 0.08
			ax, ay, bx, by = ax + ix, ay + iy, bx - ix, by - iy
			band = max(1.5, 2.5 * sc)
			hi = (1.0, 1.0, 1.0, 0.75)
			lo = (1.0, 1.0, 1.0, 0.0)
			verts = [(ax, ay, 0, 0, *hi), (bx, by, 0, 0, *hi), (bx, by + band, 0, 0, *lo), (ax, ay + band, 0, 0, *lo)]
			sdl3.render_geometry(self.renderer, None, verts, [0, 1, 2, 0, 2, 3])

		# Bubbles rising through it while playing (still, without ambient motion)
		if level > 0.2 and self.tauon.pctl.playing_state == PlayingState.PLAYING:
			spr = self._bubble_tex()
			moving = self.motion()
			clock = now if moving else 0.0
			for i in range(3):
				ph = (clock * 0.3 + i / 3) % 1.0
				by = cy + R - 2 * sc - ph * (h - 4 * sc)
				half = math.sqrt(max(0.0, R * R - (by - cy) ** 2)) * 0.6
				bx = cx + half * math.sin(i * 2.4 + clock * 0.8 + ph * 2.5)
				sz = d * (0.07 + 0.025 * i)
				a = 0.8 * min(1.0, ph * 5, (1 - ph) * 5)
				if depth(bx, by - sz / 2) <= 0 or a <= 0:
					continue
				_mod(spr.tex, 255, 255, 255, round(a * 255))
				sdl3.render_texture(self.renderer, spr.tex, None, sdl3.FRect(bx - sz / 2, by - sz / 2, sz, sz))
			if moving:
				self.schedule(1 / self.FPS)

	def ghost(self, cx: float, cy: float, d: float, glyph=None, *, hover: bool = False,
			pressed: bool = False, draw_glyph=None) -> None:
		"""A secondary transport button: the glyph etched straight on the
		glass, with a faint glass disc behind it only on hover. `glyph` is an
		icon asset, or `draw_glyph(offset, colour)` draws it."""
		d = max(6, round(d))
		r = d / 2
		rect = (round(cx - r), round(cy - r), d, d)
		if hover or pressed:
			k = 0.7 if pressed else 1.0
			self.shape(rect, r, grad=vgrad(rect[1], d, [(0.0, (1, 1, 1, 0.16 * k)), (1.0, (1, 1, 1, 0.04 * k))]))
			self.ring("top", rect, r, (1.0, 1.0, 1.0, 0.4 * k))
			self.ring("outer", rect, r, mix(rgba8(0, 10, 25, 0.4), rgba8(0, 0, 0, 0.5), self.mono))
		shadow = to_colour(mix(rgba8(0, 8, 20, 0.75), rgba8(0, 0, 0, 0.8), self.mono))
		t = self.TEXT
		colour = to_colour(t if hover else (t[0], t[1], t[2], 0.88))
		sh = max(1, round(self.gui.scale))
		if draw_glyph is not None:
			draw_glyph(sh, shadow)
			draw_glyph(0, colour)
			return
		if glyph is not None:
			gx = round(cx - glyph.w / 2)
			gy = round(cy - glyph.h / 2)
			glyph.render(gx, gy + sh, shadow)
			glyph.render(gx, gy, colour)

	def _bead_image(self, d: int, H: float, obs: bool = False) -> tuple[Image.Image, int]:
		sc = self.gui.scale
		pad = math.ceil(9 * sc) + 2
		N = d + pad * 2
		size = (N, N)
		c0 = pad
		circle = _ellipse_mask(size, (c0, c0, c0 + d, c0 + d))
		canvas = Image.new("RGBA", size, (0, 0, 0, 0))
		shade = rgba8(0, 0, 0, 0.6) if obs else rgba8(0, 30, 60, 0.45)
		drop = _outer_shadow(circle, 0, 2 * sc, 2.5 * sc)
		canvas = Image.alpha_composite(canvas, _solid(size, shade, drop))
		outer = ImageChops.subtract(_ellipse_mask(size, (c0 - 1, c0 - 1, c0 + d + 1, c0 + d + 1)), circle)
		canvas = Image.alpha_composite(canvas, _solid(size, shade, outer))
		R = d * math.hypot(0.5, 0.7)
		t = _radial_l(size, c0 + d * 0.5, c0 + d * 0.3, R, R)
		# Solid all the way out: a see-through bead showed the tube's edge
		# running through it. Same light, the translucent stops resolved
		# over a pale glass tint instead of over whatever is behind
		if obs:
			# Polished metal; the accent only in its lower glow
			stops = [
				(0.0, (1, 1, 1, 1)), (0.18, (1, 1, 1, 1)), (0.40, rgba8(231, 235, 240)),
				(0.70, rgba8(169, 177, 187)), (1.0, rgba8(94, 102, 113))]
			glow_c = hsl(H, 0.9, 0.72, 0.55)
		else:
			stops = [
				(0.0, (1, 1, 1, 1)), (0.18, (1, 1, 1, 1)), (0.40, rgba8(226, 238, 246)),
				(0.70, hsl(H, 0.50, 0.72)), (1.0, hsl(H, 0.62, 0.40))]
			glow_c = hsl(H, 1.0, 0.85, 0.7)
		body = _map_stops(t, stops)
		body.putalpha(ImageChops.multiply(body.getchannel("A"), circle))
		canvas = Image.alpha_composite(canvas, body)
		ig = _inset_shadow(circle, 0, -2 * sc, 1.5 * sc)
		canvas = Image.alpha_composite(canvas, _solid(size, glow_c, ig))
		return canvas, pad

	def bead(self, cx: float, cy: float, d: float | None = None) -> None:
		d = round(self.s(20) if d is None else d)
		x = round(cx - d / 2)
		y = round(cy - d / 2)
		m = self.mono
		if m < 1:
			hq = round(self.acc / 2) * 2
			self._blit(self._cached(("bead", d, hq), lambda: self._bead_image(d, hq), 2), x, y)
		if m > 0:
			oq = round(self.oacc / 2) * 2
			self._blit(self._cached(("bead_obs", d, oq), lambda: self._bead_image(d, oq, obs=True), 2), x, y, m)

	def _led_image(self, d: int, on: bool, H: float | None = None) -> tuple[Image.Image, int]:
		"""Green when on, or lit in hue H (Obsidian's accent)."""
		sc = self.gui.scale
		pad = math.ceil(9 * sc) + 2
		N = d + pad * 2
		size = (N, N)
		c0 = pad
		circle = _ellipse_mask(size, (c0, c0, c0 + d, c0 + d))
		canvas = Image.new("RGBA", size, (0, 0, 0, 0))
		if on:
			glow = circle.filter(ImageFilter.GaussianBlur(3 * sc))
			glow_c = rgba8(109, 255, 61, 1.0) if H is None else hsl(H, 0.95, 0.60)
			canvas = Image.alpha_composite(canvas, _solid(size, glow_c, glow))
		R = d * math.hypot(0.6, 0.65)
		t = _radial_l(size, c0 + d * 0.4, c0 + d * 0.35, R, R)
		if on and H is not None:
			stops = [(0.0, (1, 1, 1, 1)), (0.55, hsl(H, 0.9, 0.66)), (1.0, hsl(H, 0.8, 0.40))]
			ring_c = rgba8(0, 0, 0, 0.25)
		elif on:
			stops = [(0.0, rgba8(234, 255, 216)), (0.55, rgba8(95, 224, 58)), (1.0, rgba8(43, 158, 18))]
			ring_c = rgba8(0, 60, 0, 0.3)
		else:
			stops = [(0.0, rgba8(207, 216, 222)), (1.0, rgba8(123, 138, 149))]
			ring_c = rgba8(0, 0, 0, 0.25)
		body = _map_stops(t, stops)
		body.putalpha(circle)
		canvas = Image.alpha_composite(canvas, body)
		inner = ImageChops.subtract(circle, _ellipse_mask(size, (c0 + 1, c0 + 1, c0 + d - 1, c0 + d - 1)))
		canvas = Image.alpha_composite(canvas, _solid(size, ring_c, inner))
		return canvas, pad

	def led(self, cx: float, cy: float, on: bool) -> None:
		d = max(4, round(self.s(7)))
		x = round(cx - d / 2)
		y = round(cy - d / 2)
		# Off, the LED is grey in both variants; on, Obsidian's accent replaces green
		m = self.mono if on else 0.0
		if m < 1:
			self._blit(self._cached(("led", d, on), lambda: self._led_image(d, on)), x, y)
		if m > 0:
			oq = round(self.oacc / 2) * 2
			self._blit(self._cached(("led_obs", d, oq), lambda: self._led_image(d, True, oq), 2), x, y, m)

	def pill(self, rect, on: bool, hover: bool = False) -> float:
		"""A mode toggle: glass pill with an LED. Returns the x after the LED."""
		x, y, w, h = rect
		self.selection(rect, h / 2)
		if hover:
			self.shape(rect, h / 2, self.HOVER)
		lx = x + self.s(10) + self.s(3.5)
		self.led(lx, y + h / 2, on)
		return lx + self.s(3.5) + self.s(7)

	def menu_orb(self, rect, hover: bool, pressed: bool) -> None:
		"""The main menu button: Tauon's record floating in a glass marble.
		The record is its own layer so it can wobble inside the glass."""
		x, y, w, h = rect
		d = max(8, round(min(h, self.s(26))))
		ox = round(x + w / 2 - d / 2)
		oy = round(y + h / 2 - d / 2)
		angle = self._menu_wobble_angle()
		for i, part in enumerate(("under", "disc", "over")):
			t = self._cached(("menu_icon", part, d, hover, pressed),
				lambda i=i: self._menu_icon_part(d, hover, pressed, i))
			dst = sdl3.FRect(ox - t.pad, oy - t.pad, t.w, t.h)
			if part == "disc" and angle:
				sdl3.render_texture_rotated(self.renderer, t.tex, None, dst, angle, None, 0)
			else:
				sdl3.render_texture(self.renderer, t.tex, None, dst)

	MENU_CAP = 0.55   # strength of the specular cap over the marble
	MENU_GLASS_DESAT = 1.0  # how far the marble's glass is pulled from ice blue to grey
	# The record's wobble on click: degrees, swings per second, decay rate, length
	WOBBLE_ANGLE = 26.0
	WOBBLE_FREQ = 1.9
	WOBBLE_DECAY = 3.2
	WOBBLE_TIME = 1.5

	def menu_wobble(self) -> None:
		"""Set the record in the menu marble wobbling (the menu was opened)."""
		self._wobble_start = time.monotonic()
		self.schedule(1 / self.FPS_FAST)

	def _menu_wobble_angle(self) -> float:
		"""The record's tilt now, in degrees: a damped rock."""
		el = time.monotonic() - getattr(self, "_wobble_start", -10.0)
		if el < 0 or el > self.WOBBLE_TIME:
			return 0.0
		self.schedule(1 / self.FPS_FAST)
		return self.WOBBLE_ANGLE * math.exp(-el * self.WOBBLE_DECAY) * math.sin(math.tau * self.WOBBLE_FREQ * el)

	def _menu_icon_part(self, d: int, hover: bool, pressed: bool, index: int) -> tuple[Image.Image, int]:
		key = (d, hover, pressed)
		layers = getattr(self, "_menu_layers", None)
		if layers is None or layers[0] != key:
			layers = self._menu_layers = (key, self._menu_icon_layers(d, hover, pressed))
		under, disc, over, pad = layers[1]
		return (under, disc, over)[index], pad

	def _menu_icon_layers(self, d: int, hover: bool, pressed: bool) -> tuple[Image.Image, Image.Image, Image.Image, int]:
		"""Tauon's record (assets/svg/app-icon.svg) floating in a clear glass
		marble.

		The record is a thin disc tilted back 52 degrees and rolled slightly:
		its face is an ellipse cos(tilt) tall, and its thickness (3.5% of its
		diameter) shows along the ellipse's minor axis. Light comes from above,
		like the marble's cap: the far rim catches a thin highlight and the
		front of the edge is the darkest part. Its soft shadow follows its
		outline a little below.

		Returns (under: shadow, edge and glass; disc: the record and its
		shadow; over: the glow, inner rim and cap) and the padding."""
		import cairo

		def ice(r: float, g: float, b: float) -> tuple[float, float, float]:
			"""The glass's ice blue, pulled toward grey."""
			lum = 0.3 * r + 0.59 * g + 0.11 * b
			k = self.MENU_GLASS_DESAT
			return (r + (lum - r) * k, g + (lum - g) * k, b + (lum - b) * k)

		def ice8(r: int, g: int, b: int, a: float) -> RGBA:
			c = ice(r / 255, g / 255, b / 255)
			return (c[0], c[1], c[2], a)

		sc = self.gui.scale
		pad = max(math.ceil(12 * sc) + 2, d // 2)
		N = d + pad * 2
		size = (N, N)
		cx = cy = N / 2
		R = d / 2
		rr = R * 0.66
		tilt = math.radians(52)
		roll = -0.22
		squash = math.cos(tilt)
		depth = 0.035 * 2 * rr * math.sin(tilt)
		nx, ny = -math.sin(roll), math.cos(roll)
		lift_y = R * 0.02
		tau = math.tau

		def rgb(h: str) -> tuple[float, float, float]:
			return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))

		def linear(x1: float, y1: float, x2: float, y2: float, stops) -> cairo.LinearGradient:
			g = cairo.LinearGradient(x1, y1, x2, y2)
			for offset, colour in stops:
				g.add_color_stop_rgb(offset, *rgb(colour))
			return g

		def layer() -> tuple[cairo.ImageSurface, cairo.Context]:
			surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, N, N)
			return surf, cairo.Context(surf)

		def to_image(surf: cairo.ImageSurface) -> Image.Image:
			surf.flush()
			img = Image.frombuffer("RGBA", size, bytes(surf.get_data()), "raw", "BGRa", surf.get_stride(), 1).copy()
			surf.finish()
			return img

		def ellipse(cr: cairo.Context, ox: float = 0.0, oy: float = 0.0) -> None:
			cr.save()
			cr.translate(cx + ox, cy + lift_y + oy)
			cr.rotate(roll)
			cr.scale(1, squash)
			cr.arc(0, 0, rr, 0, tau)
			cr.restore()

		# Glass: nearly clear in the middle, brighter toward the rim
		surf, cr = layer()
		g = cairo.RadialGradient(cx, cy - R * 0.25, 0, cx, cy, R)
		g.add_color_stop_rgba(0, *ice(0.75, 0.9, 1.0), 0.10)
		g.add_color_stop_rgba(0.75, *ice(0.55, 0.8, 1.0), 0.22)
		g.add_color_stop_rgba(1, *ice(0.75, 0.92, 1.0), 0.55)
		cr.arc(cx, cy, R, 0, tau)
		cr.set_source(g)
		cr.fill()
		glass = to_image(surf)

		# The record's shadow
		surf, cr = layer()
		ellipse(cr, nx * R * 0.16, ny * R * 0.16 + R * 0.10)
		cr.set_source_rgba(*ice(0, 0.04, 0.12), 0.32)
		cr.fill()
		disc = to_image(surf).filter(ImageFilter.GaussianBlur(max(0.8, d / 18)))

		surf, cr = layer()
		# Its edge: the underside, dark, lighter toward the back
		edge = cairo.LinearGradient(cx - nx * rr, cy - ny * rr * squash, cx + nx * rr, cy + ny * rr * squash)
		edge.add_color_stop_rgb(0, 0.20, 0.20, 0.25)
		edge.add_color_stop_rgb(1, 0.06, 0.06, 0.09)
		ellipse(cr, nx * depth, ny * depth)
		cr.set_source(edge)
		cr.fill()
		# Its face, in the icon's own 210-unit coordinates
		k = rr / 210
		cr.save()
		cr.translate(cx, cy + lift_y)
		cr.rotate(roll)
		cr.scale(k, k * squash)
		cr.arc(0, 0, 210, 0, tau)
		cr.set_source(linear(-190, -205, 195, 210, ((0, "#302f38"), (0.5, "#1d1c24"), (1, "#15151c"))))
		cr.fill()
		if d > 30:
			for radius, alpha in ((201, 0.5), (176, 0.4), (148, 0.35)):
				cr.arc(0, 0, radius, 0, tau)
				cr.set_source_rgba(0.35, 0.34, 0.40, alpha)
				cr.set_line_width(max(2.0, 0.6 / k))
				cr.stroke()
		cr.new_path()
		cr.arc(0, 0, 208.9, math.pi, math.pi * 1.5)
		cr.arc_negative(0, 0, 123, math.pi * 1.5, math.pi)
		cr.close_path()
		cr.set_source(linear(-205, 0, 0, -205, ((0, "#7b3fa5"), (0.27, "#bb4f91"), (0.53, "#e86678"),
			(0.78, "#fa8a55"), (1, "#ffc857"))))
		cr.fill()
		cr.new_path()
		cr.arc(0, 0, 208.9, 0, math.pi * 0.5)
		cr.arc_negative(0, 0, 123, math.pi * 0.5, 0)
		cr.close_path()
		cr.set_source(linear(205, 0, 0, 205, ((0, "#514273"), (0.32, "#506da0"), (0.66, "#45a0bd"), (1, "#62d1c4"))))
		cr.fill()
		cr.arc(0, 0, 83, 0, tau)
		cr.set_source(linear(-80, -80, 80, 80, ((0, "#e86678"), (0.5, "#8b4a9a"), (1, "#45a0bd"))))
		cr.fill()
		cr.arc(0, 0, 73, 0, tau)
		cr.set_source_rgb(*rgb("#17161e"))
		cr.fill()
		cr.arc(0, 0, 18, 0, tau)
		cr.set_source_rgb(*rgb("#e86678"))
		cr.fill()
		# Light from above: a broad faint sheen over the far half, and a thin
		# highlight where the far rim catches it
		sheen = cairo.LinearGradient(0, -210, 0, 210)
		sheen.add_color_stop_rgba(0, 1, 1, 1, 0.16)
		sheen.add_color_stop_rgba(0.55, 1, 1, 1, 0.0)
		cr.arc(0, 0, 210, 0, tau)
		cr.set_source(sheen)
		cr.fill()
		cr.arc(0, 0, 208, 1.15 * math.pi, 1.85 * math.pi)
		cr.set_source_rgba(1, 1, 1, 0.35)
		cr.set_line_width(max(0.6, d / 140) / (k * squash))
		cr.stroke()
		cr.restore()
		disc = Image.alpha_composite(disc, to_image(surf))

		# Light gathered along the bottom of the marble
		surf, cr = layer()
		glow = cairo.RadialGradient(cx, cy + R * 0.85, 0, cx, cy + R * 0.85, R * 0.7)
		glow.add_color_stop_rgba(0, *ice(0.6, 0.95, 1.0), 0.55 if hover else 0.45)
		glow.add_color_stop_rgba(1, *ice(0.6, 0.95, 1.0), 0)
		cr.arc(cx, cy, R, 0, tau)
		cr.clip()
		cr.arc(cx, cy + R * 0.85, R * 0.7, 0, tau)
		cr.set_source(glow)
		cr.fill()
		light = to_image(surf)

		c0 = pad
		circle = _ellipse_mask(size, (c0, c0, c0 + d, c0 + d))
		if hover:
			# Lit from inside, like the other orbs
			lift = _lut(1.15)

			def lit(img: Image.Image) -> Image.Image:
				r, g_, b, a = img.split()
				return Image.merge("RGBA", (r.point(lift), g_.point(lift), b.point(lift), a))

			glass = Image.composite(lit(glass), glass, circle)
			disc = lit(disc)
			light = Image.composite(lit(light), light, circle)

		under = Image.new("RGBA", size, (0, 0, 0, 0))
		drop = _outer_shadow(circle, 0, 3 * sc, 4 * sc)
		under = Image.alpha_composite(under, _solid(size, ice8(0, 25, 50, 0.45), drop))
		outer = ImageChops.subtract(_ellipse_mask(size, (c0 - 1, c0 - 1, c0 + d + 1, c0 + d + 1)), circle)
		under = Image.alpha_composite(under, _solid(size, ice8(0, 15, 35, 0.6), outer))
		under = Image.alpha_composite(under, glass)
		over = light
		inner = ImageChops.subtract(circle, _ellipse_mask(size, (c0 + 1, c0 + 1, c0 + d - 1, c0 + d - 1)))
		over = Image.alpha_composite(over, _solid(size, ice8(220, 240, 255, 0.6 if hover else 0.45), inner))
		cap, _pad = self._cap_image(d, pressed)
		capped = Image.new("RGBA", size, (0, 0, 0, 0))
		capped.paste(cap, (c0, c0))
		capped.putalpha(capped.getchannel("A").point(_lut(self.MENU_CAP)))
		over = Image.alpha_composite(over, capped)
		return under, disc, over, pad

	def speaker(self, x: float, cy: float, size: float, colour: ColourRGBA) -> None:
		"""Speaker glyph (24-unit box): body, cone, and one sound wave."""
		k = size / 24
		y0 = cy - size / 2
		c = (colour.r / 255, colour.g / 255, colour.b / 255, colour.a / 255)
		r = self.renderer
		sdl3.set_render_draw_blend_mode(r, sdl3.SDL_BLENDMODE_BLEND)

		def poly(pts: list[tuple[float, float]]) -> None:
			verts = [(x + px * k, y0 + py * k, 0.0, 0.0, *c) for px, py in pts]
			idx = []
			for i in range(1, len(pts) - 1):
				idx += (0, i, i + 1)
			sdl3.render_geometry(r, None, verts, idx)

		poly([(4, 9), (8, 9), (8, 15), (4, 15)])
		poly([(8, 9), (13, 5), (13, 19), (8, 15)])
		# Wave: the arc M16 9 a4 4 0 0 1 0 6, centred at (13.35, 12)
		width = 1.6
		inner, outer = 4 - width / 2, 4 + width / 2
		steps = 8
		for i in range(steps):
			a0 = math.radians(-48 + 96 * i / steps)
			a1 = math.radians(-48 + 96 * (i + 1) / steps)
			poly([
				(13.35 + math.cos(a0) * inner, 12 + math.sin(a0) * inner),
				(13.35 + math.cos(a0) * outer, 12 + math.sin(a0) * outer),
				(13.35 + math.cos(a1) * outer, 12 + math.sin(a1) * outer),
				(13.35 + math.cos(a1) * inner, 12 + math.sin(a1) * inner)])

	# -- small window buttons --------------------------------------------------------------------

	def cap_button(self, rect, kind: str, hover: bool) -> None:
		"""Window control capsules: glass (min/max) or red gel (close)."""
		x, y, w, h = rect
		r = self.s(5)
		if kind == "close":
			# Red gel; Obsidian's is graphite, and only its hover glow is red
			m = self.mono
			dusk = (rgba8(243, 160, 140), rgba8(223, 91, 63), rgba8(196, 58, 30), rgba8(226, 112, 79))
			obs = (rgba8(123, 130, 141), rgba8(77, 83, 92), rgba8(44, 48, 55), rgba8(65, 70, 78))
			stops = [(p, mix(dusk[i], obs[i], m)) for i, p in enumerate((0.0, 0.5, 0.51, 1.0))]
			if hover:
				self.soft(rect, r, 6 * self.gui.scale, 0, rgba8(255, 90, 50, 0.7))
			self.shape(rect, r, grad=vgrad(y, h, stops))
			self.ring("top", rect, r, mix(rgba8(255, 220, 210, 0.9), rgba8(255, 255, 255, 0.6), m))
			self.ring("outer", rect, r, mix(rgba8(110, 20, 0, 0.6), rgba8(0, 0, 0, 0.7), m))
		else:
			stops = [(0.0, (1, 1, 1, 0.55)), (0.5, (1, 1, 1, 0.2)), (0.51, (1, 1, 1, 0.08)), (1.0, (1, 1, 1, 0.25))]
			self.shape(rect, r, grad=vgrad(y, h, stops))
			if hover:
				self.shape(rect, r, (1, 1, 1, 0.12))
			self.ring("top", rect, r, (1, 1, 1, 0.8))
			self.ring("outer", rect, r, self.EDGE)

	def mac_light(self, cx: float, cy: float, d: float, colour: tuple[int, int, int], hover: bool) -> None:
		"""A traffic light as a small gel bead in its own colour."""
		hue = colorsys.rgb_to_hls(colour[0] / 255, colour[1] / 255, colour[2] / 255)[0] * 360
		self.orb(cx, cy, d, hue=hue, hover=hover)

	# -- art ----------------------------------------------------------------------------------------

	def art(self, tex, rect, r: float | None = None, *, gloss: bool = True, shadow: str | None = "large",
			reflect: float = 0.0, ring: bool = True) -> None:
		"""Album art with rounded corners, a diagonal glare, a ring, a drop
		shadow and optionally a wet-floor reflection `reflect` px tall."""
		x, y, w, h = rect
		if w < 2 or h < 2:
			return
		sc = self.gui.scale
		r = self.s(6) if r is None else r
		if shadow == "large":
			# 0 14px 28px -10px rgba(0,20,40,.65)
			self.soft(rect, r, 14 * sc, -10 * sc, mix(rgba8(0, 20, 40, 0.65), rgba8(0, 0, 0, 0.75), self.mono), 0, 14 * sc)
		elif shadow == "small":
			# 0 3px 8px -3px rgba(0,20,40,.5)
			self.soft(rect, r, 4 * sc, -3 * sc, mix(rgba8(0, 20, 40, 0.5), rgba8(0, 0, 0, 0.6), self.mono), 0, 3 * sc)
		self.shape(rect, r, texture=tex, uv=lambda px, py: ((px - x) / w, (py - y) / h))
		if reflect > 0:
			gap = self.s(3)
			ry = y + h + gap
			rh = min(reflect, h)
			# Flipped: the reflection's top shows the art's bottom row
			g = vgrad(ry, rh, [(0.0, (1, 1, 1, 0.42)), (0.85, (1, 1, 1, 0.0)), (1.0, (1, 1, 1, 0.0))])
			self.shape((x, ry, w, rh), (r, r, 0, 0), grad=g, texture=tex,
				uv=lambda px, py: ((px - x) / w, 1 - (py - ry) / h))
		if gloss:
			# linear-gradient(160deg, white .5 0%, white .1 38%, transparent 38.5%)
			g = Gradient(rect, 160, [(0.0, (1, 1, 1, 0.5)), (0.38, (1, 1, 1, 0.1)), (0.385, (1, 1, 1, 0.0)), (1.0, (1, 1, 1, 0.0))])
			self.shape(rect, r, grad=g)
		if ring:
			self.ring("outer", rect, r, mix(rgba8(0, 20, 40, 0.4), rgba8(0, 0, 0, 0.5), self.mono))

	def set_art_style(self, **style) -> None:
		"""Ask for the next album art drawn through AlbumArt to be drawn with
		art() and these options. The request is consumed by that draw, or
		dropped by end_art_style() if the art wasn't ready."""
		self._art_style = style if self.active else None

	def end_art_style(self) -> None:
		self._art_style = None

	def draw_styled_art(self, tex, rect) -> bool:
		style = getattr(self, "_art_style", None)
		if style is None or not self.active:
			return False
		self._art_style = None
		self.art(tex, (rect.x, rect.y, rect.w, rect.h), **style)
		return True

	def playing_glow(self, rect, r: float | None = None) -> None:
		"""Accent glow and ring around the playing album's art."""
		r = self.s(6) if r is None else r
		x, y, w, h = rect
		g = self.s(3)
		H = _hue_lerp(self.acc, self.oacc, self.mono)
		self.soft(rect, r, 6 * self.gui.scale, g, hsl(H, 0.95, 0.55, 0.85))
		self.ring("outer", (x - g + 1, y - g + 1, w + g * 2 - 2, h + g * 2 - 2), r + g, hsl(H, 0.9, 0.72, 0.9))

	def art_placeholder(self, rect, r: float | None = None) -> None:
		r = self.s(6) if r is None else r
		x, y, w, h = rect
		m = self.mono
		top = mix(hsl(self.h1, 0.4, 0.22), rgba8(42, 46, 52), m)
		bottom = mix(hsl(self.h2, 0.4, 0.14), rgba8(22, 24, 28), m)
		self.shape(rect, r, grad=vgrad(y, h, [(0.0, top), (1.0, bottom)]))
		self.ring("outer", rect, r, rgba8(0, 20, 40, 0.4))

	# -- spectrum -----------------------------------------------------------------------------------

	def reflection_height(self) -> int:
		return self.si(46)

	def side_art_inset(self) -> int:
		"""Total inset of the side panel art (20px of glass each side)."""
		return self.si(40)

	def side_art_text_gap(self) -> int:
		"""How far the side panel text moves down to clear the reflection:
		its height and 3px gap, less the art's own bottom padding."""
		return max(0, self.reflection_height() + self.si(3) - self.side_art_inset() // 2)

	def side_spectrum_height(self) -> int:
		"""Room the side panel spectrum takes: 64px of bars, 8 above, 16 below."""
		return self.si(64 + 8 + 16)

	def spectrum_hue(self) -> float:
		"""The album accent with the skin on; otherwise the theme's own
		visualiser colour, or a calm aqua when that is grey."""
		if self.active:
			return self.acc
		c = self.tauon.colours.vis_colour
		h, l, s_ = colorsys.rgb_to_hls(c.r / 255, c.g / 255, c.b / 255)
		return h * 360 if s_ > 0.2 else 196.0

	def draw_side_spectrum(self, x: float, y: float, w: float, h: float) -> None:
		"""The glass spectrum at the bottom of a side panel region."""
		# As wide as the art above it
		art_w = w - (self.side_art_inset() if self.active else self.s(17))
		bars_h = self.s(64)
		rect = (x + (w - art_w) / 2, y + h - self.s(16) - bars_h, art_w, bars_h)
		self.draw_glass_spectrum(rect)

	def draw_glass_spectrum(self, rect) -> None:
		pctl = self.tauon.pctl
		now = time.monotonic()
		dt = min(0.1, max(0.0, now - getattr(self, "_spec_last", now)))
		self._spec_last = now
		live = pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)
		data = self.gui.glass_spec
		n = 24
		if live and data and len(data) >= n:
			values = [min(1.0, max(0.03, v / 20)) for v in data[:n]]
		else:
			values = [0.03] * n
		self.spectrum(rect, values, dt, live, self.spectrum_hue())

	def spectrum(self, rect, values: list[float], dt: float, live: bool, hue: float | None = None) -> None:
		"""Glass bars with lit caps. `values` are 0-1."""
		x, y, w, h = rect
		n = len(values)
		if n == 0 or w < n * 2:
			return
		if len(self.spec_vals) != n:
			self.spec_vals = [0.0] * n
			self.spec_peaks = [0.0] * n
		sc = self.gui.scale
		gap = self.s(3)
		bw = (w - gap * (n - 1)) / n
		H = self.acc if hue is None else hue
		# Obsidian (only while the skin is on): silver bars, accent caps
		m = self.mono if self.active else 0.0
		bar_top = hsl(H, 0.90 * (1 - m), 0.62 + 0.22 * m, 0.95)
		bar_bottom = hsl(H, 0.85 * (1 - m), 0.30 + 0.14 * m, 0.55)
		cap_glow = mix(hsl(H, 1.0, 0.60, 0.9), hsl(self.oacc, 1.0, 0.60, 0.9), m)
		cap = mix(hsl(H, 1.0, 0.80), hsl(self.oacc, 1.0, 0.78), m)
		k = 1 - math.exp(-dt * 13)   # .35 per frame at 30fps
		decay = 0.012 * 30 * dt
		for i in range(n):
			self.spec_vals[i] += (values[i] - self.spec_vals[i]) * k
			self.spec_peaks[i] = max(self.spec_peaks[i] - decay, self.spec_vals[i])
		reach = h - self.s(8)
		for i in range(n):
			v = self.spec_vals[i]
			bh = max(self.s(2), v * reach)
			bx = x + i * (bw + gap)
			by = y + h - bh
			g = vgrad(by, bh, [(0.0, bar_top), (1.0, bar_bottom)])
			rr = min(self.s(2), bw / 2, bh / 2)
			self.shape((bx, by, bw, bh), (rr, rr, 0, 0), grad=g)
			sw = max(1.0, bw * 0.35)
			if bh > 2:
				self.shape((bx + 1, by + 1, sw, bh - 2), 0, (1, 1, 1, 0.38))
			py = y + h - self.spec_peaks[i] * reach - self.s(4)
			ch = max(1.0, self.s(2))
			self.soft((bx, py, bw, ch), 0, 3 * sc, 0, cap_glow)
			self.shape((bx, py, bw, ch), 0, cap)
		if live or any(p > 0.005 for p in self.spec_peaks):
			self.schedule(1 / self.FPS)

	# -- tracklist rows ---------------------------------------------------------------------------

	def row_rect(self, box) -> tuple[float, float, float, float]:
		"""A row's highlight, inset from the panel edges (margin: 0 8px)."""
		x, y, w, h = box
		m = self.s(8)
		return (x + m, y, max(0.0, w - m * 2), h)

	def draw_tracklist_under(self, clip) -> None:
		"""Everything drawn under the cached tracklist texture: the playing
		row's gel (drawn fresh, so it follows a colour change) and the hover
		highlight."""
		old = sdl3.get_render_clip_rect(self.renderer)
		cx, cy, cw, ch = clip
		sdl3.set_render_clip_rect(self.renderer, sdl3.Rect(round(cx), round(cy), round(cw), round(ch)))
		for rect in self.playing_rows:
			if rect[1] + rect[3] >= cy and rect[1] <= cy + ch:
				self.gel(rect)
		sdl3.set_render_clip_rect(self.renderer, old)
		# No hover highlight: rows only light up when selected

	# -- scrollbar ----------------------------------------------------------------------------------

	def scroll_thumb(self, rect, hover: bool) -> None:
		x, y, w, h = rect
		# 10px track with a 2px clear border: a 6px pill
		inset = self.s(2)
		r = (w - inset * 2) / 2
		self.shape((x + inset, y + inset, w - inset * 2, h - inset * 2), r, mix(
			hsl(self.acc, 0.70, 0.55, 0.75 if hover else 0.55),
			rgba8(225, 232, 242, 0.55 if hover else 0.38), self.mono))

	# -- layout -------------------------------------------------------------------------------------

	def classic_seek_rect(self, pos, size) -> tuple[float, float, float, float]:
		"""The tube inside the classic bar's seek strip, clear of the glass edge."""
		h = self.s(12)
		return (pos[0] + self.s(4), pos[1] + self.s(6), size[0] - self.s(12), h)

	def gutter(self) -> int:
		return self.si(self.GUTTER)

	@classmethod
	def edge_gap_logical(cls, prefs) -> int:
		"""The window-edge gap in logical px: a pixel wider when the sky fills
		the window, so the panels keep a little more room from its frame."""
		return cls.EDGE_GAP + (0 if prefs.aero_see_through else 1)

	def edge_gap(self) -> int:
		return self.si(self.edge_gap_logical(self.prefs))

	def top_glass_height(self) -> int:
		# The top panel's own row (30px, or 100px for the art header) plus a
		# little glass above and below it
		row = 100 if self.gui.top_bar_mode2 else 30
		return self.si(row + self.TOP_H - 30)

	def top_glass_rect(self) -> tuple[int, int, int, int]:
		e = self.edge_gap()
		ww = self.tauon.window_size[0]
		return (e, e, ww - e * 2, self.top_glass_height())

	def bottom_glass_rect(self) -> tuple[int, int, int, int]:
		"""The bottom bar: a gutter above it, the edge gap below and beside."""
		g = self.gutter()
		e = self.edge_gap()
		ww, wh = self.tauon.window_size[0], self.tauon.window_size[1]
		by = self.gui.panelBY
		return (e, wh - by + g, ww - e * 2, by - g - e)

	def side_split_centre(self) -> float:
		"""The middle of the gutter between the side panel and the tracklist
		(rsp_split_x is the side panel's own edge, so the gap is all on one
		side of it)."""
		gui = self.gui
		half = self.gutter() / 2
		return gui.rsp_split_x + half if gui.rsp_on_left else gui.rsp_split_x - half

	def preset_rects(self) -> list[tuple[tuple[int, int, int, int], bool, float | None]]:
		"""(rect, tall, sheen) for every glass panel of the standard layout."""
		gui = self.gui
		wh = self.tauon.window_size[1]
		out = []
		top = self.top_glass_rect()
		out.append((top, False, None))
		mid_y = gui.panelY
		mid_h = wh - gui.panelY - gui.panelBY
		if gui.lsp and not gui.custom_mode:
			out.append(((gui.lsp_x, mid_y, gui.lspw, mid_h), True, 110))
		if gui.show_playlist or gui.rsp:
			if gui.plw > 4:
				out.append(((gui.playlist_left, mid_y, gui.plw, mid_h), True, 110))
		if gui.rsp:
			out.append(((gui.rsp_x, mid_y, gui.rspw, mid_h), True, 120))
		out.append((self.bottom_glass_rect(), False, None))
		return out

	def draw_preset_panels(self) -> None:
		for rect, tall, sheen in self.preset_rects():
			self.panel(rect, tall=tall, sheen_h=sheen)

	# -- standard layout bars, rendered into their glass ---------------------------------------------

	def render_preset_top(self) -> None:
		"""Draw the top panel inside the floating top glass. It renders through
		the custom layout's offscreen path, which reframes the window size and
		the input coordinates, so its tabs and buttons keep working."""
		tauon = self.tauon
		gui = self.gui
		gx, gy, gw, gh = self.top_glass_rect()
		row = round(gui.panelY2 if not gui.top_bar_mode2 else 100 * gui.scale)
		y = gy + (gh - row) // 2
		self.header_rect = (gx, y, gw, row)
		tauon.custom._draw_offscreen(_PresetTop(row), gx, y, gw, row, True)

	def render_preset_bottom(self) -> None:
		x, y, w, h = self.bottom_glass_rect()
		self.tauon.custom._draw_offscreen(_PresetBottom(), x, y, w, h, True)


class _PresetTop:
	"""Adapter: the standard top panel, drawn at a (0, 0) origin."""

	offscreen = True

	def __init__(self, row: int) -> None:
		self.row = row

	def draw(self, tauon, x, y, w, h, content_rect=None) -> None:
		gui = tauon.gui
		# TopPanel lays itself out from panelY; for the duration it is its own row
		panel_y = gui.panelY
		gui.panelY = self.row
		try:
			tauon.top_panel.render()
		finally:
			gui.panelY = panel_y


class _PresetBottom:
	"""Adapter: whichever bottom bar the standard layout shows."""

	offscreen = True

	def draw(self, tauon, x, y, w, h, content_rect=None) -> None:
		gui = tauon.gui
		prefs = tauon.prefs
		tauon.ddt.text_background_colour = tauon.colours.bottom_panel_colour
		if prefs.feux_panel:
			tauon.feux_bar.render(h)
			return
		if not prefs.shuffle_lock:
			# Aqua's own compact panel
			tauon.aero.compact_bar.render(h)
			return
		bar = tauon.bottom_bar_ao1 if prefs.shuffle_lock else tauon.bottom_bar1
		panel_by = gui.panelBY
		gui.panelBY = round(h)
		try:
			bar.update()
			bar.render()
		finally:
			gui.panelBY = panel_by


class AquaBar:
	"""Aqua's compact playback panel: the concept's bottom bar.

	Transport orbs on the left (play larger, sitting a little high), the
	track title, artist and times over the seek tube in the middle, and the
	mode pills and volume on the right. It stands in for the classic compact
	panel while the skin is on; the Feux panel keeps its own design.

	Draws against the bottom `height` px of the current window space, like
	the other bars, so the offscreen widget path can host it.
	"""

	# The concept's bar proportions (96px tall, 64px play orb lifted 5px, 40px
	# others) at a slightly smaller size
	PANEL_H = 73
	# Quiet transport: one hero play orb, the rest etched glyphs on the glass
	PLAY_D = 52
	SIDE_D = 34
	PLAY_LIFT = 0
	# The whole transport sits this much below the panel's centre line
	TRANSPORT_DROP = 3

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.seek_drag = False
		self.vol_drag = False
		self.on_seek = False

	def _s(self, v: float) -> int:
		return round(v * self.tauon.gui.scale)

	def _tip(self, x: float, y: float, text: str, tip=None) -> None:
		tauon = self.tauon
		sx, sy = tauon.inp.to_screen(x, y)
		(tip or tauon.tool_tip2).test(sx, sy, text)

	def width_right(self, a: dict) -> int:
		return (self.tauon.feux_bar._pill_w(a["feux-shuffle"]) + self._s(8)
			+ self.tauon.feux_bar._pill_w(a["feux-repeat"]) + self._s(16)
			+ self._s(30) + self._s(96) + self._s(14) + round(a["feux-menu"].w))

	def render(self, height: float | None = None) -> None:
		tauon = self.tauon
		gui = tauon.gui
		inp = tauon.inp
		pctl = tauon.pctl
		ddt = tauon.ddt
		aero = tauon.aero
		feux = tauon.feux_bar
		a = feux._load_assets()
		from tauon.t_modules.t_extra import get_display_time

		w = round(tauon.window_size[0])
		h = round(height) if height is not None else round(tauon.window_size[1])
		top = round(tauon.window_size[1]) - h
		mid = top + h / 2
		# Shrink the orbs on a short panel (the custom layout's widget can be 51px)
		k = min(1.0, h / self._s(self.PANEL_H))
		play_d = self._s(self.PLAY_D) * k
		side_d = self._s(self.SIDE_D) * k
		pad_x = self._s(22)
		gap = self._s(26)
		playing = pctl.playing_state == PlayingState.PLAYING
		text_c = to_colour(aero.TEXT)
		muted_c = to_colour(aero.MUTED)
		ddt.text_background_colour = tauon.colours.bottom_panel_colour
		self.on_seek = False

		# -- transport ---------------------------------------------------------
		x = pad_x
		down = inp.mouse_down
		orb_mid = mid + self._s(self.TRANSPORT_DROP) * k

		def orb_button(cx: float, d: float, glyph, tip: str) -> tuple[bool, tuple]:
			rect = (round(cx - d / 2), round(orb_mid - d / 2), round(d), round(d))
			tauon.fields.add(rect)
			over = tauon.coll(rect)
			if over:
				self._tip(rect[0], top - self._s(4), tip)
			return over, rect

		cx = x + side_d / 2
		over, rect = orb_button(cx, side_d, a["feux-bb"], _("Back"))
		if over and inp.mouse_click:
			pctl.back()
		if over and inp.right_click:
			tauon.toggle_repeat()
			tauon.toast(_("Repeat On") if pctl.repeat_mode else _("Repeat Off"))
			inp.right_click = False
		aero.ghost(cx, orb_mid, side_d, a["feux-bb"], hover=over, pressed=over and down)
		x += side_d + self._s(10)

		cx = x + play_d / 2
		play_mid = orb_mid - self._s(self.PLAY_LIFT) * k   # the concept lifts the play orb a little
		rect = (round(cx - play_d / 2), round(play_mid - play_d / 2), round(play_d), round(play_d))
		tauon.fields.add(rect)
		over = tauon.coll(rect)
		if over:
			if inp.mouse_click:
				if playing or pctl.playing_state == PlayingState.PAUSED:
					pctl.pause()
				else:
					pctl.play()
				inp.mouse_click = False
			if inp.right_click:
				# No stop button on this panel: right-click stops
				pctl.stop()
				inp.right_click = False
			self._tip(rect[0], top - self._s(4), _("Pause, Right-click: Stop") if playing else _("Play, Right-click: Stop"))
		glyph = a["feux-pause"] if playing else a["feux-play"]
		aero.liquid_orb(cx, play_mid, play_d, glyph, hover=over, pressed=over and down)
		x += play_d + self._s(10)

		cx = x + side_d / 2
		over, rect = orb_button(cx, side_d, a["feux-ff"], _("Forward"))
		if over and inp.mouse_click:
			pctl.advance()
		if over and inp.right_click:
			tauon.toggle_random()
			tauon.toast(_("Shuffle On") if pctl.random_mode else _("Shuffle Off"))
			inp.right_click = False
		aero.ghost(cx, orb_mid, side_d, a["feux-ff"], hover=over, pressed=over and down)
		x += side_d

		# -- right: mode pills, volume, menu ------------------------------------
		right_w = self.width_right(a)
		show_right = w - x - gap * 2 - right_w > self._s(160)
		if show_right:
			right_x = w - pad_x - right_w
			self._draw_right(a, right_x, top, mid, h)
		else:
			# Narrow: the modes and volume go, the playback menu stays
			right_x = w - pad_x - round(a["feux-menu"].w)
			self._draw_menu(a, right_x, top, mid)

		# -- middle: title line over the seek tube ------------------------------
		left = x + gap
		right = right_x - (gap if show_right else self._s(14))
		width = right - left
		if width < self._s(60):
			return
		track = pctl.playing_object()
		tube_h = self._s(14)
		block = self._s(18) + self._s(7) + tube_h
		line_y = mid - block / 2 + self._s(9)
		tube_y = round(mid + block / 2 - tube_h)
		length = pctl.playing_length

		if length > 0 and pctl.playing_state != PlayingState.STOPPED:
			times = f"{get_display_time(pctl.playing_time)} / {get_display_time(length)}"
		else:
			times = ""
		times_w = ddt.get_text_w(times, 212) if times else 0
		if times:
			ddt.text((right + 1, feux._text_y(212, line_y), 1), times, muted_c, 212)
		text_room = width - times_w - self._s(12)
		if track is not None and text_room > self._s(30):
			title = track.title or track.filename
			title_w = ddt.text((left, feux._text_y(213, line_y)), title, text_c, 213, max_w=text_room)
			artist = track.artist or ""
			room = text_room - (title_w or 0) - self._s(8)
			if artist and room > self._s(24):
				ddt.text((left + (title_w or 0) + self._s(8), feux._text_y(12, line_y)), artist, muted_c, 12, max_w=room)
			title_rect = (left, round(line_y - self._s(10)), round(text_room), self._s(20))
			if tauon.coll(title_rect) and pctl.playing_ready():
				if inp.mouse_click:
					pctl.show_current()
				if inp.right_click:
					tauon.mode_menu.activate()
					inp.right_click = False

		# The seek tube
		tube = (left, tube_y, width, tube_h)
		reach = self._s(6)
		hit = (left, tube_y - reach, width, tube_h + reach * 2)
		tauon.fields.add(hit)
		if tauon.coll(hit) and not tauon.prefs.shuffle_lock:
			self.on_seek = True
			inp.global_clicked = True
			if inp.mouse_click:
				self.seek_drag = True
			if inp.mouse_wheel != 0:
				pctl.seek_time(pctl.playing_time + inp.mouse_wheel * 3)
			if inp.right_click:
				pctl.pause()
				inp.right_click = False
		progress = 0.0
		if length > 0:
			progress = min(1.0, max(0.0, pctl.playing_time / length))
		if self.seek_drag:
			gui.update_on_drag = True
			gui.request_frame()
			progress = min(1.0, max(0.0, (inp.mouse_position[0] - left) / max(1, width)))
			if not inp.mouse_down:
				self.seek_drag = False
				if pctl.playing_ready():
					pctl.seek_decimal(progress)
		aero.tube(tube, progress, playing=playing, bubbles=True)
		tauon.draw_ab_repeat_markers(left, tube_y, width, tube_h)
		gui.seek_bar_rect = (left, tube_y, round(width * progress), tube_h)

		# Right-click anywhere unclaimed opens the panel menu; the wheel sets volume
		panel = (0, top, w, h)
		if inp.right_click and tauon.coll(panel):
			tauon.mode_menu.activate()
			inp.right_click = False
		if inp.mouse_wheel != 0 and tauon.coll(panel) and not self.on_seek:
			pctl.player_volume = min(100, max(0, pctl.player_volume + inp.mouse_wheel * tauon.prefs.volume_wheel_increment))
			pctl.set_volume()
			gui.request_frame()

	def _draw_right(self, a: dict, x: float, top: float, mid: float, h: float) -> None:
		tauon = self.tauon
		gui = tauon.gui
		inp = tauon.inp
		pctl = tauon.pctl
		aero = tauon.aero
		feux = tauon.feux_bar
		pill_h = self._s(26)

		if not tauon.prefs.shuffle_lock:
			# Shuffle
			icon = a["feux-shuffle-a"] if pctl.album_shuffle_mode else a["feux-shuffle"] if pctl.random_mode else a["feux-shuffle-off"]
			pw = feux._pill_w(a["feux-shuffle"])
			rect = (round(x), round(mid - pill_h / 2), pw, pill_h)
			tauon.fields.add(rect)
			over = tauon.coll(rect)
			if over:
				if inp.mouse_click:
					tauon.toggle_random()
				if inp.right_click:
					tauon.shuffle_menu.activate(position=(x + pw, mid + self._s(14)))
					inp.right_click = False
				self._tip(x, top - self._s(4), _("Shuffle"), tauon.tool_tip)
			feux._aero_pill(aero, round(x), round(mid), pw, icon, bool(pctl.random_mode), over)
			x += pw + self._s(8)
			# Repeat
			icon = a["feux-repeat-a"] if pctl.album_repeat_mode else a["feux-repeat"] if pctl.repeat_mode else a["feux-repeat-off"]
			pw = feux._pill_w(a["feux-repeat"])
			rect = (round(x), round(mid - pill_h / 2), pw, pill_h)
			tauon.fields.add(rect)
			over = tauon.coll(rect)
			if over:
				if inp.mouse_click:
					tauon.toggle_repeat()
				if inp.right_click:
					tauon.repeat_menu.activate(position=(x + pw, mid + self._s(14)))
					inp.right_click = False
				self._tip(x, top - self._s(4), _("Repeat album") if pctl.album_repeat_mode else _("Repeat track"), tauon.tool_tip)
			feux._aero_pill(aero, round(x), round(mid), pw, icon, bool(pctl.repeat_mode), over)
			x += pw + self._s(16)
		else:
			x += feux._pill_w(a["feux-shuffle"]) + self._s(8) + feux._pill_w(a["feux-repeat"]) + self._s(16)

		# Volume: speaker, then the tube (clear of the grip, which overhangs
		# the tube's start at low volume)
		aero.speaker(x, mid, self._s(17), to_colour(aero.TEXT))
		x += self._s(30)
		vol_w = self._s(96)
		tube_h = self._s(14)
		vol = (round(x), round(mid - tube_h / 2), vol_w, tube_h)
		hit = (vol[0], vol[1] - self._s(8), vol_w, tube_h + self._s(16))
		tauon.fields.add(hit)
		if tauon.coll(hit):
			inp.global_clicked = True
			if inp.mouse_click:
				self.vol_drag = True
			if inp.right_click:
				pctl.toggle_mute()
				inp.right_click = False
		if self.vol_drag:
			gui.update_on_drag = True
			gui.request_frame()
			pctl.player_volume = int(min(1.0, max(0.0, (inp.mouse_position[0] - vol[0]) / max(1, vol_w))) * 100)
			if not inp.mouse_down:
				self.vol_drag = False
				pctl.set_volume(True)
			else:
				pctl.set_volume(False)
		level = min(100, max(0, pctl.player_volume)) / 100
		aero.tube(vol, level, shimmer=False)
		gui.volume_bar_rect = (vol[0], vol[1], round(vol_w * level), tube_h)
		x += vol_w + self._s(14)
		self._draw_menu(a, x, top, mid)

	def _draw_menu(self, a: dict, x: float, top: float, mid: float) -> None:
		"""Playback menu (left click) / panel menu (right click), as on the other bars."""
		tauon = self.tauon
		inp = tauon.inp
		aero = tauon.aero
		feux = tauon.feux_bar
		icon = a["feux-menu"]
		rect = (round(x - self._s(6)), round(mid - self._s(15)), round(icon.w + self._s(12)), self._s(30))
		tauon.fields.add(rect)
		colour = to_colour(aero.TEXT if tauon.extra_menu.active else aero.MUTED)
		if tauon.coll(rect):
			colour = to_colour(aero.TEXT)
			if inp.mouse_click or inp.right_click:
				target = tauon.mode_menu if inp.right_click else tauon.extra_menu
				if target.active:
					feux._close(target)
				elif not target.click_dismissed:
					target.activate(position=(max(0, x + icon.w - round(target.w)), top), bottom_anchor=True)
				inp.right_click = False
		icon.render(round(x), round(mid - icon.h / 2), colour)
