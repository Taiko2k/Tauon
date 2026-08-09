"""Scrobbling services for Last.fm, ListenBrainz, and local queues."""

from __future__ import annotations

import json
import logging
import threading
import time
import webbrowser
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, Protocol

import requests

try:
	# pyLast needs to be imported AFTER setup_tls() else pyinstaller breaks; it is
	# reloaded by the application after TLS setup.
	import pylast
except Exception:
	logging.exception("pyLast module not found, Last.fm support will be disabled.")
	pylast = None

from tauon.t_modules.t_extra import (
	get_artist_strip_feat,
	get_first_artist,
	get_split_artists,
)
from tauon.t_modules.t_models import StarRecord

if TYPE_CHECKING:
	from pylast import LastFMNetwork, LibreFMNetwork, SessionKeyGenerator

	from tauon.t_modules.t_models import TrackClass


class _ScrobblePrefs(Protocol):
	auto_lfm: bool
	enable_lb: bool
	last_fm_token: str | None
	last_fm_username: str
	lastfm_pull_love: bool
	lb_token: str | None
	listenbrainz_url: str
	maloja_enable: bool
	maloja_url: str
	scrobble_hold: bool
	scrobble_jellyfin: bool
	scrobble_plex: bool
	scrobble_subsonic: bool
	scrobble_tidal: bool
	use_libre_fm: bool


class _ScrobbleGui(Protocol):
	def delay_frame(self, frames: int) -> object: ...
	def request_frame(self) -> object: ...
	def request_tracklist_redraw(self) -> object: ...


class _ScrobbleApp(Protocol):
	bag: Any
	bg_save: Callable[[], object]
	gui: _ScrobbleGui
	lastfm: Any
	lb: Any
	maloja_scrobble: Callable[[TrackClass, int], object]
	n_version: str
	perf_timer: Any
	prefs: _ScrobblePrefs
	scrobble_warning_timer: Any
	show_message: Callable[..., object]
	subsonic: Any
	t_title: str
	toggle_lfm_auto: Callable[..., object]
	love: Callable[..., object]


class _ScrobblePlayer(Protocol):
	a_time: float
	b_time: float
	lastfm: Any
	master_library: dict[int, TrackClass]
	playing_time: float
	queue_step: int
	star_store: Any
	track_queue: list[int]

	def get_track(self, index: int) -> TrackClass: ...


