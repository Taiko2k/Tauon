from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path

WINDOW_STATE_FILENAME = "window-state.json"
WINDOW_STATE_VERSION = 1


@dataclass(frozen=True)
class WindowState:
	width: int
	height: int
	scale: float
	opacity: float = 1.0
	borderless: bool = True
	maximized: bool = False
	position: tuple[int, int] | None = None


def parse_window_state(text: str, defaults: WindowState) -> WindowState:
	values = json.loads(text)
	if not isinstance(values, dict):
		raise ValueError("Window state must be a JSON object")
	if values.get("version") != WINDOW_STATE_VERSION:
		raise ValueError("Unsupported window state version")

	width = values.get("width", defaults.width)
	height = values.get("height", defaults.height)
	if not isinstance(width, int) or isinstance(width, bool) or not isinstance(height, int) or isinstance(height, bool):
		raise ValueError("Window dimensions must be integers")
	if not 100 < width < 10000 or not 100 < height < 5000:
		raise ValueError("Window size is outside the supported range")

	scale = values.get("scale", defaults.scale)
	opacity = values.get("opacity", defaults.opacity)
	if not isinstance(scale, int | float) or isinstance(scale, bool):
		raise ValueError("Window scale must be numeric")
	if not isinstance(opacity, int | float) or isinstance(opacity, bool):
		raise ValueError("Window opacity must be numeric")
	scale = float(scale)
	opacity = float(opacity)
	if not 0.5 <= scale <= 4.0:
		raise ValueError("Window scale is outside the supported range")
	if not 0.3 <= opacity <= 1.0:
		raise ValueError("Window opacity is outside the supported range")

	position_value = values.get("position")
	position: tuple[int, int] | None
	if position_value is None:
		position = None
	elif (
		isinstance(position_value, list)
		and len(position_value) == 2
		and all(isinstance(coordinate, int) and not isinstance(coordinate, bool) for coordinate in position_value)
	):
		position = (position_value[0], position_value[1])
	else:
		raise ValueError("Window position must be null or a two-integer array")

	borderless = values.get("borderless", defaults.borderless)
	maximized = values.get("maximized", defaults.maximized)
	if not isinstance(borderless, bool) or not isinstance(maximized, bool):
		raise ValueError("Window flags must be booleans")

	return replace(
		defaults,
		width=width,
		height=height,
		scale=scale,
		opacity=opacity,
		borderless=borderless,
		maximized=maximized,
		position=position,
	)


def load_window_state(path: Path, defaults: WindowState) -> WindowState:
	if not path.is_file():
		return defaults
	return parse_window_state(path.read_text(encoding="utf-8"), defaults)


def serialize_window_state(state: WindowState) -> str:
	return json.dumps(
		{
			"version": WINDOW_STATE_VERSION,
			"width": state.width,
			"height": state.height,
			"scale": state.scale,
			"opacity": state.opacity,
			"borderless": state.borderless,
			"maximized": state.maximized,
			"position": state.position,
		},
		indent=2,
	) + "\n"
