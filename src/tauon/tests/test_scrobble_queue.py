# Copyright © 2026, Tauon contributors

import json
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from xml.dom import minidom

import pytest
import requests

from tauon.t_modules import t_main
from tauon.t_modules.t_config import Config
from tauon.t_modules.t_extra import Timer
from tauon.t_modules.t_prefs import Prefs
from tauon.t_modules.t_scrobble_queue import QUEUE_FILENAME, Outcome, PendingScrobble, ScrobbleQueue
from tauon.t_modules.t_subsonic import SubsonicService

SENT, RETRY, DROP = Outcome.SENT, Outcome.RETRY, Outcome.DROP
DAY = 24 * 60 * 60


def make_prefs(directory: Path) -> Prefs:
	return Prefs(
		view_prefs={}, encoder_output=directory, window_opacity=1.0, ui_scale=1.0,
		power_save=False, discord_allow=False, left_window_control=False, macstyle=False,
		macos=False, phone=False, force_subpixel_text=False, desktop="",
	)


def make_scrobbler(directory: Path, prefs: Prefs | None = None) -> t_main.LastScrob:
	"""A scrobbler with Last.fm, Libre.fm and ListenBrainz on; every submit succeeds until told otherwise."""
	prefs = prefs or make_prefs(directory)
	prefs.lb_token = "token"
	prefs.maloja_enable = True
	prefs.maloja_url = "https://maloja.example"

	def service() -> SimpleNamespace:
		return SimpleNamespace(
			enabled=True, connected=True, details_ready=lambda: True, update=Mock(),
			submit_scrobbles=Mock(side_effect=lambda items: [SENT] * len(items)))

	lastfm = service()
	tauon = SimpleNamespace(
		prefs=prefs, lastfm=lastfm, librefm=service(), user_directory=directory,
		lb=SimpleNamespace(enable=True, submit_listens=Mock(side_effect=lambda items: [SENT] * len(items))),
		maloja_scrobble=Mock(return_value=SENT), subsonic=SimpleNamespace(submit_scrobble=Mock(return_value=SENT)),
		gui=SimpleNamespace(request_tracklist_redraw=Mock(), request_frame=Mock()), scrobble_warning_timer=Timer(1000),
	)
	return t_main.LastScrob(tauon, SimpleNamespace(lastfm=lastfm))


def make_track(title: str = "Song", index: int = 7) -> t_main.TrackClass:
	track = t_main.TrackClass()
	track.index = index
	track.artist = "Artist feat. Guest"
	track.album_artist = "Artist"
	track.title = title
	track.album = "Album"
	track.length = 201.6
	track.track_number = "3/12"
	track.musicbrainz_recordingid = "rec-id"
	track.musicbrainz_artistids = ["artist-id"]
	return track


def pending(service: str, title: str = "Song", age: int = 0) -> PendingScrobble:
	return PendingScrobble(service=service, timestamp=int(time.time()) - age, artist="Artist", title=title)


def on_disk(directory: Path) -> list[dict]:
	return json.loads((directory / QUEUE_FILENAME).read_text())["scrobbles"]


