"""Custom Layout System.

An opt-in layout engine that composes the window from a tree of nested stacks
(vertical / horizontal) whose leaves are widgets drawn into arbitrary rects. It
is completely inert unless ``gui.custom_mode`` is set, so the existing preset
layouts are unaffected.

Implemented here:

* Layout tree (``Stack`` / ``Leaf``) of arbitrary nesting depth, with empty
  leaves, per-node gutter/border, per-axis pixel locks and an aspect lock.
* The resize / layout pass: locked children take fixed (scaled) pixels, Square
  Max children take up to the stack's cross extent (so their slot is square,
  yielding so siblings keep their minimum sizes), the rest split the remainder
  by ``weight``; the cross axis fills.
* Edit mode: hover highlight, right-click context menu (Add stack / Add widget /
  Remove / Remove Stack / Lock V/H/Aspect / Gutter / Border / Load Template),
  edge-drag resizing with weight/pixel semantics and resize cursors. Stacks
  can opt in to view-mode resizing ("Make Stack Resizable"): their child
  boundaries stay draggable with edit mode off.
* Validation: single-instance widgets are gated. A row/column may be fully
  locked; leftover space along the axis stays background.
* Offscreen render-to-rect compositing (shared ``gui.tracklist_texture`` scratch
  target, clipped blit onto the frame), plus the "Size too small" fallback.
* A widget registry of adapters over the real panel renderers (every entry is
  backed by real rendering; there are no placeholder widgets).
* Window-controls fallback drawn on hover when no widget provides them.
* A single custom layout persisted to ``custom_layouts.json``.
"""
from __future__ import annotations

import builtins
import ctypes
import json
import logging
import time
from typing import TYPE_CHECKING, Callable

import sdl3

from tauon.t_modules.t_enums import Backend, PlayingState
from tauon.t_modules.t_extra import ColourRGBA, atomic_save, get_display_time

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon


def _t(s: str) -> str:
	"""Translate via the app's installed gettext ``_`` when present, else
	identity (so the module is importable/testable standalone)."""
	f = getattr(builtins, "_", None)
	return f(s) if callable(f) else s


def draw_layout_glyph(ddt, scale: float, x: float, y: float, w: float, h: float, colour) -> None:
	"""Draw the Custom Layout glyph: a left column + two stacked right panels, as
	filled rectangles. Shared by the View Switcher icon and the corner edit
	button so they're the same icon at different sizes."""
	x, y, w, h = round(x), round(y), round(w), round(h)
	g = max(1, round(2 * scale))
	lw = round(w * 0.38)
	ddt.rect((x, y, lw, h), colour)
	rx = x + lw + g
	rw = w - lw - g
	rh = round((h - g) / 2)
	ddt.rect((rx, y, rw, rh), colour)
	ddt.rect((rx, y + rh + g, rw, h - rh - g), colour)


# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------

class Widget:
	"""Base widget: knows how to draw into a local rect and, optionally, handle a
	click within it. Declares sizing constraints so the engine can auto-lock
	axes, enforce minimums and gate single-instance widgets.
	"""

	kind: str = "widget"
	name: str = "Widget"
	lock_v: bool = False
	lock_h: bool = False
	fixed_w: int = 0
	fixed_h: int = 0
	min_w: int = 40
	min_h: int = 30
	single_instance: bool = False
	draws_window_controls: bool = False
	# Show the name tag in the edit-mode overlay (the fixed chrome bars opt out).
	edit_label: bool = True
	# When True the engine routes the widget through the offscreen scratch
	# texture before compositing (for widgets that may draw out of bounds).
	offscreen: bool = True
	# Whether the leaf hosting this widget has the engine's segment border on;
	# set by _draw_leaf before each draw so widgets that paint their own border
	# (e.g. the Art Box) can skip it rather than double up.
	leaf_border: bool = False

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		raise NotImplementedError

	# Per-instance settings, persisted in the Leaf's dict as "conf" when
	# get_config returns a non-empty dict. Widgets without settings return None.
	def get_config(self) -> dict | None:
		return None

	def set_config(self, d: dict) -> None:
		pass


class ArtBoxWidget(Widget):
	"""The album Art Box: the side panel's ArtBox class (tauon.art_box) drawn
	into the segment. It takes the full rect (art is fitted inside a 17*scale
	inset, aspect preserved), and brings the side panel's behaviour: background
	fill, faint border, click to cycle art source, right-click picture/MilkDrop
	menu, hover picture metadata, "Fetching image..." indicator and the MilkDrop
	visualiser when enabled. Shows the playing-or-selected track (show_object,
	same as the preset side panel) and handles no-track itself. Drawn at real
	coordinates (offscreen=False) so its absolute-space art/visualizer and input
	all work directly with the real mouse.
	"""

	kind = "art"
	name = "Art Box"
	min_w = 32
	min_h = 32
	single_instance = True  # ArtBox writes singleton gui.main_art_box / milk state
	offscreen = False

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		# inset=False: no outer padding in custom mode — the segment's gutter
		# provides the spacing instead. quick_draw while an edit-mode drag
		# (boundary resize or widget swap) is repainting every frame: same fast
		# art path the preset uses during a side-bar drag.
		cm = tauon.custom
		dragging = cm.drag is not None or cm.widget_drag is not None
		tauon.art_box.draw(round(x), round(y), round(w), round(h),
			target_track=tauon.pctl.show_object(), inset=False, quick_draw=dragging,
			draw_border=not self.leaf_border)


class MilkDropWidget(Widget):
	"""The MilkDrop (projectM) visualiser as its own segment.

	Milky renders at the singleton gui.main_art_box rect (GL framebuffer interop
	blitted onto the current render target at real coordinates), so this widget
	points that rect at its segment and draws offscreen=False. While it is in
	the layout the engine sets gui.milkdrop_in_widget, which gates the ArtBox /
	MetaBox milk paths off — the visualiser is a singleton whose GL texture is
	recreated on any size change, so it must never be driven from two rects.

	Mirrors the existing view's interactions: click cycles a random preset,
	right-click opens the MilkDrop menu, and hovering shows the preset name /
	Auto Cycle / FPS tags.
	"""

	kind = "milkdrop"
	name = "Visualiser: Milkdrop"
	min_w = 64
	min_h = 48
	single_instance = True
	offscreen = False

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gui = tauon.gui
		ddt = tauon.ddt
		inp = tauon.inp
		rect = (round(x), round(y), round(w), round(h))
		tauon.fields.add(rect)
		track = tauon.pctl.show_object()
		hover = tauon.coll(rect) and tauon.is_level_zero(False)

		if not tauon.prefs.milk or not tauon.milky.available:
			text = _t("MilkDrop is disabled") if tauon.milky.available else _t("MilkDrop is unavailable")
			ddt.rect(rect, ColourRGBA(8, 8, 8, 255))
			ddt.text_background_colour = ColourRGBA(8, 8, 8, 255)
			ddt.text(
				(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2 - round(8 * gui.scale), 2),
				text, ColourRGBA(110, 110, 110, 255), 212,
				max_w=rect[2] - round(8 * gui.scale))
			if hover and inp.right_click:
				tauon.milky_menu.activate(in_reference=track)
				inp.right_click = False
			return

		gui.main_art_box = rect  # Milky renders at this singleton rect

		show_vis = False
		if tauon.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM, PlayingState.PAUSED):
			# Same warm-up dance as the ArtBox path: burn the album art into the
			# visualiser shortly after playback starts, then render each frame.
			if tauon.pctl.a_time < 1.3:
				if 1 < tauon.pctl.a_time < 1.3:
					tauon.milky.render(discard=True)
					if track is not None:
						tauon.milky.burn(track)
			else:
				tauon.milky.render()
				show_vis = True
			if tauon.pctl.playing_state != PlayingState.PAUSED:
				gui.delay_frame(tauon.frame_pace())

		if not show_vis:
			# Nothing playing yet (fresh launch), stopped, or still warming up: the
			# visualiser isn't covering the segment, so fill an opaque background
			# rather than leave it transparent. While the vis is live we skip this
			# so the frame — and its keyed-transparent pixels under Cut Out — show.
			ddt.rect(rect, ColourRGBA(8, 8, 8, 255))

		if hover:
			if inp.mouse_click and inp.key_focused == 0 and show_vis:
				tauon.milky.projectm.load_next = "random"
			if inp.right_click:
				tauon.milky_menu.activate(in_reference=track)
				inp.right_click = False
			if show_vis:
				self._hover_tags(tauon, rect)

	def _hover_tags(self, tauon: Tauon, rect: tuple[int, int, int, int]) -> None:
		"""The existing view's hover overlay: preset name, Auto Cycle, FPS."""
		gui = tauon.gui
		ddt = tauon.ddt

		def tag(line: str, xx: int, yy: int, font: int, pad_w: float, colour: ColourRGBA) -> None:
			mw = rect[2] - round(25 * gui.scale)
			tag_w, _th = ddt.get_text_wh(line, font, max_x=mw)
			tag_w += round(pad_w * gui.scale)
			ddt.rect_a((xx, yy), (tag_w, 18 * gui.scale), ColourRGBA(8, 8, 8, 255))
			ddt.text((xx + 6 * gui.scale, yy), line, colour, font,
				bg=ColourRGBA(30, 30, 30, 255), max_w=mw)

		xx = rect[0] + round(5 * gui.scale)
		yy = rect[1] + round(25 * gui.scale)
		tag(tauon.milky.projectm.get_current_name(), xx, yy, 312, 17, ColourRGBA(220, 220, 220, 255))

		if tauon.prefs.auto_milk:
			yy += round(30 * gui.scale)
			tag(_t("Auto Cycle"), xx, yy, 12, 14, ColourRGBA(210, 210, 210, 255))

		if tauon.pctl.playing_state not in (PlayingState.PLAYING, PlayingState.URL_STREAM):
			tauon.milky.fps.reset()
		yy += round(30 * gui.scale)
		tag(f"FPS: {round(tauon.milky.fps.get())}", xx, yy, 12, 14, ColourRGBA(210, 210, 210, 255))


class SticksVisWidget(Widget):
	"""The showcase view's bar ("sticks") visualiser, reused. The spectrum data
	(gui.spec4_array) is only produced by the PHAZOR vis thread while
	gui.vis == 4, so the engine flags gui.vis4_in_widget and update_layout_do()
	switches the mode while the widget is in the layout. Drawing reuses
	Showcase.render_vis unchanged: the bar strip is a fixed-size texture
	blitted at gui.spec4_rec, which we centre in the segment; like the
	showcase, the draw is deferred to the main loop's top-level pass
	(gui.draw_vis4_top) unless a dialog is open, in which case it renders
	inline so it stays underneath.
	"""

	kind = "vis_sticks"
	name = "Visualiser: Bars"
	min_w = 326  # gui.spec4_rec is a fixed 322x100 (scaled) strip
	min_h = 60
	single_instance = True
	offscreen = False  # positions/defers only; real drawing is at screen coords

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gui = tauon.gui
		rec = gui.spec4_rec
		rec.x = round(x + (w - rec.w) / 2)
		# The bars are drawn at by=50 in the 200-tall spec4_tex, which is blitted
		# into this 100-tall rec, so the visible strip sits a quarter of the way
		# down the rec rather than at its middle. Offset by rec.h/4 so the bars
		# (not the empty texture) land in the segment's vertical centre.
		rec.y = round(y + (h - rec.h) / 2 + rec.h / 4)
		if tauon.prefs.backend != Backend.PHAZOR:
			tauon.ddt.text_background_colour = ColourRGBA(8, 8, 8, 255)
			tauon.ddt.text(
				(round(x + w / 2), round(y + h / 2) - round(8 * gui.scale), 2),
				_t("Visualiser requires the Phazor backend"), ColourRGBA(110, 110, 110, 255), 212,
				max_w=round(w) - round(8 * gui.scale))
			return
		if gui.vis != 4:
			return  # switches on the next layout update
		if gui.message_box or not tauon.is_level_zero(include_menus=True):
			tauon.showcase.render_vis()
		else:
			gui.draw_vis4_top = True


# Spectrogram colour presets: (name, gradient stops as (position, (r, g, b))).
# The right-click menu in t_main is built from this list; the selected index is
# prefs.spectrogram_colour.
SPECTRO_PRESETS: list[tuple[str, list[tuple[float, tuple[int, int, int]]]]] = [
	("Inferno", [
		(0.0, (0, 0, 4)), (0.22, (60, 10, 90)), (0.45, (150, 40, 90)),
		(0.7, (230, 100, 30)), (0.9, (250, 200, 60)), (1.0, (255, 250, 200))]),
	("Greyscale", [(0.0, (0, 0, 0)), (1.0, (255, 255, 255))]),
]


def build_spectro_lut(preset: int) -> list[bytes]:
	"""256-entry magnitude -> pixel LUT for the given preset, as 4-byte
	ARGB8888 pixels (B, G, R, A byte order, little-endian)."""
	stops = SPECTRO_PRESETS[preset % len(SPECTRO_PRESETS)][1]
	lut = []
	for i in range(256):
		p = i / 255
		r = g = b = 0
		for j in range(len(stops) - 1):
			p0, c0 = stops[j]
			p1, c1 = stops[j + 1]
			if p <= p1 or j == len(stops) - 2:
				t = 0.0 if p1 <= p0 else min(1.0, max(0.0, (p - p0) / (p1 - p0)))
				r = round(c0[0] + (c1[0] - c0[0]) * t)
				g = round(c0[1] + (c1[1] - c0[1]) * t)
				b = round(c0[2] + (c1[2] - c0[2]) * t)
				break
		lut.append(bytes((b, g, r, 255)))
	return lut


