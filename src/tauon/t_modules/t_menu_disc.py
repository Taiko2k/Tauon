"""The main menu button: a small record drawn after the app icon, which is also
a galaxy.

Every layer is shaded per pixel on the CPU (supersampled, so edges are exactly
anti-aliased at any UI scale) and baked to a texture; each frame the GPU only
rotates, scales and blends them. The disc layers are tiny and baked on first
use; the larger effect layers are baked on a worker thread and simply skipped
until they are ready.

At rest the disc is a monochrome symbol tinted like the other corner buttons.
Hovering wakes three moons that orbit it on a tilted ring. Opening the menu
plays out in that same orbital plane, close around the disc: a ring of
stardust spirals in and the record compresses under it, then it ignites,
with a glint, a shockwave and a short spray of sparks, and springs back with
its arcs in the icon's colours, a spiral galaxy spinning down behind it. The
galaxy keeps turning while the menu is open and collapses back into the
record when it closes.
"""

from __future__ import annotations

import ctypes
import math
import random
import threading
import time
from typing import TYPE_CHECKING

import sdl3

from tauon.t_modules.t_extra import ColourRGBA

if TYPE_CHECKING:
	from collections.abc import Callable

	from tauon.t_modules.t_main import Tauon

Pixel = tuple[float, float, float, float]
RGB = tuple[float, float, float]

# Gradient stops from the app icon (assets/svg/app-icon.svg)
WARM = ((0.0, (0x7b, 0x3f, 0xa5)), (0.27, (0xbb, 0x4f, 0x91)), (0.53, (0xe8, 0x66, 0x78)),
	(0.78, (0xfa, 0x8a, 0x55)), (1.0, (0xff, 0xc8, 0x57)))
COOL = ((0.0, (0x51, 0x42, 0x73)), (0.32, (0x50, 0x6d, 0xa0)), (0.66, (0x45, 0xa0, 0xbd)),
	(1.0, (0x62, 0xd1, 0xc4)))
STAR_WHITE = (240, 244, 255)
SPARK_COLOURS = ((0xff, 0xc8, 0x57), (0xfa, 0x8a, 0x55), (0xe8, 0x66, 0x78), (0xbb, 0x4f, 0x91),
	(0x62, 0xd1, 0xc4), (0x45, 0xa0, 0xbd), (0x50, 0x6d, 0xa0))
MOON_COLOURS = ((0xff, 0xc8, 0x57), (0xe8, 0x66, 0x78), (0x62, 0xd1, 0xc4))

# Disc radii as fractions of the disc radius
RIM_IN = 0.84
ARC_IN, ARC_OUT = 0.40, 0.70
HUB_R = 0.22
# Ripple texture: ring centred on RIPPLE_R of a texture RIPPLE_SPAN discs wide
RIPPLE_SPAN = 1.6
RIPPLE_R, RIPPLE_W = 0.90, 0.07
GALAXY_TWIST = 3.4

DISC_PX = 17
GALAXY_PX = 30

# Timeline of the opening animation (seconds from the click)
INFALL = 0.3         # stardust spirals into the disc before ignition
SPIN_TIME = 0.6      # half turn, from ignition
SPRING_TIME = 0.55   # elastic return to full size, from ignition
RIPPLE_TIME = 0.5
GLINT_TIME = 0.35
INFALL_COUNT = 34
BURST_COUNT = 26
# The click effects stay within this many px either side of the disc
FX_REACH = 50
# Orbital plane shared with the moons: vertical squash and tilt
PLANE_SQUASH = 0.3
PLANE_TILT = math.radians(-18)

BLOOM_RATE = 7.0  # per second
HOVER_RATE = 14.0
GALAXY_IN, GALAXY_OUT = 3.0, 5.0
MOON_RATE = 5.0
IDLE_FPS = 40


# ---------------------------------------------------------------------------
# Shading helpers
# ---------------------------------------------------------------------------

def clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
	return lo if v < lo else hi if v > hi else v


def smoothstep(e0: float, e1: float, x: float) -> float:
	t = clamp((x - e0) / (e1 - e0))
	return t * t * (3 - 2 * t)


