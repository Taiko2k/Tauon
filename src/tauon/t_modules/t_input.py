"""Low-level touch input tracking primitives."""

from __future__ import annotations

import ctypes
import logging
import math
import time
from ctypes import c_float, c_uint32, c_void_p, pointer
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Protocol

import sdl3

from tauon.t_modules.t_extra import Timer, coll_point
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_state import ColoursClass, GuiVar

if TYPE_CHECKING:
	from tauon.t_modules.t_draw import TDraw


class _TouchApp(Protocol):
	gui: GuiVar
	ddt: Any
	colours: ColoursClass


class _InputApp(Protocol):
	logical_size: tuple[int, int] | list[int]
	window_size: tuple[int, int] | list[int]
	inp: Any
	gui: GuiVar
	prefs: Prefs
	macos: bool
	coll: Callable[[object], bool]

	def __getattr__(self, name: str) -> Any: ...


SCROLL_PHYSICS_MIN_PIXELS = 10
TOUCH_LOGIC_TAP_VS_LONG_NS = 300 * 1000000
TOUCH_LOGIC_COOL_GESTURE_PIXELS_TO_SKIP_TRACK = 150

class TouchInputTracker:
	def __init__(self, tauon: _TouchApp) -> None:
		self.tauon:             _TouchApp = tauon
		self.gui: GuiVar              = tauon.gui
		self.ddt: TDraw               = tauon.ddt
		self.colours: ColoursClass    = tauon.colours

		self.is_down: bool = False
		self.start_position_px: tuple[int, int] = (0, 0)
		self.time_started_ns: int = 0
		self.duration_so_far_ns: int = 0
		self.is_scroll: bool = False
		self.is_rightclick: bool = False
		self.is_dragndrop: bool = False
		self.has_moved: bool = False
		self.is_gesture: bool = False
		self.was_gesture: bool = False
		self.x: int = 0
		self.y: int = 0

		self.rect_size: int = round(40*self.gui.scale)
		self.rect_distance: int = round(40*self.gui.scale)

	def reset(self) -> None:
		self.is_down: bool = False
		self.start_position_px: tuple[int, int] = (0, 0)
		self.time_started_ns: int = 0
		self.duration_so_far_ns: int = 0
		self.is_scroll: bool = False
		self.is_rightclick: bool = False
		self.is_dragndrop: bool = False
		self.has_moved: bool = False
		self.is_gesture: bool = False
		self.was_gesture: bool = False

	def draw_update(self) -> None:
		if not self.is_down or self.is_scroll or self.is_rightclick or self.is_dragndrop or self.is_gesture or self.was_gesture:
			return
		if TOUCH_LOGIC_TAP_VS_LONG_NS < self.duration_so_far_ns:
			self.is_rightclick = True
			return
		self.duration_so_far_ns = time.monotonic_ns() - self.time_started_ns
		if TOUCH_LOGIC_TAP_VS_LONG_NS/2 > self.duration_so_far_ns:
			self.gui.request_frame()
			return

		rect = [
			int(self.x-0.5*self.rect_size),
			int(self.y-self.rect_distance),
			self.rect_size,
			round(10*self.gui.scale)
		]
		self.ddt.rect( rect, self.colours.media_buttons_off)
		rect[2] *= (self.duration_so_far_ns/TOUCH_LOGIC_TAP_VS_LONG_NS)
		self.ddt.rect( rect, self.colours.media_buttons_active)
		self.gui.request_frame()
class GetSDLInput:
	def __init__(self, tauon: _InputApp) -> None:
		self.logical_size = tauon.logical_size
		self.window_size = tauon.window_size
		self.mouse_capture_want = False
		self.mouse_capture = False

	def mouse(self) -> tuple[int, int]:
		sdl3.SDL_PumpEvents()
		i_y = pointer(c_float(0))
		i_x = pointer(c_float(0))
		sdl3.SDL_GetMouseState(i_x, i_y)
		return (int(i_x.contents.value / self.logical_size[0] * self.window_size[0]),
			int(i_y.contents.value / self.logical_size[0] * self.window_size[0]))

	def test_capture_mouse(self) -> None:
		if not self.mouse_capture and self.mouse_capture_want:
			sdl3.SDL_CaptureMouse(True)
			self.mouse_capture = True
		elif self.mouse_capture and not self.mouse_capture_want:
			sdl3.SDL_CaptureMouse(False)
			self.mouse_capture = False