class SpectrogramWidget(Widget):
	"""Scrolling spectrogram, built for the custom layout (the legacy top-panel
	spec2 one is preset-only and unfed on PHAZOR). Data: the PHAZOR vis thread
	feeds raw log-spaced spectrum columns (gui.spectrogram_bins tall) through
	gui.spectrogram_buffers whenever gui.spectrogram_in_widget is set (flagged by
	update_layout_do) — decoupled from gui.vis, so it runs alongside the bar
	visualiser rather than replacing it.

	Rendering: a ring texture of one column per sample, sized to the widget
	(just enough columns to span its width; recreated — newest history carried
	over — when the segment size settles after a change, never mid-drag). Each
	new column is one tiny SDL_UpdateTexture write, and the visible window is
	at most two scaled blits per frame. Float (subpixel) dest rects + a
	fractional offset give a continuous scroll instead of a per-column step;
	linear filtering smooths both axes. An adaptive playout buffer consumes the
	jittery producer queue at a smooth, self-pacing rate (holding a small column
	backlog as a cushion), so scroll velocity stays constant and occasional late
	frames or producer stalls are absorbed rather than shown as a lurch.
	The newest column slides in from the right edge. Magnitude values (0-255)
	are kept in a ring alongside the pixels so switching colour preset
	recolourises the whole history (per-byte plane translate, C speed). State
	is class-level: the widget is single-instance and this way the texture and
	history survive add/remove and layout reloads without SDL lifetime
	management on GC.
	"""

	kind = "vis_spectrogram"
	name = "Visualiser: Spectrogram"
	min_w = 60
	min_h = 40
	single_instance = True
	offscreen = False  # draws with the renderer directly at screen coords

	NORM = 30.0   # get_spectrum_hires sqrt-magnitude that maps to full scale
	              # (4096 window: magnitudes x2 vs get_spectrum, sqrt -> x1.41)
	GAMMA = 0.5
	RESIZE_SETTLE = 0.3  # s the requested size must hold before rebuilding

	_tex = None
	_tex_bins = 0
	_cols = 0                        # ring length (texture width), widget-sized
	_vals: bytearray | None = None   # row-major magnitudes, mirrors the texture
	_write = 0
	_filled = 0
	_lut: list[bytes] | None = None
	_lut_preset = -1
	# Adaptive playout buffer. The producer appends columns at a jittery rate;
	# the display consumes them at a smooth, self-pacing rate instead of draining
	# the whole queue every frame. _col_period is seconds per on-screen column;
	# it slowly integrates to hold ~TARGET_BACKLOG columns queued, which makes it
	# converge on the true production rate without ever starving or piling up.
	# _frac_accum is the sub-column scroll position (0-1), advanced by real
	# elapsed time so velocity is constant regardless of frame/producer jitter.
	TARGET_BACKLOG = 2      # columns to keep queued (jitter cushion)
	ADAPT_GAIN = 0.0015     # per-frame pull of _col_period toward the target
	_col_period = 1 / 50    # s per column (adapts to the real production rate)
	_frac_accum = 0.0       # sub-column scroll offset, 0-1
	_last_frame = 0.0       # monotonic time of the previous consumed frame
	_pending_cols = 0
	_pending_since = 0.0

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gui = tauon.gui
		cls = SpectrogramWidget
		rect = (round(x), round(y), round(w), round(h))
		tauon.fields.add(rect)

		if tauon.prefs.backend != Backend.PHAZOR:
			tauon.ddt.text_background_colour = ColourRGBA(8, 8, 8, 255)
			tauon.ddt.text(
				(rect[0] + rect[2] // 2, rect[1] + rect[3] // 2 - round(8 * gui.scale), 2),
				_t("Visualiser requires the Phazor backend"), ColourRGBA(110, 110, 110, 255), 212,
				max_w=rect[2] - round(8 * gui.scale))
			return

		bins = gui.spectrogram_bins
		self._ensure(tauon, bins, w)

		playing = tauon.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM)

		# Adaptive playout: consume queued columns at a smooth, self-pacing rate
		# rather than draining the whole queue each frame. _col_period is nudged
		# toward holding TARGET_BACKLOG columns queued, so it settles at the true
		# production rate (no starvation, no pile-up); the sub-column remainder is
		# the scroll offset, advanced by real elapsed time for constant velocity.
		now = time.monotonic()
		if playing and cls._last_frame:
			backlog = len(gui.spectrogram_buffers)
			# Slow integrator: more queued -> consume faster (shorter period).
			cls._col_period *= 1.0 - (backlog - cls.TARGET_BACKLOG) * cls.ADAPT_GAIN
			cls._col_period = min(max(cls._col_period, 0.008), 0.05)
			cls._frac_accum += (now - cls._last_frame) / cls._col_period
			guard = 0
			while cls._frac_accum >= 1.0:
				if not gui.spectrogram_buffers:
					cls._frac_accum = 1.0  # starved: hold the newest column in view
					break
				self._push_column(gui.spectrogram_buffers.pop(0), bins)
				cls._frac_accum -= 1.0
				guard += 1
				if guard >= 8:  # cap catch-up after a long stall (no visible lurch)
					cls._frac_accum = min(cls._frac_accum, 1.0)
					break
		cls._last_frame = now

		# Background in the palette's floor colour, so sparse history blends in.
		lut0 = cls._lut[0]
		tauon.ddt.rect(rect, ColourRGBA(lut0[2], lut0[1], lut0[0], 255))

		if cls._filled:
			col_px = 1.5 * gui.scale
			offset = cls._frac_accum * col_px
			visible = min(cls._filled, int(w / col_px) + 2)
			newest = (cls._write - 1) % cls._cols
			start = (newest - visible + 1) % cls._cols
			if start + visible <= cls._cols:
				runs = [(start, visible)]
			else:
				runs = [(start, cls._cols - start), (0, visible - (cls._cols - start))]

			clip = sdl3.SDL_Rect(rect[0], rect[1], rect[2], rect[3])
			sdl3.SDL_SetRenderClipRect(tauon.renderer, ctypes.byref(clip))
			# The newest column's left edge sits at (right - offset): it is
			# revealed from the right edge as time passes, then the next column
			# lands exactly where it left off — constant leftward velocity.
			dx = x + w - offset - (visible - 1) * col_px
			for s, n in runs:
				src = sdl3.SDL_FRect(s, 0, n, bins)
				dst = sdl3.SDL_FRect(dx, y, n * col_px, h)
				sdl3.SDL_RenderTexture(tauon.renderer, cls._tex, ctypes.byref(src), ctypes.byref(dst))
				dx += n * col_px
			sdl3.SDL_SetRenderClipRect(tauon.renderer, None)

		if tauon.coll(rect) and tauon.inp.right_click and tauon.is_level_zero(False):
			tauon.spectrogram_menu.activate()
			tauon.inp.right_click = False

		if tauon.pctl.playing_state in (PlayingState.PLAYING, PlayingState.URL_STREAM):
			gui.delay_frame(tauon.frame_pace())  # keep frames coming for the smooth scroll

	def _ensure(self, tauon: Tauon, bins: int, w: float) -> None:
		cls = SpectrogramWidget
		# Ring length = just enough columns to span the widget's width.
		want = max(16, int(w / (1.5 * tauon.gui.scale)) + 3)
		if cls._tex is None or cls._tex_bins != bins:
			self._rebuild(tauon, bins, want)
		elif want != cls._cols:
			# The widget is being resized. Never rebuild mid-drag (edit-mode
			# segment drags deliver a new size every frame); otherwise wait for
			# the requested size to hold briefly (live window resizes stream
			# sizes too), then rebuild, carrying the newest history over.
			cm = tauon.custom
			dragging = cm.drag is not None or cm.widget_drag is not None
			now = time.monotonic()
			if dragging:
				cls._pending_cols = 0
			elif want != cls._pending_cols:
				cls._pending_cols = want
				cls._pending_since = now
			elif now - cls._pending_since >= cls.RESIZE_SETTLE:
				self._rebuild(tauon, bins, want)
		else:
			cls._pending_cols = 0
		if cls._lut_preset != tauon.prefs.spectrogram_colour:
			cls._lut_preset = tauon.prefs.spectrogram_colour
			cls._lut = build_spectro_lut(cls._lut_preset)
			self._recolour(bins)

	def _rebuild(self, tauon: Tauon, bins: int, cols: int) -> None:
		"""Destroy and recreate the ring texture at ``cols`` columns, carrying
		over the newest min(filled, cols) columns of history."""
		cls = SpectrogramWidget
		old_vals, old_cols, old_write, old_filled = cls._vals, cls._cols, cls._write, cls._filled
		old_bins = cls._tex_bins
		if cls._tex is not None:
			sdl3.SDL_DestroyTexture(cls._tex)
		cls._tex = sdl3.SDL_CreateTexture(
			tauon.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888,
			sdl3.SDL_TEXTUREACCESS_STREAMING, cols, bins)
		sdl3.SDL_SetTextureScaleMode(cls._tex, sdl3.SDL_SCALEMODE_LINEAR)
		sdl3.SDL_SetTextureBlendMode(cls._tex, sdl3.SDL_BLENDMODE_NONE)
		cls._cols = cols
		cls._tex_bins = bins
		cls._vals = bytearray(cols * bins)
		keep = 0
		if old_vals is not None and old_filled and old_cols and old_bins == bins:
			# Copy the newest columns, oldest-first, to the start of the new
			# ring — per-row slice copies over the (max two) old-ring runs.
			keep = min(old_filled, cols)
			start = (old_write - keep) % old_cols
			if start + keep <= old_cols:
				runs = [(start, keep)]
			else:
				runs = [(start, old_cols - start), (0, keep - (old_cols - start))]
			dst = 0
			for s, n in runs:
				for row in range(bins):
					cls._vals[row * cols + dst:row * cols + dst + n] = \
						old_vals[row * old_cols + s:row * old_cols + s + n]
				dst += n
		cls._write = keep % cols
		cls._filled = keep
		cls._pending_cols = 0
		cls._lut_preset = -1  # force a LUT refresh + full texture upload

	def _push_column(self, col: list[float], bins: int) -> None:
		cls = SpectrogramWidget
		vals = cls._vals
		lut = cls._lut
		write = cls._write
		norm = cls.NORM
		gamma = cls.GAMMA
		pix = bytearray(bins * 4)
		for i in range(min(bins, len(col))):
			v = col[i] / norm
			idx = 255 if v >= 1.0 else int((v ** gamma) * 255) if v > 0 else 0
			row = bins - 1 - i  # low frequencies at the bottom
			vals[row * cls._cols + write] = idx
			pix[row * 4:row * 4 + 4] = lut[idx]
		rect = sdl3.SDL_Rect(write, 0, 1, bins)
		sdl3.SDL_UpdateTexture(cls._tex, ctypes.byref(rect), bytes(pix), 4)
		cls._write = (write + 1) % cls._cols
		cls._filled = min(cls._filled + 1, cls._cols)

	def _recolour(self, bins: int) -> None:
		"""Rewrite the whole texture from the magnitude ring with the current
		LUT — one byte-translate per colour plane, then a single upload."""
		cls = SpectrogramWidget
		vals = bytes(cls._vals)
		out = bytearray(len(vals) * 4)
		for plane in range(4):
			table = bytes(cls._lut[i][plane] for i in range(256))
			out[plane::4] = vals.translate(table)
		sdl3.SDL_UpdateTexture(cls._tex, None, bytes(out), cls._cols * 4)


class TopPanelWidget(Widget):
	"""The real Top Panel, drawn into an arbitrary rect.

	The existing TopPanel.render() draws at y=0 across the full window width and
	reads tauon.window_size[0] for layout. To place it anywhere we render it
	through the engine's offscreen scratch texture (so output is captured from a
	(0,0) origin and blitted to the segment) and temporarily narrow
	window_size[0] to the segment width so its contents lay out within it.

	Input is neutralised during this reframed render (mouse moved off-screen) so
	it draws in a clean resting state and doesn't fight the engine's own input
	handling. Live interactivity inside custom mode is a separate step (it needs
	custom mode to own the frame's input rather than overlay it).
	"""

	kind = "top_panel"
	name = "Header Bar"
	lock_v = True
	fixed_h = 30
	min_w = 80
	min_h = 20
	single_instance = True
	draws_window_controls = True
	edit_label = False
	offscreen = True

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		# Offscreen mode: the engine has already reframed the coordinate space
		# (window width, mouse, fields offset) and set the scratch render target,
		# so the panel just renders at its native (0, 0) origin and is blitted to
		# the real segment. It draws — and, in view mode, handles input — within
		# the reframed space.
		tauon.top_panel.render()


class PlaybackPanelWidget(Widget):
	"""The real Playback panel (bottom bar), drawn into an arbitrary rect.

	The bottom bar is bottom-anchored — it draws at y = window_size[1] - panelBY
	and precomputes its layout (seek/volume bars) in update() from the window
	size. The engine narrows window_size to the segment (so the bar lands at the
	scratch (0, 0) origin), and we call update() here so its bars re-lay out for
	the segment before render(). Honours prefs.shuffle_lock like the standard
	path (the album-shuffle variant uses a different bar object).
	"""

	kind = "playback_panel"
	name = "Playback Panel"
	lock_v = True
	fixed_h = 51  # = panelBY at scale 1
	min_w = 120
	min_h = 30
	single_instance = True
	edit_label = False
	offscreen = True

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		# The standard path sets this before rendering the bar; the bar's text
		# blends against it, so a stale colour from another widget bleeds through.
		tauon.ddt.text_background_colour = tauon.colours.bottom_panel_colour
		bar = tauon.bottom_bar_ao1 if tauon.prefs.shuffle_lock else tauon.bottom_bar1
		bar.update()
		bar.render()


class RectPanelWidget(Widget):
	"""Adapter for an existing panel that already draws into a given (x, y, w, h)
	rect (the left-side panels). It is rendered offscreen at a (0, 0) origin and
	the engine reframes input/menus/fields, so it is fully interactive at any
	position and size. Subclasses set the tauon attribute and method names.
	"""

	offscreen = True
	min_w = 80
	min_h = 60
	single_instance = True  # these panels hold scroll/selection state
	panel_attr = ""
	panel_method = "draw"

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		panel = getattr(tauon, self.panel_attr)
		getattr(panel, self.panel_method)(round(x), round(y), round(w), round(h))


class PlaylistListWidget(RectPanelWidget):
	kind = "playlist_list"
	name = "Playlist List"
	panel_attr = "playlist_box"
	panel_method = "draw"


class QueueWidget(RectPanelWidget):
	kind = "queue"
	name = "Queue"
	panel_attr = "queue_box"
	panel_method = "draw"


class ArtistListWidget(RectPanelWidget):
	kind = "artist_list"
	name = "Artist List"
	panel_attr = "artist_list_box"
	panel_method = "render"


class FolderNavWidget(RectPanelWidget):
	kind = "folder_nav"
	name = "Folder Navigator"
	panel_attr = "tree_view_box"
	panel_method = "render"


class ArtistInfoWidget(RectPanelWidget):
	# The artist bio panel (ArtistInfoBox: picture + last.fm bio + link pins).
	# panel_mode=False disables the standard panel's self-management (the
	# bio-pref auto-shrink and the too-narrow auto-close) — the engine's min_w
	# gate handles small segments instead.
	kind = "artist_info"
	name = "Artist Info"
	min_w = 300
	min_h = 60

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		tauon.artist_info_box.draw(round(x), round(y), round(w), round(h), panel_mode=False)


class MetaWidget(Widget):
	"""Adapter for the MetaBox renderers, which take (x, y, w, h, track). The
	track is the current "show object" (playing or selected per prefs). Rendered
	offscreen so the engine reframes input/menus (right-click showcase menu on
	the lyrics box; the titles widgets never open the lyrics menus)."""

	offscreen = True
	min_w = 80
	min_h = 40
	meta_method = "draw"

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		track = tauon.pctl.show_object()
		getattr(tauon.meta_box, self.meta_method)(round(x), round(y), round(w), round(h), track)


class MetaCenterWidget(MetaWidget):
	# The default side-panel metadata (prefs.side_panel_layout == 0).
	kind = "meta_center"
	name = "Track: Titles"
	meta_method = "draw"

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		track = tauon.pctl.show_object()
		tauon.meta_box.draw(round(x), round(y), round(w), round(h), track, lyrics_ui=False)


class MetaCenteredWidget(MetaWidget):
	# Centered track text (based on the side_panel_layout == 1 layout, no art).
	kind = "meta_centered"
	name = "Track: Titles (Centred)"
	meta_method = "centered"


class LyricsWidget(MetaWidget):
	"""Static lyrics via MetaBox.lyrics, or synced (LRC) lyrics via
	TimedLyricsRen when available — the preset side panel does this branch in
	the main render loop, so the widget replicates it. The synced renderer's
	side_panel mode lays out against gui.rsp_x/rspw/panelY/panelBY, so those
	are pointed at the segment for the call (window_size is already reframed).
	"""

	kind = "lyrics"
	name = "Lyrics Box"
	meta_method = "lyrics"
	single_instance = True  # shared lyrics scroll state

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		track = tauon.pctl.show_object()
		gui = tauon.gui
		tauon.test_auto_lyrics(track)
		# Synced when preferred, or when there are no static lyrics to fall
		# back on (matching toggle_lyrics, which flips prefer_synced_lyrics on
		# in that case).
		synced = track is not None and (
			tauon.prefs.prefer_synced_lyrics or not track.lyrics
		) and tauon.timed_lyrics_ren.generate(track)
		if not synced:
			tauon.meta_box.lyrics(round(x), round(y), round(w), round(h), track)
			return

		# TimedLyricsRen's own right-click test is skipped at a zero origin
		# (it requires truthy x and y), so open the showcase menu here.
		if tauon.inp.right_click and tauon.coll((x + 10, y, w - 10, h)):
			gui.force_showcase_index = -1
			tauon.showcase_menu.activate(track)

		saved = (gui.rsp_x, gui.rspw, gui.panelY, gui.panelBY)
		gui.rsp_x, gui.rspw = round(x), round(w)
		gui.panelY = round(y)
		gui.panelBY = max(0, tauon.window_size[1] - round(y + h))
		try:
			tauon.timed_lyrics_ren.render(
				track.index, round(x + 9 * gui.scale), round(y),
				side_panel=True, w=round(w), h=round(h))
		finally:
			gui.rsp_x, gui.rspw, gui.panelY, gui.panelBY = saved


class TracklistWidget(Widget):
	"""The main Tracklist (playlist view).

	It owns gui.tracklist_texture as its render cache and blits to the main
	texture itself, so it is not routed through the engine's offscreen scratch
	(offscreen=False) and renders at real screen coordinates — its input
	(selection, scroll, right-click menu) works with the real mouse. The renderer
	now accepts a rect: full_render(rect) repaints into the segment when the
	content (gui.pl_update) or the segment changed; otherwise cache_render()
	re-blits the cached texture.
	"""

	kind = "tracklist"
	name = "Tracklist"
	min_w = 120
	min_h = 80
	single_instance = True
	offscreen = False

	def __init__(self) -> None:
		self._last_rect: tuple | None = None

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		pr = tauon.playlist_render
		gui = tauon.gui
		inp = tauon.inp
		rect = (round(x), round(y), round(w), round(h))
		# Input is handled inside the playlist render, so a full_render must run
		# whenever the pointer is over the tracklist or there's a mouse event —
		# otherwise the cheap cache_render path would swallow clicks/scroll/hover.
		mx, my = inp.mouse_position[0], inp.mouse_position[1]
		over = rect[0] <= mx < rect[0] + rect[2] and rect[1] <= my < rect[1] + rect[3]
		interacting = over or inp.mouse_click or inp.right_click or inp.mouse_down or inp.mouse_wheel != 0
		view = not gui.custom_edit
		if view:
			# The standard scroll bar's interaction lock, pointed at this
			# segment's bar hitbox (same geometry as the shared render function).
			# It updates gui.scrollbar_active, which the body render reads, so the
			# bar and the album-rating stars yield to each other exactly like the
			# preset tracklist.
			scale = gui.scale
			hb_top = rect[1]
			hb_h = rect[3]
			if gui.set_bar and gui.set_mode:
				# Drop below the columns header, matching the bar itself.
				hb_top += gui.set_height
				hb_h -= gui.set_height
			if tauon.prefs.tracklist_scrollbar_left:
				hb_x = rect[0]
			else:
				hb_x = rect[0] + rect[2] - 2 * scale - 28 * scale
			hitbox = (hb_x, hb_top, 28 * scale, hb_h)
			tauon.tracklist_scrollbar_lock(hitbox)
		if view and gui.set_mode:
			# Columns header bar input, pointed at this segment. Must run before
			# the body render so a grip resize/reorder reflects the same frame
			# (mirrors the preset order: input, then body, then bar draw). The
			# widget draws at real coords, so the real mouse/fields line up.
			saved = (gui.playlist_left, gui.plw, gui.panelY)
			gui.playlist_left, gui.plw, gui.panelY = rect[0], rect[2], rect[1]
			tauon.column_bar_input()
			gui.playlist_left, gui.plw, gui.panelY = saved
		if gui.pl_update or rect != self._last_rect or interacting:
			# Flip the request flag off at the start of the render, same as the
			# standard path: a request_tracklist_redraw() made during it means
			# "render the tracklist again next frame".
			gui.pl_update = False
			# Mirror the standard path: heart_fields is repopulated by full_render,
			# so it must be cleared first or it grows unbounded every frame (the
			# normal loop clears it before its full_render; that path is skipped in
			# custom mode).
			gui.heart_fields.clear()
			pr.full_render(rect=rect)
			self._last_rect = rect
		else:
			pr.cache_render()
		if view:
			# The standard scroll bar itself (auto-hide until hovered, thumb
			# drag, continuous click-slide, right-click jump, album-rating
			# suppression), pointed at the segment. Drawn after the body so it
			# sits on top, same as the preset frame order.
			tauon.tracklist_scrollbar_render(
				rect[0], rect[2], rect[1], rect[1] + rect[3],
				rect[1] + rect[3] - 1 * gui.scale)
		if view and gui.set_mode:
			# Columns header bar drawing (and the hover strip to re-show a hidden
			# bar), on top of the body — pointed at this segment.
			saved = (gui.playlist_left, gui.plw, gui.panelY)
			gui.playlist_left, gui.plw, gui.panelY = rect[0], rect[2], rect[1]
			tauon.column_bar_draw()
			gui.playlist_left, gui.plw, gui.panelY = saved