def mix(a: RGB, b: RGB, t: float) -> RGB:
	return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def gradient(stops: tuple, t: float) -> RGB:
	t = clamp(t)
	for (t0, c0), (t1, c1) in zip(stops, stops[1:], strict=False):
		if t <= t1:
			return mix(c0, c1, (t - t0) / (t1 - t0) if t1 > t0 else 0.0)
	return stops[-1][1]


def hash2(ix: int, iy: int, seed: int = 0) -> float:
	h = (ix * 374761393 + iy * 668265263 + seed * 1442695041) & 0xFFFFFFFF
	h = ((h ^ (h >> 13)) * 1274126177) & 0xFFFFFFFF
	return ((h ^ (h >> 16)) & 0xFFFFFF) / 0xFFFFFF


def value_noise(x: float, y: float, seed: int = 0) -> float:
	ix, iy = math.floor(x), math.floor(y)
	fx, fy = x - ix, y - iy
	ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
	a, b = hash2(ix, iy, seed), hash2(ix + 1, iy, seed)
	c, d = hash2(ix, iy + 1, seed), hash2(ix + 1, iy + 1, seed)
	return a + (b - a) * ux + (c - a) * uy + (a - b - c + d) * ux * uy


def fbm(x: float, y: float, seed: int = 0, octaves: int = 4) -> float:
	v, amp, total = 0.0, 0.5, 0.0
	for i in range(octaves):
		v += amp * value_noise(x, y, seed + i * 17)
		total += amp
		x, y, amp = x * 2.03 + 1.7, y * 2.03 - 0.9, amp * 0.5
	return v / total


def light(r: float, g: float, b: float) -> Pixel:
	"""Pack an emitted light value: hue at full strength, strength in alpha."""
	peak = max(r, g, b)
	if peak <= 0:
		return (0, 0, 0, 0.0)
	a = min(1.0, peak / 255)
	return (r / a if a else 0, g / a if a else 0, b / a if a else 0, a)


# ---------------------------------------------------------------------------
# Shaders: (x, y) in the texture's span -> straight-alpha (r, g, b, a)
# ---------------------------------------------------------------------------

def in_quadrant_arcs(x: float, y: float) -> int:
	"""0 outside the arcs, 1 in the warm (top-left) arc, 2 in the cool (bottom-right) one."""
	r = math.hypot(x, y)
	if not ARC_IN <= r <= ARC_OUT:
		return 0
	if x < 0 and y < 0:
		return 1
	if x > 0 and y > 0:
		return 2
	return 0


def shade_rim(x: float, y: float) -> Pixel:
	r = math.hypot(x, y)
	return (255, 255, 255, 1.0) if RIM_IN <= r <= 1.0 else (0, 0, 0, 0.0)


def shade_hub(x: float, y: float) -> Pixel:
	return (255, 255, 255, 1.0) if math.hypot(x, y) <= HUB_R else (0, 0, 0, 0.0)


def shade_core_mono(x: float, y: float) -> Pixel:
	return (255, 255, 255, 1.0) if in_quadrant_arcs(x, y) else (0, 0, 0, 0.0)


def shade_core_colour(x: float, y: float) -> Pixel:
	arc = in_quadrant_arcs(x, y)
	if arc == 1:
		# Along the icon's gradient axes: left edge to top, right edge to bottom
		return (*gradient(WARM, (x - y + 1) / 2), 1.0)
	if arc == 2:
		return (*gradient(COOL, (y - x + 1) / 2), 1.0)
	return (0, 0, 0, 0.0)


def shade_ripple(x: float, y: float) -> Pixel:
	"""A soft ring whose colour sweeps around through the icon's gradients."""
	r = math.hypot(x, y) / RIPPLE_SPAN
	a = max(0.0, 1 - abs(r - RIPPLE_R) / RIPPLE_W)
	if a <= 0:
		return (0, 0, 0, 0.0)
	t = (math.atan2(y, x) / math.tau) % 1
	colour = gradient(WARM, t * 2) if t < 0.5 else gradient(COOL, (t - 0.5) * 2)
	return (*colour, a * a * (3 - 2 * a))


