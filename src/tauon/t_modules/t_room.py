"""Easter egg moduel, just for fun

**WAKE UP**

Implementation notes:

* Everything is drawn with ``SDL_RenderGeometry`` (perspective projection,
  near-plane clipping and painter's-order compositing are done here in
  Python), so it works on the app's existing SDL renderer / OpenGL context
  without touching raw GL state.
* The live UI frame (``gui.main_texture``) is mapped onto the monitor screen
  as a subdivided grid of textured quads, which approximates
  perspective-correct texturing well at this scale. The camera's start pose
  is computed so the screen quad exactly fills the viewport at t=0, making
  the F7 transition seamless.
* The room is a convex cell viewed from inside, so no depth sorting is
  needed: draw order is city -> rain -> glass -> walls -> furniture ->
  monitor -> glows -> vignette.
* The scene only hooks the final compose step of the frame; the UI keeps
  rendering into ``gui.main_texture`` as normal (so the little monitor stays
  live), and input to it is muted while the camera is out.
"""
from __future__ import annotations

import ctypes
import math
import random
import time
from typing import TYPE_CHECKING

import sdl3

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon

NEAR = 0.06
FOV = math.radians(58.0)
ZOOM_OUT_TIME = 5.4
ZOOM_IN_TIME = 2.4

# Room shell (metres). Front wall (monitor + window) is at z=0, the room
# extends toward +z; y is up.
RX0, RX1 = -2.4, 2.4
RY0, RY1 = 0.0, 2.7
RZ0, RZ1 = 0.0, 4.2

# Window opening in the front wall (spans most of the wall's width)
WX0, WX1 = 0.02, 2.18
WY0, WY1 = 0.92, 2.4
GLASS_Z = -0.05
WIN_CX, WIN_CY = (WX0 + WX1) / 2, (WY0 + WY1) / 2

# Monitor
SCR_CX, SCR_CY = -0.98, 1.16	# screen centre on the front wall
SCR_H = 0.36					# screen height in metres; width follows window aspect
SCR_Z = 0.30					# screen plane (monitor sits toward the back of the desk)
DESK_Y = 0.72					# desk top height

RAIN_N = 110
RUNNER_N = 24

# Backdrop clear colour. Matches the city sky (the far layer's lower-sky fill
# (7, 6, 16) times the far quad's (215, 212, 232) tint) so that when the camera
# pans at an angle and sees past the projected city quads, the exposed area
# blends with the skyline instead of showing black.
CITY_BACKDROP = (6, 5, 15)
MICRO_N = 42
MOTE_N = 12


def _smooth(t: float) -> float:
	"""Smootherstep ease 0..1."""
	t = min(1.0, max(0.0, t))
	return t * t * t * (t * (t * 6.0 - 15.0) + 10.0)


def _lerp(a: float, b: float, f: float) -> float:
	return a + (b - a) * f


class _Batch:
	"""Accumulates screen-space triangles and issues SDL_RenderGeometry calls,
	flushing whenever the texture / blend state changes."""

	def __init__(self, renderer) -> None:
		self.renderer = renderer
		self.verts: list[tuple] = []	# (x, y, u, v, r, g, b, a) floats, colours 0..1
		self.idx: list[int] = []
		self.texture = None
		self.additive = False

	def set_state(self, texture, additive: bool) -> None:
		if texture is not self.texture or additive != self.additive:
			self.flush()
			self.texture = texture
			self.additive = additive

	def poly(self, pts: list[tuple]) -> None:
		"""Add a convex polygon (fan-triangulated)."""
		base = len(self.verts)
		self.verts.extend(pts)
		for i in range(1, len(pts) - 1):
			self.idx += (base, base + i, base + i + 1)

	def flush(self) -> None:
		if not self.idx:
			self.verts.clear()
			return
		n = len(self.verts)
		arr = (sdl3.SDL_Vertex * n)()
		for i, (x, y, u, v, r, g, b, a) in enumerate(self.verts):
			w = arr[i]
			w.position.x = x
			w.position.y = y
			w.tex_coord.x = u
			w.tex_coord.y = v
			c = w.color
			c.r = r
			c.g = g
			c.b = b
			c.a = a
		ind = (ctypes.c_int * len(self.idx))(*self.idx)
		mode = sdl3.SDL_BLENDMODE_ADD if self.additive else sdl3.SDL_BLENDMODE_BLEND
		if self.texture is not None:
			sdl3.SDL_SetTextureBlendMode(self.texture, mode)
		else:
			sdl3.SDL_SetRenderDrawBlendMode(self.renderer, mode)
		sdl3.SDL_RenderGeometry(self.renderer, self.texture, arr, n, ind, len(self.idx))
		self.verts.clear()
		self.idx.clear()


