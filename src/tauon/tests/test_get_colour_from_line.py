
import os

os.environ["SDL_DISABLE_METADATA"]         = "1" # Disable metadata method,                     "0"        by default.

from tauon.t_modules.t_themeload import get_colour_from_line


def test_get_colour_from_line() -> None:
	colour = get_colour_from_line("230,230,230     tab over")
	assert colour.r == 230
	assert colour.g == 230
	assert colour.b == 230
	assert colour.a == 255

	colour = get_colour_from_line("180,140,255,255 tab active background")
	assert colour.r == 180
	assert colour.g == 140
	assert colour.b == 255
	assert colour.a == 255

	colour = get_colour_from_line("0xtrackff     mini text 2")
	assert colour.r == 255
	assert colour.g == 255
	assert colour.b == 255
	assert colour.a == 255

	colour = get_colour_from_line("track1        mini text 2")
	assert colour.r == 255
	assert colour.g == 255
	assert colour.b == 255
	assert colour.a == 255

	colour = get_colour_from_line("2024-01-01")
	assert colour.r == 255
	assert colour.g == 255
	assert colour.b == 255
	assert colour.a == 255
