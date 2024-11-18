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


import re
import urllib.parse
from http import HTTPStatus

import requests
from bs4 import BeautifulSoup
from unidecode import unidecode

# def lyricwiki(artist: str, title: str) -> str:
#
# 	lyrics = PyLyrics.getLyrics(artist, title)
#
# 	if lyrics and lyrics[0] == "<" and "Instrumental" in lyrics:
# 		lyrics = "[Instrumental]"
#
# 	return lyrics

def ovh(artist: str, title: str) -> str:
	"""Get lyrics from lyrics.ovh API"""
	q = urllib.parse.quote(f"{artist}/{title}")
	point = f"https://api.lyrics.ovh/v1/{q}"
	r = requests.get(point, timeout=10)
	if r.status_code == HTTPStatus.OK:
		j = r.json()
		return j["lyrics"]
	return ""


# def happi(artist: str, title: str) -> str:
# 	q = urllib.parse.quote(f"{artist} {title}")
# 	point = f"https://api.happi.dev/v1/music?q={q}&limit=1&apikey=23b23b30Ca5nqZSe5JWJ8I4smmgO1JK6grVTEXpkBz1O8mNjTCmmCjnX&type=track"
# 	r = requests.get(point)
# 	j = r.json()
# 	if not j["result"][0]["haslyrics"]:
# 		return ""
# 	a_id = j["result"][0]["id_artist"]
# 	t_id = j["result"][0]["id_track"]
# 	al_id = j["result"][0]["id_album"]
#
# 	point = f"https://api.happi.dev/v1/music/artists/{a_id}/albums/{al_id}/tracks/{t_id}/lyrics?apikey=23b23b30Ca5nqZSe5JWJ8I4smmgO1JK6grVTEXpkBz1O8mNjTCmmCjnX"
# 	r = requests.get(point)
# 	j = r.json()
# 	return j["result"]["lyrics"]

def genius(artist: str, title: str, return_url: bool=False) -> str:
	"""Scrape lyrics from genius.com"""
	artist = artist.split("feat.")[0]
	title = title.split("(feat.")[0]
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

	result = html.find("div", class_="lyrics") #.get_text()
	if result is not None:
		lyrics = result.get_text()
		lyrics2 = []
		for line in lyrics.splitlines():
			if line.startswith("["):
				pass
			else:
				lyrics2.append(line)

		lyrics = "\n".join(lyrics2)
		lyrics = lyrics.strip("\n")
		return lyrics

	# New layout type
	results = html.findAll("div", {"class": lambda l: l and "Lyrics__Container" in l})
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
	new_lines = []
	for line in lines:
		if "[" in line:
			line = line.split("[", 1)[0]
			if line:
				line += "\n"

		new_lines.append(line.lstrip().rstrip(" ") + "\n")

	lyrics = "".join(new_lines)
	lyrics = lyrics.replace("(\n", "(")
	lyrics = lyrics.replace("\n)", ")")
	lyrics = lyrics.lstrip("\n")
	lyrics = lyrics.lstrip()
	return lyrics


lyric_sources = {
	# "Apiseeds": apiseeds,
	# "Happi": happi,
	"Genius": genius,
	#"LyricWiki": lyricwiki,
	"lyrics.ovh": ovh,
}

uses_scraping = {
	#"LyricWiki",
	"Genius",
}
