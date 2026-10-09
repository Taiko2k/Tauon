"""Compact background activity display for the header bar."""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import math
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sdl3

from tauon.t_modules.t_extra import ColourRGBA, alpha_blend, alpha_mod
from tauon.t_modules.t_menu_disc import bake, smoothstep, texture_from_pixels

if TYPE_CHECKING:
	from collections.abc import Callable

	from tauon.t_modules.t_main import Tauon


@dataclass
class Activity:
	key: str
	title: str
	colour: ColourRGBA
	detail: str = ""
	progress: float | None = None
	cancel: bool = False
	busy: bool = True
	album_progress: float | None = None
	album_active: float = 0
	album_count: str = ""
	folder_progress: float | None = None
	folder_count: str = ""
	overall_count: str = ""


SPINNER_PX = 14
SPINNER_IN = 0.72  # inner radius of the ring, as a fraction of its outer radius
SPINNER_RPS = 1.1  # turns per second


def shade_spinner(x: float, y: float) -> tuple[float, float, float, float]:
	"""A comet ring: a faint track with a bright, round-capped head at the top
	and a tail fading back anticlockwise, so it leads when turned clockwise."""
	r = math.hypot(x, y)
	mid, half = (1 + SPINNER_IN) / 2, (1 - SPINNER_IN) / 2
	cap = math.hypot(x, y + mid) <= half
	if not (SPINNER_IN <= r <= 1 or cap):
		return (0, 0, 0, 0.0)
	# 0 just clockwise of the top, rising to 1 at the head
	t = ((math.atan2(y, x) + math.pi / 2) / math.tau) % 1
	a = 1.0 if cap else 0.16 + 0.84 * smoothstep(0.25, 1.0, t) ** 1.6
	return (255, 255, 255, a)


def fraction(done: float, total: float) -> float | None:
	return min(1.0, max(0.0, done / total)) if total > 0 else None


class Countdown:
	"""Progress through a queue that is drained from the front: remembers the
	largest size seen since the queue was last empty, so the work done is
	peak - remaining. Fed every snapshot, even while its row is hidden."""

	def __init__(self) -> None:
		self.peak = 0

	def progress(self, remaining: int) -> float | None:
		if remaining <= 0:
			self.peak = 0
			return None
		self.peak = max(self.peak, remaining)
		return fraction(self.peak - remaining, self.peak)


scan_countdown = Countdown()
rescan_countdown = Countdown()


