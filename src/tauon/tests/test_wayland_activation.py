"""Serial tracking and the non-Wayland path of t_wayland_activation"""

from __future__ import annotations

from types import SimpleNamespace

from tauon.t_modules import t_wayland_activation
from tauon.t_modules.t_wayland_activation import WL_POINTER_BUTTON_STATE_PRESSED, WaylandActivation


def make() -> WaylandActivation:
	return WaylandActivation(SimpleNamespace(t_window=None))


def test_button_press_sets_serial_release_does_not():
	activation = make()
	activation.on_button(0, 0, 10, 0, 272, WL_POINTER_BUTTON_STATE_PRESSED)
	activation.on_button(0, 0, 11, 0, 272, 0)
	assert activation.serial == 10


def test_key_release_counts():
	activation = make()
	activation.on_key(0, 0, 20, 0, 30, 1)
	activation.on_key(0, 0, 21, 0, 30, 0)
	assert activation.serial == 21


def test_touch_down_counts():
	activation = make()
	activation.on_touch_down(0, 0, 30, 0, 0, 1, 0, 0)
	assert activation.serial == 30


def test_no_token_off_wayland(monkeypatch):
	monkeypatch.setattr(t_wayland_activation.sdl3, "get_current_video_driver", lambda: b"x11")
	activation = make()
	assert activation.request_token() is None
	assert activation.unavailable
	# Stays off without asking SDL again
	activation.drain()
	assert activation.lib is None