class XcursorImage(ctypes.Structure):
	_fields_ = [
			("version", c_uint32),
			("size", c_uint32),
			("width", c_uint32),
			("height", c_uint32),
			("xhot", c_uint32),
			("yhot", c_uint32),
			("delay", c_uint32),
			("pixels", c_void_p),
		]
@dataclass
class ScrollMotionState:
	velocity: float = 0.0
	last_velocity: float = 0.0
	pending: float = 0.0
	accumulator: float = 0.0
	precise_buffer: float = 0.0
	last_precise_input: float = 0.0
	touching: bool = False
	from_touch: bool = False
	wheel_streak: int = 0
	last_wheel_direction: float = 0.0
	last_wheel_time: float = 0.0
	last_update: float = field(default_factory=time.monotonic)
class SmoothScroll:
	def __init__(self, tauon: _InputApp) -> None:
		self.tauon = tauon
		self.inp = tauon.inp
		self.gui = tauon.gui
		self.coll = tauon.coll
		self.scroll_bins:    dict[str:list[float]] = {}
		self.scroll_timeouts:      dict[str:Timer] = {}
		self.physics_states: dict[str, ScrollMotionState] = {}
		self.scroll_debug_modes: dict[str, str] = {}
		self.scroll_debug_last_logs: dict[str, float] = {}
		self.timeout = 0.5
		self.start_location: tuple[int, int] = (0,0)

	def _pixel_scale(self) -> float:
		return max(self.gui.scale, 0.1)

	def _scaled_max_velocity(self) -> float:
		return SCROLL_PHYSICS_MAX_VELOCITY * self._pixel_scale()

	def _scaled_min_velocity(self) -> float:
		return SCROLL_PHYSICS_MIN_VELOCITY * self._pixel_scale()

	def enabled(self) -> bool:
		prefs = self.tauon.prefs
		return prefs.smooth_scroll_enable or prefs.macos

	def speed(self) -> float:
		return max(self.tauon.prefs.smooth_scroll_speed, 0.05)

	def precise_scroll_active(self) -> bool:
		return self.enabled() and self.inp.mouse_wheel_precise

	def _debug_enabled(self) -> bool:
		return logging.getLogger().isEnabledFor(logging.DEBUG)

	@staticmethod
	def _format_debug_value(value: object) -> str:
		if isinstance(value, float):
			return f"{value:.4f}"
		return str(value)

	def _log_scroll_detail(self, source: str, event: str, throttle: float = 0.0, **fields: object) -> None:
		if not self._debug_enabled():
			return
		now = time.monotonic()
		key = f"{source}:{event}"
		if throttle > 0 and now - self.scroll_debug_last_logs.get(key, 0.0) < throttle:
			return
		if throttle > 0:
			self.scroll_debug_last_logs[key] = now
		payload = " ".join(
			f"{name}={self._format_debug_value(value)}"
			for name, value in fields.items()
		)
		# if payload:
		# 	logging.debug("Smooth scroll %s source=%s %s", event, source, payload)
		# else:
		# 	logging.debug("Smooth scroll %s source=%s", event, source)

	def scroll(self, source: str, coeff: float = 1) -> int:
		"""Used for sections that require integer scroll values, e.g. pixels or lines.
		Coeff should be the number that the scroll would be multiplied by if the scroll input was an integer;
		Source keeps everything straight (the string's contents don't matter at all).
		"""
		state = self._state(source)
		effective_wheel = self.inp.mouse_wheel
		if effective_wheel != 0:
			effective_wheel *= self._wheel_boost(state, effective_wheel)

		# if smooth scrolling isn't necessary
		if effective_wheel % 1 == 0:
			return int(effective_wheel * coeff)
		try:
			self.scroll_bins[source]
		except KeyError: # create for first time
			self.scroll_bins[source] = []
			self.scroll_timeouts[source] = Timer()

		# tally up float inputs over time & only return when the final output can be integerized
		if self.scroll_timeouts[source].get() > self.timeout:
			self.scroll_bins[source] = []
		self.scroll_bins[source].append(effective_wheel)

		if sum(self.scroll_bins[source]) * coeff > 1 or sum(self.scroll_bins[source]) * coeff < -1:
			scroll_distance = int(sum(self.scroll_bins[source]) * coeff)
			self.scroll_bins[source] = [sum(self.scroll_bins[source]) % (1 / coeff)] # save the remainder
		else:
			scroll_distance = 0
		self.scroll_timeouts[source].set()

		return scroll_distance

	def get_scroll(self, scroll_source: str, scroll_area: tuple[int, int, int, int], coeff: float=1.0) -> float:
		touch_scroll = self.inp.touch_scroll_y != 0 and coll_point(self.start_location, scroll_area)
		use_smooth_scroll = (
			self.enabled()
			or touch_scroll
			or self.active(scroll_source)
		)
		if use_smooth_scroll:
			if self.coll(scroll_area) and self.inp.mouse_wheel:
				self.add_wheel_motion(scroll_source, -self.inp.mouse_wheel, coeff)
			if self.inp.touch_released and coll_point(self.start_location, scroll_area):
				self.release_touch(scroll_source)
			elif touch_scroll:
				self.apply_touch_drag(scroll_source, -self.inp.touch_scroll_y)
			return self.step_motion(scroll_source)
		elif self.coll(scroll_area):
			return -self.scroll(scroll_source, coeff)
		else:
			return 0.0

	def _state(self, source: str) -> ScrollMotionState:
		if source not in self.physics_states:
			self.physics_states[source] = ScrollMotionState()
		return self.physics_states[source]

	def _update_wheel_streak(self, state: ScrollMotionState, delta: float) -> tuple[float, float]:
		now = time.monotonic()
		dt = now - state.last_wheel_time if state.last_wheel_time else SCROLL_PHYSICS_REPEAT_WINDOW
		direction = 1.0 if delta > 0 else -1.0
		if (
			state.last_wheel_direction == direction
			and now - state.last_wheel_time <= SCROLL_PHYSICS_REPEAT_WINDOW
		):
			state.wheel_streak = min(state.wheel_streak + 1, 10)
		else:
			state.wheel_streak = 0
		state.last_wheel_direction = direction
		state.last_wheel_time = now
		streak = min(state.wheel_streak, 8)
		repeat_boost = 1.0 + streak * SCROLL_PHYSICS_REPEAT_ACCELERATION
		if streak > 1:
			repeat_boost += (streak - 1) ** 2 * SCROLL_PHYSICS_REPEAT_CURVE
		repeat_boost += max(abs(delta) - 1.0, 0.0) * SCROLL_PHYSICS_WHEEL_MAGNITUDE_ACCELERATION
		return repeat_boost, dt

	def _wheel_boost(self, state: ScrollMotionState, delta: float) -> float:
		repeat_boost, dt = self._update_wheel_streak(state, delta)
		return repeat_boost

	def reset_motion(self, source: str) -> None:
		state = self.physics_states.get(source)
		if state is None:
			return
		state.velocity = 0.0
		state.pending = 0.0
		state.accumulator = 0.0
		state.precise_buffer = 0.0
		state.last_precise_input = 0.0
		state.touching = False
		state.from_touch = False
		state.wheel_streak = 0
		state.last_wheel_direction = 0.0
		state.last_wheel_time = 0.0
		state.last_update = time.monotonic()
		self.scroll_debug_modes.pop(source, None)
		for key in [k for k in self.scroll_debug_last_logs if k.startswith(f"{source}:")]:
			del self.scroll_debug_last_logs[key]

	def _log_scroll_mode(
		self, source: str, mode: str, delta: float, px_per_unit: float, precise_scale: float, precise_px_per_unit: float | None
	) -> None:
		prev_mode = self.scroll_debug_modes.get(source)
		if prev_mode == mode:
			return
		self.scroll_debug_modes[source] = mode
		self._log_scroll_detail(
			source,
			"route",
			mode=mode,
			delta=delta,
			px_per_unit=px_per_unit,
			precise_scale=precise_scale,
			precise_px_per_unit=precise_px_per_unit if precise_px_per_unit is not None else "None",
			wheel_precise=self.inp.mouse_wheel_precise,
			window_active=time.monotonic() < self.inp.trackpad_scroll_mode_until,
		)

	def reset_disabled_motion(self) -> None:
		for source, state in self.physics_states.items():
			if not state.from_touch:
				self.reset_motion(source)

	def add_wheel_motion(
		self, source: str, delta: float, px_per_unit: float, precise_scale: float = 1.0, precise_px_per_unit: float | None = None
	) -> None:
		if delta == 0:
			return

		state = self._state(source)
		max_velocity = self._scaled_max_velocity()
		velocity_limit = max_velocity
		pending_before = state.pending
		precise_before = state.precise_buffer
		velocity_before = state.velocity
		state.from_touch = False
		route = "wheel"
		speed = self.speed()
		precise_unit = precise_px_per_unit if precise_px_per_unit is not None else px_per_unit
		pixel_delta = 0.0
		repeat_boost = 0.0
		boost = 0.0
		impulse = 0.0
		if self.precise_scroll_active():
			route = "precise"
			self._log_scroll_mode(source, "precise", delta, px_per_unit, precise_scale, precise_px_per_unit)
			state.velocity = 0.0
			state.wheel_streak = 0
			state.last_wheel_direction = 0.0
			state.last_wheel_time = 0.0
			pixel_delta = delta * precise_unit * SCROLL_PHYSICS_PRECISE_WHEEL_PIXEL_MULTIPLIER * precise_scale * speed
			state.precise_buffer += pixel_delta
			state.last_precise_input = time.monotonic()
		else:
			self._log_scroll_mode(source, "wheel", delta, px_per_unit, precise_scale, precise_px_per_unit)
			velocity_limit *= SCROLL_PHYSICS_WHEEL_MAX_VELOCITY_MULTIPLIER
			repeat_boost = self._wheel_boost(state, delta)
			boost = 1.0 + min(abs(state.velocity) / velocity_limit, 1.0) * SCROLL_PHYSICS_ACCELERATION_BOOST
			impulse = delta * px_per_unit * repeat_boost * speed
			state.velocity += impulse * SCROLL_PHYSICS_WHEEL_VELOCITY * boost
			state.last_update = time.monotonic()
		state.last_velocity = state.velocity
		state.velocity = max(min(state.velocity, velocity_limit), -velocity_limit)
		state.touching = False
		self._log_scroll_detail(
			source,
			"wheel-input",
			route=route,
			delta=delta,
			px_per_unit=px_per_unit,
			precise_scale=precise_scale,
			speed=speed,
			precise_unit=precise_unit,
			pixel_delta=pixel_delta,
			repeat_boost=repeat_boost,
			boost=boost,
			impulse=impulse,
			pending_before=pending_before,
			pending_after=state.pending,
			precise_before=precise_before,
			precise_after=state.precise_buffer,
			velocity_before=state.last_velocity,
			velocity_after=state.velocity,
			velocity_limit=velocity_limit,
		)

	def apply_touch_drag(self, source: str, delta_pixels: float) -> None:
		state = self._state(source)
		max_velocity = self._scaled_max_velocity()
		now = time.monotonic()
		dt = max(now - state.last_update, 1 / 240)
		pending_before = state.pending
		precise_before = state.precise_buffer
		state.last_velocity = state.velocity
		state.touching = True
		state.from_touch = True
		state.precise_buffer = 0.0
		state.pending += delta_pixels * SCROLL_PHYSICS_TOUCH_DRAG_MULTIPLIER
		state.velocity = delta_pixels / dt * SCROLL_PHYSICS_TOUCH_FLING_MULTIPLIER
		state.velocity = max(min(state.velocity, max_velocity), -max_velocity)
		state.last_update = now
		self._log_scroll_detail(
			source,
			"touch-drag",
			delta_pixels=delta_pixels,
			dt=dt,
			pending_before=pending_before,
			pending_after=state.pending,
			precise_before=precise_before,
			precise_after=state.precise_buffer,
			velocity_before=state.last_velocity,
			velocity_after=state.velocity,
			max_velocity=max_velocity,
		)

	def release_touch(self, source: str) -> None:
		if source in self.physics_states:
			self.physics_states[source].touching = False
			self.physics_states[source].from_touch = True
			self.physics_states[source].last_update = time.monotonic()
			# velocity on release should be based on the last two frames of motion
			if self.physics_states[source].last_velocity != 0.0:
				self.physics_states[source].velocity = (self.physics_states[source].velocity + self.physics_states[source].last_velocity) / 2
			state = self.physics_states[source]
			self._log_scroll_detail(
				source,
				"touch-release",
				pending=state.pending,
				precise_buffer=state.precise_buffer,
				velocity=state.velocity,
			)

	def step_motion(self, source: str) -> float:
		state = self._state(source)
		min_velocity = self._scaled_min_velocity()
		now = time.monotonic()
		dt = min(max(now - state.last_update, 0.0), SCROLL_PHYSICS_MAX_TIMESTEP)
		accumulator_before = state.accumulator
		velocity_before = state.velocity
		pending_before = state.pending
		precise_before = state.precise_buffer
		state.last_update = now
		state.accumulator = min(state.accumulator + dt, SCROLL_PHYSICS_MAX_TIMESTEP)

		delta = state.pending
		state.pending = 0.0
		precise_dt = 0.0
		precise_delta = 0.0
		precise_release_age = 0.0
		precise_snapped = False
		fixed_steps = 0
		exit_reason = "active"

		if abs(state.precise_buffer) >= 0.01:
			precise_dt = min(max(dt, 1 / 240), SCROLL_PHYSICS_PRECISE_MAX_TIMESTEP)
			precise_alpha = 1.0 - math.exp(-precise_dt / max(SCROLL_PHYSICS_PRECISE_SMOOTHING, 1e-4))
			precise_delta = state.precise_buffer * precise_alpha
			delta += precise_delta
			state.precise_buffer -= precise_delta
			if state.last_precise_input:
				precise_release_age = max(now - state.last_precise_input, 0.0)
			if (
				precise_release_age >= SCROLL_PHYSICS_PRECISE_RELEASE_GRACE
				and abs(state.precise_buffer) <= SCROLL_PHYSICS_PRECISE_STOP_THRESHOLD
			):
				state.precise_buffer = 0.0
				precise_snapped = True
			if abs(state.precise_buffer) < 0.01:
				state.precise_buffer = 0.0

		if state.touching:
			state.accumulator = 0.0
			self._log_scroll_detail(
				source,
				"step",
				dt=dt,
				accumulator_before=accumulator_before,
				accumulator_after=state.accumulator,
				pending_before=pending_before,
				precise_before=precise_before,
				precise_dt=precise_dt,
				precise_delta=precise_delta,
				precise_release_age=precise_release_age,
				precise_snapped=precise_snapped,
				precise_after=state.precise_buffer,
				velocity_before=velocity_before,
				velocity_after=state.velocity,
				fixed_steps=fixed_steps,
				delta_out=delta,
				reason="touching",
			)
			return delta

		if abs(state.velocity) < min_velocity:
			state.velocity = 0.0
			state.accumulator = 0.0
			self._log_scroll_detail(
				source,
				"step",
				dt=dt,
				accumulator_before=accumulator_before,
				accumulator_after=state.accumulator,
				pending_before=pending_before,
				precise_before=precise_before,
				precise_dt=precise_dt,
				precise_delta=precise_delta,
				precise_release_age=precise_release_age,
				precise_snapped=precise_snapped,
				precise_after=state.precise_buffer,
				velocity_before=velocity_before,
				velocity_after=state.velocity,
				fixed_steps=fixed_steps,
				delta_out=delta,
				min_velocity=min_velocity,
				reason="below-min-velocity",
			)
			return delta

		while state.accumulator >= SCROLL_PHYSICS_FIXED_TIMESTEP:
			fixed_steps += 1
			delta += state.velocity * SCROLL_PHYSICS_FIXED_TIMESTEP
			state.velocity *= SCROLL_PHYSICS_FIXED_DAMPING
			state.accumulator -= SCROLL_PHYSICS_FIXED_TIMESTEP
			if abs(state.velocity) < min_velocity:
				state.velocity = 0.0
				state.accumulator = 0.0
				exit_reason = "damped-below-min"
				break

		if state.velocity != 0.0 and state.accumulator > 0:
			delta += state.velocity * state.accumulator
			state.velocity *= SCROLL_PHYSICS_DAMPING ** (state.accumulator * 60)
			state.accumulator = 0.0

		if abs(state.velocity) < min_velocity:
			state.velocity = 0.0
			if exit_reason == "active":
				exit_reason = "clamped-below-min"
		self._log_scroll_detail(
			source,
			"step",
			dt=dt,
			accumulator_before=accumulator_before,
			accumulator_after=state.accumulator,
			pending_before=pending_before,
			pending_after=state.pending,
			precise_before=precise_before,
			precise_dt=precise_dt,
			precise_delta=precise_delta,
			precise_release_age=precise_release_age,
			precise_snapped=precise_snapped,
			precise_after=state.precise_buffer,
			velocity_before=velocity_before,
			velocity_after=state.velocity,
			min_velocity=min_velocity,
			fixed_steps=fixed_steps,
			delta_out=delta,
			reason=exit_reason,
		)
		return delta

	def active(self, source: str) -> bool:
		state = self.physics_states.get(source)
		if state is None:
			return False
		return (
			state.touching
			or abs(state.velocity) >= self._scaled_min_velocity()
			or abs(state.pending) >= 0.01
			or abs(state.precise_buffer) >= 0.01
		)

	def any_active(self) -> bool:
		return any(self.active(source) for source in self.physics_states)