def collect_activities(tauon: Tauon) -> list[Activity]:
	"""Take a fresh snapshot; independent operations must not mask one another."""
	gui, pctl = tauon.gui, tauon.pctl
	green = ColourRGBA(100, 200, 100, 255)
	amber = ColourRGBA(245, 170, 50, 255)
	purple = ColourRGBA(173, 119, 219, 255)
	rows = []
	# These older operations share counters. Don't attribute another job's count.
	count_owners = sum(bool(active) for active in (
		pctl.loading_in_progress, tauon.cm_clean_db, tauon.plex.scanning,
		tauon.subsonic.scanning, tauon.jellyfin.scanning,
	))
	count = gui.to_got if count_owners == 1 and isinstance(gui.to_got, (int, float)) else None
	if pctl.loading_in_progress:
		title = _("Importing tracks")
		if gui.to_got in ("xspf", "xspfl"):
			title = _("Importing XSPF playlist")
		elif gui.to_got == "ex":
			title = _("Extracting Archive…")
		detail = _("{N} tracks imported").format(N=count) if count is not None else ""
		if gui.im_cancel:
			detail = _("Stopping import…")
		rows.append(Activity("import", title, amber, detail, cancel=not gui.im_cancel))
	# Imported tracks are tag scanned alongside the import; show that as its own
	# step once the import is done, with progress counted from the queue's peak
	scan_progress = scan_countdown.progress(len(tauon.after_scan))
	if tauon.after_scan and not pctl.loading_in_progress:
		rows.append(Activity("scan", _("Scanning Tags…"), green,
			_("{N} remaining").format(N=len(tauon.after_scan)), progress=scan_progress))
	if tauon.playlist_autoscan:
		rows.append(Activity("playlists", _("Auto-importing playlists…"), green))
	if tauon.move_in_progress:
		rows.append(Activity("copy", _("File copy in progress…"), tauon.colours.status_info_text))
	if tauon.cm_clean_db:
		progress = fraction(count, gui.to_get) if count is not None else None
		rows.append(Activity("database", _("Cleaning database"), green, progress=progress))
	rescan_progress = rescan_countdown.progress(len(tauon.to_scan))
	if tauon.to_scan:
		rows.append(Activity("rescan", _("Rescanning Tags…"), green,
			_("{N} remaining").format(N=len(tauon.to_scan)), progress=rescan_progress))
	for key, service, title, colour in (
		("plex", tauon.plex, _("Accessing PLEX library…"), ColourRGBA(229, 160, 13, 255)),
		("subsonic", tauon.subsonic, _("Accessing AIRSONIC library…"), ColourRGBA(58, 194, 224, 255)),
		("jellyfin", tauon.jellyfin, _("Accessing JELLYFIN library…"), ColourRGBA(90, 170, 240, 255)),
	):
		if service.scanning:
			detail = ""
			if count is not None and count > 0:
				detail = (_("{N} albums scanned") if key == "plex" else _("{N} tracks scanned")).format(N=count)
			rows.append(Activity(key, title, colour, detail))
	if tauon.chrome_mode:
		rows.append(Activity("chromecast", _("Chromecast Mode"), ColourRGBA(207, 94, 219, 255), busy=False))
	if gui.sync_progress:
		progress = fraction(gui.sync_folders_done, gui.sync_folders_total)
		folder = fraction(gui.sync_files_done, gui.sync_files_total)
		count = _("{done} / {total} files").format(done=gui.sync_files_done, total=gui.sync_files_total)
		if not gui.sync_files_total:
			count = _("Transcoding…") if gui.sync_transcode_folder else _("Preparing…")
		rows.append(Activity("sync", _("Syncing to device"), green, gui.sync_progress,
			progress=progress, cancel=not gui.stop_sync, folder_progress=folder, folder_count=count,
			overall_count=_("{done} / {total} folders").format(done=gui.sync_folders_done, total=gui.sync_folders_total)))
	if tauon.transcode_list:
		done = min(gui.transcoding_batch_done, gui.transcoding_batch_total)
		album = fraction(done, gui.transcoding_batch_total)
		active = fraction(gui.transcoding_batch_active, gui.transcoding_batch_total) or 0
		overall = fraction(gui.transcoding_overall_done + done, gui.transcoding_overall_total)
		title = _("Stopping transcode…") if gui.tc_cancel else _("Transcoding")
		remaining = len(tauon.transcode_list)
		detail = gui.sync_progress or (_("1 album remaining") if remaining == 1 else _("{N} albums remaining").format(N=remaining))
		if tauon.transcode_state:
			detail = tauon.transcode_state
		rows.append(Activity("transcode", title, purple, detail, overall, not gui.tc_cancel,
			album_progress=album, album_active=min(active, 1 - (album or 0)),
			album_count=_("{done} / {total} tracks").format(done=done, total=gui.transcoding_batch_total)))
	if tauon.lrclib_uploads:
		rows.append(Activity("lyrics", _("Uploading lyrics to LRCLIB…"), green))
	if tauon.lastfm.scanning_friends or tauon.lastfm.scanning_loves:
		rows.append(Activity("lastfm", _("Scanning: ") + tauon.lastfm.scanning_username, ColourRGBA(200, 150, 240, 255)))
	if tauon.lastfm.scanning_scrobbles:
		rows.append(Activity("scrobbles", _("Scanning Scrobbles…"), ColourRGBA(219, 88, 18, 255)))
	if gui.buffering:
		try:
			progress = fraction(float(gui.buffering_text.rstrip("%")), 100) if gui.buffering_text.endswith("%") else None
		except ValueError:
			progress = None
		rows.append(Activity("buffering", _("Buffering…"), ColourRGBA(18, 180, 180, 255), progress=progress))
	if tauon.lfm_scrobbler.queue and tauon.scrobble_warning_timer.get() < 260:
		rows.append(Activity("scrobble-error", _("Scrobbling"), ColourRGBA(250, 90, 90, 255),
			_("Network error. Will try again later."), busy=False))
	listeners = sum(timer.get() < 6 for timer in tuple(tauon.listen_alongers.values()))
	if listeners:
		rows.append(Activity("listeners", _("{N} listening along").format(N=listeners),
			ColourRGBA(40, 190, 235, 255), busy=False))
	return rows