def shade_galaxy(x: float, y: float) -> Pixel:
	"""Two logarithmic spiral arms, one warm and one cool, dust, a hot core and stars."""
	r = math.hypot(x, y)
	if r >= 1:
		return (0, 0, 0, 0.0)
	th = math.atan2(y, x)
	lr = math.log(r + 0.04)
	a1 = (0.5 + 0.5 * math.cos(th - GALAXY_TWIST * lr)) ** 5
	a2 = (0.5 + 0.5 * math.cos(th + math.pi - GALAXY_TWIST * lr)) ** 5
	fade = (1 - r) ** 1.5 * smoothstep(0.06, 0.32, r)
	dust = 0.45 + 0.55 * fbm(x * 4 + 3, y * 4 + 7, 11, 3)
	warm = gradient(WARM, 1 - r)
	cool = gradient(COOL, 1 - r * 0.8)
	k1, k2 = a1 * fade * dust * 1.25, a2 * fade * dust * 1.25
	core = math.exp(-(r / 0.15) ** 2)
	cr = warm[0] * k1 + cool[0] * k2 + 255 * core
	cg = warm[1] * k1 + cool[1] * k2 + 228 * core
	cb = warm[2] * k1 + cool[2] * k2 + 240 * core
	cx, cy = math.floor(x * 8), math.floor(y * 8)
	if hash2(cx, cy, 5) < 0.4:
		sx = (cx + 0.2 + 0.6 * hash2(cx, cy, 6)) / 8
		sy = (cy + 0.2 + 0.6 * hash2(cx, cy, 7)) / 8
		s = math.exp(-((x - sx) ** 2 + (y - sy) ** 2) * 2600) * (0.5 + 0.5 * hash2(cx, cy, 8)) * (1.2 - r)
		cr, cg, cb = cr + 240 * s, cg + 244 * s, cb + 255 * s
	return light(cr, cg, cb)


def shade_star(x: float, y: float) -> Pixel:
	r2 = x * x + y * y
	return (255, 255, 255, clamp(0.55 * math.exp(-r2 * 5) + math.exp(-r2 * 45)))


def shade_streak(x: float, y: float) -> Pixel:
	"""A comet trail pointing right: bright head, tapering tail."""
	u = (x + 1) / 2
	tail = u ** 1.8 * math.exp(-(y * 2.4) ** 2)
	head = math.exp(-((x - 0.82) * 7) ** 2 - (y * 2.0) ** 2)
	return (255, 255, 255, clamp(tail + head))


def shade_flare(x: float, y: float) -> Pixel:
	"""Anamorphic lens flare: a thin horizontal streak, brightest in the middle."""
	return (255, 255, 255, clamp(math.exp(-(y * 3.2) ** 2) * (1 - abs(x)) ** 2.2))


def bake(shader: Callable[[float, float], Pixel], w: int, h: int | None = None,
		span: float = 1.0, ss: int = 4) -> bytes:
	"""Evaluate shader with ss x ss supersampling over a w x h grid. Square
	textures (h omitted) cover [-span, span] on both axes; others cover
	[-span, span] x [-1, 1]. Returns straight-alpha BGRA bytes (SDL ARGB8888,
	little endian)."""
	if h is None:
		h = w
		span_y = span
	else:
		span_y = 1.0
	out = bytearray(w * h * 4)
	step_x = 2 * span / w
	step_y = 2 * span_y / h
	sub = [(i + 0.5) / ss for i in range(ss)]
	n = ss * ss
	for py in range(h):
		for px in range(w):
			r = g = b = a = 0.0
			for sy in sub:
				y = -span_y + (py + sy) * step_y
				for sx in sub:
					x = -span + (px + sx) * step_x
					cr, cg, cb, ca = shader(x, y)
					r += cr * ca
					g += cg * ca
					b += cb * ca
					a += ca
			i = (py * w + px) * 4
			if a > 0:
				out[i] = min(255, round(b / a))
				out[i + 1] = min(255, round(g / a))
				out[i + 2] = min(255, round(r / a))
				out[i + 3] = min(255, round(255 * a / n))
	return bytes(out)


