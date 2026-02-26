from tauon.t_modules import t_extra


def test_get_year_from_string() -> None:
	year = t_extra.get_year_from_string("2024-01-01")
	assert year == "2024"

	year = t_extra.get_year_from_string("2025-01")
	assert year == "2025"

	year = t_extra.get_year_from_string("2026")
	assert year == "2026"