class LastFMapi:
	def __init__(
		self,
		tauon: _ScrobbleApp,
		pctl: _ScrobblePlayer,
		copy_to_clipboard_fn: Callable[[str], None],
	) -> None:
		self.tauon = tauon
		self.star_store = pctl.star_store
		self.show_message = tauon.show_message
		self.last_fm_enable: bool = tauon.bag.last_fm_enable
		self.gui = self.tauon.gui
		self.pctl = pctl
		self.prefs = self.tauon.prefs
		self.copy_to_clipboard = copy_to_clipboard_fn
		self.sg: SessionKeyGenerator | None = None
		self.url: str | None = None
		self.API_SECRET = "6e433964d3ff5e817b7724d16a9cf0cc"  # noqa: S105
		self.connected = False
		self.API_KEY = "bfdaf6357f1dddd494e5bee1afe38254"
		self.scanning_username = ""

		self.network: LibreFMNetwork | None = None
		self.lastfm_network: LastFMNetwork | None = None
		self.tries = 0

		self.scanning_friends = False
		self.scanning_loves = False
		self.scanning_scrobbles = False

	def get_network(self) -> type[LibreFMNetwork | LastFMNetwork]:
		if self.prefs.use_libre_fm:
			return pylast.LibreFMNetwork
		return pylast.LastFMNetwork

	def auth1(self) -> None:
		r"""Step 1 where the user clicks \"Login\""""
		if not self.last_fm_enable:
			self.show_message(_("Optional module python-pylast not installed"), mode="warning")
			return

		if self.network is None:
			self.no_user_connect()

		self.sg = pylast.SessionKeyGenerator(self.network)
		try:
			self.url = self.sg.get_web_auth_url()
		except pylast.NetworkError:
			logging.exception("Failed to get web auth URL from pylast due to a network error")
			self.show_message("Failed to get web auth URL from pylast", "Network error")
			return
		except Exception:
			logging.exception("Failed to get web auth URL from pylast due to an unknown issue")
			self.show_message("Failed to get web auth URL from pylast", "Unknown error")
			return
		logging.info(str(self.url))
		self.copy_to_clipboard(self.url)
		self.show_message(_("Web auth page opened"), _("Once authorised click the 'done' button."), mode="arrow")
		webbrowser.open(self.url, new=2, autoraise=True)

	def auth2(self) -> None:
		r"""Step 2 where the user clicks \"Done\""""
		if self.sg is None:
			self.show_message(_("You need to log in first"))
			return

		try:
			# session_key = self.sg.get_web_auth_session_key(self.url)
			session_key, username = self.sg.get_web_auth_session_key_username(self.url)
			self.prefs.last_fm_token = session_key
			self.network = self.get_network()(api_key=self.API_KEY, api_secret=
			self.API_SECRET, session_key=self.prefs.last_fm_token)
			# user = self.network.get_authenticated_user()
			# username = user.get_name()
			self.prefs.last_fm_username = username

		except Exception as e:
			if "Unauthorized Token" in str(e):
				logging.exception("Not authorized")
				self.show_message(_("Error - Not authorized"), mode="error")
			else:
				logging.exception("Unknown error")
				self.show_message(_("Error"), _("Unknown error."), mode="error")

		if not self.tauon.toggle_lfm_auto(mode=1):
			self.tauon.toggle_lfm_auto()

	def auth3(self) -> None:
		"""Used for 'logout'"""
		self.prefs.last_fm_token = None
		self.prefs.last_fm_username = ""
		self.show_message(_("Logout will complete on app restart."))

	def connect(self, m_notify: bool = True) -> bool | None:
		if not self.last_fm_enable:
			return False

		if self.connected is True:
			if m_notify:
				self.show_message(_("Already connected to Last.fm"))
			return True

		if self.prefs.last_fm_token is None:
			self.show_message(_("No Last.Fm account registered"), _("Authorise an account in settings"), mode="info")
			return None

		logging.info("Attempting to connect to Last.fm network")

		try:
			self.network = self.get_network()(
				api_key=self.API_KEY, api_secret=self.API_SECRET, session_key=self.prefs.last_fm_token)  # , username=lfm_username, password_hash=lfm_hash)

			self.connected = True
			if m_notify:
				self.show_message(_("Connection to Last.fm was successful."), mode="done")

			logging.info("Connection to lastfm appears successful")
			return True

		except Exception as e:
			logging.exception("Error connecting to Last.fm network")
			self.show_message(_("Error connecting to Last.fm network"), str(e), mode="warning")
			return False

	def toggle(self) -> None:
		self.prefs.scrobble_hold ^= True

	def details_ready(self) -> bool:
		return bool(self.prefs.last_fm_token)

	def last_fm_only_connect(self) -> bool:
		if not self.last_fm_enable:
			return False
		try:
			self.lastfm_network = pylast.LastFMNetwork(api_key=self.API_KEY, api_secret=self.API_SECRET)
			logging.info("Connection appears successful")
			return True

		except Exception as e:
			logging.exception("Error communicating with Last.fm network")
			self.show_message(_("Error communicating with Last.fm network"), str(e), mode="warning")
			return False

	def no_user_connect(self) -> bool:
		if not self.last_fm_enable:
			return False
		try:
			self.network = self.get_network()(api_key=self.API_KEY, api_secret=self.API_SECRET)
			logging.info("Connection appears successful")
			return True

		except Exception as e:
			logging.exception("Error communicating with Last.fm network")
			self.show_message(_("Error communicating with Last.fm network"), str(e), mode="warning")
			return False

	def get_all_scrobbles_estimate_time(self) -> float | None:
		if not self.connected:
			self.connect(False)
		if not self.connected or not self.prefs.last_fm_username:
			return None

		user = pylast.User(self.prefs.last_fm_username, self.network)
		total = user.get_playcount()

		if total:
			return 0.04364 * total
		return 0

	def get_all_scrobbles(self) -> None:
		if not self.connected:
			self.connect(False)
		if not self.connected or not self.prefs.last_fm_username:
			return

		try:
			self.scanning_scrobbles = True
			self.network.enable_rate_limit()
			user = pylast.User(self.prefs.last_fm_username, self.network)
			# username = user.get_name()
			self.tauon.perf_timer.set()
			tracks = user.get_recent_tracks(None)

			counts: dict[tuple[str, str], int] = {}

			# Count up the unique pairs
			for track in tracks:
				key = (str(track.track.artist), str(track.track.title))
				c = counts.get(key, 0)
				counts[key] = c + 1

			touched: list[int] = []

			# Add counts to matching tracks
			for key, value in counts.items():
				artist, title = key
				artist = artist.lower()
				title = title.lower()

				for track in self.pctl.master_library.values():
					t_artist = track.artist.lower()
					artists = [x.lower() for x in get_split_artists(track)]
					if t_artist == artist or artist in artists or (
							track.album_artist and track.album_artist.lower() == artist):
						if track.title.lower() == title:
							if track.index in touched:
								track.lfm_scrobbles += value
							else:
								track.lfm_scrobbles = value
								touched.append(track.index)
		except Exception:
			logging.exception("Scanning failed. Try again?")
			self.gui.request_tracklist_redraw()
			self.scanning_scrobbles = False
			self.show_message(_("Scanning failed. Try again?"), mode="error")
			return

		logging.info(self.tauon.perf_timer.get())
		self.gui.request_tracklist_redraw()
		self.scanning_scrobbles = False
		self.tauon.bg_save()
		self.show_message(_("Scanning scrobbles complete"), mode="done")

	def artist_info(self, artist: str) -> tuple[bool, str | None, str, str | None, str | None] | tuple[bool, str, str]:
		if self.lastfm_network is None and self.last_fm_only_connect() is False:
			return False, "", ""

		if artist:
			first_artist = get_first_artist(artist)
			logging.info(f"Artist info lookup: '{artist}' -> first_artist='{first_artist}'")
			attempts = [artist] if artist != first_artist else []
			attempts.append(first_artist)
		else:
			attempts = []

		for attempt_artist in attempts:
			try:
				logging.info(f"Trying Last.fm: '{attempt_artist}'")
				l_artist = pylast.Artist(attempt_artist, self.lastfm_network)
				bio = l_artist.get_bio_content()
				mbid = l_artist.get_mbid()
				url = l_artist.get_url()
				logging.info(f"Success for '{attempt_artist}'")
				return True, bio, "", mbid, url
			except Exception:
				logging.exception(f"last.fm get artist info failed for '{attempt_artist}'")

		return False, "", "", "", ""

	def artist_mbid(self, artist: str) -> str | None:
		if self.lastfm_network is None and self.last_fm_only_connect() is False:
			return ""

		if artist:
			first_artist = get_first_artist(artist)
			attempts = [artist] if artist != first_artist else []
			attempts.append(first_artist)
		else:
			attempts = []

		for attempt_artist in attempts:
			try:
				l_artist = pylast.Artist(attempt_artist, self.lastfm_network)
				return l_artist.get_mbid()
			except Exception:
				logging.exception("last.fm get artist mbid info failed")

		return ""

	def sync_pull_love(self, track_object: TrackClass) -> None:
		if not self.prefs.lastfm_pull_love or not (track_object.artist and track_object.title):
			return
		if not self.last_fm_enable:
			return
		if self.prefs.auto_lfm:
			self.connect(False)
		if not self.connected:
			return

		try:
			track = self.network.get_track(track_object.artist, track_object.title)
			if not track:
				logging.error("Get love: track not found")
				return
			track.username = self.prefs.last_fm_username

			remote_loved = track.get_userloved()

			if track_object.title != track.get_correction() or track_object.artist != track.get_artist().get_correction():
				logging.warning(f"pyLast/Last.fm bug workaround. API thought {track_object.artist} - {track_object.title} loved status was: {remote_loved}")
				return

			if remote_loved is None:
				logging.error("Error getting loved status")
				return

			local_loved = self.tauon.love(set=False, track_id=track_object.index, notify=False, sync=False)

			if remote_loved != local_loved:
				self.tauon.love(set=True, track_id=track_object.index, notify=False, sync=False)
		except Exception:
			logging.exception("Failed to pull love")

	def scrobble(self, track_object: TrackClass, timestamp: int | None = None) -> bool:
		if not self.last_fm_enable:
			return True
		if self.prefs.scrobble_hold:
			return True
		if self.prefs.auto_lfm:
			self.connect(False)

		if timestamp is None:
			timestamp = int(time.time())

		# lastfm_user = self.network.get_user(self.username)

		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)
		album_artist = track_object.album_artist

		logging.info("Submitting scrobble...")

		# Act
		try:
			if title and artist:
				if album:
					if album_artist and album_artist != artist:
						self.network.scrobble(
							artist=artist, title=title, album=album, album_artist=album_artist, timestamp=timestamp)
					else:
						self.network.scrobble(artist=artist, title=title, album=album, timestamp=timestamp)
				else:
					self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
				# logging.info('Scrobbled')

				# Pull loved status

				self.sync_pull_love(track_object)
			else:
				logging.warning("Not sent, incomplete metadata")

		except Exception as e:
			logging.exception("Failed to Scrobble!")
			if "retry" in str(e):
				logging.warning("Retrying in a couple seconds...")
				time.sleep(7)

				try:
					self.network.scrobble(artist=artist, title=title, timestamp=timestamp)
					# logging.info('Scrobbled')
					return True
				except Exception:
					logging.exception("Failed to retry!")

			# self.show_message(_("Error: Could not scrobble. ", str(e), mode='warning')
			logging.error("Error connecting to last.fm")
			self.tauon.scrobble_warning_timer.set()
			self.gui.request_frame()
			self.gui.delay_frame(5)

			return False
		return True

	def get_bio(self, artist: str) -> str:
		if self.lastfm_network is None and self.last_fm_only_connect() is False:
			return ""

		first_artist = get_first_artist(artist)
		attempts = [artist] if artist != first_artist else []
		attempts.append(first_artist)

		for attempt_artist in attempts:
			try:
				artist_object = pylast.Artist(attempt_artist, self.lastfm_network)
				return artist_object.get_bio_summary(language="en")
			except Exception:
				logging.exception(f"Last.fm bio lookup failed for '{attempt_artist}'")

		return ""
		# logging.info(artist_object.get_cover_image())
		# logging.info("\n\n")
		# logging.info(bio)
		# logging.info("\n\n")
		# logging.info(artist_object.get_bio_content())
		# return bio
		# else:
		#	return ""

	def love(self, artist: str, title: str) -> None:
		if not self.connected and self.prefs.auto_lfm:
			self.connect(False)
			self.prefs.scrobble_hold = True
		if self.connected and artist and title:
			track = self.network.get_track(artist, title)
			track.love()

	def unlove(self, artist: str, title: str) -> None:
		if not self.last_fm_enable:
			return
		if not self.connected and self.prefs.auto_lfm:
			self.connect(False)
			self.prefs.scrobble_hold = True
		if self.connected and artist and title:
			track = self.network.get_track(artist, title)
			track.love()
			track.unlove()

	def clear_friends_love(self) -> None:
		count = 0
		for index, tr in self.pctl.master_library.items():
			count += len(tr.lfm_friend_likes)
			tr.lfm_friend_likes.clear()

		self.show_message(_("Removed {N} loves.").format(N=count))

	def get_friends_love(self) -> None:
		if not self.last_fm_enable:
			return
		self.scanning_friends = True

		try:
			username = self.prefs.last_fm_username
			logging.info(f"Username is {username}")

			if not username:
				self.scanning_friends = False
				self.show_message(_("There was an error, try re-log in"))
				return

			if self.network is None:
				self.no_user_connect()

			self.network.enable_rate_limit()
			lastfm_user = self.network.get_user(username)
			friends = lastfm_user.get_friends(limit=None)
			self.show_message(_("Getting friend data..."), _("This may take a very long time."), mode="info")
			for friend in friends:
				self.scanning_username = friend.name
				logging.info(f"Getting friend loves: {friend.name}")

				try:
					loves = friend.get_loved_tracks(limit=None)
				except Exception:
					logging.exception("Failed to get_loved_tracks!")
					continue

				for track in loves:
					title = track.track.title.casefold()
					artist = track.track.artist.name.casefold()
					for index, tr in self.pctl.master_library.items():
						if tr.title.casefold() == title and tr.artist.casefold() == artist:
							tr.lfm_friend_likes.add(friend.name)
							logging.info("MATCH")
							logging.info(f"     {artist} - {title}")
							logging.info(f"      ----- {friend.name}")

		except Exception:
			logging.exception("There was an error getting friends loves")
			self.show_message(_("There was an error getting friends loves"), "", mode="warning")

		self.scanning_friends = False

	def dl_love(self) -> None:
		if not self.last_fm_enable:
			return
		username = self.prefs.last_fm_username
		self.show_message(_("Scanning loved tracks for: {username}").format(username=username), mode="info")
		self.scanning_username = username

		if not username:
			self.show_message(_("No username found"), mode="error")
			return

		if len(username) > 25:
			logging.error("Aborted due to long username")
			return

		self.scanning_loves = True

		logging.info("Connect for friend scan")

		try:
			if self.network is None:
				self.no_user_connect()

			self.network.enable_rate_limit()
			logging.info("Get user...")
			lastfm_user = self.network.get_user(username)
			tracks = lastfm_user.get_loved_tracks(limit=None)

			matches = 0
			updated = 0

			for track in tracks:
				title = track.track.title.casefold()
				artist = track.track.artist.name.casefold()

				for index, tr in self.pctl.master_library.items():
					if tr.title.casefold() == title and tr.artist.casefold() == artist:
						matches += 1
						logging.info("MATCH:")
						logging.info(f"     {artist} - {title}")
						star = self.star_store.full_get(index)
						if star is None:
							star = StarRecord()
						if not star.loved:
							updated += 1
							logging.info("     NEW LOVE")
							star.loved = True

						self.star_store.insert(index, star)

			self.scanning_loves = False
			if len(tracks) == 0:
				self.show_message(_("User has no loved tracks."))
				return
			if matches > 0 and updated == 0:
				self.show_message(_("{N} matched tracks are up to date.").format(N=str(matches)))
				return
			if matches > 0 and updated > 0:
				self.show_message(_("{N} tracks matched. {T} were updated.").format(N=str(matches), T=str(updated)))
				return
			self.show_message(_("Of {N} loved tracks, no matches were found in local db").format(N=str(len(tracks))))
			return
		except Exception:
			logging.exception("This doesn't seem to be working :(")
			self.show_message(_("This doesn't seem to be working :("), mode="error")
		self.scanning_loves = False

	def update(self, track_object: TrackClass) -> int | None:
		if not self.last_fm_enable:
			return None
		if self.prefs.scrobble_hold:
			return 0
		if self.prefs.auto_lfm:
			if self.connect(False) is False:
				self.prefs.auto_lfm = False
		else:
			return 0

		# logging.info('Updating Now Playing')

		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)

		try:
			if title and artist:
				self.network.update_now_playing(
					artist=artist, title=title, album=album)
				return 0
			logging.error("Not sent, incomplete metadata")
			return 0
		except Exception as e:
			logging.exception("Error connecting to last.fm.")
			if "retry" in str(e):
				return 2
				# self.show_message(_("Could not update Last.fm. ", str(e), mode='warning')
			self.pctl.b_time -= 5000
			return 1

