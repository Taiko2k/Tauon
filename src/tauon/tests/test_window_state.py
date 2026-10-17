import pytest

from tauon.t_modules.t_window_state import WindowState, parse_window_state, serialize_window_state


def test_window_state_round_trip() -> None:
	state = WindowState(
		width=1440,
		height=900,
		scale=1.5,
		opacity=0.85,
		borderless=False,
		maximized=True,
		position=(-120, 48),
	)
	assert parse_window_state(serialize_window_state(state), WindowState(1120, 600, 1.0)) == state


def test_window_state_uses_defaults_for_optional_values() -> None:
	defaults = WindowState(1120, 600, 2.0, opacity=0.9, maximized=True)
	state = parse_window_state('{"version": 1, "width": 800, "height": 500}', defaults)
	assert state == WindowState(800, 500, 2.0, opacity=0.9, maximized=True)


@pytest.mark.parametrize(
	"text",
	[
		'{"version": 2}',
		'{"version": 1, "width": 20, "height": 500}',
		'{"version": 1, "position": [20]}',
		'{"version": 1, "opacity": 2}',
	],
)
def test_window_state_rejects_invalid_content(text: str) -> None:
	with pytest.raises(ValueError):
		parse_window_state(text, WindowState(1120, 600, 1.0))