class DetailsWidget(Widget):
	"""A table of the current track's metadata (playing-or-selected track, like
	the side panel): one row per populated field with alternating row
	backgrounds, ordered most-common-first (Title at the top). Fields without a
	value are skipped entirely. Stateless and input-free, so duplicates are
	allowed and it draws at real coordinates (offscreen=False); rows stop at the
	segment bottom and text is clipped to the columns.
	"""

	kind = "details"
	name = "Track: Details"
	min_w = 100
	min_h = 40
	offscreen = False

	# (label, value getter) — most common fields first; the no-track state
	# lists every label from this table.
	_FIELDS: list[tuple[str, Callable]] = [
		("Title", lambda t: t.title),
		("Artist", lambda t: t.artist),
		("Album", lambda t: t.album),
		("Album Artist", lambda t: t.album_artist),
		("Composer", lambda t: t.composer),
		("Date", lambda t: t.date),
		("Genre", lambda t: t.genre),
		("Track", lambda t: f"{t.track_number}/{t.track_total}" if t.track_number and t.track_total
			else t.track_number),
		("Disc", lambda t: f"{t.disc_number}/{t.disc_total}" if t.disc_number and t.disc_total
			else t.disc_number),
		("Duration", lambda t: get_display_time(t.length) if t.length else ""),
		("Codec", lambda t: t.file_ext),
		("Bitrate", lambda t: f"{t.bitrate} kbps" if t.bitrate else ""),
		("Sample rate", lambda t: f"{t.samplerate} Hz" if t.samplerate else ""),
		("Bit depth", lambda t: f"{t.bit_depth} bit" if t.bit_depth else ""),
		("Comment", lambda t: t.comment.splitlines()[0] if t.comment else ""),
	]

	def __init__(self) -> None:
		self.scroll = 0  # whole rows scrolled off the top

	@classmethod
	def _rows(cls, track) -> list[tuple[str, str]]:
		rows = [(_t(label), str(getter(track)).strip()) for label, getter in cls._FIELDS]
		return [(label, value) for label, value in rows if value]

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gui = tauon.gui
		ddt = tauon.ddt
		inp = tauon.inp
		colours = tauon.colours
		base = colours.side_panel_background
		ddt.rect((x, y, w, h), base)
		track = tauon.pctl.show_object()

		# No track: keep the table furniture — every possible field name with its
		# row background, both fading out further down the list.
		empty = track is None
		if empty:
			rows = [(_t(label), "") for label, _ in self._FIELDS]
		else:
			rows = self._rows(track)

		row_h = round(22 * gui.scale)
		pad = round(10 * gui.scale)
		label_w = min(round(110 * gui.scale), round(w * 0.35))

		# Wheel scrolling (whole rows, so drawing stays row-aligned and in
		# bounds). Per-instance scroll position.
		visible = max(1, int(h // row_h))
		max_scroll = max(0, len(rows) - visible)
		mx, my = inp.mouse_position[0], inp.mouse_position[1]
		if inp.mouse_wheel and x <= mx < x + w and y <= my < y + h:
			# mouse_wheel is a float (precise trackpad scrolling sends
			# fractional deltas); accumulate as float so small steps add up,
			# but draw from a whole row below.
			self.scroll -= inp.mouse_wheel
			gui.request_frame()
		self.scroll = max(0, min(self.scroll, max_scroll))

		# Alternate row tint: slightly lighter on dark themes, darker on light.
		tint_up = not colours.lm
		ry = round(y + 2 * gui.scale)  # first row's top
		for i in range(int(self.scroll), len(rows)):
			if ry + row_h > y + h:
				break
			label, value = rows[i]
			# Fade per absolute row index so the empty list dissolves downward.
			fade = max(0.0, 1.0 - i / len(rows)) if empty else 1.0
			if i % 2:  # parity by field, so stripes stay put when scrolled
				a = round(9 * fade) if empty else 9
				tint = ColourRGBA(255, 255, 255, a) if tint_up else ColourRGBA(0, 0, 0, a)
				ddt.rect((x, ry, w, row_h), tint)
			ddt.text_background_colour = base
			# ddt.text's y is baseline-anchored internally but offset back by
			# 13*scale in t_draw for legacy compat, so it behaves near enough to
			# a top anchor; this centres these fonts in the 22*scale row.
			ty = ry + round(2 * gui.scale)
			lc = colours.side_bar_line2
			if empty:
				lc = ColourRGBA(lc.r, lc.g, lc.b, round(lc.a * fade))
			ddt.text((round(x) + pad, ty), label, lc, 211, max_w=label_w - pad)
			if value:
				ddt.text((round(x) + label_w + pad, ty), value, colours.side_bar_line1, 212,
					max_w=round(w) - label_w - pad * 2)
			ry += row_h


class GalleryWidget(Widget):
	"""The Album Gallery grid.

	Reuses the main loop's gallery renderer (render_gallery in main(), exposed as
	tauon.gallery_render), which draws — and handles input for — the grid in the
	area described by gui.rspw / gui.panelY / gui.panelBY / window_size. The
	engine routes this widget through the offscreen scratch texture (window
	narrowed to the segment, mouse/fields/menus reframed), so the grid can't draw
	out of bounds; here we just point those geometry vars at the reframed segment
	for the duration of the call, then restore them.

	The preset paths only rebuild tauon.album_dex (the album index) while
	prefs.album_mode is on, so the widget rebuilds it itself when the viewed
	playlist changes (or the index is missing). Content edits to the *same*
	playlist while in custom mode aren't detected yet (same gap as elsewhere:
	those reload hooks are album_mode-gated).
	"""

	kind = "gallery"
	name = "Gallery: Classic"
	min_w = 100
	min_h = 80
	single_instance = True  # shared scroll/selection state (gui.album_scroll_px, gallery_scroll)
	offscreen = True

	# The gallery-family widget currently inside its render, if any. Lets
	# gallery_locate detect a locate triggered from within a widget's own
	# render (gallery click → show_current): that widget's per-instance scroll
	# is already live in the gui vars, so the swap must be skipped or the
	# draw's save-back would overwrite the located position.
	_rendering: GalleryWidget | None = None

	def __init__(self) -> None:
		self._dex_playlist_id: int | None = None

	def _ensure_album_dex(self, tauon: Tauon) -> None:
		pctl = tauon.pctl
		playlist = pctl.multi_playlist[pctl.active_playlist_viewing]
		if self._dex_playlist_id != playlist.uuid_int or (
			not tauon.album_dex and playlist.playlist_ids):
			tauon.reload_albums(quiet=True)
			self._dex_playlist_id = playlist.uuid_int

	def draw(self, tauon: Tauon, x: float, y: float, w: float, h: float) -> None:
		gallery_render = tauon.gallery_render
		self._ensure_album_dex(tauon)
		gui = tauon.gui
		ddt = tauon.ddt
		ws = tauon.window_size
		inp = tauon.inp
		saved = (gui.rspw, gui.panelY, gui.panelBY, gui.lsp, gui.show_playlist,
			gui.album_v_slide_value)
		# Match the text anti-aliasing background to the grid's fill so titles blend
		# cleanly (render_gallery sets this too, but set it up front and restore it
		# below so the gallery's value doesn't leak onto later widgets this frame).
		saved_text_bg = ddt.text_background_colour
		ddt.text_background_colour = tauon.colours.gallery_background
		# The preset's wheel gate only checks "right of the gallery's left edge"
		# (it always touches the window's right edge there), so in the reframed
		# space it would also catch a cursor over widgets beside this segment.
		# Zero the wheel for the call when the (segment-local) cursor is outside,
		# and restore it after so other widgets still receive the event.
		mx, my = inp.mouse_position[0], inp.mouse_position[1]
		over = x <= mx < x + round(w) and y <= my < y + round(h)
		saved_wheel = inp.mouse_wheel
		if not over:
			inp.mouse_wheel = 0
		# The renderer right-anchors at window_size[0] - rspw and spans panelY to
		# window_size[1] - panelBY; in the reframed space the segment IS the
		# window, so full width and no panels puts the grid exactly in the rect.
		gui.rspw = round(w)
		gui.panelY = round(y)
		gui.panelBY = max(0, ws[1] - round(y + h))
		gui.lsp = False
		gui.show_playlist = True
		# Rows are drawn at y = render_pos - album_scroll_px with no panelY term:
		# the preset's top slide (~50*scale) implicitly clears its ~30*scale top
		# panel, leaving a ~20*scale visible gap. The segment has no panel above
		# it, so keep only the visible gap or the grid sits ~30*scale too low.
		gui.album_v_slide_value = max(0, gui.album_v_slide_value - round(30 * gui.scale))
		# The scroll floor is -slide_value and the shared scroll position may sit
		# below the new floor (set while the preset slide was active); lift it or
		# the first row shows offset until the first wheel event re-clamps.
		gui.album_scroll_px = max(gui.album_scroll_px, -gui.album_v_slide_value)
		# Subclass hook: the Album Grid derives art size / gaps / row count from
		# the segment instead of the global gallery settings.
		grid = self._grid_overrides(tauon, w)
		saved_grid = None
		if grid is not None:
			art, h_gap, v_gap, n, margin = grid
			saved_grid = (tauon.album_mode_art_size, gui.album_h_gap, gui.album_v_gap,
				tauon.gall_ren.size, gui.gallery_forced_row_len, gui.gallery_grid_margin,
				gui.gallery_show_text, gui.gallery_scroll_key, gui.album_scroll_px,
				gui.last_row, tauon.gallery_scroll)
			tauon.album_mode_art_size = art
			gui.album_h_gap = h_gap
			gui.album_v_gap = v_gap
			# Thumbnails are cache-keyed by size; render them at the derived size
			# (the default arg of gall_ren.render reads this).
			tauon.gall_ren.size = art
			gui.gallery_forced_row_len = n
			gui.gallery_grid_margin = margin
			gui.gallery_show_text = self.titles
			# Per-instance gallery state: own scroll position / row memory /
			# smooth-scroll momentum channel / scroll-bar thumb, so several
			# galleries can coexist without fighting over the shared globals
			# (the Classic widget keeps using the globals).
			gui.gallery_scroll_key = self._scroll_key
			gui.album_scroll_px = self.scroll_px
			gui.last_row = self.last_row
			if self._scroll_box is None:
				self._scroll_box = type(tauon.gallery_scroll)(tauon=tauon, pctl=tauon.pctl)
			tauon.gallery_scroll = self._scroll_box
			GalleryWidget._rendering = self
			# The top margin comes from the slide gap: the scroll floor is
			# -slide, so at rest the first row sits `margin` below the top.
			gui.album_v_slide_value = margin
			gui.album_scroll_px = max(gui.album_scroll_px, -margin)
		try:
			gallery_render()
		finally:
			(gui.rspw, gui.panelY, gui.panelBY, gui.lsp, gui.show_playlist,
				gui.album_v_slide_value) = saved
			if saved_grid is not None:
				GalleryWidget._rendering = None
				self.scroll_px = gui.album_scroll_px
				self.last_row = gui.last_row
				(tauon.album_mode_art_size, gui.album_h_gap, gui.album_v_gap,
					tauon.gall_ren.size, gui.gallery_forced_row_len,
					gui.gallery_grid_margin, gui.gallery_show_text,
					gui.gallery_scroll_key, gui.album_scroll_px, gui.last_row,
					tauon.gallery_scroll) = saved_grid
			inp.mouse_wheel = saved_wheel
			ddt.text_background_colour = saved_text_bg
		self._after_render(tauon, over)

	def _grid_overrides(self, tauon: Tauon, seg_w: float) -> tuple[int, int, int, int, int] | None:
		"""Return (art_size, h_gap, v_gap, row_len, margin) in scaled px to force
		on the renderer for this widget, or None to use the global gallery
		settings. ``margin`` is the uniform outer inset (left/right/top)."""
		return None

	def _after_render(self, tauon: Tauon, over: bool) -> None:
		"""Hook run after the grid has rendered (overrides restored); ``over`` is
		whether the (segment-local) pointer is inside the segment."""


GRID_PER_ROW_MAX = 30
# Uniform outer margin (px unscaled) around the Gallery: Compact grid —
# based on the inset the preset's narrow-window branch gives on the left
# (20), pulled in slightly, applied on left/right/top so the edges match.
GRID_MARGIN = 15


class GridGalleryWidget(GalleryWidget):
	"""Gallery: Compact — the Album Gallery with tight, segment-derived spacing.

	Instead of the global album_mode_art_size / gap settings, the row length is
	a per-widget setting (albums per row) and the art size is computed so the
	row fills the segment width with the configured spacing between tiles.
	Everything else (scrolling, clicks, the album context menu, the scroll bar,
	titles under the art) is the shared gallery renderer, driven through
	_grid_overrides. Right-click on the background opens gallery_grid_menu
	(built in t_main), whose rows edit this instance's settings.

	NOT single-instance: each instance keeps its own scroll position, row
	memory, smooth-scroll momentum channel and scroll-bar thumb (swapped in
	around the render), so several Compact galleries — and the Classic one,
	which keeps the shared globals — can be shown at the same time.
	"""

	kind = "gallery_grid"
	name = "Gallery: Compact"
	min_w = 100
	min_h = 80
	single_instance = False
	offscreen = True

	# The instance whose settings gallery_grid_menu edits, set by whichever
	# instance opened the menu.
	menu_target: GridGalleryWidget | None = None
	menu_tauon: Tauon | None = None
	# Monotonic id source for per-instance smooth-scroll channel keys.
	_instance_counter: int = 0

	def __init__(self) -> None:
		super().__init__()
		self.per_row: int = 5
		self.spacing: int = 4    # px between tiles in a row (unscaled)
		self.v_spacing: int = 4  # px between rows (unscaled)
		self.titles: bool = True  # album/artist lines under the art
		# Per-instance gallery state, swapped into the shared gui vars around
		# the render (and by gallery_locate).
		self.scroll_px: float = 0.0
		self.last_row: int = 0
		GridGalleryWidget._instance_counter += 1
		self._scroll_key: str = f"gallery_grid_{GridGalleryWidget._instance_counter}"
		self._scroll_box = None  # lazily-made private ScrollBox (thumb drag state)

	# -- persistence --
	def get_config(self) -> dict | None:
		return {"per_row": self.per_row, "spacing": self.spacing,
			"v_spacing": self.v_spacing, "titles": self.titles}

	def set_config(self, d: dict) -> None:
		self.per_row = min(GRID_PER_ROW_MAX, max(1, int(d.get("per_row", 5))))
		self.spacing = min(CL_INSET_MAX, max(0, int(d.get("spacing", 4))))
		self.v_spacing = min(CL_INSET_MAX, max(0, int(d.get("v_spacing", 4))))
		self.titles = bool(d.get("titles", True))

	# -- geometry --
	def _grid_overrides(self, tauon: Tauon, seg_w: float) -> tuple[int, int, int, int, int] | None:
		gui = tauon.gui
		scale = gui.scale
		# The renderer's narrow-window width adjustment is disabled under
		# gallery_forced_row_len (it would double the left margin), so the
		# drawing width is exactly the segment width.
		w = round(seg_w)
		n = max(1, self.per_row)
		# With gallery_forced_row_len set, render_gallery lays tiles on the
		# uniform float pitch (w - 2*margin + h_gap) / n starting at margin, so
		# n tiles of art = pitch - spacing separated by `spacing` span the width
		# between matching left/right margins.
		margin = round(GRID_MARGIN * scale)
		if w - margin * 2 < n * round(8 * scale):
			margin = 0  # tiny segment: give the space to the art
		sp = round(self.spacing * scale)
		art = max(round(8 * scale), int((w - margin * 2 + sp) / n - sp))
		# Keep room for the text lines under each tile when this instance shows
		# them (gui.gallery_show_text is overridden to self.titles for the
		# render), like the preset gaps do (update_layout_do: text adds
		# ~41*scale; light-mode card style draws a taller card below the art).
		allow = 0
		if self.titles:
			allow = round(41 * scale)
			if tauon.prefs.use_card_style and tauon.colours.lm:
				allow = round(58 * scale)
		v_gap = round(self.v_spacing * scale) + allow
		return art, sp, v_gap, n, margin

	# -- background context menu --
	def _after_render(self, tauon: Tauon, over: bool) -> None:
		inp = tauon.inp
		# A right-click on an album tile has already activated gallery_menu by
		# now (making is_level_zero False), so this only fires on background.
		if over and inp.right_click and tauon.is_level_zero():
			inp.right_click = False
			GridGalleryWidget.menu_target = self
			GridGalleryWidget.menu_tauon = tauon
			tauon.gallery_grid_menu.activate()

	# -- incrementor callbacks (menu built in t_main; reference arg unused) --
	@classmethod
	def _menu_changed(cls) -> None:
		tauon = cls.menu_tauon
		if tauon is not None:
			tauon.gui.request_frame()
			tauon.custom.save_slots()

	@classmethod
	def menu_per_row_value(cls, ref=None) -> int:
		w = cls.menu_target
		return w.per_row if w else 0

	@classmethod
	def menu_per_row_minus(cls, ref=None) -> None:
		w = cls.menu_target
		if w and w.per_row > 1:
			w.per_row -= 1
			cls._menu_changed()

	@classmethod
	def menu_per_row_plus(cls, ref=None) -> None:
		w = cls.menu_target
		if w and w.per_row < GRID_PER_ROW_MAX:
			w.per_row += 1
			cls._menu_changed()

	@classmethod
	def menu_spacing_value(cls, ref=None) -> int:
		w = cls.menu_target
		return w.spacing if w else 0

	@classmethod
	def menu_spacing_minus(cls, ref=None) -> None:
		w = cls.menu_target
		if w and w.spacing > 0:
			w.spacing -= 1
			cls._menu_changed()

	@classmethod
	def menu_spacing_plus(cls, ref=None) -> None:
		w = cls.menu_target
		if w and w.spacing < CL_INSET_MAX:
			w.spacing += 1
			cls._menu_changed()

	@classmethod
	def menu_toggle_titles(cls, ref=None) -> None:
		w = cls.menu_target
		if w:
			w.titles = not w.titles
			cls._menu_changed()

	@classmethod
	def menu_titles_value(cls, ref=None) -> bool:
		w = cls.menu_target
		return w.titles if w else True

	@classmethod
	def menu_v_spacing_value(cls, ref=None) -> int:
		w = cls.menu_target
		return w.v_spacing if w else 0

	@classmethod
	def menu_v_spacing_minus(cls, ref=None) -> None:
		w = cls.menu_target
		if w and w.v_spacing > 0:
			w.v_spacing -= 1
			cls._menu_changed()

	@classmethod
	def menu_v_spacing_plus(cls, ref=None) -> None:
		w = cls.menu_target
		if w and w.v_spacing < CL_INSET_MAX:
			w.v_spacing += 1
			cls._menu_changed()


class WidgetSpec:
	"""Registry entry describing an addable widget and its sizing defaults."""

	def __init__(self, kind: str, name: str, category: str, factory: Callable[[WidgetSpec], Widget],
			lock_v: bool = False, lock_h: bool = False, fixed_w: int = 0, fixed_h: int = 0,
			single_instance: bool = False, draws_window_controls: bool = False,
			colour: ColourRGBA | None = None) -> None:
		self.kind = kind
		self.name = name
		self.category = category
		self.factory = factory
		self.lock_v = lock_v
		self.lock_h = lock_h
		self.fixed_w = fixed_w
		self.fixed_h = fixed_h
		self.single_instance = single_instance
		self.draws_window_controls = draws_window_controls
		self.colour = colour or ColourRGBA(28, 28, 34, 255)

	def make(self) -> Widget:
		return self.factory(self)


def _art(spec: WidgetSpec) -> Widget:
	return ArtBoxWidget()


def _top_panel(spec: WidgetSpec) -> Widget:
	return TopPanelWidget()


def _playback_panel(spec: WidgetSpec) -> Widget:
	return PlaybackPanelWidget()


def _playlist_list(spec: WidgetSpec) -> Widget:
	return PlaylistListWidget()


def _queue(spec: WidgetSpec) -> Widget:
	return QueueWidget()


def _artist_list(spec: WidgetSpec) -> Widget:
	return ArtistListWidget()


def _folder_nav(spec: WidgetSpec) -> Widget:
	return FolderNavWidget()


def _artist_info(spec: WidgetSpec) -> Widget:
	return ArtistInfoWidget()


def _tracklist(spec: WidgetSpec) -> Widget:
	return TracklistWidget()


def _gallery(spec: WidgetSpec) -> Widget:
	return GalleryWidget()


def _gallery_grid(spec: WidgetSpec) -> Widget:
	return GridGalleryWidget()


def _details(spec: WidgetSpec) -> Widget:
	return DetailsWidget()


def _meta_center(spec: WidgetSpec) -> Widget:
	return MetaCenterWidget()


def _meta_centered(spec: WidgetSpec) -> Widget:
	return MetaCenteredWidget()


def _lyrics(spec: WidgetSpec) -> Widget:
	return LyricsWidget()


def _milkdrop(spec: WidgetSpec) -> Widget:
	return MilkDropWidget()


def _vis_sticks(spec: WidgetSpec) -> Widget:
	return SticksVisWidget()


def _vis_spectrogram(spec: WidgetSpec) -> Widget:
	return SpectrogramWidget()


# Registry — the Add menu and (de)serialization are driven by this table. The
# lock / single-instance defaults follow the agreed widget table.
WIDGET_SPECS: list[WidgetSpec] = [
	WidgetSpec("tracklist", "Tracklist", "Content", _tracklist, single_instance=True,
		colour=ColourRGBA(24, 24, 28, 255)),
	WidgetSpec("gallery", "Gallery: Classic", "Content", _gallery, single_instance=True,
		colour=ColourRGBA(26, 24, 30, 255)),
	WidgetSpec("gallery_grid", "Gallery: Compact", "Content", _gallery_grid,
		colour=ColourRGBA(26, 24, 30, 255)),
	WidgetSpec("art", "Art Box", "Content", _art, single_instance=True, colour=ColourRGBA(20, 20, 20, 255)),
	WidgetSpec("playlist_list", "Playlist List", "Side Panels", _playlist_list, single_instance=True,
		colour=ColourRGBA(24, 26, 30, 255)),
	WidgetSpec("folder_nav", "Folder Navigator", "Side Panels", _folder_nav, single_instance=True,
		colour=ColourRGBA(24, 26, 28, 255)),
	WidgetSpec("artist_list", "Artist List", "Side Panels", _artist_list, single_instance=True,
		colour=ColourRGBA(24, 28, 26, 255)),
	WidgetSpec("queue", "Queue", "Side Panels", _queue, single_instance=True,
		colour=ColourRGBA(28, 26, 24, 255)),
	WidgetSpec("lyrics", "Lyrics Box", "Content", _lyrics, single_instance=True, colour=ColourRGBA(26, 26, 30, 255)),
	WidgetSpec("meta_center", "Track: Titles", "Content", _meta_center, colour=ColourRGBA(30, 30, 34, 255)),
	WidgetSpec("meta_centered", "Track: Titles (Centred)", "Content", _meta_centered, colour=ColourRGBA(30, 31, 35, 255)),
	WidgetSpec("details", "Track: Details", "Content", _details, colour=ColourRGBA(28, 30, 36, 255)),
	WidgetSpec("artist_info", "Artist Info", "Content", _artist_info, single_instance=True,
		colour=ColourRGBA(30, 28, 34, 255)),
	WidgetSpec("milkdrop", "Visualiser: Milkdrop", "Visualizers", _milkdrop,
		single_instance=True, colour=ColourRGBA(18, 18, 28, 255)),
	WidgetSpec("vis_sticks", "Visualiser: Bars", "Visualizers", _vis_sticks,
		single_instance=True, colour=ColourRGBA(16, 16, 22, 255)),
	WidgetSpec("vis_spectrogram", "Visualiser: Spectrogram", "Visualizers", _vis_spectrogram,
		single_instance=True, colour=ColourRGBA(12, 12, 16, 255)),
	WidgetSpec("playback_panel", "Playback Panel", "Panels", _playback_panel,
		lock_v=True, fixed_h=51, single_instance=True, colour=ColourRGBA(32, 32, 40, 255)),
	WidgetSpec("top_panel", "Header Bar", "Panels", _top_panel,
		lock_v=True, fixed_h=30, single_instance=True, draws_window_controls=True,
		colour=ColourRGBA(38, 38, 46, 255)),
]
SPEC_BY_KIND: dict[str, WidgetSpec] = {s.kind: s for s in WIDGET_SPECS}


def make_widget(kind: str) -> Widget | None:
	spec = SPEC_BY_KIND.get(kind)
	return spec.make() if spec else None


# ---------------------------------------------------------------------------
# Layout tree
# ---------------------------------------------------------------------------

class Node:
	"""Base layout node: sizing within the parent stack + computed rect."""

	def __init__(self) -> None:
		self.weight: float = 1.0
		self.lock_v: bool = False
		self.lock_h: bool = False
		self.fixed_w: int = 0
		self.fixed_h: int = 0
		self.aspect: bool = False          # keep widget content aspect on draw
		self.square: bool = False          # Square Max: take the parent-axis length that makes the slot square
		self.gutter: int = 0               # margin outside the border, px (unscaled)
		self.padding: int = 0              # inset inside the border, px (unscaled)
		self.border: bool = False
		self.rect: tuple[float, float, float, float] = (0, 0, 0, 0)
		# The full slot allotted by the parent stack, before the gutter inset
		# (equals rect when gutter is 0). Resize boundaries and drag math use
		# this, so hot spots and behaviour don't shift when a gutter is set.
		self.slot_rect: tuple[float, float, float, float] = (0, 0, 0, 0)

	# -- serialization --
	def _base_dict(self) -> dict:
		return {
			"weight": self.weight, "lock_v": self.lock_v, "lock_h": self.lock_h,
			"fixed_w": self.fixed_w, "fixed_h": self.fixed_h, "aspect": self.aspect,
			"square": self.square,
			"gutter": self.gutter, "padding": self.padding, "border": self.border,
		}

	def _load_base(self, d: dict) -> None:
		self.weight = d.get("weight", 1.0)
		self.lock_v = d.get("lock_v", False)
		self.lock_h = d.get("lock_h", False)
		self.fixed_w = d.get("fixed_w", 0)
		self.fixed_h = d.get("fixed_h", 0)
		self.aspect = d.get("aspect", False)
		self.square = d.get("square", False)
		self.gutter = d.get("gutter", 0)
		self.padding = d.get("padding", 0)
		self.border = d.get("border", False)


class Leaf(Node):
	def __init__(self, widget: Widget | None = None) -> None:
		super().__init__()
		self.widget = widget
		if widget is not None:
			self._adopt(widget)

	def _adopt(self, widget: Widget) -> None:
		if widget.lock_v:
			self.lock_v = True
			self.fixed_h = widget.fixed_h
		if widget.lock_h:
			self.lock_h = True
			self.fixed_w = widget.fixed_w

	@property
	def kind(self) -> str | None:
		return self.widget.kind if self.widget else None

	def to_dict(self) -> dict:
		d = self._base_dict()
		d["type"] = "leaf"
		d["kind"] = self.kind
		if self.widget is not None:
			conf = self.widget.get_config()
			if conf:
				d["conf"] = conf
		return d

	@staticmethod
	def from_dict(d: dict) -> "Leaf":
		kind = d.get("kind")
		leaf = Leaf(make_widget(kind) if kind else None)
		leaf._load_base(d)
		conf = d.get("conf")
		if leaf.widget is not None and isinstance(conf, dict):
			leaf.widget.set_config(conf)
		return leaf


class Stack(Node):
	def __init__(self, orient: str, children: list[Node]) -> None:
		super().__init__()
		assert orient in ("v", "h")
		self.orient = orient
		self.children = children
		# When set, the boundaries between this stack's children can be dragged
		# in view mode too (edit mode off).
		self.resizable: bool = False

	def to_dict(self) -> dict:
		d = self._base_dict()
		d["type"] = "stack"
		d["orient"] = self.orient
		d["resizable"] = self.resizable
		d["children"] = [c.to_dict() for c in self.children]
		return d

	@staticmethod
	def from_dict(d: dict) -> "Stack":
		st = Stack(d.get("orient", "v"), [node_from_dict(c) for c in d.get("children", [])])
		st._load_base(d)
		st.resizable = d.get("resizable", False)
		return st


def node_from_dict(d: dict) -> Node:
	return Stack.from_dict(d) if d.get("type") == "stack" else Leaf.from_dict(d)


# -- layout pass ------------------------------------------------------------

def _fixed_on(node: Node, axis: str, scale: float) -> float | None:
	if axis == "v" and node.lock_v:
		return node.fixed_h * scale
	if axis == "h" and node.lock_h:
		return node.fixed_w * scale
	return None


def _min_on(node: Node, axis: str, scale: float) -> float:
	"""Smallest length (scaled px) ``node`` can be squeezed to along ``axis``
	without pushing a widget below its declared minimum: a locked node needs
	its fixed px, a widget leaf its ``min_w``/``min_h``, a stack the sum of its
	children's minimums along its own axis (the max across it). Empty cells
	collapse to nothing."""
	f = _fixed_on(node, axis, scale)
	if f is not None:
		return f
	if isinstance(node, Stack):
		if not node.children:
			return 0.0
		mins = [_min_on(c, axis, scale) for c in node.children]
		return sum(mins) if node.orient == axis else max(mins)
	if isinstance(node, Leaf) and node.widget is not None:
		return (node.widget.min_h if axis == "v" else node.widget.min_w) * scale
	return 0.0


def _eff_edge(node: Node, side: str, scale: float) -> float:
	"""Total natural inset (scaled px) a subtree applies between its slot edge
	and its content at ``side`` ("l"/"r"/"t"/"b"): the node's own gutter plus
	whatever its edge children add inside. Along a stack's axis only the
	first/last child touches that edge; across it every child does, so take the
	minimum (a child with no gutter means content reaches that edge)."""
	g = node.gutter * scale
	if not isinstance(node, Stack) or not node.children:
		return g
	first = ("t" if node.orient == "v" else "l")
	last = ("b" if node.orient == "v" else "r")
	if side == first:
		return g + _eff_edge(node.children[0], side, scale)
	if side == last:
		return g + _eff_edge(node.children[-1], side, scale)
	return g + min(_eff_edge(c, side, scale) for c in node.children)


def layout(node: Node, x: float, y: float, w: float, h: float, scale: float,
		consumed: frozenset[str] = frozenset()) -> None:
	"""Assign rects to ``node`` and its descendants. Locked children take fixed
	(scaled) pixels along the parent's axis; the remainder splits by weight; the
	cross axis fills. Locks only steer this distribution — they never inset or
	clamp drawing (a lock on the cross axis is applied to the ancestor whose
	parent divides that axis; see CustomLayout._lock_target). Gutter insets each child's allotted slot; where the
	subtrees on BOTH sides of an internal boundary are guttered at their facing
	edges (per _eff_edge, so this works across nesting levels — e.g. a leaf
	beside a stack of guttered leaves) they share the gutter: each side insets
	max(e1, e2) / 2, so the visible gap is the larger gutter rather than the
	sum. The shared inset is applied here in full and the edge is marked
	``consumed`` for the child's subtree, so descendants add nothing on top.
	Boundaries with a bare edge on either side, outer edges and the cross axis
	keep natural (nested) gutters.
	"""
	node.rect = (x, y, w, h)
	node.slot_rect = (x, y, w, h)  # parent overwrites with the pre-gutter slot below
	if not isinstance(node, Stack) or not node.children:
		return

	axis = node.orient
	total = h if axis == "v" else w
	fixed = [_fixed_on(c, axis, scale) for c in node.children]
	# Square Max children take the length that makes their slot square (the
	# stack's cross extent), capped so locked siblings keep their px and the
	# remaining flex siblings can still reach their minimum sizes. They then
	# behave like locked children for the weight split below.
	squares = [i for i, (c, f) in enumerate(zip(node.children, fixed)) if f is None and c.square]
	if squares:
		cross = w if axis == "v" else h
		others_min = sum(
			_min_on(c, axis, scale)
			for i, (c, f) in enumerate(zip(node.children, fixed))
			if f is None and i not in squares)
		cap = max(0.0, total - sum(f for f in fixed if f is not None) - others_min)
		grant = max(0.0, min(cross, cap / len(squares)))
		for i in squares:
			fixed[i] = grant
	locked_total = sum(f for f in fixed if f is not None)
	flex = [c for c, f in zip(node.children, fixed) if f is None]
	weight_total = sum(c.weight for c in flex) or 1.0
	available = max(0.0, total - locked_total)

	lead_side, trail_side = ("t", "b") if axis == "v" else ("l", "r")
	cross_sides = ("l", "r") if axis == "v" else ("t", "b")
	n = len(node.children)
	gutters = [c.gutter * scale for c in node.children]
	# Per-child axis insets: the child's own gutter by default (its descendants
	# nest inside naturally), overridden at shared boundaries and consumed edges.
	lead = list(gutters)
	trail = list(gutters)
	child_consumed: list[set[str]] = [set() for _ in range(n)]

	# This node's consumed edges pass through to the children touching them.
	if lead_side in consumed:
		lead[0] = 0.0
		child_consumed[0].add(lead_side)
	if trail_side in consumed:
		trail[-1] = 0.0
		child_consumed[-1].add(trail_side)

	for i in range(n - 1):
		e_a = _eff_edge(node.children[i], trail_side, scale)
		e_b = _eff_edge(node.children[i + 1], lead_side, scale)
		if e_a > 0 and e_b > 0:
			shared = max(e_a, e_b) / 2
			trail[i] = shared
			lead[i + 1] = shared
			child_consumed[i].add(trail_side)
			child_consumed[i + 1].add(lead_side)

	cursor = y if axis == "v" else x
	for i, (child, f) in enumerate(zip(node.children, fixed)):
		length = f if f is not None else available * (child.weight / weight_total)
		g = gutters[i]
		# Cross-axis insets: the child's own gutter, unless this node's edge
		# there was consumed by a shared boundary in the grandparent.
		c0 = 0.0 if cross_sides[0] in consumed else g
		c1 = 0.0 if cross_sides[1] in consumed else g
		for side in cross_sides:
			if side in consumed:
				child_consumed[i].add(side)
		if axis == "v":
			cx, cy = x + c0, cursor + lead[i]
			cw, ch = max(0.0, w - c0 - c1), max(0.0, length - lead[i] - trail[i])
		else:
			cx, cy = cursor + lead[i], y + c0
			cw, ch = max(0.0, length - lead[i] - trail[i]), max(0.0, h - c0 - c1)
		# The child's rect already accounts for its gutter inset; descendants and
		# draw use it directly (no double inset).
		layout(child, cx, cy, cw, ch, scale, frozenset(child_consumed[i]))
		child.slot_rect = (x, cursor, w, length) if axis == "v" else (cursor, y, length, h)
		cursor += length


def content_rect(leaf: Leaf, scale: float) -> tuple[float, float, float, float]:
	"""Drawable rect of a leaf. The gutter inset is already baked into
	``leaf.rect`` by the layout pass, so this is just the rect."""
	return leaf.rect


def iter_leaves(node: Node):
	if isinstance(node, Stack):
		for c in node.children:
			yield from iter_leaves(c)
	else:
		yield node


def leaf_at(node: Node, px: float, py: float) -> Node | None:
	x, y, w, h = node.rect
	if not (x <= px < x + w and y <= py < y + h):
		return None
	if isinstance(node, Stack):
		for c in node.children:
			hit = leaf_at(c, px, py)
			if hit is not None:
				return hit
		return node
	return node


def find_parent(root: Node, target: Node) -> Stack | None:
	if isinstance(root, Stack):
		for c in root.children:
			if c is target:
				return root
			found = find_parent(c, target)
			if found is not None:
				return found
	return None


def count_kind(root: Node, kind: str) -> int:
	return sum(1 for leaf in iter_leaves(root) if isinstance(leaf, Leaf) and leaf.kind == kind)




# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

# Upper clamp (unscaled px) for the gutter / padding incrementor steppers.
CL_INSET_MAX = 64
# Half-width (unscaled px) of the grab band around a stack boundary for resize
# dragging. One constant so the drag hit-test, the hover fields and the resize
# cursor stay aligned — a mismatch makes the cursor stick or show where a drag
# can't start.
BOUNDARY_GRAB = 5
# Defaults applied to a segment when a widget is first added to it (Add menu
# and template leaves). Replacing an existing widget keeps the segment's
# configured gutter/border.
DEFAULT_WIDGET_GUTTER = 3
DEFAULT_WIDGET_BORDER = True
STACK_COUNTS = [2, 3, 4, 5]
TEMPLATES = ["Blank", "Volcano", "Tracks + Gallery (Compact)"]


class CustomLayout:
	"""Owns the custom layout trees and drives them. Active only while
	``gui.custom_mode`` is set; edits only while ``gui.custom_edit`` is set.
	"""

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.gui = tauon.gui
		self.ddt = tauon.ddt
		self.renderer = tauon.renderer
		# Custom layout slots: a dynamic list (create/delete via the edit
		# context menu, always at least one). Each slot has an optional
		# user-visible name (None = derived: "Empty Slot" for empty/Blank
		# slots, see slot_title()). load_slots() replaces these lists.
		self.slots: list[Node | None] = [None]
		self.slot_names: list[str | None] = [None]
		self.active_slot = 0
		self._loaded = False
		# Guards save_slots(): only True after load_slots() succeeded (or seeded
		# a first run). While False, saving would serialise the placeholder
		# defaults above and destroy the user's file — e.g. exiting the app from
		# mini mode with custom_mode restored from state.p but never rendered.
		self._save_ok = False

		# Per-slot columns header-bar config: each slot remembers its own
		# gui.pl_st (columns) / set_bar / set_mode / pl_st_left. The preset's
		# columns are stashed in _preset_columns while a slot is active so
		# exiting custom mode restores them. _columns_owner tracks whose config
		# gui currently holds (None = preset, else a slot index). Persisted in
		# custom_layouts.json, not the global state.p.
		self.slot_columns: list[dict | None] = [None]
		self._preset_columns: dict | None = None
		self._columns_owner: int | None = None

		# edit-mode transient state
		self.menu_target: Node | None = None
		self.drag: dict | None = None          # {stack, index, axis} — edge resize
		self.widget_drag: Node | None = None   # leaf being dragged to swap
		# View-mode input handed from handle_input() to render(): the real mouse
		# state, stashed while the underlying UI is neutralised, then restored so
		# the custom widgets receive it during their own render.
		self._held_mouse: tuple | None = None
		# Real held-button state during a view-mode boundary drag (the stash above
		# gets a neutralised copy so widgets don't react); re-applied after render.
		self._drag_held_down: bool = False
		# Dedicated scratch texture for offscreen widget compositing, kept separate
		# from gui.tracklist_texture so the Tracklist widget can keep caching into
		# that. Created lazily and recreated if the max window texture size grows.
		self._scratch = None
		self._scratch_size = 0
		# Native context menu (a t_main Menu instance), built by
		# build_custom_layout_menu() in t_main and assigned here. The engine only
		# activates it and exposes callbacks; all drawing is the native system's.
		self.menu = None

	# -- templates / defaults -----------------------------------------------

	def _empty(self) -> Leaf:
		return Leaf(None)

	def _leaf(self, kind: str) -> Leaf:
		leaf = Leaf(make_widget(kind))
		spec = SPEC_BY_KIND.get(kind)
		# Fixed-size (locked-axis) widgets like the Top / Playback panels don't
		# get the default gutter.
		if spec is None or spec.lock_v or spec.lock_h:
			leaf.gutter = 0
		else:
			leaf.gutter = DEFAULT_WIDGET_GUTTER
		leaf.border = DEFAULT_WIDGET_BORDER
		return leaf

	def template(self, name: str) -> Node:
		if name == "Volcano":
			return self._template_volcano()
		if name == "Tracks + Gallery (Compact)":
			return self._template_tracks_gallery_compact()
		return self._template_blank()

	def _bars(self, body: Node) -> Stack:
		"""Wrap a body in the standard top / bottom bars (borderless, gutterless)."""
		top = self._leaf("top_panel")
		top.gutter = 0
		top.border = False
		bottom = self._leaf("playback_panel")
		bottom.gutter = 0
		bottom.border = False
		return Stack("v", [top, body, bottom])

	def _template_blank(self) -> Node:
		# "Blank": top bar / empty scalable middle / bottom bar.
		body = self._empty()
		body.weight = 1.0
		return self._bars(body)

	def _template_volcano(self) -> Node:
		# "Volcano": tracklist over a fixed-height spectrogram strip on the
		# left, a fixed-width art-over-details column on the right.
		tracks = self._leaf("tracklist")
		tracks.weight = 1.76
		spectro = self._leaf("vis_spectrogram")
		spectro.weight = 0.24
		spectro.lock_v = True
		spectro.fixed_h = 61
		left = Stack("v", [tracks, spectro])
		left.weight = 1.38
		art = self._leaf("art")
		details = self._leaf("details")
		right = Stack("v", [art, details])
		right.weight = 0.62
		right.lock_h = True
		right.fixed_w = 285
		body = Stack("h", [left, right])
		body.weight = 1.0
		return self._bars(body)

	def _template_tracks_gallery_compact(self) -> Node:
		# "Tracks + Gallery (Compact)": a resizable split of the tracklist
		# beside a compact gallery (3 albums per row).
		tracks = self._leaf("tracklist")
		tracks.weight = 0.81
		gallery = self._leaf("gallery_grid")
		gallery.weight = 1.19
		if gallery.widget is not None:
			gallery.widget.set_config({"per_row": 3, "spacing": 4, "v_spacing": 4, "titles": True})
		body = Stack("h", [tracks, gallery])
		body.weight = 1.0
		body.resizable = True
		return self._bars(body)

	def ensure_loaded(self) -> None:
		"""Load the slot lists from disk if they haven't been yet (the settings
		card reads and edits them without entering custom mode)."""
		if not self._loaded:
			self.load_slots()

	def ensure_slot(self) -> Node:
		if not self._loaded:
			self.load_slots()
		if self.slots[self.active_slot] is None:
			# An empty slot materialises as the Blank template (bars + empty
			# scalable middle) — that's what "Empty Slot" means.
			self.slots[self.active_slot] = self.template("Blank")
		return self.slots[self.active_slot]

	# -- slot names ------------------------------------------------------------

	@staticmethod
	def _is_blank_tree(root: Node | None) -> bool:
		"""True when the tree has no content widgets (only the top/playback bars
		and empty cells) — i.e. it is the Blank template or equivalent."""
		if root is None:
			return True

		def walk(n: Node) -> bool:
			if isinstance(n, Stack):
				return all(walk(c) for c in n.children)
			if isinstance(n, Leaf) and n.widget is not None:
				return n.widget.kind in ("top_panel", "playback_panel")
			return True
		return walk(root)

	def slot_title(self, slot: int) -> str:
		"""The user-visible name of a slot, shown in the corner layout menu.
		Renaming or loading a template sets an explicit name; unnamed slots
		derive one: "Empty Slot" when empty/Blank, else a generic label."""
		if not 0 <= slot < len(self.slots):
			return _t("Empty Slot")
		name = self.slot_names[slot]
		if name:
			return name
		if self._is_blank_tree(self.slots[slot]):
			return _t("Empty Slot")
		return _t("Custom Layout")

	def _refresh_layout_menu(self) -> None:
		"""Rebuild the corner layout menu's slot entries (names/count changed).
		The rebuild function is installed by t_main's menu construction; absent
		in headless tests."""
		cb = getattr(self.tauon, "rebuild_layout_menu", None)
		if callable(cb):
			cb()

	# -- persistence ---------------------------------------------------------

	def _path(self):
		return self.tauon.user_directory / "custom_layouts.json"

	def load_slots(self) -> None:
		self._loaded = True
		try:
			p = self._path()
			if p.is_file():
				data = json.loads(p.read_text(encoding="utf-8"))
				# Slots are numbered keys "0".."n-1"; read consecutively so the
				# count is whatever was saved (legacy files hold three).
				slots: list[Node | None] = []
				i = 0
				while str(i) in data:
					d = data[str(i)]
					slots.append(node_from_dict(d) if d else None)
					i += 1
				if not slots:
					slots = [None]
				self.slots = slots
				names = data.get("names")
				self.slot_names = [
					(names.get(str(i)) if isinstance(names, dict) else None) or None
					for i in range(len(slots))
				]
				# Which slot was last active (so a restart into custom mode
				# resumes the same layout).
				a = data.get("active")
				self.active_slot = a if isinstance(a, int) and 0 <= a < len(self.slots) else 0
				# Per-slot columns header-bar config.
				cols = data.get("columns")
				self.slot_columns = [
					(cols.get(str(i)) if isinstance(cols, dict) else None)
					for i in range(len(slots))
				]
				self.slot_columns = [c if isinstance(c, dict) else None for c in self.slot_columns]
			else:
				# First run (no saved layouts): seed ready-made layouts plus one
				# empty slot.
				self.slots = [
					self.template("Volcano"),
					self.template("Tracks + Gallery (Compact)"),
					None,
				]
				self.slot_names = ["Volcano", "Tracks + Gallery (Compact)", None]
				self.slot_columns = [None, None, None]
			self._save_ok = True
		except Exception:
			# _save_ok stays False: the file may hold layouts we couldn't read,
			# so refuse to overwrite it for the rest of the session.
			logging.exception("Failed to load custom layouts")
		self._refresh_layout_menu()

	def save_slots(self) -> None:
		if not self._save_ok:
			logging.warning("Refusing to save custom layouts: current file was never successfully loaded")
			return
		try:
			# Capture the live columns into the active slot so edits made via the
			# header bar (resize/reorder/hide) are persisted.
			if self._columns_owner is not None and 0 <= self._columns_owner < len(self.slot_columns):
				self.slot_columns[self._columns_owner] = self._capture_columns()
			data = {str(i): (s.to_dict() if s else None) for i, s in enumerate(self.slots)}
			data["active"] = self.active_slot
			data["names"] = {str(i): n for i, n in enumerate(self.slot_names) if n}
			data["columns"] = {str(i): c for i, c in enumerate(self.slot_columns) if c is not None}
			with atomic_save(self._path(), "w") as file:
				file.write(json.dumps(data, indent=1))
		except Exception:
			logging.exception("Failed to save custom layouts")

	# -- per-slot columns config --------------------------------------------

	@staticmethod
	def _copy_columns(cfg: dict) -> dict:
		return {
			"pl_st": [list(c) for c in cfg["pl_st"]],
			"set_bar": bool(cfg["set_bar"]),
			"set_mode": bool(cfg["set_mode"]),
			"pl_st_left": cfg["pl_st_left"],
		}

	def _capture_columns(self) -> dict:
		"""Snapshot the live columns header-bar config off gui."""
		gui = self.gui
		return {
			"pl_st": [list(c) for c in gui.pl_st],
			"set_bar": bool(gui.set_bar),
			"set_mode": bool(gui.set_mode),
			"pl_st_left": gui.pl_st_left,
		}

	def _apply_columns(self, cfg: dict) -> None:
		"""Push a columns config onto gui and repaint the tracklist/layout."""
		gui = self.gui
		gui.pl_st = [list(c) for c in cfg["pl_st"]]
		gui.set_bar = bool(cfg.get("set_bar", True))
		gui.set_mode = bool(cfg.get("set_mode", False))
		gui.pl_st_left = cfg.get("pl_st_left", 16)
		gui.request_tracklist_redraw()
		gui.update_layout = True
		gui.request_frame()

	def _activate_columns(self, owner: int | None) -> None:
		"""Swap the global columns config between the preset (owner=None) and a
		custom slot (owner=slot index): save the outgoing owner's live config,
		then load the incoming one. A slot with no saved config yet is seeded
		from the preset columns."""
		if owner == self._columns_owner:
			return
		cur = self._capture_columns()
		if self._columns_owner is None:
			self._preset_columns = cur
		else:
			self.slot_columns[self._columns_owner] = cur
		if owner is None:
			cfg = self._preset_columns
		else:
			cfg = self.slot_columns[owner]
			if cfg is None:
				cfg = self._copy_columns(self._preset_columns or cur)
				self.slot_columns[owner] = cfg
		if cfg is not None:
			self._apply_columns(cfg)
		self._columns_owner = owner

	def preset_columns_snapshot(self) -> dict:
		"""The columns config that state.p should persist as the PRESET one —
		the backup while a slot is active, else the live gui config. Keeps a
		custom slot's columns from leaking into the global (preset) save."""
		if self.gui.custom_mode and self._preset_columns is not None:
			return self._preset_columns
		return self._capture_columns()

	# -- entry / exit --------------------------------------------------------

	def enter(self, slot: int | None = None) -> None:
		"""Enter a custom layout slot, in view mode. slot=None re-enters the
		last-active slot (restored from disk on first load)."""
		if self.gui.radio_view:
			# Leave radio view like any other layout pick would — a lingering
			# radio_view flag leaks into custom mode (the main menu's "New
			# Playlist" entry turns into "New Radio List" and creates radio
			# playlists, the Header Bar tab strip shows radio lists).
			self.tauon.exit_combo(restore=True)
		# Load before setting the slot — load_slots restores the last-active
		# slot index, which would clobber an explicit pick made afterwards.
		if not self._loaded:
			self.load_slots()
		if slot is not None:
			self.active_slot = max(0, min(slot, len(self.slots) - 1))
		self.gui.custom_mode = True
		self.gui.custom_edit = False
		self._close_menu()
		self.ensure_slot()
		# Swap in this slot's own columns header-bar config (backing up the
		# preset columns on the first entry from a non-custom view).
		self._activate_columns(self.active_slot)
		self.save_slots()  # persist the active slot + its columns
		# Recompute panel geometry immediately (as exit_mode does). Without this
		# the switch only partially applies and needs a click/scroll to finish —
		# update_layout_do() runs at the top of the next frame from this flag.
		self.gui.request_tracklist_redraw()
		self.gui.update_layout = True
		self.gui.request_frame()

	def exit_mode(self) -> None:
		# Save the active slot's columns and restore the preset columns before
		# leaving, then persist so the slot config survives.
		self._activate_columns(None)
		self.save_slots()
		self.gui.custom_mode = False
		self.gui.custom_edit = False
		self.gui.milkdrop_in_widget = False  # hand the visualisers back to the presets
		self.gui.vis4_in_widget = False
		self.gui.draw_vis4_top = False
		self.gui.spectrogram_in_widget = False
		self._close_menu()
		# Force a full preset playlist render so it repaints at full size and
		# clears the Tracklist widget's clip rect (else cache_render would keep
		# copying only the old segment).
		self.gui.request_tracklist_redraw()
		self.gui.update_layout = True
		self.gui.request_frame()

	def toggle_edit(self) -> None:
		self.gui.custom_edit = not self.gui.custom_edit
		self._close_menu()
		self.gui.request_frame()

	# -- tree actions (pure; unit-tested) -----------------------------------

	def act_add_stack(self, target: Node, orient: str, count: int) -> None:
		root = self.ensure_slot()
		children: list[Node] = []
		if isinstance(target, Leaf) and target.widget is not None:
			# Keep the existing widget as the first cell.
			keep = Leaf(target.widget)
			keep._load_base(target.to_dict())
			children.append(keep)
		while len(children) < count:
			children.append(self._empty())
		new = Stack(orient, children)
		# Inherit the target's sizing within its own parent.
		new.weight = target.weight
		self._replace(root, target, new)
		self.save_slots()

	def act_add_widget(self, target: Node, kind: str) -> bool:
		root = self.ensure_slot()
		spec = SPEC_BY_KIND.get(kind)
		if spec is None:
			return False
		if spec.single_instance and count_kind(root, kind) > 0:
			self.tauon.show_message(_t("Only one %s allowed") % spec.name, mode="warning")
			return False
		if not isinstance(target, Leaf):
			return False
		was_empty = target.widget is None
		target.widget = spec.make()
		target._adopt(target.widget)
		if was_empty:
			# Fresh add: apply the widget defaults — except fixed-size
			# (locked-axis) widgets like the Top / Playback panels, which get no
			# gutter. Replace keeps the segment's configured gutter/border.
			target.gutter = 0 if (spec.lock_v or spec.lock_h) else DEFAULT_WIDGET_GUTTER
			target.border = DEFAULT_WIDGET_BORDER
		self.save_slots()
		return True

	def act_remove_widget(self, target: Node) -> None:
		if isinstance(target, Leaf):
			target.widget = None
			target.lock_v = target.lock_h = False
			target.aspect = False
			target.square = False
			self.save_slots()

	def act_remove_stack(self, target: Node) -> None:
		"""Remove the stack the target segment is directly in — its immediate
		parent stack — collapsing just that one row/column into a single empty
		segment in its place. Everything outside that stack is left intact.

		If the segment sits directly in the root (no enclosing sub-stack), this is
		a no-op: there is no nested stack to remove and we never clear the whole
		layout. (Use Remove to clear a single segment's widget.)
		"""
		root = self.slots[self.active_slot]
		if not isinstance(root, Stack) or target is None:
			return
		parent = find_parent(root, target)
		if parent is None or parent is root:
			return
		grand = find_parent(root, parent)
		if grand is None:
			return
		new = self._empty()
		new.weight = parent.weight
		grand.children[grand.children.index(parent)] = new
		self.save_slots()

	def _lock_target(self, root: Node, target: Node, axis: str) -> Node | None:
		"""The node a v/h lock controls: the nearest node on the path from
		``target`` up to the root whose parent stack divides space along
		``axis``. A lock anywhere deeper would sit on a filled cross axis and
		do nothing. None when no ancestor stack divides that axis."""
		node = target
		while True:
			parent = find_parent(root, node)
			if parent is None:
				return None
			if parent.orient == axis:
				return node
			node = parent

	def act_set_lock(self, target: Node, axis: str) -> None:
		"""Toggle a v/h size lock. Locks only steer how window-resize deltas
		are distributed: the locked node (the segment, or the container stack
		that actually divides that axis — see _lock_target) keeps its pixel
		size while unlocked siblings scale. Drawing, margins and insets are
		never affected. A row/column may end up fully locked: layout then
		leaves the leftover space as background rather than stretching
		anything. Aspect ("Lock Square") stays per-segment and does affect
		how the widget draws."""
		root = self.ensure_slot()
		if axis == "a":  # aspect
			target.aspect = not target.aspect
			self.save_slots()
			return
		node = self._lock_target(root, target, axis)
		if node is None:
			self.tauon.show_message(_t("Can't lock: nothing divides the layout in that direction"), mode="warning")
			return
		if axis == "v":
			new = not node.lock_v
			if new:
				# Slot size, not the gutter-inset content size — fixed_h/w are
				# slot lengths in the layout pass (the gutter insets within).
				node.fixed_h = max(1, round(node.slot_rect[3] / self.gui.scale))
			node.lock_v = new
		else:
			new = not node.lock_h
			if new:
				node.fixed_w = max(1, round(node.slot_rect[2] / self.gui.scale))
			node.lock_h = new
		self.save_slots()

	def act_toggle_square(self, target: Node) -> None:
		"""Toggle Square Max: instead of a weight share, the segment takes as
		much of its parent stack as makes its slot square (parent-axis length =
		cross extent), yielding only so locked siblings keep their px and other
		widgets keep their minimum sizes."""
		target.square = not target.square
		if target.square:
			# A parent-axis lock on the same node wins over square in layout()
			# — and edge-dragging a Square Max boundary installs exactly that
			# lock (the drag converts square to a plain px lock). Clear it so
			# re-enabling from the menu actually takes effect again.
			parent = find_parent(self.ensure_slot(), target)
			if parent is not None:
				if parent.orient == "v":
					target.lock_v = False
				else:
					target.lock_h = False
		self.save_slots()

	def act_toggle_stack_resizable(self, stack: Stack) -> None:
		"""Toggle view-mode resizing for a stack: when set, the boundaries
		between its children can be dragged with edit mode off (same weight/px
		semantics as edit-mode resizing)."""
		stack.resizable = not stack.resizable
		self.save_slots()

	def act_set_gutter(self, target: Node, px: int) -> None:
		target.gutter = px
		self.save_slots()

	def act_set_padding(self, target: Node, px: int) -> None:
		target.padding = px
		self.save_slots()

	def act_toggle_border(self, target: Node) -> None:
		target.border = not target.border
		self.save_slots()

	def act_swap(self, a: Node, b: Node) -> None:
		"""Swap two leaves' widgets (and their widget-related lock/aspect state),
		keeping each slot's position attributes (weight, gutter, border). Dragging
		a widget onto an empty segment therefore moves it there."""
		if a is b or not isinstance(a, Leaf) or not isinstance(b, Leaf):
			return
		a.widget, b.widget = b.widget, a.widget
		a.lock_v, b.lock_v = b.lock_v, a.lock_v
		a.lock_h, b.lock_h = b.lock_h, a.lock_h
		a.fixed_w, b.fixed_w = b.fixed_w, a.fixed_w
		a.fixed_h, b.fixed_h = b.fixed_h, a.fixed_h
		a.aspect, b.aspect = b.aspect, a.aspect
		a.square, b.square = b.square, a.square
		self.save_slots()

	def act_load_template(self, name: str) -> None:
		self._loaded = True  # authored in memory; don't let a lazy load replace it
		self.slots[self.active_slot] = self.template(name)
		# The slot inherits the template's name; Blank clears it so the slot
		# reads "Empty Slot" again.
		self.slot_names[self.active_slot] = None if name == "Blank" else name
		self.save_slots()
		self._refresh_layout_menu()

	def act_rename_slot(self, name: str) -> None:
		name = name.strip()
		if not name:
			return
		self.slot_names[self.active_slot] = name
		self.save_slots()
		self._refresh_layout_menu()

	def act_new_slot(self) -> None:
		"""Append a fresh empty slot and switch to it."""
		self.ensure_slot()  # make sure lists are loaded before growing them
		self.slots.append(None)
		self.slot_names.append(None)
		self.slot_columns.append(None)
		self.active_slot = len(self.slots) - 1
		self.ensure_slot()
		self._activate_columns(self.active_slot)
		self.save_slots()
		self._refresh_layout_menu()
		self.gui.request_tracklist_redraw()
		self.gui.update_layout = True
		self.gui.request_frame()

	def act_delete_slot(self) -> None:
		"""Delete the active slot. Stays in custom mode, showing the next slot."""
		self.delete_slot(self.active_slot)

	def add_slot(self) -> None:
		"""Append a fresh empty slot without switching to it (the settings
		card's New Empty Slot; act_new_slot is the in-custom-mode variant
		that also switches)."""
		self.ensure_loaded()
		self.slots.append(None)
		self.slot_names.append(None)
		self.slot_columns.append(None)
		self.save_slots()
		self._refresh_layout_menu()

	def move_slot(self, i: int, delta: int) -> None:
		"""Swap slot ``i`` with a neighbour (reorders the layout menu).
		active_slot and the live-columns owner follow their slots."""
		self.ensure_loaded()
		j = i + delta
		if i == j or not (0 <= i < len(self.slots) and 0 <= j < len(self.slots)):
			return
		for lst in (self.slots, self.slot_names, self.slot_columns):
			lst[i], lst[j] = lst[j], lst[i]

		def follow(v: int) -> int:
			return j if v == i else i if v == j else v
		self.active_slot = follow(self.active_slot)
		if self._columns_owner is not None:
			self._columns_owner = follow(self._columns_owner)
		self.save_slots()
		self._refresh_layout_menu()

	def delete_slot(self, i: int) -> None:
		"""Delete slot ``i`` (its layout, name and columns config). The list
		never goes empty — deleting the last slot leaves one fresh empty slot.
		Works on any slot, in or out of custom mode."""
		self.ensure_loaded()
		if not 0 <= i < len(self.slots):
			return
		was_owner = self._columns_owner == i
		del self.slots[i]
		del self.slot_names[i]
		del self.slot_columns[i]
		if not self.slots:
			self.slots = [None]
			self.slot_names = [None]
			self.slot_columns = [None]
		if self._columns_owner is not None and self._columns_owner > i:
			self._columns_owner -= 1
		if self.active_slot > i:
			self.active_slot -= 1
		else:
			self.active_slot = min(self.active_slot, len(self.slots) - 1)
		if was_owner:
			# The deleted slot was the one being viewed: gui currently holds
			# its columns; discard them and adopt the new active slot's
			# directly (going through _activate_columns would stash the dead
			# config somewhere live).
			self.ensure_slot()
			cfg = self.slot_columns[self.active_slot]
			if cfg is None:
				cfg = self._copy_columns(self._preset_columns or self._capture_columns())
				self.slot_columns[self.active_slot] = cfg
			self._apply_columns(cfg)
			self._columns_owner = self.active_slot
		self.save_slots()
		self._refresh_layout_menu()
		self.gui.request_tracklist_redraw()
		self.gui.update_layout = True
		self.gui.request_frame()

	def _replace(self, root: Node, target: Node, new: Node) -> None:
		if target is root:
			self.slots[self.active_slot] = new
			return
		parent = find_parent(root, target)
		if parent is not None:
			parent.children[parent.children.index(target)] = new

	# -- input ---------------------------------------------------------------

	def handle_input(self) -> None:
		"""Process interaction early in the frame. Called only while custom_mode
		is set. In edit mode this drives the layout tools (and consumes events);
		in view mode it hands the real mouse to render() for the widgets.
		"""
		inp = self.tauon.inp
		gui = self.gui

		# Full-screen overlays (Milkdrop preset chooser, Dream Room) capture and
		# mute the pointer themselves later in the frame. Stand down entirely so we
		# don't neutralise the mouse first — otherwise they only ever see the muted
		# position and hover tracking (e.g. the preset chooser's highlight) breaks.
		if self.tauon.milk_choose.active or self.tauon.dream_room.active:
			return

		# While any menu or a message box (confirm dialog) is open, let those
		# systems own input. The main loop already routes clicks to active menus
		# before this runs (and menus need the real mouse position for hover), so
		# stand down entirely — no neutralising.
		from tauon.t_modules.t_main import Menu  # local import avoids cycle
		if Menu.active or gui.message_box or gui.rename_playlist_box:
			# Edit mode: right-clicking another widget while a menu is already
			# open re-targets the layout menu there. Without this we'd stand
			# down, and the right-click would fall through to the widget's own
			# renderer, which doesn't test for open menus (is_level_zero(False))
			# and would open its normal context menu instead.
			if gui.custom_edit and inp.right_click and not gui.message_box and not gui.rename_playlist_box:
				for m in Menu.instances:
					m.active = False
				Menu.active = False
				root = self.ensure_slot()
				layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], gui.scale)
				self.menu_target = leaf_at(root, inp.mouse_position[0], inp.mouse_position[1])
				if self.menu is not None:
					self.menu.activate(in_reference=None, position=[inp.mouse_position[0], inp.mouse_position[1]])
				self._consume(inp)
			return

		# Corner layout/edit button — clickable in BOTH view and edit mode; opens
		# the shared layout menu (view options + edit-mode toggle). Handled
		# before everything else.
		if inp.mouse_click and self._corner_button_hit(inp.mouse_position[0], inp.mouse_position[1]):
			# In edit mode the corner button immediately exits edit mode (back to
			# custom view) without showing the menu.
			if gui.custom_edit:
				self.gui.custom_edit = False
				self.widget_drag = None
				self._close_menu()
				self.gui.request_frame()
				self._consume(inp)
				return
			menu = getattr(self.tauon, "layout_menu", None)
			# Skip reopening when this same click just dismissed the menu's
			# popup window (the event loop closes it and lets the click through).
			if menu is not None and not menu.click_dismissed:
				x, y, w, h = self._corner_rect()
				menu.activate(position=[x, y + h])
			self._consume(inp)
			return

		if not gui.custom_edit:
			# Boundary resize on stacks marked resizable works with edit mode off.
			# While a drag is live (or starting), swallow the buttons/wheel before
			# the stash below so the widgets underneath don't also react — only the
			# position reaches them (for hover).
			dragging = False
			if self.drag is not None:
				if inp.mouse_down:
					self._drag_move(inp)
				else:
					self.drag = None
					self.save_slots()
				dragging = True
			elif inp.mouse_click and self._try_start_drag(inp, resizable_only=True):
				dragging = True
			if dragging:
				# mouse_down is a persistent held flag (SDL only flips it on
				# press/release events), so zeroing it here would also zero the
				# stash below, render()'s restore would carry False into the next
				# frame and the drag would end after one frame. Remember the real
				# state; render() re-applies it after the widgets have drawn.
				self._drag_held_down = inp.mouse_down
				inp.mouse_click = False
				inp.right_click = False
				inp.mouse_down = False
				inp.mouse_up = False
				inp.mouse_wheel = 0

			# Decide the resize cursor here, at frame start with the untouched
			# mouse — the same state the drag hit-test uses. _view_resize_hints
			# re-asserts it at end of render, but widget rendering in between can
			# perturb input state and make that late hit-test miss even though a
			# drag here would work; this early set is what the user actually sees.
			if self.drag is not None:
				gui.cursor_want = 12 if self.drag["axis"] == "v" else 1
			else:
				root = self.ensure_slot()
				layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], gui.scale)
				grab = BOUNDARY_GRAB * gui.scale
				hit = self._boundary_at(root, inp.mouse_position[0], inp.mouse_position[1], grab, resizable_only=True)
				if hit is not None:
					gui.cursor_want = 12 if hit[0] == "v" else 1

			# View mode: the widgets handle their own input during render(), which
			# runs later in the frame. Stash the real mouse and neutralise it so
			# the (hidden) standard UI underneath doesn't also react; render()
			# restores it for the widgets. Keyboard is left intact for global
			# shortcuts. Escape no longer exits custom mode (use the View Switcher).
			self._held_mouse = (inp.mouse_click, inp.right_click, inp.mouse_down,
				inp.mouse_up, inp.mouse_wheel, inp.mouse_position[0], inp.mouse_position[1])
			inp.mouse_click = False
			inp.right_click = False
			inp.mouse_down = False
			inp.mouse_up = False
			inp.mouse_wheel = 0
			inp.mouse_position[0] = -99999
			inp.mouse_position[1] = -99999
			return

		# --- edit mode ---
		# Escape exits edit mode (back to custom view), not custom mode.
		if inp.key_esc_press:
			self.gui.custom_edit = False
			self.widget_drag = None
			self._close_menu()
			self.gui.request_frame()
			self._consume(inp)
			return

		if self.drag is not None:
			# Active edge-drag resize.
			if inp.mouse_down:
				self._drag_move(inp)
			else:
				self.drag = None
				self.save_slots()
		elif self.widget_drag is not None:
			# Active widget drag — swap on release.
			if not inp.mouse_down:
				self._finish_widget_drag(inp)
			else:
				gui.request_frame()  # keep repainting the drag feedback
		elif inp.mouse_click:
			# Start an edge resize if on a boundary, else grab a widget to drag.
			if not self._try_start_drag(inp):
				self._try_start_widget_drag(inp)

		# Right-click opens the native context menu (not while dragging a widget).
		if inp.right_click and self.widget_drag is None:
			root = self.ensure_slot()
			layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], gui.scale)
			self.menu_target = leaf_at(root, inp.mouse_position[0], inp.mouse_position[1])
			if self.menu is not None:
				self.menu.activate(in_reference=None, position=[inp.mouse_position[0], inp.mouse_position[1]])

		self._consume(inp)

	def _try_start_widget_drag(self, inp) -> None:
		root = self.ensure_slot()
		layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], self.gui.scale)
		seg = leaf_at(root, inp.mouse_position[0], inp.mouse_position[1])
		if isinstance(seg, Leaf) and seg.widget is not None:
			self.widget_drag = seg
			self.gui.request_frame()

	def _finish_widget_drag(self, inp) -> None:
		root = self.ensure_slot()
		layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], self.gui.scale)
		target = leaf_at(root, inp.mouse_position[0], inp.mouse_position[1])
		if isinstance(target, Leaf) and target is not self.widget_drag:
			self.act_swap(self.widget_drag, target)
		self.widget_drag = None
		self.gui.request_frame()

	def _consume(self, inp) -> None:
		inp.mouse_click = False
		inp.right_click = False
		inp.mouse_up = False
		inp.key_esc_press = False
		inp.key_return_press = False

	# -- drag ----------------------------------------------------------------

	def _try_start_drag(self, inp, resizable_only: bool = False) -> bool:
		root = self.ensure_slot()
		layout(root, 0, 0, self.tauon.window_size[0], self.tauon.window_size[1], self.gui.scale)
		grab = BOUNDARY_GRAB * self.gui.scale
		hit = self._boundary_at(root, inp.mouse_position[0], inp.mouse_position[1], grab, resizable_only)
		if hit is not None:
			orient, stack, index = hit
			# A Square Max child has no stored size to edit (its length tracks
			# the cross extent), so a drag on its boundary would shift weights it
			# ignores and visibly do nothing. Dragging is an explicit manual
			# override: convert it to a plain axis lock at its current size and
			# resize that (Square Max can be re-enabled from the menu).
			for child in (stack.children[index], stack.children[index + 1]):
				if child.square and _fixed_on(child, stack.orient, self.gui.scale) is None:
					child.square = False
					if stack.orient == "v":
						child.lock_v = True
						child.fixed_h = max(1, round(child.slot_rect[3] / self.gui.scale))
					else:
						child.lock_h = True
						child.fixed_w = max(1, round(child.slot_rect[2] / self.gui.scale))
			self.drag = {"stack": stack, "index": index, "axis": stack.orient,
				"last": (inp.mouse_position[0], inp.mouse_position[1])}
			return True
		return False

	def _iter_boundaries(self, node: Node, grab: float):
		"""Yield (orient, grab_rect, stack, index) for every internal stack
		boundary, outermost first. Single source of truth for both the
		resize-cursor hit-test and the hover field registration, so the two stay
		byte-aligned — any mismatch makes the cursor stick (cursor set on a pixel
		that no field covers, so leaving it never triggers a repaint)."""
		if isinstance(node, Stack):
			for i, c in enumerate(node.children[:-1]):
				x, y, w, h = node.rect
				# Slot rect, not the gutter-inset content rect: the hot spot sits
				# on the true boundary between segments regardless of gutters.
				sx, sy, sw, sh = c.slot_rect
				if node.orient == "v":
					yield ("v", (x, sy + sh - grab, w, grab * 2), node, i)
				else:
					yield ("h", (sx + sw - grab, y, grab * 2, h), node, i)
			for c in node.children:
				yield from self._iter_boundaries(c, grab)

	def _boundary_at(self, node: Node, mx: float, my: float, grab: float,
			resizable_only: bool = False):
		"""First boundary under the point. With ``resizable_only`` only stacks
		flagged resizable count (the view-mode path), so a non-resizable outer
		boundary can't shadow a resizable nested one."""
		for orient, rect, stack, index in self._iter_boundaries(node, grab):
			if resizable_only and not stack.resizable:
				continue
			rx, ry, rw, rh = rect
			if rx <= mx < rx + rw and ry <= my < ry + rh:
				return (orient, stack, index)
		return None

	def _drag_move(self, inp) -> None:
		d = self.drag
		stack: Stack = d["stack"]
		i = d["index"]
		axis = d["axis"]
		lx, ly = d["last"]
		mx, my = inp.mouse_position[0], inp.mouse_position[1]
		delta = (my - ly) if axis == "v" else (mx - lx)
		d["last"] = (mx, my)
		if delta == 0:
			return
		a = stack.children[i]
		b = stack.children[i + 1]
		a_locked = a.lock_v if axis == "v" else a.lock_h
		b_locked = b.lock_v if axis == "v" else b.lock_h
		scale = self.gui.scale
		min_px = 24 * scale

		def px(n: Node) -> float:
			# Slot lengths, not gutter-inset content lengths: weights split slot
			# space, so using content sizes here overshoots by the gutter total
			# and lets the min/max clamp invert (total - min_px < min_px) into a
			# negative weight — the boundary then jumps the opposite way.
			return n.slot_rect[3] if axis == "v" else n.slot_rect[2]

		if a_locked:
			# Covers both-locked too: the boundary follows the mouse by editing
			# the leading child's px; the trailing child keeps its px and slides.
			cur = (a.fixed_h if axis == "v" else a.fixed_w) * scale
			newpx = max(min_px, cur + delta)
			if axis == "v":
				a.fixed_h = round(newpx / scale)
			else:
				a.fixed_w = round(newpx / scale)
		elif b_locked:
			cur = (b.fixed_h if axis == "v" else b.fixed_w) * scale
			newpx = max(min_px, cur - delta)
			if axis == "v":
				b.fixed_h = round(newpx / scale)
			else:
				b.fixed_w = round(newpx / scale)
		else:
			pa, pb = px(a), px(b)
			total_px = pa + pb
			total_w = a.weight + b.weight
			new_pa = min(max(min_px, pa + delta), total_px - min_px)
			a.weight = total_w * (new_pa / total_px)
			b.weight = total_w - a.weight
		self.gui.request_frame()

	# -- context menu (native Menu system) ----------------------------------
	#
	# The MenuItem objects are built once in build_custom_layout_menu() (t_main)
	# and wired to the callbacks below. They act on self.menu_target, which is
	# set when the menu is activated. Submenu items receive their value via the
	# MenuItem ``args`` field, so callbacks are (reference, value); main-item
	# callbacks take no arguments. show_test/disable_test predicates receive the
	# menu reference (unused — they read self.menu_target).

	def _close_menu(self) -> None:
		"""Close the native context menu if it is the active one."""
		if self.menu is not None and self.menu.active:
			self.menu.active = False
			from tauon.t_modules.t_main import Menu  # local import avoids cycle
			for m in Menu.instances:
				if m.active:
					break
			else:
				Menu.active = False

	# -- action callbacks --
	def _menu_add_stack(self, ref, payload) -> None:
		orient, count = payload
		if self.menu_target is not None:
			self.act_add_stack(self.menu_target, orient, count)

	def _menu_add_widget(self, ref, kind) -> None:
		if self.menu_target is not None:
			self.act_add_widget(self.menu_target, kind)

	def _menu_remove_widget(self) -> None:
		if self.menu_target is not None:
			self.act_remove_widget(self.menu_target)

	def _menu_remove_stack(self) -> None:
		if self.menu_target is not None:
			self.act_remove_stack(self.menu_target)

	def _menu_lock_v(self) -> None:
		if self.menu_target is not None:
			self.act_set_lock(self.menu_target, "v")

	def _menu_lock_h(self) -> None:
		if self.menu_target is not None:
			self.act_set_lock(self.menu_target, "h")

	def _menu_lock_aspect(self) -> None:
		if self.menu_target is not None:
			self.act_set_lock(self.menu_target, "a")

	def _menu_square_max(self) -> None:
		if self.menu_target is not None:
			self.act_toggle_square(self.menu_target)

	def _menu_stack_resizable(self) -> None:
		stack = self._resizable_stack_node()
		if stack is not None:
			self.act_toggle_stack_resizable(stack)

	def _menu_border(self) -> None:
		if self.menu_target is not None:
			self.act_toggle_border(self.menu_target)

	# Gutter / padding incrementor rows (see Menu.add_incrementor). The getters
	# return the current value to display; the +/- steppers adjust by 1px, clamped.
	def _menu_gutter_value(self, ref=None) -> int:
		return self.menu_target.gutter if self.menu_target is not None else 0

	def _menu_gutter_minus(self, ref=None) -> None:
		if self.menu_target is not None:
			self.act_set_gutter(self.menu_target, max(0, self.menu_target.gutter - 1))

	def _menu_gutter_plus(self, ref=None) -> None:
		if self.menu_target is not None:
			self.act_set_gutter(self.menu_target, min(CL_INSET_MAX, self.menu_target.gutter + 1))

	def _menu_padding_value(self, ref=None) -> int:
		return self.menu_target.padding if self.menu_target is not None else 0

	def _menu_padding_minus(self, ref=None) -> None:
		if self.menu_target is not None:
			self.act_set_padding(self.menu_target, max(0, self.menu_target.padding - 1))

	def _menu_padding_plus(self, ref=None) -> None:
		if self.menu_target is not None:
			self.act_set_padding(self.menu_target, min(CL_INSET_MAX, self.menu_target.padding + 1))

	def _menu_template(self, ref, name) -> None:
		self.tauon.gui.message_box_confirm_callback = self._confirm_load_template
		self.tauon.gui.message_box_no_callback = None
		self.tauon.gui.message_box_confirm_reference = (name,)
		self.tauon.show_message(_t("Load '%s' template? Replaces this layout.") % name, mode="confirm")

	def _confirm_load_template(self, name) -> None:
		self.act_load_template(name)

	def _menu_rename(self, ref=None) -> None:
		"""Open the shared rename box (the playlist one) targeting this slot."""
		tauon = self.tauon
		gui = self.gui
		# Drop back to view mode: edit mode's input handling interferes with
		# the rename box's text entry, and the rename doesn't need it.
		gui.custom_edit = False
		gui.request_frame()
		box = tauon.rename_playlist_box
		box.edit_generator = False
		box.done_callback = self.act_rename_slot
		box.x = tauon.inp.mouse_position[0]
		box.y = tauon.inp.mouse_position[1]
		# Same on-screen clamping rename_playlist() applies (the box's render
		# clamps x itself).
		box.y = min(box.y, round(350 * gui.scale))
		if box.y < gui.panelY:
			box.y = gui.panelY + round(10 * gui.scale)
		tauon.rename_text_area.set_text(self.slot_title(self.active_slot))
		tauon.rename_text_area.highlight_all()
		gui.rename_playlist_box = True

	def _menu_new_slot(self, ref=None) -> None:
		self.act_new_slot()

	def _menu_delete_slot(self, ref=None) -> None:
		self.tauon.gui.message_box_confirm_callback = self._confirm_delete_slot
		self.tauon.gui.message_box_no_callback = None
		self.tauon.gui.message_box_confirm_reference = ()
		self.tauon.show_message(
			_t("Delete layout '%s'?") % self.slot_title(self.active_slot), mode="confirm")

	def _confirm_delete_slot(self) -> None:
		self.act_delete_slot()

	# -- test predicates (receive the menu reference; read self.menu_target) --
	def _t_has_widget(self, ref=None) -> bool:
		return isinstance(self.menu_target, Leaf) and self.menu_target.widget is not None

	def _resolved_lock_node(self, axis: str) -> Node | None:
		"""The node the Lock V/H menu items would act on for the current
		menu_target (see _lock_target)."""
		if self.menu_target is None:
			return None
		root = self.slots[self.active_slot]
		if root is None:
			return None
		return self._lock_target(root, self.menu_target, axis)

	def _t_locked_v(self, ref=None) -> bool:
		node = self._resolved_lock_node("v")
		return node is not None and node.lock_v

	def _t_unlocked_v(self, ref=None) -> bool:
		node = self._resolved_lock_node("v")
		return node is not None and not node.lock_v

	def _t_locked_h(self, ref=None) -> bool:
		node = self._resolved_lock_node("h")
		return node is not None and node.lock_h

	def _t_unlocked_h(self, ref=None) -> bool:
		node = self._resolved_lock_node("h")
		return node is not None and not node.lock_h

	def _t_aspect_on(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.aspect

	def _t_aspect_off(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.aspect

	def _t_square_on(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.square

	def _t_square_off(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.square

	def _resizable_stack_node(self) -> Stack | None:
		"""The stack the resizable toggle acts on: the right-clicked segment's
		immediate parent stack (same targeting as Remove Stack), or the segment
		itself when the click landed on a stack's background."""
		if self.menu_target is None:
			return None
		if isinstance(self.menu_target, Stack):
			return self.menu_target
		root = self.ensure_slot()
		return find_parent(root, self.menu_target)

	def _t_stack_resizable_on(self, ref=None) -> bool:
		stack = self._resizable_stack_node()
		return stack is not None and stack.resizable

	def _t_stack_resizable_off(self, ref=None) -> bool:
		stack = self._resizable_stack_node()
		return stack is not None and not stack.resizable

	def _t_border_on(self, ref=None) -> bool:
		return self.menu_target is not None and self.menu_target.border

	def _t_border_off(self, ref=None) -> bool:
		return self.menu_target is not None and not self.menu_target.border

	def top_panel_rect(self) -> tuple[float, float, float, float] | None:
		"""The active layout's Header Bar (top panel) widget content rect, or
		None when custom mode is off / no top panel is placed. Used by the main
		loop's window-menu right-click fallback, which needs the panel's real
		on-screen geometry (the widget itself renders reframed to a (0,0)
		origin).
		"""
		if not self.gui.custom_mode:
			return None
		root = self.slots[self.active_slot]
		if root is None:
			return None
		for lf in iter_leaves(root):
			if isinstance(lf, Leaf) and isinstance(lf.widget, TopPanelWidget):
				return content_rect(lf, self.gui.scale)
		return None

	def tracklist_rect(self) -> tuple[int, int, int, int] | None:
		"""The active layout's Tracklist widget segment rect as last drawn, or
		None when custom mode is off / no tracklist is placed / it hasn't drawn
		yet. Column sizing (Auto Resize, update_set) runs from menu callbacks
		outside the widget's draw, where gui.plw holds the preset width — this
		gives those the real segment geometry.
		"""
		if not self.gui.custom_mode:
			return None
		root = self.slots[self.active_slot]
		if root is None:
			return None
		for lf in iter_leaves(root):
			if isinstance(lf, Leaf) and isinstance(lf.widget, TracklistWidget):
				return lf.widget._last_rect
		return None

	def gallery_locate(self, playlist_no: int, highlight: bool = False, force: bool = False) -> bool:
		"""Locate an album in a custom-layout gallery widget (Gallery: Classic /
		Compact) the way the preset gallery's show-playing does: run
		tauon.goto_album with the widget's segment geometry applied — and, for
		the Compact grid, its derived art size / gaps / forced row length — so
		the shared scroll lands on the right row, optionally with the select
		animation. goto_album is otherwise gated behind prefs.album_mode, which
		is the preset gallery's flag and off in custom mode. Returns True when
		handled (a gallery widget is in the active layout and has been laid
		out); the caller then skips the preset album_mode path.
		"""
		gui = self.gui
		if not gui.custom_mode:
			return False
		root = self.slots[self.active_slot]
		if root is None:
			return False
		tauon = self.tauon
		handled = False
		result = None
		for lf in iter_leaves(root):
			if not (isinstance(lf, Leaf) and isinstance(lf.widget, GalleryWidget)):
				continue
			widget = lf.widget
			# The widget's drawable rect: gutter-inset content rect, then the
			# padding inset (same clamped math as _draw_leaf).
			cx, cy, cw, ch = content_rect(lf, gui.scale)
			pad = lf.padding * gui.scale
			cw -= min(pad, cw / 2) * 2
			ch -= min(pad, ch / 2) * 2
			if cw <= 0 or ch <= 0:
				continue  # no layout pass yet this session
			saved_win = (tauon.window_size[0], tauon.window_size[1])
			saved = (gui.rspw, gui.lsp, gui.album_v_slide_value,
				tauon.album_mode_art_size, gui.album_h_gap, gui.album_v_gap,
				gui.gallery_forced_row_len)
			# Mirror GalleryWidget.draw's reframing: the segment is the window.
			tauon.window_size[0] = round(cw)
			tauon.window_size[1] = round(ch)
			gui.rspw = round(cw)
			gui.lsp = False
			gui.album_v_slide_value = max(0, gui.album_v_slide_value - round(30 * gui.scale))
			grid = widget._grid_overrides(tauon, cw)
			# A Compact grid keeps its own scroll/row state: swap it in so
			# goto_album moves THIS widget's view — unless the locate came from
			# within this widget's own render (gallery click → show_current),
			# where its state is already live and the draw saves it back.
			own_scroll = grid is not None and widget is not GalleryWidget._rendering
			saved_scroll = (gui.album_scroll_px, gui.last_row)
			if grid is not None:
				art, h_gap, v_gap, n, margin = grid
				tauon.album_mode_art_size = art
				gui.album_h_gap = h_gap
				gui.album_v_gap = v_gap
				gui.gallery_forced_row_len = n
				gui.album_v_slide_value = margin
				if own_scroll:
					gui.album_scroll_px = widget.scroll_px
					gui.last_row = widget.last_row
			try:
				result = tauon.goto_album(playlist_no, force=force)
			finally:
				if own_scroll:
					widget.scroll_px = gui.album_scroll_px
					widget.last_row = gui.last_row
					gui.album_scroll_px, gui.last_row = saved_scroll
				tauon.window_size[0], tauon.window_size[1] = saved_win
				(gui.rspw, gui.lsp, gui.album_v_slide_value,
					tauon.album_mode_art_size, gui.album_h_gap, gui.album_v_gap,
					gui.gallery_forced_row_len) = saved
			handled = True
		if not handled:
			return False
		if highlight:
			gui.gallery_animate_highlight_on = result
			tauon.gallery_select_animate_timer.set()
		gui.request_frame()
		return True

	def kind_disabled(self, kind: str) -> bool:
		"""Disable-test for an Add-widget item: True if the (single-instance)
		widget already exists in the active layout."""
		spec = SPEC_BY_KIND.get(kind)
		if spec is None or not spec.single_instance:
			return False
		root = self.slots[self.active_slot]
		return root is not None and count_kind(root, kind) > 0

	# -- rendering -----------------------------------------------------------

	def render(self) -> None:
		tauon = self.tauon
		gui = self.gui
		ddt = self.ddt
		inp = tauon.inp
		ww, wh = tauon.window_size[0], tauon.window_size[1]

		# View mode: restore the real mouse that handle_input() stashed, so the
		# widgets receive it during their own render. Edit mode keeps widgets
		# inert (the edit tools use the real mouse directly).
		interactive = not gui.custom_edit
		if interactive and self._held_mouse is not None:
			mc, rc, md, mu, mw, mx, my = self._held_mouse
			inp.mouse_click, inp.right_click, inp.mouse_down, inp.mouse_up = mc, rc, md, mu
			inp.mouse_wheel = mw
			inp.mouse_position[0], inp.mouse_position[1] = mx, my
		self._held_mouse = None

		# Cover the standard layout rendered underneath. With the art
		# background active the panel colour carries alpha and would let the
		# standard UI ghost through, so lay down the opaque base + blurred
		# art again and let the translucent widget fills blend over that.
		if gui.have_art_bg:
			tauon.style_overlay.display(background=True)
		else:
			ddt.rect((0, 0, ww, wh), tauon.colours.playlist_panel_background)

		root = self.ensure_slot()
		# Make sure the active slot's columns config is applied. Covers a restart
		# straight into custom mode (state.p restores the flag without calling
		# enter()) and any path that changed active_slot without swapping columns.
		if self._columns_owner != self.active_slot:
			self._activate_columns(self.active_slot)
		layout(root, 0, 0, ww, wh, gui.scale)

		if gui.have_art_bg:
			self._draw_art_bg_veil(root, ww, wh)

		# The MilkDrop Box widget owns the (singleton) visualiser while it is in
		# the layout: gates the ArtBox / MetaBox milk paths off so both never
		# drive it at once. Set before drawing so it holds regardless of the
		# widgets' draw order within this frame.
		gui.milkdrop_in_widget = count_kind(root, "milkdrop") > 0

		# Same ownership idea for the Sticks visualiser, but the gui.vis mode
		# switch lives in update_layout_do(), so poke a layout update when the
		# widget appears/disappears.
		sticks = count_kind(root, "vis_sticks") > 0
		if sticks != gui.vis4_in_widget:
			gui.vis4_in_widget = sticks
			gui.update_layout = True
		spectro = count_kind(root, "vis_spectrogram") > 0
		if spectro != gui.spectrogram_in_widget:
			gui.spectrogram_in_widget = spectro
			gui.update_layout = True

		for leaf in iter_leaves(root):
			if isinstance(leaf, Leaf):
				self._draw_leaf(leaf, interactive)

		# Widgets receive the deferred mouse-up event above so a later widget can
		# accept a track drop. Once every widget has had that chance, end the drag
		# just as the standard TopPanel path does.
		if interactive and inp.mouse_up:
			inp.quick_drag = False

		# Window-controls fallback when nothing provides them.
		if not self._provides_window_controls(root):
			self._draw_window_controls_fallback()

		if gui.custom_edit:
			self._draw_edit_overlay(root)
		else:
			self._view_resize_hints(root)
			if self.drag is not None:
				# Re-apply the real held-button state a view-mode boundary drag
				# swallowed from the widgets, so next frame's handle_input still
				# sees the button down and the drag continues.
				inp.mouse_down = self._drag_held_down

		# Corner edit-toggle button, on top, in both view and edit mode.
		self._draw_corner_edit_button()

	def _view_resize_hints(self, root: Node) -> None:
		"""View-mode counterpart of the edit overlay's boundary handling, for
		stacks marked resizable: register their boundary hot spots as hover
		fields (so crossing them repaints) and show the resize cursor."""
		gui = self.gui
		inp = self.tauon.inp
		grab = BOUNDARY_GRAB * gui.scale
		found = False
		for _orient, brect, stack, _idx in self._iter_boundaries(root, grab):
			if stack.resizable:
				self.tauon.fields.add(brect)
				found = True
		if not found:
			return
		from tauon.t_modules.t_main import Menu  # local import avoids cycle
		if Menu.active or gui.message_box or gui.rename_playlist_box:
			return
		if self.drag is not None:
			# Keep the cursor while dragging even when the pointer outruns the
			# hot spot.
			gui.cursor_want = 12 if self.drag["axis"] == "v" else 1
			return
		hit = self._boundary_at(root, inp.mouse_position[0], inp.mouse_position[1], grab, resizable_only=True)
		if hit is not None:
			gui.cursor_want = 12 if hit[0] == "v" else 1

	# -- corner edit-toggle button ------------------------------------------

	def _corner_rect(self) -> tuple[int, int, int, int]:
		"""Top-left edit-toggle rect, aligned to where the standard corner panel
		button sits (clearing the window controls)."""
		gui = self.gui
		tauon = self.tauon
		scale = gui.scale
		wwx = 0
		if tauon.prefs.left_window_control and not gui.compact_bar:
			if gui.macstyle:
				wwx = 24
				if tauon.draw_min_button:
					wwx += 20
				if tauon.draw_max_button:
					wwx += 20
			else:
				wwx = 26
				if tauon.draw_min_button:
					wwx += 35
				if tauon.draw_max_button:
					wwx += 33
			wwx = round(wwx * scale)
		yy = gui.panelY - gui.panelY2
		return (round(wwx + 9 * scale), round(yy + 3 * scale), round(34 * scale), round(25 * scale))

	def _corner_button_hit(self, mx: float, my: float) -> bool:
		if not self.gui.custom_mode:
			return False
		x, y, w, h = self._corner_rect()
		return x <= mx < x + w and y <= my < y + h

	def _draw_corner_edit_button(self) -> None:
		gui = self.gui
		ddt = self.ddt
		colours = self.tauon.colours
		x, y, w, h = self._corner_rect()
		# Match the standard corner panel-switcher button it replaces: the same
		# dimmed corner_button colour, corner_button_active while edit mode is
		# on or the layout menu is open, and no background or hover treatment.
		menu = getattr(self.tauon, "layout_menu", None)
		active = gui.custom_edit or (menu is not None and menu.active)
		col = colours.corner_button_active if active else colours.corner_button
		# Same 3-panel layout glyph as the View Switcher icon, just smaller.
		gw = round(18 * gui.scale)
		gh = round(13 * gui.scale)
		gx = x + round((w - gw) / 2)
		gy = y + round((h - gh) / 2)
		draw_layout_glyph(ddt, gui.scale, gx, gy, gw, gh, col)

	def _provides_window_controls(self, root: Node) -> bool:
		return any(isinstance(l, Leaf) and l.widget is not None and l.widget.draws_window_controls
			for l in iter_leaves(root))

	def _leaf_paint_rect(self, leaf: Leaf) -> tuple[float, float, float, float] | None:
		"""The rect the leaf's widget actually paints: the content rect snapped
		to whole pixels, inset by padding, shrunk to a centred square for aspect
		leaves. None when nothing paints (empty segment, or below the widget's
		minimum size — _draw_leaf fills those itself). Shared between _draw_leaf
		and the art-background veil so its holes can't drift from the widgets."""
		widget = leaf.widget
		if widget is None:
			return None
		gui = self.gui
		cx, cy, cw, ch = content_rect(leaf, gui.scale)
		# Snap to whole pixels up front so the border (drawn by _draw_leaf at
		# these exact coords) and the widget's own draw rect land on the same
		# edges. Widgets like the Art Box round their rect independently (and
		# blit the visualiser at those rounded coords); with a fractional cx/cy
		# that rounding pushed the art/visualiser a pixel past the float border
		# — flush at padding 0, but a 1px overhang here, a 1px gap once padded.
		cx, cy, cw, ch = round(cx), round(cy), round(cw), round(ch)
		# Padding: inset the widget's drawable rect inside the border (which is
		# drawn at cx/cy/cw/ch). Clamped so it can never invert on tiny segments.
		pad = leaf.padding * gui.scale
		px = min(pad, cw / 2)
		py = min(pad, ch / 2)
		dx, dy, dw, dh = cx + px, cy + py, cw - px * 2, ch - py * 2
		if dw < widget.min_w * gui.scale or dh < widget.min_h * gui.scale:
			return None
		if leaf.aspect:
			# Keep a square content region (Art Box-style), centred.
			side = min(dw, dh)
			dx = cx + (cw - side) / 2
			dy = cy + (ch - side) / 2
			dw = dh = side
		return dx, dy, dw, dh

	def _draw_leaf(self, leaf: Leaf, interactive: bool) -> None:
		tauon = self.tauon
		gui = self.gui
		ddt = self.ddt
		cx, cy, cw, ch = content_rect(leaf, gui.scale)
		cx, cy, cw, ch = round(cx), round(cy), round(cw), round(ch)
		widget = leaf.widget

		if widget is None:
			return  # empty segment: just background

		widget.leaf_border = leaf.border
		paint = self._leaf_paint_rect(leaf)
		if paint is None:
			ddt.rect((cx, cy, cw, ch), ColourRGBA(40, 20, 20, 255))
			ddt.text_background_colour = ColourRGBA(40, 20, 20, 255)
			ddt.text((round(cx + cw / 2), round(cy + ch / 2) - 8 * gui.scale, 2),
				"Size too small", ColourRGBA(200, 120, 120, 255), 211)
		else:
			dx, dy, dw, dh = paint
			if not widget.offscreen:
				widget.draw(tauon, dx, dy, dw, dh)
			else:
				self._draw_offscreen(widget, dx, dy, dw, dh, interactive)

		if leaf.border:
			b = max(1, round(1 * gui.scale))
			col = ColourRGBA(60, 60, 68, 255)
			ddt.rect((cx, cy, cw, b), col)
			ddt.rect((cx, cy + ch - b, cw, b), col)
			ddt.rect((cx, cy, b, ch), col)
			ddt.rect((cx + cw - b, cy, b, ch), col)

	def _draw_offscreen(self, widget: Widget, x: float, y: float, w: float, h: float,
			interactive: bool) -> None:
		"""Render an offscreen widget into the scratch texture at a (0, 0) origin,
		then blit to (x, y). The widget draws — and, when interactive, handles
		input — in a reframed coordinate space: window width narrowed to the
		segment, mouse translated to the segment-local origin, and a fields offset
		so its hover regions are registered at real screen coordinates.
		"""
		tauon = self.tauon
		gui = self.gui
		inp = tauon.inp
		renderer = self.renderer
		scratch = self._get_scratch()
		iw, ih = max(1, round(w)), max(1, round(h))
		ox, oy = round(x), round(y)

		saved_w = tauon.window_size[0]
		saved_h = tauon.window_size[1]
		saved_mouse = (inp.mouse_position[0], inp.mouse_position[1])
		# The whole family of stored input positions must move into the local
		# space together — widget code compares them against local geometry
		# (e.g. TopPanel tests mouse_up_position against tab rects, PlaylistBox
		# runs click-vs-drag proximity tests on drag_source_position). Leaving
		# any of them in screen space makes those tests miss (or hit the wrong
		# tab) whenever the widget sits away from the window origin — clicking
		# a Header Bar tab could enter tab-drag mode instead of just switching.
		saved_up = (inp.mouse_up_position[0], inp.mouse_up_position[1])
		saved_click = (inp.click_location[0], inp.click_location[1])
		saved_last_click = (inp.last_click_location[0], inp.last_click_location[1])
		saved_drag_source = tuple(gui.drag_source_position)
		saved_drag_source_persist = tuple(gui.drag_source_position_persist)
		saved_view = inp.view_offset
		# Narrow the window to the segment so the widget lays out within it as if
		# it were the whole window. This also lets bottom/right-anchored widgets
		# (e.g. the Playback panel at window_size[1] - panelBY) land at the scratch
		# origin so the (0,0,iw,ih) blit captures them.
		tauon.window_size[0] = iw
		tauon.window_size[1] = ih
		# Establish the view transform (screen = local + (ox, oy)). Fields,
		# Menu.activate() and any widget code that calls inp.to_screen/to_local
		# now convert correctly between this widget's local space and the screen.
		inp.view_offset = (ox, oy)
		local_click = local_drag_source = local_drag_source_persist = None
		if interactive:
			inp.mouse_position[0], inp.mouse_position[1] = inp.to_local(*saved_mouse)
			inp.mouse_up_position[0], inp.mouse_up_position[1] = inp.to_local(*saved_up)
			local_click = inp.to_local(*saved_click)
			inp.click_location[0], inp.click_location[1] = local_click
			inp.last_click_location[0], inp.last_click_location[1] = inp.to_local(*saved_last_click)
			local_drag_source = inp.to_local(*saved_drag_source)
			local_drag_source_persist = inp.to_local(*saved_drag_source_persist)
			gui.drag_source_position = local_drag_source
			gui.drag_source_position_persist = local_drag_source_persist
		else:
			inp.mouse_position[0] = -99999
			inp.mouse_position[1] = -99999

		prev = sdl3.SDL_GetRenderTarget(renderer)
		sdl3.SDL_SetRenderTarget(renderer, scratch)
		sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		sdl3.SDL_RenderClear(renderer)
		try:
			widget.draw(tauon, 0, 0, iw, ih)
		finally:
			sdl3.SDL_SetRenderTarget(renderer, prev)
			tauon.window_size[0] = saved_w
			tauon.window_size[1] = saved_h
			inp.view_offset = saved_view
			# Restore the mouse position (but not the click flags — a widget that
			# consumed the click should keep it consumed for later overlays).
			inp.mouse_position[0], inp.mouse_position[1] = saved_mouse
			if interactive:
				# A value the widget rewrote during the render is a local-space
				# point (set_drag_source copies click_location; the gallery
				# resets click_location) — map it back to screen. Untouched
				# values just get their saved screen coordinates back.
				def unmap(cur: tuple, local: tuple, saved: tuple) -> tuple:
					if tuple(cur) != tuple(local):
						return (cur[0] + ox, cur[1] + oy)
					return saved
				gui.drag_source_position = unmap(
					gui.drag_source_position, local_drag_source, saved_drag_source)
				gui.drag_source_position_persist = unmap(
					gui.drag_source_position_persist, local_drag_source_persist,
					saved_drag_source_persist)
				inp.click_location[0], inp.click_location[1] = unmap(
					(inp.click_location[0], inp.click_location[1]), local_click, saved_click)
				inp.mouse_up_position[0], inp.mouse_up_position[1] = saved_up
				inp.last_click_location[0], inp.last_click_location[1] = saved_last_click

		src = sdl3.SDL_FRect(0, 0, iw, ih)
		dst = sdl3.SDL_FRect(ox, oy, iw, ih)
		sdl3.SDL_RenderTexture(renderer, scratch, src, dst)

	def _draw_art_bg_veil(self, root: Node, ww: int, wh: int) -> None:
		"""Dim the art background between widgets. Widgets dim their own rects
		with translucent panel fills, but the gutters, border gaps and empty
		segments have no fill and would show the art at full brightness. Fill
		the scratch texture with the panel colour, punch zero-alpha holes at
		each widget's painted rect, and composite over the art — one continuous
		veil, so the gaps match widget interiors with no bright seams.

		Runs after layout() (the holes need the leaf rects) and before the
		leaves draw, so the offscreen widgets are free to reuse the scratch
		texture afterwards."""
		renderer = self.renderer
		veil = self._get_scratch()
		sdl3.SDL_SetRenderTarget(renderer, veil)
		# Blend NONE writes store the exact straight-alpha colour (and zeros in
		# the holes) for the texture's BLENDMODE_BLEND composite below
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_NONE)
		colour = self.tauon.colours.playlist_panel_background
		sdl3.SDL_SetRenderDrawColor(renderer, colour.r, colour.g, colour.b, colour.a)
		area = sdl3.SDL_FRect(0, 0, ww, wh)
		sdl3.SDL_RenderFillRect(renderer, area)
		sdl3.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 0)
		for leaf in iter_leaves(root):
			if not isinstance(leaf, Leaf):
				continue
			paint = self._leaf_paint_rect(leaf)
			if paint is None:
				continue
			sdl3.SDL_RenderFillRect(renderer, sdl3.SDL_FRect(paint[0], paint[1], paint[2], paint[3]))
		sdl3.SDL_SetRenderDrawBlendMode(renderer, sdl3.SDL_BLENDMODE_BLEND)
		sdl3.SDL_SetRenderTarget(renderer, self.gui.main_texture)
		sdl3.SDL_RenderTexture(renderer, veil, area, area)

	def _get_scratch(self):
		"""Lazily create (and resize) the offscreen scratch texture, kept separate
		from gui.tracklist_texture (the Tracklist widget's cache)."""
		size = self.gui.max_window_tex
		if self._scratch is None or self._scratch_size != size:
			if self._scratch is not None:
				sdl3.SDL_DestroyTexture(self._scratch)
			self._scratch = sdl3.SDL_CreateTexture(
				self.renderer, sdl3.SDL_PIXELFORMAT_ARGB8888, sdl3.SDL_TEXTUREACCESS_TARGET, size, size)
			sdl3.SDL_SetTextureBlendMode(self._scratch, sdl3.SDL_BLENDMODE_BLEND)
			self._scratch_size = size
		return self._scratch

	def _draw_edit_overlay(self, root: Node) -> None:
		gui = self.gui
		ddt = self.ddt
		inp = self.tauon.inp
		ww, wh = self.tauon.window_size[0], self.tauon.window_size[1]
		ddt.rect((0, 0, ww, wh), ColourRGBA(170, 225, 90, 10))

		grab = BOUNDARY_GRAB * gui.scale
		# Register hover regions so the GUI repaints as the mouse moves across
		# segments and resize boundaries. Tauon only redraws when the set of
		# fields under the cursor changes (see fields.test() in the main loop),
		# so these must be added every render regardless of current hover state.
		for lf in iter_leaves(root):
			self.tauon.fields.add(tuple(lf.rect))
		for _orient, brect, _stack, _idx in self._iter_boundaries(root, grab):
			self.tauon.fields.add(brect)

		self._draw_widget_labels(root)

		menu_active = self.menu is not None and self.menu.active
		mx, my = inp.mouse_position[0], inp.mouse_position[1]

		if self.widget_drag is not None:
			# Drag-to-swap feedback: dim the source, outline the target slot, and
			# show the dragged widget's name by the cursor.
			gui.cursor_want = 3  # hand
			sx, sy, sw, sh = self.widget_drag.rect
			ddt.rect((sx, sy, sw, sh), ColourRGBA(170, 225, 90, 35))
			target = leaf_at(root, mx, my)
			if isinstance(target, Leaf) and target is not self.widget_drag:
				tx, ty, tw, th = target.rect
				b = round(2 * gui.scale)
				edge = ColourRGBA(120, 200, 255, 235)
				ddt.rect((tx, ty, tw, b), edge)
				ddt.rect((tx, ty + th - b, tw, b), edge)
				ddt.rect((tx, ty, b, th), edge)
				ddt.rect((tx + tw - b, ty, b, th), edge)
				ddt.rect((tx, ty, tw, th), ColourRGBA(120, 200, 255, 28))
			name = self.widget_drag.widget.name if self.widget_drag.widget else ""
			# Black backing rectangle behind the label, sized to the text (with a
			# little padding), and the text background colour set to match so the
			# glyph anti-aliasing blends cleanly against it.
			black = ColourRGBA(0, 0, 0, 255)
			tx = round(mx + 20 * gui.scale)
			ty = round(my - 20 * gui.scale)
			pad = round(4 * gui.scale)
			tw = ddt.get_text_w(name, 211)
			th = ddt.get_text_w(name, 211, height=True)
			ddt.rect((tx - pad, ty - pad, tw + pad * 2, th + pad * 2), black)
			ddt.text_background_colour = black
			ddt.text((tx, ty), name, ColourRGBA(235, 235, 235, 255), 211, bg=black)
			return

		# While the menu is open, keep the right-clicked segment highlighted;
		# otherwise track the segment under the cursor and show resize cursors.
		if menu_active:
			seg = self.menu_target
		else:
			if self.drag is not None:
				# Hold the resize cursor while a drag is live, even when the
				# pointer outruns the grab band between frames.
				gui.cursor_want = 12 if self.drag["axis"] == "v" else 1
				# A boundary drag is in progress: mark the whole draggable region
				# with the red line, not the green segment highlight.
				self._draw_boundary_line(self.drag["axis"], self.drag["stack"], self.drag["index"])
				return
			hit = self._boundary_at(root, mx, my, grab)
			if hit is not None:
				# 12 = custom NS-resize cursor (see dispatch in main loop); 1 =
				# EW-resize (cursor_shift). cursor_top_side (9) isn't an NS cursor
				# on macOS/Linux, so we use our own.
				gui.cursor_want = 12 if hit[0] == "v" else 1
				# Over a draggable boundary: show a solid red line spanning the
				# whole region that would resize, and suppress the green segment
				# highlight so the drag affordance reads unambiguously.
				self._draw_boundary_line(hit[0], hit[1], hit[2])
				return
			seg = leaf_at(root, mx, my)
		if seg is not None:
			# Yellow highlight on the hovered segment itself.
			x, y, w, h = seg.rect
			b = round(2 * gui.scale)
			edge = ColourRGBA(170, 225, 90, 220)
			ddt.rect((x, y, w, b), edge)
			ddt.rect((x, y + h - b, w, b), edge)
			ddt.rect((x, y, b, h), edge)
			ddt.rect((x + w - b, y, b, h), edge)
			ddt.rect((x, y, w, h), ColourRGBA(170, 225, 90, 18))

	def _draw_boundary_line(self, orient: str, stack: "Stack", index: int) -> None:
		"""Solid red line over a resize boundary's hit zone, spanning the full
		extent of the two segments that share it. Red is the green hover
		highlight colour (170, 225, 90) with its hue rotated to 0 — same
		saturation and value — so the drag affordance stays visually related to
		the segment highlight while clearly meaning "this edge drags"."""
		ddt = self.ddt
		scale = self.gui.scale
		child = stack.children[index]
		sx, sy, sw, sh = child.slot_rect
		x, y, w, h = stack.rect
		red = ColourRGBA(225, 90, 90, 255)
		thick = max(1, round(3 * scale))
		inset = round(5 * scale)  # shorten the line by 5px on each end
		if orient == "v":
			ly = round(sy + sh - thick / 2)
			ddt.rect((x + inset, ly, w - inset * 2, thick), red)
		else:
			lx = round(sx + sw - thick / 2)
			ddt.rect((lx, y + inset, thick, h - inset * 2), red)

	def _draw_widget_labels(self, root: Node) -> None:
		"""Name tag in the top-left corner of every widget segment (edit mode),
		in the same style as the album-art hover metadata tags."""
		ddt = self.ddt
		scale = self.gui.scale
		pad = round(6 * scale)
		tag_h = round(18 * scale)
		for lf in iter_leaves(root):
			if lf.widget is None or not lf.widget.edit_label:
				continue
			x, y, w, h = lf.rect
			if w < 50 * scale or h < tag_h + pad * 2:
				continue
			name = lf.widget.name
			tag_w = min(ddt.get_text_w(name, 12) + round(12 * scale), round(w) - pad * 2)
			xx = round(x) + pad
			yy = round(y) + pad
			ddt.rect_a((xx, yy), (tag_w, tag_h), ColourRGBA(8, 8, 8, 255))
			ddt.text((xx + round(6 * scale), yy), name, ColourRGBA(200, 200, 200, 255), 12,
				bg=ColourRGBA(30, 30, 30, 255), max_w=tag_w - round(10 * scale))

	# -- window controls fallback -------------------------------------------

	def _draw_window_controls_fallback(self) -> None:
		"""Minimal min/maximize/close drawn top-right, shown on hover — so a
		layout without a Top Panel is still controllable.
		"""
		gui = self.gui
		ddt = self.ddt
		inp = self.tauon.inp
		ww = self.tauon.window_size[0]
		bw = round(46 * gui.scale)
		bh = round(28 * gui.scale)
		zone = (ww - bw * 3, 0, bw * 3, bh)
		# Register the hover zone every frame so moving into it triggers a redraw
		# (and the controls appear) — same fields requirement as everything else.
		self.tauon.fields.add(zone)
		hovering = self.tauon.coll(zone)
		if not hovering:
			return
		labels = [("—", self._win_minimize), ("□", self._win_maximize), ("✕", self._win_close)]
		for i, (label, cb) in enumerate(labels):
			bx = ww - bw * (3 - i)
			rect = (bx, 0, bw, bh)
			self.tauon.fields.add(rect)
			over = self.tauon.coll(rect)
			ddt.rect(rect, ColourRGBA(70, 70, 78, 200) if over else ColourRGBA(40, 40, 46, 160))
			ddt.text_background_colour = ColourRGBA(70, 70, 78, 200) if over else ColourRGBA(40, 40, 46, 160)
			ddt.text((bx + round(bw / 2), round(bh / 2) - 8 * gui.scale, 2), label, ColourRGBA(230, 230, 230, 255), 212)
			if over and inp.mouse_click:
				inp.mouse_click = False
				cb()

	def _win_minimize(self) -> None:
		try:
			sdl3.SDL_MinimizeWindow(self.tauon.t_window)
		except Exception:
			logging.exception("minimize failed")

	def _win_maximize(self) -> None:
		try:
			flags = sdl3.SDL_GetWindowFlags(self.tauon.t_window)
			if flags & sdl3.SDL_WINDOW_MAXIMIZED:
				sdl3.SDL_RestoreWindow(self.tauon.t_window)
			else:
				sdl3.SDL_MaximizeWindow(self.tauon.t_window)
		except Exception:
			logging.exception("maximize failed")

	def _win_close(self) -> None:
		self.tauon.exit("Custom layout close button")