class ListenBrainz:

	def __init__(
		self,
		tauon: _ScrobbleApp,
		copy_from_clipboard_fn: Callable[[], str],
		save_prefs_fn: Callable[[Any], None],
	) -> None:
		self.bag          = tauon.bag
		self.prefs        = tauon.prefs
		self.t_title      = tauon.t_title
		self.n_version    = tauon.n_version
		self.show_message = tauon.show_message
		self.copy_from_clipboard = copy_from_clipboard_fn
		self.save_prefs = save_prefs_fn
		self.enable       = tauon.prefs.enable_lb
		# self.url = "https://api.listenbrainz.org/1/submit-listens"

	def url(self) -> str:
		url = self.prefs.listenbrainz_url
		if not url:
			url = "https://api.listenbrainz.org/"
		if not url.endswith("/"):
			url += "/"
		return url + "1/submit-listens"

	def listen_full(self, track_object: TrackClass, time: int) -> bool | None:
		if self.enable is False:
			return True
		if self.prefs.scrobble_hold is True:
			return True
		if self.prefs.lb_token is None:
			self.show_message(_("ListenBrainz is enabled but there is no token."), _("How did this even happen."), mode="error")
			return None

		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)

		if title == "" or artist == "":
			return True

		data = {"listen_type": "single", "payload": []}
		metadata = {
			"track_name": title,
			**({"release_name": album} if album else {}),
			"artist_name": artist,
			}

		additional: dict[str, str] = {}

		# MusicBrainz Artist IDs
		if track_object.musicbrainz_artistids is not None:
			additional["artist_mbids"] = track_object.musicbrainz_artistids

		# MusicBrainz Release ID
		if track_object.musicbrainz_albumid is not None:
			additional["release_mbid"] = track_object.musicbrainz_albumid

		# MusicBrainz Recording ID
		if track_object.musicbrainz_recordingid is not None:
			additional["recording_mbid"] = track_object.musicbrainz_recordingid

		# MusicBrainz Track ID
		if track_object.musicbrainz_trackid is not None:
			additional["track_mbid"] = track_object.musicbrainz_trackid

		if additional:
			metadata["additional_info"] = additional

		# logging.info(additional)
		data["payload"].append({"track_metadata": metadata})
		data["payload"][0]["listened_at"] = time

		r = requests.post(self.url(), headers={"Authorization": "Token " + self.prefs.lb_token}, data=json.dumps(data), timeout=10)
		if r.status_code != 200:
			self.show_message(_("There was an error submitting data to ListenBrainz"), r.text, mode="warning")
			return False
		return True

	def listen_playing(self, track_object: TrackClass) -> None:
		if self.enable is False:
			return
		if self.prefs.scrobble_hold is True:
			return
		if self.prefs.lb_token is None:
			self.show_message(_("ListenBrainz is enabled but there is no token."), _("How did this even happen."), mode="error")
		title = track_object.title
		album = track_object.album
		artist = get_artist_strip_feat(track_object)

		if title == "" or artist == "":
			return

		data = {"listen_type": "playing_now", "payload": []}
		metadata = {
			"track_name": title,
			**({"release_name": album} if album else {}),
			"artist_name": artist,
			}

		additional: dict[str, str] = {}

		# MusicBrainz Artist IDs
		if track_object.musicbrainz_artistids is not None:
			additional["artist_mbids"] = track_object.musicbrainz_artistids

		# MusicBrainz Release ID
		if track_object.musicbrainz_albumid is not None:
			additional["release_mbid"] = track_object.musicbrainz_albumid

		# MusicBrainz Recording ID
		if track_object.musicbrainz_recordingid is not None:
			additional["recording_mbid"] = track_object.musicbrainz_recordingid

		# MusicBrainz Track ID
		if track_object.musicbrainz_trackid is not None:
			additional["track_mbid"] = track_object.musicbrainz_trackid

		if track_object.track_number:
			try:
				additional["tracknumber"] = str(int(track_object.track_number))
			except Exception:
				logging.exception("Error trying to get track_number")

		if track_object.length:
			additional["duration"] = str(int(track_object.length))

		additional["media_player"] = self.t_title
		additional["submission_client"] = self.t_title
		additional["media_player_version"] = str(self.n_version)

		metadata["additional_info"] = additional
		data["payload"].append({"track_metadata": metadata})
		# data["payload"][0]["listened_at"] = int(time.time())

		r = requests.post(self.url(), headers={"Authorization": "Token " + self.prefs.lb_token}, data=json.dumps(data), timeout=10)
		if r.status_code != 200:
			self.show_message(_("There was an error submitting data to ListenBrainz"), r.text, mode="warning")
			logging.error("There was an error submitting data to ListenBrainz")
			logging.error(r.status_code)
			logging.error(r.json())

	def paste_key(self) -> None:
		text = self.copy_from_clipboard()
		if text == "":
			self.show_message(_("There is no text in the clipboard"), mode="error")
			return

		if self.prefs.listenbrainz_url:
			self.prefs.lb_token = text
			return

		if len(text) == 36 and text[8] == "-":
			self.prefs.lb_token = text
		else:
			self.show_message(_("That is not a valid token."), mode="error")

	def clear_key(self) -> None:
		self.prefs.lb_token = ""
		self.save_prefs(self.bag)
		self.enable = False