def test_queue_survives_restart(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.scrob_full_track(make_track())
	queued = [item.to_dict() for item in scrobbler.queue]
	assert [item["service"] for item in queued] == ["lfm", "libre", "lb", "maloja"]
	assert on_disk(tmp_path) == queued

	restarted = make_scrobbler(tmp_path)
	restarted.queue.load()
	assert [item.to_dict() for item in restarted.queue] == queued
	lfm = restarted.queue.pending("lfm")[0]
	assert (lfm.artist, lfm.duration, lfm.recording_mbid, lfm.track_id) == ("Artist", 201, "rec-id", 7)
	# Maloja gets the full artist string and splits it itself
	assert restarted.queue.pending("maloja")[0].artist == "Artist feat. Guest"

	restarted.send_due()
	assert not restarted.queue
	assert on_disk(tmp_path) == []
	# Sent with the original play time
	sent = restarted.tauon.lastfm.submit_scrobbles.call_args.args[0][0]
	assert sent.timestamp == queued[0]["timestamp"]


def test_unreadable_file_is_moved_aside(tmp_path: Path) -> None:
	(tmp_path / QUEUE_FILENAME).write_text("{not json")
	queue = ScrobbleQueue(tmp_path / QUEUE_FILENAME)
	queue.load()
	assert not queue
	assert (tmp_path / (QUEUE_FILENAME + ".bad")).read_text() == "{not json"


def test_transient_failure_keeps_scrobble_and_backs_off(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	submit = scrobbler.tauon.lb.submit_listens
	submit.side_effect = lambda items: [RETRY] * len(items)
	scrobbler.queue.add(pending("lb"), keep=True)

	scrobbler.send_due()
	assert len(scrobbler.queue) == 1
	assert len(on_disk(tmp_path)) == 1
	assert scrobbler.retry_delay["lb"] == 60
	assert 55 < scrobbler.next_retry_in() <= 60
	assert scrobbler.tauon.scrobble_warning_timer.get() < 260

	# Not retried before the backoff runs out
	scrobbler.send_due()
	assert submit.call_count == 1

	scrobbler.retry_at["lb"] = 0
	scrobbler.send_due()
	assert submit.call_count == 2
	assert scrobbler.retry_delay["lb"] == 120

	# A new play is tried straight away; success clears the backoff
	submit.side_effect = lambda items: [SENT] * len(items)
	scrobbler.queue.add(pending("lb", "Next"), keep=True)
	scrobbler.retry_at.pop("lb")
	scrobbler.send_due()
	assert not scrobbler.queue
	assert "lb" not in scrobbler.retry_delay
	assert scrobbler.next_retry_in() is None
	assert scrobbler.tauon.scrobble_warning_timer.get() > 260
	# Both went in one request
	assert len(submit.call_args.args[0]) == 2


def test_backoff_caps_at_fifteen_minutes(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.tauon.maloja_scrobble.return_value = RETRY
	scrobbler.queue.add(pending("maloja"), keep=True)
	delays = []
	for _attempt in range(6):
		scrobbler.retry_at.pop("maloja", None)
		scrobbler.send_due()
		delays.append(scrobbler.retry_delay["maloja"])
	assert delays == [60, 120, 240, 480, 900, 900]


def test_enqueue_skips_the_backoff(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.retry_at["lfm"] = time.time() + 600
	scrobbler.enqueue(make_track(), "lfm", int(time.time()))
	assert "lfm" not in scrobbler.retry_at


def test_one_service_failing_does_not_block_others(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.tauon.maloja_scrobble.return_value = RETRY
	scrobbler.scrob_full_track(make_track())
	scrobbler.send_due()
	assert [item.service for item in scrobbler.queue] == ["maloja"]


def test_permanent_rejection_drops_only_the_bad_scrobble(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)

	def submit(items: list[PendingScrobble]) -> list[Outcome]:
		# The service refuses the whole request if any listen is bad
		return [DROP if any(item.title == "Bad" for item in items) else SENT] * len(items)

	scrobbler.tauon.lb.submit_listens.side_effect = submit
	for title in ("One", "Bad", "Three"):
		scrobbler.queue.add(pending("lb", title), keep=True)

	scrobbler.send_due()
	calls = [[item.title for item in call.args[0]] for call in scrobbler.tauon.lb.submit_listens.call_args_list]
	assert calls == [["One", "Bad", "Three"], ["One"], ["Bad"], ["Three"]]
	assert not scrobbler.queue
	assert on_disk(tmp_path) == []
	assert "lb" not in scrobbler.retry_at


def test_lastfm_drops_scrobbles_older_than_fourteen_days(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.queue.add(pending("lfm", "Old", age=15 * DAY), keep=True)
	scrobbler.queue.add(pending("lfm", "Recent", age=13 * DAY), keep=True)
	scrobbler.queue.add(pending("libre", "Old", age=15 * DAY), keep=True)

	scrobbler.send_due()
	assert not scrobbler.queue
	sent = [item.title for item in scrobbler.tauon.lastfm.submit_scrobbles.call_args.args[0]]
	assert sent == ["Recent"]
	# Libre.fm has no such limit
	scrobbler.tauon.librefm.submit_scrobbles.assert_called_once()


def test_disabled_service_drops_its_scrobbles(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.queue.add(pending("lb"), keep=True)
	scrobbler.tauon.lb.enable = False
	scrobbler.send_due()
	assert not scrobbler.queue
	scrobbler.tauon.lb.submit_listens.assert_not_called()


def test_paused_scrobbling_holds_the_queue(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.queue.add(pending("lfm"), keep=True)
	scrobbler.prefs.scrobble_hold = True
	scrobbler.send_due()
	assert len(scrobbler.queue) == 1
	assert scrobbler.next_retry_in() is None
	scrobbler.prefs.scrobble_hold = False
	scrobbler.send_due()
	assert not scrobbler.queue


def test_clear(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.tauon.lastfm.submit_scrobbles.side_effect = lambda items: [RETRY] * len(items)
	scrobbler.scrob_full_track(make_track())
	scrobbler.clear_queue()
	assert not scrobbler.queue
	assert on_disk(tmp_path) == []

	restarted = make_scrobbler(tmp_path)
	restarted.queue.load()
	assert not restarted.queue


def test_setting_off_keeps_new_scrobbles_in_memory_only(tmp_path: Path) -> None:
	prefs = make_prefs(tmp_path)
	assert prefs.scrobble_offline_queue is True
	prefs.scrobble_offline_queue = False
	scrobbler = make_scrobbler(tmp_path, prefs)
	scrobbler.scrob_full_track(make_track())
	assert len(scrobbler.queue) == 4
	assert not (tmp_path / QUEUE_FILENAME).exists()

	# Switching on saves what is already waiting
	scrobbler.toggle_offline_queue()
	assert scrobbler.toggle_offline_queue(1) is True
	assert len(on_disk(tmp_path)) == 4


def test_setting_off_leaves_saved_scrobbles_alone(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	scrobbler.tauon.lb.submit_listens.side_effect = lambda items: [RETRY] * len(items)
	scrobbler.queue.add(pending("lb", "Saved"), keep=True)
	scrobbler.toggle_offline_queue()
	assert scrobbler.prefs.scrobble_offline_queue is False

	scrobbler.enqueue(make_track("Unsaved"), "lfm", int(time.time()))
	assert [item["title"] for item in on_disk(tmp_path)] == ["Saved"]

	# Once sent it leaves the file, so it is never sent twice
	scrobbler.tauon.lb.submit_listens.side_effect = lambda items: [SENT] * len(items)
	scrobbler.retry_at.clear()
	scrobbler.send_due()
	assert on_disk(tmp_path) == []


def test_incomplete_metadata_is_not_queued(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	track = make_track("")
	scrobbler.scrob_full_track(track)
	assert not scrobbler.queue


def test_prefs_round_trip(tmp_path: Path) -> None:
	def bag() -> SimpleNamespace:
		return SimpleNamespace(
			cf=Config(), prefs=make_prefs(tmp_path), dirs=SimpleNamespace(config_directory=tmp_path),
			windows=False, formats=SimpleNamespace(VID=set(), DA=set()), download_directories=[])

	first = bag()
	t_main.load_prefs(first)
	assert first.prefs.scrobble_offline_queue is True
	first.prefs.scrobble_offline_queue = False
	t_main.save_prefs(first)

	second = bag()
	t_main.load_prefs(second)
	assert second.prefs.scrobble_offline_queue is False


# --- Per-service submit functions ---


def lastfm_reply(*codes: str) -> minidom.Document:
	scrobbles = "".join(f'<scrobble><ignoredMessage code="{code}"></ignoredMessage></scrobble>' for code in codes)
	return minidom.parseString(f'<lfm status="ok"><scrobbles>{scrobbles}</scrobbles></lfm>')


def make_lastfm(tmp_path: Path) -> t_main.LastFMapi:
	tauon = SimpleNamespace(bag=SimpleNamespace(last_fm_enable=True), gui=None, prefs=make_prefs(tmp_path), show_message=Mock())
	api = t_main.LastFMapi(tauon, SimpleNamespace(star_store=None, master_library={}))
	api.connected = True
	api.network = object()
	return api


def test_lastfm_reads_ignored_scrobbles(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	api = make_lastfm(tmp_path)
	requests_made = []

	def fake_request(network: object, method: str, params: dict) -> SimpleNamespace:
		requests_made.append(params)
		return SimpleNamespace(execute=lambda: lastfm_reply("0", "3", "5"))

	monkeypatch.setattr(t_main.pylast, "_Request", fake_request)
	items = [pending("lfm", title) for title in ("Fine", "Too old", "Over the daily limit")]
	items[0].album, items[0].album_artist, items[0].duration, items[0].track_number = "Album", "Other", 200, "3/12"
	assert api.submit_scrobbles(items) == [SENT, DROP, RETRY]
	params = requests_made[0]
	assert params["track[2]"] == "Over the daily limit"
	assert params["timestamp[0]"] == items[0].timestamp
	assert (params["albumArtist[0]"], params["duration[0]"], params["trackNumber[0]"]) == ("Other", 200, 3)


@pytest.mark.parametrize(("status", "expected"), [("6", DROP), ("13", DROP), ("11", RETRY), ("9", RETRY), (503, RETRY)])
def test_lastfm_error_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: str | int, expected: Outcome) -> None:
	api = make_lastfm(tmp_path)

	def fail() -> None:
		raise t_main.pylast.WSError(None, status, "nope")

	monkeypatch.setattr(t_main.pylast, "_Request", lambda *args: SimpleNamespace(execute=fail))
	assert api.submit_scrobbles([pending("lfm"), pending("lfm")]) == [expected, expected]


def test_lastfm_network_error_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	api = make_lastfm(tmp_path)

	def fail() -> None:
		raise t_main.pylast.NetworkError(None, OSError("offline"))

	monkeypatch.setattr(t_main.pylast, "_Request", lambda *args: SimpleNamespace(execute=fail))
	assert api.submit_scrobbles([pending("lfm")]) == [RETRY]


def make_listenbrainz(tmp_path: Path) -> t_main.ListenBrainz:
	prefs = make_prefs(tmp_path)
	prefs.enable_lb = True
	prefs.lb_token = "token"
	tauon = SimpleNamespace(bag=None, prefs=prefs, t_title="Tauon", n_version="9.0", show_message=Mock())
	return t_main.ListenBrainz(tauon)


def test_listenbrainz_backlog_goes_in_as_import(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	lb = make_listenbrainz(tmp_path)
	posted = []
	monkeypatch.setattr(t_main.requests, "post", lambda url, **kwargs: posted.append(kwargs["json"]) or SimpleNamespace(status_code=200, text=""))

	fresh = pending("lb")
	assert lb.submit_listens([fresh]) == [SENT]
	assert posted[-1]["listen_type"] == "single"
	assert posted[-1]["payload"][0]["listened_at"] == fresh.timestamp

	backlog = [pending("lb", age=3 * DAY), pending("lb", age=DAY)]
	assert lb.submit_listens(backlog) == [SENT, SENT]
	assert posted[-1]["listen_type"] == "import"
	assert [listen["listened_at"] for listen in posted[-1]["payload"]] == [item.timestamp for item in backlog]

	# A single old listen is a backlog too
	lb.submit_listens([pending("lb", age=DAY)])
	assert posted[-1]["listen_type"] == "import"


@pytest.mark.parametrize(("status", "expected"), [(400, DROP), (401, RETRY), (429, RETRY), (502, RETRY)])
def test_listenbrainz_status_codes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, status: int, expected: Outcome) -> None:
	lb = make_listenbrainz(tmp_path)
	monkeypatch.setattr(t_main.requests, "post", lambda url, **kwargs: SimpleNamespace(status_code=status, text="error"))
	assert lb.submit_listens([pending("lb")]) == [expected]


def test_listenbrainz_offline_retries(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	lb = make_listenbrainz(tmp_path)

	def offline(url: str, **kwargs: object) -> None:
		raise requests.ConnectionError("offline")

	monkeypatch.setattr(t_main.requests, "post", offline)
	assert lb.submit_listens([pending("lb")]) == [RETRY]
	lb.show_message.assert_not_called()


def test_maloja_sends_play_time(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
	prefs = make_prefs(tmp_path)
	prefs.maloja_url = "https://maloja.example"
	tauon = SimpleNamespace(prefs=prefs, show_message=Mock())
	posted = []
	monkeypatch.setattr(t_main.requests, "post", lambda url, **kwargs: posted.append((url, kwargs["json"])) or SimpleNamespace(status_code=200, text=""))
	item = pending("maloja", age=DAY)
	assert t_main.Tauon.maloja_scrobble(tauon, item) is SENT
	url, data = posted[0]
	assert url == "https://maloja.example/apis/mlj_1/newscrobble"
	assert (data["time"], data["artists"], data["title"]) == (item.timestamp, ["Artist"], "Song")

	def offline(url: str, **kwargs: object) -> None:
		raise requests.ConnectionError("offline")

	monkeypatch.setattr(t_main.requests, "post", offline)
	assert t_main.Tauon.maloja_scrobble(tauon, item) is RETRY


@pytest.mark.parametrize(("reply", "expected"), [
	({"subsonic-response": {"status": "ok"}}, SENT),
	({"subsonic-response": {"status": "failed", "error": {"code": 70}}}, DROP),
	({"subsonic-response": {"status": "failed", "error": {"code": 40}}}, RETRY),
	(None, RETRY),
])
def test_subsonic_scrobble(reply: dict | None, expected: Outcome) -> None:
	subsonic = SubsonicService.__new__(SubsonicService)
	subsonic.r = Mock(return_value=reply)
	item = PendingScrobble(service="air", timestamp=1_700_000_000, artist="A", title="T", server_id="song-1")
	assert subsonic.submit_scrobble(item) is expected
	params = subsonic.r.call_args.kwargs["p"]
	assert params == {"id": "song-1", "submission": "true", "time": "1700000000000"}


def test_subsonic_offline_retries() -> None:
	subsonic = SubsonicService.__new__(SubsonicService)
	subsonic.r = Mock(side_effect=requests.ConnectionError("offline"))
	assert subsonic.submit_scrobble(pending("air")) is RETRY


# --- Settings rows ---


def test_settings_rows_show_live_count_and_clear(tmp_path: Path) -> None:
	scrobbler = make_scrobbler(tmp_path)
	gui = SimpleNamespace(message_box_confirm_callback=None, message_box_confirm_reference=None, message_box_no_callback=None)
	over = SimpleNamespace(tauon=SimpleNamespace(lfm_scrobbler=scrobbler), gui=gui, show_message=Mock())
	over.confirm_clear_scrobble_queue = lambda: t_main.Over.confirm_clear_scrobble_queue(over)

	def draw() -> Mock:
		rows = Mock()
		t_main.Over.settings_body_scrobbling(over, rows)
		return rows

	rows = draw()
	assert rows.switch.call_args.args[0] == scrobbler.toggle_offline_queue
	assert rows.readout.call_args.args[1] == "No scrobbles waiting"
	rows.action.assert_not_called()

	scrobbler.queue.add(pending("lfm"), keep=True)
	assert draw().readout.call_args.args[1] == "1 scrobble waiting"
	scrobbler.queue.add(pending("lb"), keep=True)
	rows = draw()
	assert rows.readout.call_args.args[1] == "2 scrobbles waiting"
	assert rows.action.call_args.kwargs["hint"] == "Last.fm 1, ListenBrainz 1"

	# Clear asks first, then empties the queue
	(_label, clear, _emphasis), = rows.action.call_args.args[1]
	clear()
	assert over.show_message.call_args.kwargs["mode"] == "confirm"
	assert len(scrobbler.queue) == 2
	gui.message_box_confirm_callback(*gui.message_box_confirm_reference)
	assert not scrobbler.queue
	assert on_disk(tmp_path) == []


def connect_sections(account_view: int) -> tuple[Mock, dict[str, t_main.SettingsSection]]:
	over = Mock(account_view=account_view, SCROBBLE_VIEWS=t_main.Over.SCROBBLE_VIEWS)
	groups = t_main.Over.build_settings_groups(over)
	connect = next(group for group in groups if group.key == "connect")
	return over, {section.key: section for section in connect.sections}


@pytest.mark.parametrize(("view", "shown"), [(0, False), (1, True), (13, True), (2, True), (9, True), (10, False), (4, False)])
def test_scrobbling_section_shows_only_for_scrobble_services(view: int, shown: bool) -> None:
	_over, sections = connect_sections(view)
	assert sections["scrobbling"].shown() is shown
	assert sections["account"].shown() is bool(view)


def test_hidden_section_is_skipped_on_the_page_but_surveyed(tmp_path: Path) -> None:
	over, sections = connect_sections(0)
	over.gui.scale = 1
	over.settings_doc_origin = 0
	over.settings_section_heights = {}
	over.settings_section_offsets = {("connect", "scrobbling"): 500}
	group = t_main.SettingsGroup("connect", "Connect", Mock(), [sections["services"], sections["scrobbling"]])

	over.settings_surveying = False
	t_main.Over.render_settings_group(over, group, 0, 0, 400)
	over.settings_body_scrobbling.assert_not_called()
	assert ("connect", "scrobbling") not in over.settings_section_offsets

	over.settings_surveying = True
	t_main.Over.render_settings_group(over, group, 0, 0, 400)
	over.settings_body_scrobbling.assert_called_once()


@pytest.mark.parametrize(("enabled", "opened"), [((), 1), ((2,), 2), ((9, 13), 13)])
def test_search_result_opens_a_scrobble_service(enabled: tuple[int, ...], opened: int) -> None:
	over, sections = connect_sections(0)
	over.settings_service_status = lambda view: (view in enabled, "")
	over.show_scrobble_service = lambda: t_main.Over.show_scrobble_service(over)
	group = t_main.SettingsGroup("connect", "Connect", Mock(), [t_main.SettingsSection(
		"scrobbling", "Scrobbling", Mock(), shown=sections["scrobbling"].shown, reveal=over.show_scrobble_service)])
	over.settings_group = lambda key: group
	entry = t_main.SettingsEntry("Keep scrobbles while offline", "", "", "connect", "scrobbling", "Scrobbling")

	t_main.Over.settings_go_to(over, "key", entry)
	over.select_account_view.assert_called_once_with(opened)

	# Already showing: stays on the open service
	over.account_view = 2
	over.select_account_view.reset_mock()
	t_main.Over.settings_go_to(over, "key", entry)
	over.select_account_view.assert_not_called()