# ---------------------------------------------------------------------------
# Motion
# ---------------------------------------------------------------------------

def texture_from_pixels(renderer, pixels: bytes, w: int, h: int):
	"""Upload bake() output as a linearly filtered, alpha-blended texture."""
	buffer = ctypes.create_string_buffer(pixels)
	surface = sdl3.SDL_CreateSurfaceFrom(
		w, h, sdl3.SDL_PIXELFORMAT_ARGB8888, ctypes.cast(buffer, ctypes.c_void_p), w * 4)
	texture = sdl3.SDL_CreateTextureFromSurface(renderer, surface)
	sdl3.SDL_DestroySurface(surface)
	if texture:
		sdl3.SDL_SetTextureBlendMode(texture, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_SetTextureScaleMode(texture, sdl3.SDL_SCALEMODE_LINEAR)
	return texture


def ease_out_cubic(t: float) -> float:
	t = clamp(t)
	return 1 - (1 - t) ** 3


def ease_out_elastic(t: float) -> float:
	t = clamp(t)
	if t in (0.0, 1.0):
		return t
	return 2 ** (-9 * t) * math.sin((t * 9 - 0.75) * math.tau / 3) + 1


def plane(r: float, th: float) -> tuple[float, float]:
	"""Offset of polar point (r, th) on the tilted orbital plane."""
	ox, oy = math.cos(th) * r, math.sin(th) * r * PLANE_SQUASH
	ct, st = math.cos(PLANE_TILT), math.sin(PLANE_TILT)
	return ox * ct - oy * st, ox * st + oy * ct


def approach(value: float, target: float, rate: float, dt: float) -> float:
	step = rate * dt
	if value < target:
		return min(target, value + step)
	return max(target, value - step)


class Spark:
	__slots__ = ("colour", "curl", "life", "size", "ttl", "vx", "vy", "x", "y")

	def __init__(self, x: float, y: float, scale: float, additive: bool) -> None:
		# Out along the orbital plane; heavy drag keeps them close to the disc
		self.x, self.y = x, y
		self.vx, self.vy = plane(random.uniform(60, 190) * scale, random.uniform(0, math.tau))
		self.vy *= 1.6
		# Launch staggered over a moment so the burst doesn't blow out to white
		self.life = -random.uniform(0, 0.04)
		self.ttl = random.uniform(0.3, 0.6)
		self.size = random.uniform(0.6, 1.2)
		# Curl with the spin, so the spray swirls like the galaxy behind it
		self.curl = random.uniform(2.0, 6.0)
		if additive and random.random() < 0.15:
			self.colour = STAR_WHITE
		else:
			self.colour = random.choice(SPARK_COLOURS)

	def step(self, dt: float) -> bool:
		self.life += dt
		if self.life >= self.ttl:
			return False
		if self.life < 0:
			return True
		drag = math.exp(-5.5 * dt)
		# Curl the path, fading as the spark slows, so trails spiral outwards
		turn = self.curl * dt * (1 - self.life / self.ttl)
		c, s = math.cos(turn), math.sin(turn)
		self.vx, self.vy = (self.vx * c - self.vy * s) * drag, (self.vx * s + self.vy * c) * drag
		self.x += self.vx * dt
		self.y += self.vy * dt
		return True


class MenuDisc:
	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.size = 0
		self.rim = None
		self.hub = None
		self.core_mono = None
		self.core_colour = None
		self.ripple = None
		# Effect layers, baked off the main thread
		self.fx: dict[str, object] = {}
		self.fx_size = 0
		self.fx_pixels: dict[str, tuple[int, int, bytes]] | None = None
		self.fx_thread: threading.Thread | None = None

		self.hover = 0.0
		self.bloom = 0.0
		self.galaxy = 0.0
		self.moons = 0.0
		self.galaxy_angle = 0.0
		self.moon_phase = [0.0, 2.1, 4.2]
		self.spin_start: float | None = None
		self.burst_done = True
		# The colour layer is not symmetric under a half turn, so the disc rests
		# wherever its last spin left it rather than snapping back to 0
		self.angle = 0.0
		self.spin_from = 0.0
		self.spin_to = 0.0
		self.sparks: list[Spark] = []
		# Infalling stardust: (delay, start radius, start angle, colour, size)
		self.infall: list[tuple[float, float, float, RGB, float]] = []
		self.burst_at: float | None = None
		self.centre = (0.0, 0.0)
		self.bar = (0, 0, 0, 0)
		self.additive = True
		self.last_time = time.monotonic()
		self.fx_time = self.last_time

	# -- Textures -----------------------------------------------------------

	def texture(self, pixels: bytes, w: int, h: int):
		return texture_from_pixels(self.tauon.renderer, pixels, w, h)

	def destroy(self) -> None:
		for texture in (self.rim, self.hub, self.core_mono, self.core_colour, self.ripple, *self.fx.values()):
			if texture:
				sdl3.SDL_DestroyTexture(texture)
		self.rim = self.hub = self.core_mono = self.core_colour = self.ripple = None
		self.fx = {}
		self.size = 0
		self.fx_size = 0

	def bake_fx(self, galaxy_px: int) -> None:
		pixels = {
			"galaxy": (galaxy_px, galaxy_px, bake(shade_galaxy, galaxy_px, ss=2)),
			"star": (24, 24, bake(shade_star, 24, ss=2)),
			"streak": (48, 8, bake(shade_streak, 48, 8, ss=2)),
			"flare": (160, 10, bake(shade_flare, 160, 10, ss=2)),
		}
		self.fx_pixels = pixels

	def ensure(self, size: int, galaxy_px: int) -> None:
		if size != self.size or not self.rim:
			for texture in (self.rim, self.hub, self.core_mono, self.core_colour, self.ripple):
				if texture:
					sdl3.SDL_DestroyTexture(texture)
			self.size = size
			self.rim = self.texture(bake(shade_rim, size), size, size)
			self.hub = self.texture(bake(shade_hub, size), size, size)
			self.core_mono = self.texture(bake(shade_core_mono, size), size, size)
			self.core_colour = self.texture(bake(shade_core_colour, size), size, size)
			rs = round(size * RIPPLE_SPAN)
			self.ripple = self.texture(bake(shade_ripple, rs, span=RIPPLE_SPAN, ss=3), rs, rs)
		if galaxy_px != self.fx_size and self.fx_thread is None:
			self.fx_size = galaxy_px
			self.fx_pixels = None
			self.fx_thread = threading.Thread(target=self.bake_fx, args=(galaxy_px,), daemon=True)
			self.fx_thread.start()
		if self.fx_thread is not None and not self.fx_thread.is_alive():
			self.fx_thread = None
			if self.fx_pixels:
				for texture in self.fx.values():
					if texture:
						sdl3.SDL_DestroyTexture(texture)
				self.fx = {name: self.texture(px, w, h) for name, (w, h, px) in self.fx_pixels.items()}
				self.fx_pixels = None

	# -- Drawing ------------------------------------------------------------

	def blit(self, texture, cx: float, cy: float, w: float, h: float, colour: RGB | ColourRGBA | None,
			alpha: float, angle: float = 0.0, glow: bool = False) -> None:
		"""Draw texture centred on (cx, cy). glow: additive light (on dark themes)."""
		if not texture or alpha <= 0.004:
			return
		if colour is None:
			r = g = b = 255
			a = 255
		elif isinstance(colour, ColourRGBA):
			r, g, b, a = colour.r, colour.g, colour.b, colour.a
		else:
			r, g, b = (round(v) for v in colour)
			a = 255
		sdl3.SDL_SetTextureColorMod(texture, r, g, b)
		sdl3.SDL_SetTextureAlphaMod(texture, round(clamp(a * alpha, 0, 255)))
		sdl3.SDL_SetTextureBlendMode(
			texture, sdl3.SDL_BLENDMODE_ADD if glow and self.additive else sdl3.SDL_BLENDMODE_BLEND)
		dst = sdl3.SDL_FRect(cx - w / 2, cy - h / 2, w, h)
		if angle % 360:
			sdl3.SDL_RenderTextureRotated(self.tauon.renderer, texture, None, dst, angle, None, sdl3.SDL_FLIP_NONE)
		else:
			sdl3.SDL_RenderTexture(self.tauon.renderer, texture, None, dst)

	def clip(self, reach: float | None = None):
		"""Clip to the bar, or to reach px either side of the disc within it.
		Returns the previous clip state for unclip()."""
		renderer = self.tauon.renderer
		prev = None
		if sdl3.SDL_RenderClipEnabled(renderer):
			prev = sdl3.SDL_Rect()
			sdl3.SDL_GetRenderClipRect(renderer, ctypes.byref(prev))
		x, y, w, h = self.bar
		if reach is not None:
			left = max(x, self.centre[0] - reach)
			w = min(x + w, self.centre[0] + reach) - left
			x = left
		rect = sdl3.SDL_Rect(round(x), round(y), round(w), round(h))
		sdl3.SDL_SetRenderClipRect(renderer, ctypes.byref(rect))
		return prev

	def unclip(self, prev) -> None:
		sdl3.SDL_SetRenderClipRect(self.tauon.renderer, ctypes.byref(prev) if prev is not None else None)

	def trigger(self) -> None:
		"""Play the open animation: turn on to the next half-turn rest position,
		continuing from mid-spin if already turning."""
		self.spin_from = self.angle
		self.spin_to = (math.floor(self.angle / 180 + 1e-6) + 1) * 180
		self.spin_start = time.monotonic()
		self.burst_done = False
		scale = self.tauon.gui.scale
		self.infall = [
			(random.uniform(0, 0.08), random.uniform(22, 46) * scale, random.uniform(0, math.tau),
				STAR_WHITE if self.additive and random.random() < 0.2 else random.choice(SPARK_COLOURS),
				random.uniform(0.7, 1.2))
			for _ in range(INFALL_COUNT)]

	def burst(self, now: float) -> None:
		scale = self.tauon.gui.scale
		cx, cy = self.centre
		self.sparks.extend(Spark(cx, cy, scale, self.additive) for _ in range(BURST_COUNT))
		self.burst_at = now
		self.fx_time = now

	def render(self, rect: tuple[int, int, int, int], hot: bool, open_: bool,
			idle: ColourRGBA, active: ColourRGBA, bar: tuple[int, int, int, int], additive: bool) -> None:
		"""Draw centred in rect. hot: hovered or open; open_: the menu is showing.
		bar: the strip effects are confined to; additive: glow with additive light."""
		gui = self.tauon.gui
		scale = gui.scale
		size = round(DISC_PX * scale)
		self.ensure(size, round(GALAXY_PX * scale))
		self.bar = bar
		self.additive = additive
		now = time.monotonic()
		dt = min(0.05, now - self.last_time)
		self.last_time = now

		self.hover = approach(self.hover, 1.0 if hot else 0.0, HOVER_RATE, dt)
		self.bloom = approach(self.bloom, 1.0 if open_ else 0.0, BLOOM_RATE, dt)
		self.galaxy = approach(self.galaxy, 1.0 if open_ else 0.0, GALAXY_IN if open_ else GALAXY_OUT, dt)
		self.moons = approach(self.moons, 1.0 if hot else 0.0, MOON_RATE, dt)
		h = self.hover
		mono = ColourRGBA(
			round(idle.r + (active.r - idle.r) * h), round(idle.g + (active.g - idle.g) * h),
			round(idle.b + (active.b - idle.b) * h), round(idle.a + (active.a - idle.a) * h))

		squash = 1.0
		galaxy_speed = 32.0
		ripple_t = None
		el = None
		if self.spin_start is not None:
			el = now - self.spin_start
			if el < INFALL:
				# Compresses faster as the stardust falls in
				squash = 1 - 0.24 * (el / INFALL) ** 2.2
			else:
				if not self.burst_done:
					self.burst_done = True
					self.burst(now)
				be = el - INFALL
				squash = 0.78 + 0.22 * ease_out_elastic(be / SPRING_TIME)
				p = ease_out_cubic(be / SPIN_TIME)
				self.angle = self.spin_from + (self.spin_to - self.spin_from) * p
				galaxy_speed += 1300 * math.exp(-4.5 * be)
				if be < RIPPLE_TIME:
					ripple_t = be / RIPPLE_TIME
				if be >= max(SPIN_TIME, SPRING_TIME, RIPPLE_TIME):
					self.spin_start = None
					self.angle = self.spin_to % 360
					squash = 1.0
		self.galaxy_angle = (self.galaxy_angle + galaxy_speed * dt) % 360

		x0 = rect[0] + (rect[2] - size) // 2
		y0 = rect[1] + (rect[3] - size) // 2
		cx, cy = x0 + size / 2, y0 + size / 2
		self.centre = (cx, cy)
		ds = size * squash

		prev = self.clip()
		if self.galaxy > 0 and "galaxy" in self.fx:
			g = ease_out_cubic(self.galaxy)
			gs = round(GALAXY_PX * scale) * (0.35 + 0.65 * g)
			self.blit(self.fx["galaxy"], cx, cy, gs, gs, None, 0.95 * g, self.galaxy_angle, glow=True)
		if ripple_t is not None:
			rs = size * RIPPLE_SPAN * (0.6 + 0.9 * ease_out_cubic(ripple_t))
			self.blit(self.ripple, cx, cy, rs, rs, None, (1 - ripple_t) ** 2, glow=True)

		moons = self.moon_positions(dt, cx, cy, scale) if self.moons > 0 and "star" in self.fx else []
		for mx, my, depth, colour in moons:
			if depth < 0:
				self.draw_moon(mx, my, depth, colour, scale)

		# The rim steps back as the arcs take colour so they read as the focus
		self.blit(self.rim, cx, cy, ds, ds, mono, 1 - 0.4 * self.bloom)
		self.blit(self.core_mono, cx, cy, ds, ds, mono, 1 - self.bloom, self.angle)
		self.blit(self.core_colour, cx, cy, ds, ds, None, self.bloom, self.angle)
		# Colour stays on the arcs: a neutral spindle keeps them reading as two
		# reflections around a centre rather than one continuous stroke
		self.blit(self.hub, cx, cy, ds, ds, mono, 1.0)

		for mx, my, depth, colour in moons:
			if depth >= 0:
				self.draw_moon(mx, my, depth, colour, scale)

		# Flash of the core at the burst
		if self.burst_at is not None and "star" in self.fx:
			ft = (now - self.burst_at) / 0.3
			if ft < 1:
				fs = size * (1.0 + 1.2 * ease_out_cubic(ft))
				self.blit(self.fx["star"], cx, cy, fs, fs, STAR_WHITE if additive else WARM[1][1], 0.8 * (1 - ft) ** 2, glow=True)
		self.unclip(prev)

		animating = (el is not None or self.sparks or self.burst_at is not None
			or self.hover not in (0.0, 1.0) or self.bloom not in (0.0, 1.0)
			or self.galaxy not in (0.0, 1.0) or self.moons not in (0.0, 1.0))
		if animating:
			gui.delay_frame(self.tauon.frame_pace())
		elif self.galaxy or self.moons:
			# Idle orbit: a gentler frame rate is plenty
			gui.delay_frame(1 / IDLE_FPS)

	def moon_positions(self, dt: float, cx: float, cy: float, scale: float) -> list[tuple[float, float, float, RGB]]:
		rx, ry = 14.5 * scale, 4.2 * scale
		tilt = math.radians(-18)
		ct, st = math.cos(tilt), math.sin(tilt)
		out = []
		for i, speed in enumerate((1.9, 2.7, 3.6)):
			self.moon_phase[i] = (self.moon_phase[i] + speed * dt) % math.tau
			p = self.moon_phase[i]
			ox, oy = math.cos(p) * rx, math.sin(p) * ry
			out.append((cx + ox * ct - oy * st, cy + ox * st + oy * ct, math.sin(p), MOON_COLOURS[i]))
		return out

	def draw_moon(self, x: float, y: float, depth: float, colour: RGB, scale: float) -> None:
		s = (5.5 + 1.8 * depth) * scale
		self.blit(self.fx["star"], x, y, s, s, colour, self.moons * (0.62 + 0.38 * depth), glow=True)

	def render_fx(self) -> None:
		"""Click effects around the disc; drawn last so they sit over everything
		near it, clipped to FX_REACH either side."""
		now = time.monotonic()
		infalling = self.spin_start is not None and now - self.spin_start < INFALL
		if not self.fx or (not self.sparks and self.burst_at is None and not infalling):
			return
		dt = min(0.05, now - self.fx_time)
		self.fx_time = now
		scale = self.tauon.gui.scale
		cx, cy = self.centre
		streak, star, flare = self.fx["streak"], self.fx["star"], self.fx["flare"]
		prev = self.clip(FX_REACH * scale)

		if infalling:
			el = now - self.spin_start
			for delay, r0, th0, colour, size in self.infall:
				p = (el - delay) / (INFALL - delay)
				if not 0 < p < 1:
					continue
				# Accelerating inward spiral, turning faster as it closes in
				e = p ** 2.2
				dx, dy = plane(r0 * (1 - e), th0 + 2.4 * math.pi * e)
				e0 = max(0.0, p - 0.08) ** 2.2
				px, py = plane(r0 * (1 - e0), th0 + 2.4 * math.pi * e0)
				x, y = cx + dx, cy + dy
				vx, vy = dx - px, dy - py
				dist = math.hypot(vx, vy)
				fade = smoothstep(0.0, 0.2, p) * (0.45 + 0.55 * p) * smoothstep(1.0, 0.9, p)
				if dist > 0.5:
					length = clamp(dist * 1.3, 2 * scale, 16 * scale)
					ux, uy = vx / dist, vy / dist
					self.blit(streak, x - ux * length * 0.4, y - uy * length * 0.4, length, 2.4 * scale * size,
						colour, fade, math.degrees(math.atan2(uy, ux)), glow=True)
				hs = 3.6 * scale * size
				self.blit(star, x, y, hs, hs, colour, fade, glow=True)

		if self.burst_at is not None:
			t = now - self.burst_at
			if t < GLINT_TIME:
				# Four-point glint: a long horizontal spike and a shorter vertical one
				gt = t / GLINT_TIME
				fade = (1 - gt) ** 2
				gw = 2 * FX_REACH * scale * (0.35 + 0.65 * ease_out_cubic(gt * 1.5))
				self.blit(flare, cx, cy, gw, 4 * scale, COOL[3][1], fade, glow=True)
				self.blit(flare, cx, cy, gw * 0.6, 2 * scale, STAR_WHITE, fade, glow=True)
				self.blit(flare, cx, cy, gw * 0.3, 2.5 * scale, STAR_WHITE, fade, 90, glow=True)
			else:
				self.burst_at = None

		alive = []
		for spark in self.sparks:
			if not spark.step(dt):
				continue
			alive.append(spark)
			if spark.life < 0:
				continue
			fade = (1 - spark.life / spark.ttl) ** 1.3 * clamp(spark.life / 0.04)
			speed = math.hypot(spark.vx, spark.vy)
			length = clamp(speed * 0.06, 2 * scale, 14 * scale)
			thick = 2.6 * scale * spark.size
			ux, uy = (spark.vx / speed, spark.vy / speed) if speed else (1.0, 0.0)
			angle = math.degrees(math.atan2(uy, ux))
			# The streak texture's head is at its right end; centre it behind the spark
			self.blit(streak, spark.x - ux * length * 0.4, spark.y - uy * length * 0.4, length, thick,
				spark.colour, fade, angle, glow=True)
			hs = 3.8 * scale * spark.size
			self.blit(star, spark.x, spark.y, hs, hs, spark.colour, fade, glow=True)
		self.sparks = alive
		self.unclip(prev)
		self.tauon.gui.delay_frame(self.tauon.frame_pace())
