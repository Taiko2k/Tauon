from tauon.t_modules import t_lyrics


def test_genius_return_url_normalizes_input() -> None:
	url = t_lyrics.genius("Beyoncé feat. Jay-Z", "Déjà Vu (feat. X)", return_url=True)
	assert url == "https://genius.com/Beyonce-Deja-Vu-lyrics"