def copy_to_clipboard(text: str) -> None:
	sdl3.SDL_SetClipboardText(text.encode(errors="surrogateescape"))


def copy_from_clipboard() -> str:
	try:
		return sdl3.SDL_GetClipboardText().decode()
	except UnicodeDecodeError:
		logging.exception("Clipboard text decode error")
		return ""
	except Exception:
		logging.exception("Unknown clipboard text decode error")
		return ""


def field_copy(text_field) -> None:
	text_field.copy()


def field_paste(text_field) -> None:
	text_field.paste()


def field_clear(text_field) -> None:
	text_field.clear()
SCROLL_PHYSICS_WHEEL_VELOCITY = 16.0
SCROLL_PHYSICS_PRECISE_WHEEL_PIXEL_MULTIPLIER = 0.11
SCROLL_PHYSICS_GALLERY_PRECISE_PIXEL_BASE = 15
SCROLL_PHYSICS_TRACKPAD_GESTURE_WINDOW = 0.25
SCROLL_PHYSICS_REPEAT_WINDOW = 0.22
SCROLL_PHYSICS_REPEAT_ACCELERATION = 0.35
SCROLL_PHYSICS_REPEAT_CURVE = 0.08
SCROLL_PHYSICS_WHEEL_MAGNITUDE_ACCELERATION = 0.45
SCROLL_PHYSICS_WHEEL_MAX_VELOCITY_MULTIPLIER = 5.0
SCROLL_PHYSICS_PRECISE_SMOOTHING = 0.026
SCROLL_PHYSICS_PRECISE_MAX_TIMESTEP = 1.0 / 60.0
SCROLL_PHYSICS_PRECISE_RELEASE_GRACE = 0.03
SCROLL_PHYSICS_PRECISE_STOP_THRESHOLD = 5.0
SCROLL_PHYSICS_TOUCH_DRAG_MULTIPLIER = 1.0
SCROLL_PHYSICS_TOUCH_FLING_MULTIPLIER = 1.15
SCROLL_ANIMATION_MAX_FPS = 144.0
SCROLL_ANIMATION_FRAME_INTERVAL = 1.0 / SCROLL_ANIMATION_MAX_FPS
SCROLL_PHYSICS_FIXED_TIMESTEP = 1.0 / 240.0
SCROLL_PHYSICS_MAX_TIMESTEP = 0.05
SCROLL_PHYSICS_ACCELERATION_BOOST = 2
SCROLL_PHYSICS_DAMPING = 0.95
SCROLL_PHYSICS_FIXED_DAMPING = SCROLL_PHYSICS_DAMPING ** (SCROLL_PHYSICS_FIXED_TIMESTEP * 60)
SCROLL_PHYSICS_MAX_VELOCITY = 2100.0
SCROLL_PHYSICS_MIN_VELOCITY = 8.0
