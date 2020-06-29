from bs4 import BeautifulSoup
import requests

def bandcamp_search(artist, callback=None):

    try:
        page = requests.get("https://bandcamp.com/search?q=" + artist)
        html = BeautifulSoup(page.text, 'html.parser')
        results = html.find_all("div", {"class": "result-info"})
        for result in results:
            children = result.findChildren("div")
            okay = False
            for child in children:
                if child.string and "ARTIST" in child.string:
                    okay = True
                    break
            if not okay:
                continue
            for child in children:
                if child["class"][0] == "heading":
                    if child.a.string.strip().lower() == artist.lower():
                        url = child.a["href"].split("?")[0]
                        if callback:
                            callback(url)
                        return url

    except:
        print("Bandcamp search error")

    if callback:
        callback(None)
    return None