class LastScrob:

	def __init__(self, tauon: _ScrobbleApp, pctl: _ScrobblePlayer) -> None:
		self.pctl    = pctl
		self.tauon   = tauon
		self.lb      = tauon.lb
		self.gui     = tauon.gui
		self.prefs   = tauon.prefs
		self.lastfm  = pctl.lastfm
		self.a_index = -1
		self.a_sc    = False
		self.a_pt    = False
		self.running = False
		self.queue: list[tuple[TrackClass, int, str]] = []

	def scrobble_allowed(self, track_object: TrackClass) -> bool:
		"""Whether Tauon may scrobble this track to Last.fm/ListenBrainz/Maloja.

		Lets the user disable scrobbling per streaming service when that service
		already scrobbles on its own (e.g. a Jellyfin plugin or an Airsonic/TIDAL
		account linked directly to Last.fm), avoiding double scrobbles.
		"""
		prefs = self.prefs
		ext = track_object.file_ext
		if ext == "JELY":
			return prefs.scrobble_jellyfin
		if ext == "TIDAL":
			return prefs.scrobble_tidal
		if ext == "SUB":
			return prefs.scrobble_subsonic
		if ext == "PLEX":
			return prefs.scrobble_plex
		return True

	def start_queue(self) -> None:
		self.running = True
		mini_t = threading.Thread(target=self.process_queue)
		mini_t.daemon = True
		mini_t.start()

	def process_queue(self) -> None:
		time.sleep(0.4)

		while self.queue:
			try:
				tr = self.queue.pop()

				self.gui.request_tracklist_redraw()
				logging.info(f"Submit Scrobble {tr[0].artist} - {tr[0].title}")

				success = True

				if tr[2] == "lfm" and self.prefs.auto_lfm and (self.lastfm.connected or self.lastfm.details_ready()):
					success = self.lastfm.scrobble(tr[0], tr[1])
				elif tr[2] == "lb" and self.lb.enable:
					success = self.lb.listen_full(tr[0], tr[1])
				elif tr[2] == "maloja":
					success = self.tauon.maloja_scrobble(tr[0], tr[1])
				elif tr[2] == "air":
					success = self.tauon.subsonic.listen(tr[0], submit=True)

				if not success:
					logging.info("Re-queue scrobble")
					self.queue.append(tr)
					time.sleep(10)
					break

			except Exception:
				logging.exception("SCROBBLE QUEUE ERROR")

		if not self.queue:
			self.tauon.scrobble_warning_timer.force_set(1000)

		self.running = False

	def update(self, add_time: float) -> None:
		if self.pctl.queue_step > len(self.pctl.track_queue) - 1:
			logging.info("Queue step error 1")
			return

		if self.a_index != self.pctl.track_queue[self.pctl.queue_step]:
			self.pctl.a_time = 0
			self.pctl.b_time = 0
			self.a_index = self.pctl.track_queue[self.pctl.queue_step]
			self.a_pt = False
			self.a_sc = False
		if self.pctl.playing_time == 0 and self.a_sc is True:
			logging.info("Reset scrobble timer")
			self.pctl.a_time = 0
			self.pctl.b_time = 0
			self.a_pt = False
			self.a_sc = False

		if self.pctl.a_time > 6 and self.a_pt is False and self.pctl.master_library[self.a_index].length > 30:
			self.a_pt = True
			self.listen_track(self.pctl.master_library[self.a_index])
			# if prefs.auto_lfm and (lastfm.connected or lastfm.details_ready()) and not prefs.scrobble_hold:
			#	 mini_t = threading.Thread(target=lastfm.update, args=([pctl.master_library[self.a_index]]))
			#	 mini_t.daemon = True
			#	 mini_t.start()
			#
			# if lb.enable and not prefs.scrobble_hold:
			#	 mini_t = threading.Thread(target=lb.listen_playing, args=([pctl.master_library[self.a_index]]))
			#	 mini_t.daemon = True
			#	 mini_t.start()

		if self.pctl.a_time > 6 and self.a_pt:
			self.pctl.b_time += add_time
			if self.pctl.b_time > 20:
				self.pctl.b_time = 0
				self.listen_track(self.pctl.master_library[self.a_index])

		send_full = False
		if self.pctl.master_library[self.a_index].length > 30 and self.pctl.a_time > self.pctl.master_library[self.a_index].length \
				* 0.50 and self.a_sc is False:
			self.a_sc = True
			send_full = True

		if self.a_sc is False and self.pctl.master_library[self.a_index].length > 30 and self.pctl.a_time > 240:
			self.a_sc = True
			send_full = True

		if send_full:
			self.scrob_full_track(self.pctl.master_library[self.a_index])

	def listen_track(self, track_object: TrackClass) -> None:
		# logging.info("LISTEN")

		if track_object.is_network and track_object.file_ext == "SUB":
			self.tauon.subsonic.listen(track_object, submit=False)

		if track_object.is_network and not self.scrobble_allowed(track_object):
			return

		if not self.prefs.scrobble_hold:
			if self.prefs.auto_lfm and (self.tauon.lastfm.connected or self.tauon.lastfm.details_ready()):
				mini_t = threading.Thread(target=self.tauon.lastfm.update, args=([track_object]))
				mini_t.daemon = True
				mini_t.start()

			if self.lb.enable:
				mini_t = threading.Thread(target=self.lb.listen_playing, args=([track_object]))
				mini_t.daemon = True
				mini_t.start()

	def scrob_full_track(self, track_object: TrackClass) -> None:
		# logging.info("SCROBBLE")
		track_object.lfm_scrobbles += 1
		self.gui.request_tracklist_redraw()

		if track_object.is_network:
			if track_object.file_ext == "SUB":
				self.queue.append((track_object, int(time.time()), "air"))

		if not self.scrobble_allowed(track_object):
			return

		if not self.prefs.scrobble_hold:
			if self.prefs.auto_lfm and (self.tauon.lastfm.connected or self.tauon.lastfm.details_ready()):
				self.queue.append((track_object, int(time.time()), "lfm"))
			if self.lb.enable:
				self.queue.append((track_object, int(time.time()), "lb"))
			if self.prefs.maloja_url and self.prefs.maloja_enable:
				self.queue.append((track_object, int(time.time()), "maloja"))