class ActivityPopover:
	def __init__(self, tauon: Tauon, readable_colour: Callable) -> None:
		self.tauon = tauon
		self.readable_colour = readable_colour
		self.rows: list[Activity] = []
		self.open = False
		self.button_rect = (0, 0, 0, 0)
		self.panel_rect = (0, 0, 0, 0)
		self.cancel_rects: list[tuple[str, tuple[int, int, int, int]]] = []
		self.button_drawn = False
		self.spinner = None
		self.spinner_size = 0

	def refresh(self) -> None:
		self.rows = collect_activities(self.tauon)
		if not self.rows:
			self.close()
			self.button_rect = (0, 0, 0, 0)
			self.button_drawn = False

	def close(self) -> None:
		if self.open:
			self.tauon.gui.request_frame()
		self.open = False
		self.cancel_rects.clear()

	def cancel(self, key: str) -> None:
		tauon = self.tauon
		gui = tauon.gui
		if key == "import":
			gui.im_cancel = True
		elif key in ("sync", "transcode"):
			if key == "transcode" or gui.sync_transcode_folder:
				del tauon.transcode_list[1:]
				gui.tc_cancel = True
			if gui.sync_progress:
				gui.stop_sync = True
				gui.sync_progress = _("Aborting Sync")
		gui.request_frame()

	def consume_pointer(self) -> None:
		inp = self.tauon.inp
		inp.mouse_click = inp.d_mouse_click = inp.right_click = inp.middle_click = False
		inp.mouse_down = inp.right_down = inp.mouse_up = False
		inp.mouse_wheel = 0

	def handle_input(self, allowed: bool) -> None:
		"""Run before the playlist and custom-layout input consumers."""
		tauon = self.tauon
		inp = tauon.inp
		if not allowed or not tauon.is_level_zero(False):
			self.close()
			return
		if not self.open:
			return
		if inp.key_esc_press:
			self.close()
			inp.key_esc_press = False
			return
		if inp.mouse_click and tauon.coll(self.button_rect):
			self.close()
			self.consume_pointer()
			return
		if tauon.coll(self.panel_rect):
			if inp.mouse_click:
				live = {row.key for row in collect_activities(tauon) if row.cancel}
				for key, rect in self.cancel_rects:
					if key in live and tauon.coll(rect):
						self.cancel(key)
						break
			self.consume_pointer()
		elif inp.mouse_click or inp.right_click or inp.middle_click:
			self.close()
			self.consume_pointer()

	def animate(self) -> None:
		self.tauon.gui.delay_frame(self.tauon.frame_pace())

	def render_button(self, x: float, y: float, align_right: bool = False) -> int:
		"""Draw the activity button at x, or ending at x when align_right. Returns its width."""
		self.refresh()
		if not self.rows:
			return 0
		tauon = self.tauon
		gui, inp, ddt = tauon.gui, tauon.inp, tauon.ddt
		scale = gui.scale
		width = round((36 if len(self.rows) > 1 else 24) * scale)
		if align_right:
			x -= width
		rect = (round(x), round(y - 3 * scale), width, round(24 * scale))
		ox, oy = inp.view_offset
		self.button_rect = (rect[0] + ox, rect[1] + oy, rect[2], rect[3])
		self.button_drawn = True
		tauon.fields.add(rect)
		hover = tauon.coll(rect) and (self.open or tauon.is_level_zero())
		bg = tauon.colours.top_panel_background
		colour = self.readable_colour(self.rows[0].colour, bg, 3)
		if self.open or hover:
			ddt.rect(rect, alpha_blend(alpha_mod(colour, 24), bg))
		if hover and not self.open:
			tauon.tool_tip.test(rect[0] + ox, rect[1] + oy + rect[3] + 4 * scale, _("Activity"))
		if hover and inp.mouse_click:
			self.open = not self.open
			self.consume_pointer()
			gui.request_frame()
		self.draw_spinner(x + 12 * scale, y + 9 * scale, colour)
		if len(self.rows) > 1:
			ddt.text((x + 24 * scale, y + scale), str(len(self.rows)), colour, 311, bg=bg)
		self.animate()
		return width

	def draw_spinner(self, cx: float, cy: float, colour: ColourRGBA) -> None:
		"""The comet ring, baked once per size and turned on the GPU."""
		renderer = self.tauon.renderer
		size = round(SPINNER_PX * self.tauon.gui.scale)
		if size != self.spinner_size or not self.spinner:
			if self.spinner:
				sdl3.SDL_DestroyTexture(self.spinner)
			self.spinner = texture_from_pixels(renderer, bake(shade_spinner, size), size, size)
			self.spinner_size = size
		if not self.spinner:
			return
		sdl3.SDL_SetTextureColorMod(self.spinner, colour.r, colour.g, colour.b)
		sdl3.SDL_SetTextureAlphaMod(self.spinner, colour.a)
		angle = time.monotonic() * SPINNER_RPS * 360 % 360
		dst = sdl3.SDL_FRect(round(cx - size / 2), round(cy - size / 2), size, size)
		sdl3.SDL_RenderTextureRotated(renderer, self.spinner, None, dst, angle, None, sdl3.SDL_FLIP_NONE)

	def row_height(self, row: Activity) -> int:
		if row.key in ("transcode", "sync"):
			return 110
		return 30 + (16 if row.detail else 0) + (14 if row.busy else 0)

	def draw_bar(self, x: int, y: int, width: int, colour: ColourRGBA,
			*, progress: float | None, active: float = 0) -> None:
		tauon = self.tauon
		ddt = tauon.ddt
		height = max(1, round(8 * tauon.gui.scale))
		bg = alpha_mod(tauon.colours.menu_background, 255)
		track = alpha_blend(alpha_mod(tauon.colours.menu_text, 25), bg)
		ddt.rect((x, y, width, height), track)
		if progress is None:
			block = round(width * 0.25)
			offset = round((width - block) * (0.5 + 0.5 * math.sin(time.monotonic() * 2)))
			ddt.rect((x + offset, y, block, height), colour)
		else:
			done = round(width * min(1, max(0, progress)))
			doing = min(width - done, round(width * max(0, active)))
			ddt.rect((x, y, done, height), colour)
			if doing:
				ddt.rect((x + done, y, doing, height), alpha_blend(alpha_mod(colour, 105), track))

	def render(self) -> None:
		tauon = self.tauon
		if not self.button_drawn or not tauon.is_level_zero(False):
			self.close()
		if not self.open or not self.rows:
			return
		gui, ddt = tauon.gui, tauon.ddt
		scale = gui.scale
		pad = round(10 * scale)
		width = min(round(316 * scale), tauon.window_size[0] - 2 * pad)
		height = round((29 + sum(self.row_height(row) for row in self.rows)) * scale)
		x = max(pad, min(self.button_rect[0], tauon.window_size[0] - width - pad))
		y = self.button_rect[1] + self.button_rect[3] + round(3 * scale)
		y = max(pad, min(y, tauon.window_size[1] - height - pad))
		self.panel_rect = (x, y, width, height)
		tauon.fields.add(self.panel_rect)
		bg = alpha_mod(tauon.colours.menu_background, 255)
		text = self.readable_colour(tauon.colours.menu_text, bg)
		muted = alpha_blend(alpha_mod(text, 175), bg)
		border = alpha_blend(alpha_mod(text, 40), bg)
		ddt.bordered_rect(self.panel_rect, bg, border, max(1, round(scale)))
		ddt.text((x + pad, y + 7 * scale), _("Activity"), text, 212, bg=bg)
		ddt.text((x + width - pad, y + 8 * scale, 1),
			_("{N} active").format(N=len(self.rows)), muted, 311, bg=bg)
		y += round(29 * scale)
		self.cancel_rects.clear()
		bar_width = width - 2 * pad - round(22 * scale)
		for row in self.rows:
			ddt.rect((x, y, width, max(1, round(scale))), border)
			colour = self.readable_colour(row.colour, bg, 3)
			top = y + round(7 * scale)
			value = f"{round(row.progress * 100)}%" if row.progress is not None and row.key not in ("transcode", "sync") else ""
			value_w = ddt.get_text_w(value, 311) + pad if value else 0
			ddt.text((x + pad, top), row.title, text, 212, max_w=bar_width - value_w, bg=bg)
			if value:
				ddt.text((x + pad + bar_width, top, 1), value, muted, 311, bg=bg)
			if row.cancel:
				rect = (x + width - pad - round(16 * scale), top - round(3 * scale), round(20 * scale), round(20 * scale))
				self.cancel_rects.append((row.key, rect))
				tauon.fields.add(rect)
				ink = text if tauon.coll(rect) else muted
				cx, cy = rect[0] + 10 * scale, rect[1] + 10 * scale
				ddt.line(cx - 3 * scale, cy - 3 * scale, cx + 3 * scale, cy + 3 * scale, ink)
				ddt.line(cx + 3 * scale, cy - 3 * scale, cx - 3 * scale, cy + 3 * scale, ink)
			top += round(19 * scale)
			if row.detail:
				ddt.text((x + pad, top), row.detail, muted, 311, max_w=bar_width, bg=bg)
				top += round(16 * scale)
			if row.key in ("transcode", "sync"):
				label = _("Overall")
				if row.key == "sync":
					label = row.overall_count
				ddt.text((x + pad, top), label, muted, 311, bg=bg)
				if row.progress is not None:
					ddt.text((x + pad + bar_width, top, 1), f"{round(row.progress * 100)}%", muted, 311, bg=bg)
				top += round(17 * scale)
				self.draw_bar(x + pad, top, bar_width, colour, progress=row.progress)
				top += round(14 * scale)
				label = _("Current folder") if row.key == "sync" else _("Current album")
				count = row.folder_count if row.key == "sync" else row.album_count
				ddt.text((x + pad, top), label, muted, 311, bg=bg)
				ddt.text((x + pad + bar_width, top, 1), count, muted, 311, bg=bg)
				top += round(17 * scale)
				progress = row.folder_progress if row.key == "sync" else row.album_progress
				self.draw_bar(x + pad, top, bar_width, colour, progress=progress, active=row.album_active)
			elif row.busy:
				self.draw_bar(x + pad, top + round(scale), bar_width, colour, progress=row.progress)
			y += round(self.row_height(row) * scale)
