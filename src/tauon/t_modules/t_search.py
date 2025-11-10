"""Tauon Music Box - Search an artist by scrape/fetch module"""
# Copyright © 2015-2019, Taiko2k captain(dot)gxj(at)gmail.com

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
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import requests
from bs4 import BeautifulSoup

if TYPE_CHECKING:
	from collections.abc import Callable


def bandcamp_search(artist: str, callback: Callable[[str | None], None] | None = None) -> str | None:
	"""Search Bandcamp for the artist and return their URL"""
	try:
		page = requests.get(f"https://bandcamp.com/search?q={artist}", timeout=10)
		html = BeautifulSoup(page.text, "html.parser")
		results = html.find_all("div", {"class": "result-info"})
		for result in results:
			children = result.find_all("div")
			okay = False
			for child in children:
				if child.string and "ARTIST" in child.string:
					okay = True
					break
			if not okay:
				continue
			for child in children:
				if child["class"][0] == "heading" and child.a.string.strip().lower() == artist.lower():
					url = child.a["href"].split("?")[0]
					if callback:
						callback(url)
					return url

	except Exception:
		logging.exception("Bandcamp search error")

	if callback:
		callback(None)
	return None
