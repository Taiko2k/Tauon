"""Tauon Music Box - Lyrics scrape/fetch module

You can add lyric providers in this module

Create a function that takes artist and title, and returns lyrics as a str
If failed to find lyrics, you can return None or raise an exception.
Finally add provider name and function reference to lyric_sources dict below
"""

# Copyright © 2018-2023, Taiko2k captain(dot)gxj(at)gmail.com

#     This file is part of Tauon Music Box.
#
#     Tauon Music Box is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     Tauon Music Box is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Lesser General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with Tauon Music Box.  If not, see <http://www.gnu.org/licenses/>.

import logging
import re
import urllib.parse
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode


def ovh(
	artist: str, title: str, user_agent: str = "unused here but it needs to exist in every lyrics function"
) -> tuple[str, str]:
	"""Get lyrics from lyrics.ovh API"""
	q = urllib.parse.quote(f"{artist}/{title}")
	point = f"https://api.lyrics.ovh/v1/{q}"
	r = requests.get(point, timeout=10)
	if r.status_code == HTTPStatus.OK:
		j = r.json()
		return j["lyrics"], ""
	return "", ""


def genius(
	artist: str,
	title: str,
	return_url: bool = False,
	user_agent: str = "unused here but it needs to exist in every lyrics function",
) -> tuple[str, str] | str:
	"""Scrape lyrics from genius.com"""
	artist = artist.split("feat.", maxsplit=1)[0].strip()
	title = title.split("(feat.", maxsplit=1)[0].strip()
	line = f"{artist}-{title}"
	line = re.sub("[,._@!#%^*+:;'()]", "", line)
	line = line.replace("]", "")
	line = line.replace("[", "")
	line = line.replace("?", "")
	line = line.replace(" ", "-")
	line = line.replace("/", "-")
	line = line.replace("-&-", "-and-")
	line = line.replace("&", "-and-")
	line = unidecode(line)
	line = urllib.parse.quote(line)
	line = f"https://genius.com/{line}-lyrics"

	if return_url:
		return line

	page = requests.get(line, timeout=10)
	html = BeautifulSoup(page.text, "html.parser")

	result = html.find("div", class_="lyrics")
	if result is not None:
		lyrics = result.get_text()
		lyrics2: list[str] = []
		for line in lyrics.splitlines():
			if line.startswith("["):
				pass
			else:
				lyrics2.append(line)

		lyrics = "\n".join(lyrics2)
		lyrics = lyrics.strip("\n")
		return lyrics, ""

	results = html.find_all("div", {"class": lambda l: l and "Lyrics__Container" in l})
	if not results:
		return "", ""

	lyrics = "".join([r.get_text("\n") for r in results])

	level = 0
	new = ""
	for cha in lyrics:
		if level <= 0:
			new += cha
		if cha == "[":
			level += 1
		if cha == "]":
			level -= 1
	lyrics = new

	lines = lyrics.splitlines()
	new_lines: list[str] = []
	# fmt:off
	skip_patterns = [
		r"^\d+\s+Contributors?$",   # "3 Contributors"
		r"^[^a-zA-Z]*Lyrics$",      # "[Song Name] Lyrics"
		r"^\s*$",                   # Empty lines
		r"^Embed$",                 # "Embed" button text
		r"^\d+$",                   # Standalone numbers
		r"^See .* Live$",           # "See Artist Live"
		r"^Get tickets as low as",  # Ticket advertisements
		r"^You might also like",    # Related content
		r"^\w+ on Apple Music",     # Apple Music links
	]
	# fmt:on

	for line in lines:
		line = line.strip()

		if not line:
			continue

		should_skip = False
		for pattern in skip_patterns:
			if re.match(pattern, line, re.IGNORECASE):
				should_skip = True
				break

		if should_skip:
			continue

		if "[" in line:
			line = line.split("[", 1)[0].strip()
			if not line:
				continue

		if line.lower() in ["lyrics", "embed", "more on genius"] or line.isdigit() or len(line) < 2:
			continue

		new_lines.append(line.rstrip() + "\n")

	lyrics = "".join(new_lines)
	lyrics = lyrics.replace("(\n", "(")
	lyrics = lyrics.replace("\n)", ")")
	lyrics = lyrics.lstrip("\n")
	lyrics = lyrics.lstrip()

	lyrics_lines = lyrics.split("\n")

	while lyrics_lines:
		first_line = lyrics_lines[0].strip()
		if (
			re.match(r"^\d+\s+Contributors?$", first_line, re.IGNORECASE)
			or re.match(r"^.*Lyrics$", first_line, re.IGNORECASE)
			or first_line.lower() in ["embed", "lyrics"]
			or len(first_line) < 3
		):
			lyrics_lines.pop(0)
		else:
			break

	while lyrics_lines:
		last_line = lyrics_lines[-1].strip()
		if last_line.lower() in ["embed", "more on genius"] or len(last_line) < 3:
			lyrics_lines.pop()
		else:
			break

	final_lyrics = "\n".join(lyrics_lines).strip()

	if len(final_lyrics) > 10:
		return final_lyrics, ""

	return "", ""


def lrclib(artist: str, title: str, user_agent: str = "TauonMusicBox/Devel") -> tuple[str, str]:
	h = {
		"User-Agent": user_agent,
	}

	p = {
		"track_name": title,
		"artist_name": artist,
	}

	r = requests.get("https://lrclib.net/api/get", headers=h, params=p, timeout=10)
	if r.status_code == HTTPStatus.OK:
		p = r.json().get("plainLyrics")
		s = r.json().get("syncedLyrics")
		if p or s:
			return p, s
	return "", ""


def get_lrclib_challenge(user_agent: str = "TauonMusicBox/Devel") -> tuple[str, str]:
	h = {
		"User-Agent": user_agent,
	}
	try:
		r = requests.post("https://lrclib.net/api/request-challenge", headers=h, timeout=10)
	except requests.exceptions.ConnectionError:
		return "", ""
	except Exception:
		logging.exception()
		return "", ""
	if r.status_code == HTTPStatus.OK:
		p = r.json().get("prefix")
		t = r.json().get("target")
		if p or t:
			return p, t
	return "", ""


lyric_sources = {
	"Genius": genius,
	"lyrics.ovh": ovh,
	"LRCLIB": lrclib,
}

uses_scraping = {
	"Genius",
}