class DreamRoom:

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.gui = tauon.gui
		self.inp = tauon.inp
		self.renderer = tauon.renderer
		self.window_size = tauon.window_size

		self.phase: str = "off"		# off | out | idle | in
		self.t: float = 0.0			# 0 = camera in the screen, 1 = pulled back
		self.T: float = 0.0			# scene clock for animation
		self.last_frame: float = 0.0

		self.batch = _Batch(self.renderer)
		self.city_far = None
		self.city_near = None

		# Camera state for the current frame (set in render)
		self._eye = (0.0, 0.0, 0.0)
		self._right = (1.0, 0.0, 0.0)
		self._up = (0.0, 1.0, 0.0)
		self._fwd = (0.0, 0.0, -1.0)
		self._focal = 1.0
		self._cx = 0.0
		self._cy = 0.0

		rnd = random.Random(2077)
		# Rain outside the window: [x, y, z, speed, length, drift]
		self.rain = [[
			rnd.uniform(-4.0, 8.0), rnd.uniform(-3.0, 7.0), rnd.uniform(-8.0, -0.3),
			rnd.uniform(6.0, 9.5), rnd.uniform(0.22, 0.5), rnd.uniform(-0.9, -0.4),
		] for _ in range(RAIN_N)]
		# Droplets running down the glass, in window UV space: [u, v, size, speed, phase]
		self.runners = [[
			rnd.random(), rnd.random(), rnd.uniform(0.0025, 0.006),
			rnd.uniform(0.015, 0.075), rnd.uniform(0, 9),
		] for _ in range(RUNNER_N)]
		# Static micro-droplets on the glass: [u, v, size, phase]
		self.micro = [[
			rnd.random(), rnd.random(), rnd.uniform(0.0025, 0.006), rnd.uniform(0, 9),
		] for _ in range(MICRO_N)]
		# Dust motes drifting in the window light: [x, y, z, phase]
		self.motes = [[
			rnd.uniform(0.2, 2.1), rnd.uniform(0.3, 2.2), rnd.uniform(0.15, 2.6), rnd.uniform(0, 9),
		] for _ in range(MOTE_N)]
		# Aircraft drifting across the skyline: [y, z, speed, phase, direction]
		self.craft = [
			[4.8, -30.0, 1.6, 3.0, 1],
			[3.4, -24.0, 2.3, 14.0, -1],
			[6.1, -36.0, 1.1, 27.0, 1],
		]

	# ---------------------------------------------------------------- control

	@property
	def active(self) -> bool:
		return self.phase != "off"

	def toggle(self) -> None:
		if self.phase == "off":
			self.phase = "out"
			self.t = 0.0
			self.last_frame = time.monotonic()
		elif self.phase in ("out", "idle"):
			self.phase = "in"
		elif self.phase == "in":
			self.phase = "out"

	def close_instant(self) -> None:
		self.phase = "off"

	def handle_input(self) -> None:
		"""Mute mouse input to the (hidden, full-size) UI while the camera is
		out, and let Escape or a click fly back in. Keyboard passes through so
		playback control keeps working on the little screen."""
		if not self.active:
			return
		inp = self.inp
		if inp.key_esc_press:
			inp.key_esc_press = False
			if self.phase in ("out", "idle"):
				self.phase = "in"
		# A click anywhere also flies the camera back in
		if (inp.mouse_click or inp.right_click) and self.phase in ("out", "idle"):
			self.phase = "in"
		inp.mouse_click = False
		inp.d_mouse_click = False
		inp.right_click = False
		inp.middle_click = False
		inp.mouse_wheel = 0
		inp.mouse_position[0] = -3000.0
		inp.mouse_position[1] = -3000.0

	# ------------------------------------------------------------- projection

	def _camera(self, eye, target) -> None:
		ex, ey, ez = eye
		fx, fy, fz = target[0] - ex, target[1] - ey, target[2] - ez
		fl = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
		fx, fy, fz = fx / fl, fy / fl, fz / fl
		# right = forward x world-up
		rx, ry, rz = -fz, 0.0, fx
		rl = math.sqrt(rx * rx + rz * rz) or 1.0
		rx, rz = rx / rl, rz / rl
		# up = right x forward
		ux = ry * fz - rz * fy
		uy = rz * fx - rx * fz
		uz = rx * fy - ry * fx
		self._eye = eye
		self._right = (rx, ry, rz)
		self._up = (ux, uy, uz)
		self._fwd = (fx, fy, fz)
		w, h = self.window_size[0], self.window_size[1]
		self._focal = (h * 0.5) / math.tan(FOV / 2)
		self._cx = w * 0.5
		self._cy = h * 0.5

	def _quad(self, pts, cols, uvs=None, texture=None, additive=False) -> None:
		"""Project a world-space polygon (3-4 points, convex) and queue it.
		``cols`` are per-vertex (r, g, b, a) 0..255."""
		ex, ey, ez = self._eye
		rx, ry, rz = self._right
		ux, uy, uz = self._up
		fx, fy, fz = self._fwd
		poly = []
		behind = 0
		for i, (px, py, pz) in enumerate(pts):
			dx, dy, dz = px - ex, py - ey, pz - ez
			xv = dx * rx + dy * ry + dz * rz
			yv = dx * ux + dy * uy + dz * uz
			zv = dx * fx + dy * fy + dz * fz
			u, v = uvs[i] if uvs else (0.0, 0.0)
			r, g, b, a = cols[i]
			poly.append((xv, yv, zv, u, v, r, g, b, a))
			if zv < NEAR:
				behind += 1
		if behind == len(poly):
			return
		if behind:
			out = []
			n = len(poly)
			for i in range(n):
				a_ = poly[i]
				b_ = poly[(i + 1) % n]
				a_in = a_[2] >= NEAR
				b_in = b_[2] >= NEAR
				if a_in:
					out.append(a_)
				if a_in != b_in:
					f = (NEAR - a_[2]) / (b_[2] - a_[2])
					out.append(tuple(a_[j] + (b_[j] - a_[j]) * f for j in range(9)))
			poly = out
			if len(poly) < 3:
				return
		focal, cx, cy = self._focal, self._cx, self._cy
		scr = []
		for (xv, yv, zv, u, v, r, g, b, a) in poly:
			s = focal / zv
			scr.append((cx + xv * s, cy - yv * s, u, v, r / 255, g / 255, b / 255, a / 255))
		self.batch.set_state(texture, additive)
		self.batch.poly(scr)

	def _glow(self, centre, half_w, half_h, col, alpha, axis="z") -> None:
		"""Soft radial glow: a fan from a bright centre vertex to transparent
		corners, on an axis-aligned plane through ``centre``."""
		x, y, z = centre
		if axis == "z":
			corners = [(x - half_w, y - half_h, z), (x + half_w, y - half_h, z),
				(x + half_w, y + half_h, z), (x - half_w, y + half_h, z)]
		else:	# horizontal plane (glow lying on a surface)
			corners = [(x - half_w, y, z - half_h), (x + half_w, y, z - half_h),
				(x + half_w, y, z + half_h), (x - half_w, y, z + half_h)]
		r, g, b = col
		cc = (r, g, b, alpha)
		oc = (r, g, b, 0)
		for i in range(4):
			a = corners[i]
			b_ = corners[(i + 1) % 4]
			self._quad([centre, a, b_], [cc, oc, oc], additive=True)

	# ------------------------------------------------------------ city assets

	def _fill(self, x, y, w, h, col) -> None:
		r, g, b, a = col
		sdl3.SDL_SetRenderDrawColor(self.renderer, r, g, b, a)
		rect = sdl3.SDL_FRect(float(x), float(y), float(w), float(h))
		sdl3.SDL_RenderFillRect(self.renderer, ctypes.byref(rect))

	def _neon(self, x, y, w, h, col) -> None:
		r, g, b = col
		self._fill(x - 4, y - 4, w + 8, h + 8, (r, g, b, 26))
		self._fill(x - 2, y - 2, w + 4, h + 4, (r, g, b, 66))
		self._fill(x, y, w, h, (r, g, b, 235))

	def _ensure_assets(self) -> None:
		if self.city_far is not None:
			return
		renderer = self.renderer
		prev_target = sdl3.SDL_GetRenderTarget(renderer)

		# --- Far layer: sky gradient, stars, distant towers ---
		fw, fh = 1024, 256
		tex = sdl3.SDL_CreateTexture(
			renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, fw, fh)
		sdl3.SDL_SetTextureScaleMode(tex, sdl3.SDL_SCALEMODE_LINEAR)
		sdl3.SDL_SetRenderTarget(renderer, tex)
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
		rnd = random.Random(1808)
		horizon = 195
		stops = [
			(0.00, (5, 6, 15)), (0.45, (16, 14, 42)), (0.72, (48, 26, 70)),
			(0.82, (96, 46, 96)), (1.00, (58, 30, 62)),
		]
		strips = 64
		for i in range(strips):
			f = i / (strips - 1)
			for j in range(len(stops) - 1):
				f0, c0 = stops[j]
				f1, c1 = stops[j + 1]
				if f0 <= f <= f1:
					k = (f - f0) / (f1 - f0) if f1 > f0 else 0
					col = tuple(round(_lerp(c0[n], c1[n], k)) for n in range(3))
					break
			y = f * horizon
			self._fill(0, y, fw, horizon / strips + 1, (*col, 255))
		self._fill(0, horizon, fw, fh - horizon, (7, 6, 16, 255))
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
		for _ in range(90):	# stars
			self._fill(rnd.uniform(0, fw), rnd.uniform(0, 140), 1, 1,
				(200, 210, 255, rnd.randint(30, 110)))
		window_palette = [(95, 210, 255), (255, 170, 105), (250, 120, 190), (180, 200, 255)]
		x = 0.0
		while x < fw:
			bw = rnd.uniform(14, 42)
			bh = rnd.uniform(25, 150)
			top = horizon - bh
			self._fill(x, top, bw, bh + 4, (10, 9, 22, 255))
			self._fill(x, top, bw, 1, (20, 18, 42, 255))
			if rnd.random() < 0.3:	# antenna
				self._fill(x + bw / 2, top - rnd.uniform(8, 20), 1, 20, (12, 11, 26, 255))
				if rnd.random() < 0.6:
					self._fill(x + bw / 2, top - rnd.uniform(8, 18), 2, 2, (255, 60, 80, 180))
			if bh > 45:
				wy = top + 4
				while wy < horizon - 6:
					wx = x + 2
					while wx < x + bw - 3:
						if rnd.random() < 0.14:
							c = rnd.choice(window_palette)
							self._fill(wx, wy, 2, 2, (*c, rnd.randint(120, 220)))
						wx += 5
					wy += 6
			x += bw + rnd.uniform(0, 14)
		for _ in range(8):	# distant neon signage
			c = rnd.choice([(255, 40, 180), (40, 230, 255), (150, 80, 255)])
			self._neon(rnd.uniform(20, fw - 50), rnd.uniform(120, horizon - 12),
				rnd.uniform(8, 26), rnd.uniform(3, 6), c)
		self.city_far = tex

		# --- Near layer: dark silhouettes, sparse bright windows, big neon ---
		nw, nh = 1024, 320
		tex = sdl3.SDL_CreateTexture(
			renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, nw, nh)
		sdl3.SDL_SetTextureScaleMode(tex, sdl3.SDL_SCALEMODE_LINEAR)
		sdl3.SDL_SetRenderTarget(renderer, tex)
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderClear(renderer)
		x = 0.0
		while x < nw:
			bw = rnd.uniform(34, 95)
			top = rnd.uniform(40, 230) if rnd.random() < 0.75 else rnd.uniform(20, 60)
			self._fill(x, top, bw, nh - top, (6, 5, 14, 255))
			sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
			if rnd.random() < 0.6:	# city-glow rim light on the roofline
				self._fill(x, top, bw, 1, (60, 140, 190, 110))
			wy = top + 6
			while wy < nh - 8:
				wx = x + 4
				while wx < x + bw - 5:
					if rnd.random() < 0.08:
						c = rnd.choice(window_palette)
						self._fill(wx, wy, 3, 2, (*c, rnd.randint(150, 240)))
					wx += 8
				wy += 9
			sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
			x += bw + rnd.uniform(0, 26)
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
		for _ in range(3):	# large neon signs
			c = rnd.choice([(255, 40, 180), (40, 230, 255), (255, 120, 60)])
			self._neon(rnd.uniform(40, nw - 110), rnd.uniform(70, 220),
				rnd.uniform(30, 70), rnd.uniform(8, 14), c)
		c = rnd.choice([(255, 40, 180), (40, 230, 255)])
		self._neon(rnd.uniform(100, nw - 100), rnd.uniform(60, 140), 8, 60, c)	# vertical sign
		self.city_near = tex

		sdl3.SDL_SetRenderTarget(renderer, prev_target)
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

	# --------------------------------------------------------------- animate

	def _advance(self, dt: float) -> None:
		for d in self.rain:
			d[1] -= d[3] * dt
			d[0] += d[5] * dt
			if d[1] < -3.2:
				d[1] += 10.0 + random.uniform(0, 1.5)
				d[0] = random.uniform(-4.0, 8.0)
		for r in self.runners:
			# Runners stall and surge a little, like drops gaining mass
			r[1] += (r[3] + r[3] * 0.8 * math.sin(self.T * 0.9 + r[4])) * dt
			r[0] += math.sin(self.T * 2.2 + r[4]) * 0.004 * dt
			if r[1] > 1.02:
				r[1] = -random.uniform(0.02, 0.25)
				r[0] = random.random()
				r[3] = random.uniform(0.015, 0.075)
		for m in self.motes:
			m[0] += math.sin(self.T * 0.21 + m[3]) * 0.010 * dt
			m[1] += 0.008 * dt * math.sin(self.T * 0.13 + m[3] * 2)

	# ----------------------------------------------------------------- render

	def render(self) -> None:
		gui = self.gui
		renderer = self.renderer
		now = time.monotonic()
		dt = min(max(now - self.last_frame, 0.0), 0.05)
		self.last_frame = now
		self.T += dt

		if self.phase == "out":
			self.t += dt / ZOOM_OUT_TIME
			if self.t >= 1.0:
				self.t = 1.0
				self.phase = "idle"
		elif self.phase == "in":
			self.t -= dt / ZOOM_IN_TIME
			if self.t <= 0.0:
				self.t = 0.0

		self._ensure_assets()
		self._advance(dt)

		w, h = self.window_size[0], self.window_size[1]
		aspect = w / max(1, h)
		scr_w = SCR_H * aspect
		e = _smooth(self.t)
		T = self.T

		# Camera path: dolly out of the screen, drifting up-right so both the
		# monitor and the window frame the final shot. Gentle idle sway.
		d0 = (SCR_H / 2) / math.tan(FOV / 2)
		start_eye = (SCR_CX, SCR_CY, SCR_Z + d0)
		end_eye = (0.85, 1.58, 3.35)
		end_tgt = (-0.22, 1.28, 0.0)
		sway = e
		eye = (
			_lerp(start_eye[0], end_eye[0], e) + math.sin(T * 0.31) * 0.05 * sway,
			_lerp(start_eye[1], end_eye[1], e) + 0.10 * math.sin(math.pi * e)
			+ math.sin(T * 0.23 + 1.7) * 0.03 * sway,
			_lerp(start_eye[2], end_eye[2], e) + math.sin(T * 0.17 + 0.6) * 0.04 * sway,
		)
		tgt = (
			_lerp(SCR_CX, end_tgt[0], e) + math.sin(T * 0.19 + 4.0) * 0.02 * sway,
			_lerp(SCR_CY, end_tgt[1], e) + math.sin(T * 0.27 + 2.2) * 0.015 * sway,
			_lerp(SCR_Z, end_tgt[2], e),
		)
		self._camera(eye, tgt)

		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
		sdl3.SDL_SetRenderDrawColor(renderer, *CITY_BACKDROP, 255)
		sdl3.SDL_RenderClear(renderer)
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

		q = self._quad
		batch = self.batch

		# ------------------------------------------------ the world outside
		# Far skyline (sky gradient lives in the texture)
		fcol = [(215, 212, 232, 255)] * 4
		q([(-14, 18, -45), (20, 18, -45), (20, -6, -45), (-14, -6, -45)], fcol,
			uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], texture=self.city_far)
		# Pulsing beacons on the far layer
		q3 = 60 + 55 * math.sin(T * 0.8)
		self._glow((7.2, 5.8, -44.8), 0.9, 0.9, (255, 60, 160), int(max(0, q3)))
		q3 = 50 + 45 * math.sin(T * 1.3 + 3)
		self._glow((-6.5, 3.9, -44.8), 0.7, 0.7, (60, 220, 255), int(max(0, q3)))

		# Aircraft lights drifting between the layers
		for (cy_, cz, speed, phase, direction) in self.craft:
			span = 26.0
			x = ((T * speed + phase) % span) - 8.0
			if direction < 0:
				x = 18.0 - x
			self._glow((x, cy_, cz), 0.22, 0.22, (255, 235, 190), 150)
			tail = 0.9 * direction
			q([(x - tail, cy_ + 0.03, cz), (x, cy_ + 0.05, cz),
				(x, cy_ - 0.05, cz), (x - tail, cy_ - 0.03, cz)],
				[(255, 220, 170, 0), (255, 220, 170, 90), (255, 220, 170, 90), (255, 220, 170, 0)],
				additive=True)

		# Near skyline
		ncol = [(190, 188, 210, 255)] * 4
		q([(-5.5, 7, -16), (9, 7, -16), (9, -3, -16), (-5.5, -3, -16)], ncol,
			uvs=[(0, 0), (1, 0), (1, 1), (0, 1)], texture=self.city_near)

		# Rain, lit faintly by the city
		for (x, y, z, speed, ln, drift) in self.rain:
			k = (z + 8.0) / 7.7	# 0 far .. 1 near the glass
			a = 25 + 70 * k
			hw = 0.004 + 0.005 * k
			tx = drift * 0.05
			q([(x - hw, y, z), (x + hw, y, z), (x + hw + tx, y + ln, z), (x - hw + tx, y + ln, z)],
				[(150, 190, 235, int(a)), (150, 190, 235, int(a)),
				(150, 190, 235, 0), (150, 190, 235, 0)], additive=True)

		# ------------------------------------------------------- glass pane
		gcol = [(70, 110, 160, 26), (90, 130, 180, 34), (70, 110, 160, 22), (60, 90, 140, 18)]
		q([(WX0, WY1, GLASS_Z), (WX1, WY1, GLASS_Z), (WX1, WY0, GLASS_Z), (WX0, WY0, GLASS_Z)], gcol)
		# Diagonal sheen
		q([(WX0 + 0.2, WY1, GLASS_Z), (WX0 + 0.55, WY1, GLASS_Z),
			(WX1 - 0.3, WY0, GLASS_Z), (WX1 - 0.65, WY0, GLASS_Z)],
			[(200, 220, 255, 14), (200, 220, 255, 4), (200, 220, 255, 14), (200, 220, 255, 4)],
			additive=True)

		def glass_pt(u: float, v: float) -> tuple[float, float, float]:
			return (WX0 + u * (WX1 - WX0), WY1 - v * (WY1 - WY0), GLASS_Z + 0.002)

		for (u, v, ph) in [(m[0], m[1], m[3]) for m in self.micro]:
			a = 28 + 24 * math.sin(T * 0.7 + ph)
			s = 0.006
			x, y, z = glass_pt(u, v)
			q([(x - s, y + s, z), (x + s, y + s, z), (x + s, y - s, z), (x - s, y - s, z)],
				[(190, 215, 240, int(max(6, a)))] * 4, additive=True)
		for (u, v, s, _sp, _ph) in self.runners:
			if not (0.0 <= v <= 1.0):
				continue
			x, y, z = glass_pt(u, v)
			sw = s * (WX1 - WX0)
			# trail
			q([(x - sw * 0.4, y + sw * 12, z), (x + sw * 0.4, y + sw * 12, z),
				(x + sw * 0.6, y, z), (x - sw * 0.6, y, z)],
				[(190, 215, 240, 0), (190, 215, 240, 0), (190, 215, 240, 60), (190, 215, 240, 60)],
				additive=True)
			# head
			q([(x - sw, y + sw, z), (x + sw, y + sw, z), (x + sw, y - sw, z), (x - sw, y - sw, z)],
				[(210, 230, 250, 120)] * 4, additive=True)

		# ------------------------------------------------------- room shell
		def wall_col(base, px, py, pz=0.0):
			"""Shade a wall vertex: darker toward the floor/back, with a faint
			warm (reddish) interior wash near the window."""
			d = math.sqrt((px - WIN_CX) ** 2 + (py - WIN_CY) ** 2 + pz * pz)
			lit = max(0.0, 1.0 - d / 2.8)
			depth = 0.60 + 0.30 * min(1.0, py / 1.5)
			return (
				min(255, int(base[0] * depth + lit * 20)),
				min(255, int(base[1] * depth + lit * 8)),
				min(255, int(base[2] * depth + lit * 7)),
				255,
			)

		fw_base = (32, 24, 26)
		def fw(px, py):
			return wall_col(fw_base, px, py)
		# Front wall in four pieces around the window opening
		for (x0, x1, y0, y1) in [
			(RX0, WX0, RY0, RY1),
			(WX1, RX1, RY0, RY1),
			(WX0, WX1, RY0, WY0),
			(WX0, WX1, WY1, RY1),
		]:
			q([(x0, y1, 0), (x1, y1, 0), (x1, y0, 0), (x0, y0, 0)],
				[fw(x0, y1), fw(x1, y1), fw(x1, y0), fw(x0, y0)])

		# Window reveal (opening depth) + frame + sill
		rev = (16, 18, 26, 255)
		q([(WX0, WY1, 0), (WX0, WY1, GLASS_Z), (WX0, WY0, GLASS_Z), (WX0, WY0, 0)], [rev] * 4)
		q([(WX1, WY1, 0), (WX1, WY1, GLASS_Z), (WX1, WY0, GLASS_Z), (WX1, WY0, 0)], [rev] * 4)
		q([(WX0, WY1, 0), (WX1, WY1, 0), (WX1, WY1, GLASS_Z), (WX0, WY1, GLASS_Z)], [rev] * 4)
		sill = (52, 50, 62, 255)
		q([(WX0 - 0.06, WY0, 0.09), (WX1 + 0.06, WY0, 0.09),
			(WX1 + 0.06, WY0, GLASS_Z), (WX0 - 0.06, WY0, GLASS_Z)], [sill] * 4)
		q([(WX0 - 0.06, WY0, 0.09), (WX1 + 0.06, WY0, 0.09),
			(WX1 + 0.06, WY0 - 0.05, 0.09), (WX0 - 0.06, WY0 - 0.05, 0.09)],
			[(38, 37, 47, 255)] * 4)
		# Mullions
		mull = (24, 26, 36, 255)
		mx = (WX0 + WX1) / 2
		q([(mx - 0.016, WY1, -0.02), (mx + 0.016, WY1, -0.02),
			(mx + 0.016, WY0, -0.02), (mx - 0.016, WY0, -0.02)], [mull] * 4)
		my = WY0 + (WY1 - WY0) * 0.62
		q([(WX0, my + 0.014, -0.02), (WX1, my + 0.014, -0.02),
			(WX1, my - 0.014, -0.02), (WX0, my - 0.014, -0.02)], [mull] * 4)

		# Side walls, ceiling, floor, back wall
		lw_base = (27, 21, 23)
		def lw(py, pz):
			return wall_col(lw_base, RX0, py, pz + 0.8)
		q([(RX0, RY1, RZ0), (RX0, RY1, RZ1), (RX0, RY0, RZ1), (RX0, RY0, RZ0)],
			[lw(RY1, RZ0), lw(RY1, RZ1), lw(RY0, RZ1), lw(RY0, RZ0)])
		def rw(py, pz):
			return wall_col(lw_base, RX1, py, pz * 0.55)
		q([(RX1, RY1, RZ1), (RX1, RY1, RZ0), (RX1, RY0, RZ0), (RX1, RY0, RZ1)],
			[rw(RY1, RZ1), rw(RY1, RZ0), rw(RY0, RZ0), rw(RY0, RZ1)])
		q([(RX0, RY1, RZ1), (RX1, RY1, RZ1), (RX1, RY0, RZ1), (RX0, RY0, RZ1)],
			[(18, 15, 16, 255)] * 4)
		ceil_near = (28, 22, 23, 255)
		ceil_far = (14, 12, 13, 255)
		q([(RX0, RY1, RZ0), (RX1, RY1, RZ0), (RX1, RY1, RZ1), (RX0, RY1, RZ1)],
			[ceil_near, ceil_near, ceil_far, ceil_far])
		fl_near = (36, 27, 29, 255)
		fl_far = (21, 16, 18, 255)
		q([(RX0, RY0, RZ0), (RX1, RY0, RZ0), (RX1, RY0, RZ1), (RX0, RY0, RZ1)],
			[fl_near, fl_near, fl_far, fl_far])
		for i in range(1, 7):	# floorboard seams
			z = RZ0 + i * 0.6
			q([(RX0, 0.001, z), (RX1, 0.001, z), (RX1, 0.001, z + 0.014), (RX0, 0.001, z + 0.014)],
				[(0, 0, 0, 55)] * 4)
		# Skirting boards
		sk = (46, 39, 41, 255)
		q([(RX0, 0.07, 0.002), (RX1, 0.07, 0.002), (RX1, 0.0, 0.002), (RX0, 0.0, 0.002)], [sk] * 4)
		q([(RX0 + 0.002, 0.07, RZ0), (RX0 + 0.002, 0.07, RZ1),
			(RX0 + 0.002, 0.0, RZ1), (RX0 + 0.002, 0.0, RZ0)], [sk] * 4)

		# City light pooling onto the floor through the window, shimmering
		# slightly with the rain
		pool_a = 46 * (0.9 + 0.1 * math.sin(T * 2.7) * math.sin(T * 1.3))
		q([(WX0, 0.002, 0.02), (WX1, 0.002, 0.02), (WX1 + 0.4, 0.002, 2.3), (WX0 + 0.3, 0.002, 2.3)],
			[(90, 140, 200, int(pool_a)), (110, 150, 210, int(pool_a)),
			(90, 140, 200, 0), (90, 140, 200, 0)], additive=True)
		# ...and up the ceiling a little
		q([(WX0, RY1 - 0.002, 0.02), (WX1, RY1 - 0.002, 0.02),
			(WX1 + 0.2, RY1 - 0.002, 1.1), (WX0 + 0.15, RY1 - 0.002, 1.1)],
			[(80, 120, 180, 22), (90, 130, 190, 22), (80, 120, 180, 0), (80, 120, 180, 0)],
			additive=True)

		# Curtains flanking the wide window (kept within the wall edges)
		def curtain(x0, x1):
			cc_top = (44, 28, 32, 255)
			cc_bot = (30, 20, 23, 255)
			q([(x0, 2.52, 0.10), (x1, 2.52, 0.10), (x1, 0.55, 0.10), (x0, 0.55, 0.10)],
				[cc_top, cc_top, cc_bot, cc_bot])
			for i in range(3):	# fold shadows
				fx = _lerp(x0, x1, 0.2 + i * 0.3)
				q([(fx, 2.52, 0.101), (fx + 0.025, 2.52, 0.101),
					(fx + 0.025, 0.55, 0.101), (fx, 0.55, 0.101)], [(0, 0, 0, 70)] * 4)
		curtain(WX0 - 0.28, WX0 - 0.02)
		curtain(WX1 + 0.02, WX1 + 0.20)
		# Inner curtain edges catch the city light
		q([(WX0 - 0.045, 2.5, 0.102), (WX0 - 0.02, 2.5, 0.102),
			(WX0 - 0.02, 0.6, 0.102), (WX0 - 0.045, 0.6, 0.102)],
			[(70, 110, 160, 60)] * 4, additive=True)
		q([(WX1 + 0.02, 2.5, 0.102), (WX1 + 0.045, 2.5, 0.102),
			(WX1 + 0.045, 0.6, 0.102), (WX1 + 0.02, 0.6, 0.102)],
			[(70, 110, 160, 60)] * 4, additive=True)
		rod = (14, 13, 15, 255)
		q([(WX0 - 0.32, 2.56, 0.10), (WX1 + 0.22, 2.56, 0.10),
			(WX1 + 0.22, 2.52, 0.10), (WX0 - 0.32, 2.52, 0.10)], [rod] * 4)

		# ------------------------------------------------------- furnishings
		# Rug
		q([(-0.5, 0.003, 1.15), (1.7, 0.003, 1.15), (1.7, 0.003, 3.1), (-0.5, 0.003, 3.1)],
			[(34, 24, 28, 255), (38, 27, 31, 255), (26, 19, 22, 255), (24, 17, 20, 255)])
		q([(-0.42, 0.004, 1.23), (1.62, 0.004, 1.23), (1.62, 0.004, 1.27), (-0.42, 0.004, 1.27)],
			[(52, 38, 42, 255)] * 4)
		q([(-0.42, 0.004, 2.98), (1.62, 0.004, 2.98), (1.62, 0.004, 3.02), (-0.42, 0.004, 3.02)],
			[(52, 38, 42, 255)] * 4)

		# Bed along the right wall
		q([(1.32, 0.42, 1.9), (1.32, 0.42, 3.9), (1.32, 0.0, 3.9), (1.32, 0.0, 1.9)],
			[(15, 14, 22, 255)] * 4)	# side
		q([(1.32, 0.42, 1.9), (2.4, 0.42, 1.9), (2.4, 0.0, 1.9), (1.32, 0.0, 1.9)],
			[(19, 18, 27, 255)] * 4)	# foot
		bl_lit = (64, 56, 96, 255)
		bl = (42, 35, 64, 255)
		q([(1.32, 0.44, 1.9), (2.4, 0.44, 1.9), (2.4, 0.44, 3.9), (1.32, 0.44, 3.9)],
			[bl_lit, bl, bl, bl])	# blanket, corner toward window catches light
		q([(1.32, 0.445, 2.6), (2.4, 0.445, 2.6), (2.4, 0.445, 2.68), (1.32, 0.445, 2.68)],
			[(0, 0, 0, 70)] * 4)	# fold
		q([(1.45, 0.60, 3.45), (2.3, 0.60, 3.45), (2.3, 0.44, 3.85), (1.45, 0.44, 3.85)],
			[(60, 58, 80, 255), (60, 58, 80, 255), (48, 46, 64, 255), (48, 46, 64, 255)])	# pillows
		q([(1.32, 1.05, 3.9), (2.4, 1.05, 3.9), (2.4, 0.0, 3.9), (1.32, 0.0, 3.9)],
			[(24, 23, 33, 255)] * 4)	# headboard

		# Posters on the left wall, glowing faintly
		def poster(z0, z1, y0, y1, c0, c1):
			q([(RX0 + 0.004, y1, z0), (RX0 + 0.004, y1, z1),
				(RX0 + 0.004, y0, z1), (RX0 + 0.004, y0, z0)], [(12, 12, 18, 255)] * 4)
			q([(RX0 + 0.005, y1 - 0.03, z0 + 0.03), (RX0 + 0.005, y1 - 0.03, z1 - 0.03),
				(RX0 + 0.005, y0 + 0.03, z1 - 0.03), (RX0 + 0.005, y0 + 0.03, z0 + 0.03)],
				[(*c0, 255), (*c0, 255), (*c1, 255), (*c1, 255)])
		poster(0.8, 1.6, 1.3, 2.2, (74, 26, 86), (24, 66, 92))
		poster(1.9, 2.45, 1.45, 2.05, (90, 48, 30), (50, 20, 52))

		# Desk chair silhouette
		q([(-1.78, 0.46, 0.85), (-1.34, 0.46, 0.85), (-1.34, 0.46, 1.3), (-1.78, 0.46, 1.3)],
			[(17, 17, 24, 255)] * 4)
		q([(-1.78, 1.22, 1.28), (-1.34, 1.22, 1.28), (-1.34, 0.5, 1.28), (-1.78, 0.5, 1.28)],
			[(15, 15, 22, 255)] * 4)

		# Desk. Drawn back-to-front (no depth buffer): the side stands and the
		# front fascia first, then the desktop surface last so it renders in
		# front of its stands.
		dk_top_lit = (56, 46, 56, 255)
		dk_top = (40, 33, 40, 255)
		q([(0.05, 0.70, 0.02), (0.05, 0.70, 0.60), (0.05, 0.0, 0.60), (0.05, 0.0, 0.02)],
			[(28, 24, 30, 255)] * 4)	# right side panel
		q([(-1.85, 0.70, 0.02), (-1.85, 0.70, 0.60), (-1.85, 0.0, 0.60), (-1.85, 0.0, 0.02)],
			[(22, 19, 24, 255)] * 4)	# left side panel
		q([(-1.85, 0.74, 0.62), (0.05, 0.74, 0.62), (0.05, 0.70, 0.62), (-1.85, 0.70, 0.62)],
			[(30, 25, 30, 255)] * 4)	# front fascia
		q([(-1.85, 0.74, 0.0), (0.05, 0.74, 0.0), (0.05, 0.74, 0.62), (-1.85, 0.74, 0.62)],
			[dk_top, dk_top_lit, dk_top_lit, dk_top])	# desktop surface (front-most)

		# ---------------------------------------------------------- monitor
		# Drawn before the keyboard: the monitor sits toward the back of the
		# desk (near the wall), the keyboard in front of it.
		sx0, sx1 = SCR_CX - scr_w / 2, SCR_CX + scr_w / 2
		sy0, sy1 = SCR_CY - SCR_H / 2, SCR_CY + SCR_H / 2
		# glow on the wall behind, and spilling onto the desk
		self._glow((SCR_CX, SCR_CY, 0.02), scr_w * 1.5, SCR_H * 1.9, (120, 150, 210), 40)
		self._glow((SCR_CX, 0.748, 0.26), scr_w * 0.85, 0.30, (120, 150, 210), 34, axis="y")
		# stand
		q([(SCR_CX - 0.14, 0.745, 0.18), (SCR_CX + 0.14, 0.745, 0.18),
			(SCR_CX + 0.14, 0.745, 0.36), (SCR_CX - 0.14, 0.745, 0.36)],
			[(20, 20, 26, 255)] * 4)
		q([(SCR_CX - 0.03, sy0 + 0.02, 0.27), (SCR_CX + 0.03, sy0 + 0.02, 0.27),
			(SCR_CX + 0.03, 0.745, 0.27), (SCR_CX - 0.03, 0.745, 0.27)],
			[(24, 24, 30, 255)] * 4)
		# bezel
		bz = 0.018
		q([(sx0 - bz, sy1 + bz, SCR_Z - 0.006), (sx1 + bz, sy1 + bz, SCR_Z - 0.006),
			(sx1 + bz, sy0 - 0.035, SCR_Z - 0.006), (sx0 - bz, sy0 - 0.035, SCR_Z - 0.006)],
			[(13, 13, 17, 255)] * 4)
		self._glow((SCR_CX, sy0 - 0.028, SCR_Z), 0.006, 0.006, (90, 200, 255), 150)	# power LED

		# The live application, perspective-mapped onto the screen
		tex_size = float(getattr(gui, "max_window_tex", 1000))
		u1 = w / tex_size
		v1 = h / tex_size
		cols_x, cols_y = 10, 6
		white = (255, 255, 255, 255)
		main_tex = gui.main_texture
		sdl3.SDL_SetTextureScaleMode(main_tex, sdl3.SDL_SCALEMODE_LINEAR)
		for j in range(cols_y):
			fy0, fy1 = j / cols_y, (j + 1) / cols_y
			py0 = _lerp(sy1, sy0, fy0)
			py1 = _lerp(sy1, sy0, fy1)
			for i in range(cols_x):
				fx0, fx1 = i / cols_x, (i + 1) / cols_x
				px0 = _lerp(sx0, sx1, fx0)
				px1 = _lerp(sx0, sx1, fx1)
				q([(px0, py0, SCR_Z), (px1, py0, SCR_Z), (px1, py1, SCR_Z), (px0, py1, SCR_Z)],
					[white] * 4,
					uvs=[(fx0 * u1, fy0 * v1), (fx1 * u1, fy0 * v1),
						(fx1 * u1, fy1 * v1), (fx0 * u1, fy1 * v1)],
					texture=main_tex)

		# Backlit keyboard + mouse, in front of the monitor near the desk edge
		q([(SCR_CX - 0.24, 0.745, 0.44), (SCR_CX + 0.24, 0.745, 0.44),
			(SCR_CX + 0.24, 0.745, 0.60), (SCR_CX - 0.24, 0.745, 0.60)],
			[(15, 15, 20, 255)] * 4)
		for i in range(3):
			z = 0.47 + i * 0.045
			q([(SCR_CX - 0.22, 0.747, z), (SCR_CX + 0.22, 0.747, z),
				(SCR_CX + 0.22, 0.747, z + 0.008), (SCR_CX - 0.22, 0.747, z + 0.008)],
				[(60, 180, 220, 26)] * 4, additive=True)
		q([(SCR_CX + 0.32, 0.745, 0.48), (SCR_CX + 0.37, 0.745, 0.48),
			(SCR_CX + 0.37, 0.745, 0.57), (SCR_CX + 0.32, 0.745, 0.57)],
			[(16, 16, 21, 255)] * 4)
		self._glow((SCR_CX + 0.345, 0.75, 0.49), 0.02, 0.02, (60, 200, 240), 120, axis="y")

		# Dust motes drifting in the light
		for (x, y, z, ph) in self.motes:
			a = 16 + 13 * math.sin(T * 0.6 + ph)
			s = 0.006
			q([(x - s, y + s, z), (x + s, y + s, z), (x + s, y - s, z), (x - s, y - s, z)],
				[(140, 170, 210, int(max(4, a)))] * 4, additive=True)

		batch.flush()

		# ------------------------------------------------ screen-space grade
		# Vignette, fading in with the zoom so frame zero stays pixel-clean
		va = 150 * e
		if va > 1:
			ew = w * 0.17
			eh = h * 0.17
			batch.set_state(None, False)
			def edge(p0, p1, p2, p3, a_outer):
				batch.poly([
					(*p0, 0, 0, 0, 0, 0, a_outer), (*p1, 0, 0, 0, 0, 0, a_outer),
					(*p2, 0, 0, 0, 0, 0, 0.0), (*p3, 0, 0, 0, 0, 0, 0.0)])
			a1 = va / 255
			edge((0, 0), (w, 0), (w, eh), (0, eh), a1)
			edge((w, h), (0, h), (0, h - eh), (w, h - eh), a1)
			edge((0, 0), (0, h), (ew, h), (ew, 0), a1)
			edge((w, h), (w, 0), (w - ew, 0), (w - ew, h), a1)
			batch.flush()

		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)

		# Suppress the visualiser overlay path this frame (it blits fixed-rect
		# textures straight onto the backbuffer, over the scene)
		gui.level_update = False

		if self.phase == "in" and self.t <= 0.0:
			# This frame drew the t=0 pose (identical to the normal blit);
			# hand back to the standard pipeline from the next frame on.
			self.phase = "off"
