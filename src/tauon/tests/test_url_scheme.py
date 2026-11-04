# Copyright © 2026, Tauon contributors

import pytest

from tauon.t_modules.t_extra import with_url_scheme


@pytest.mark.parametrize(
	("typed", "expected"),
	[
		# On this machine or the local network: plain http
		("localhost:8096", "http://localhost:8096"),
		("127.0.0.1:8096", "http://127.0.0.1:8096"),
		("192.168.1.20:8096", "http://192.168.1.20:8096"),
		("10.0.0.5", "http://10.0.0.5"),
		("172.20.1.1:9000", "http://172.20.1.1:9000"),
		("[::1]:8096", "http://[::1]:8096"),
		("nas:8096", "http://nas:8096"),
		("music.local", "http://music.local"),
		# Jellyfin's own port is http, wherever it is
		("media.example.com:8096", "http://media.example.com:8096"),
		# Anything else is assumed to be behind a TLS proxy
		("jellyfin.example.com", "https://jellyfin.example.com"),
		("example.com/jellyfin/", "https://example.com/jellyfin/"),
		("8.8.8.8:8920", "https://8.8.8.8:8920"),
		# Typed schemes are left alone
		("http://jellyfin.example.com", "http://jellyfin.example.com"),
		("https://localhost:8096", "https://localhost:8096"),
		("  localhost:8096 ", "http://localhost:8096"),
		("", ""),
	],
)
def test_with_url_scheme(typed: str, expected: str) -> None:
	assert with_url_scheme(typed, 8096) == expected


def test_navidrome_port_is_http() -> None:
	assert with_url_scheme("music.example.com:4533", 4533) == "http://music.example.com:4533"
	assert with_url_scheme("music.example.com:8096", 4533) == "https://music.example.com:8096"


def test_unparseable_port_is_left_alone() -> None:
	assert with_url_scheme("host:notaport", 8096) == "host:notaport"
