# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

from types import SimpleNamespace

from tauon.t_modules.t_subsonic import SubsonicService

# OpenSubsonic songs carry comment, musicBrainzId and a replayGain object.


def _track() -> SimpleNamespace:
	return SimpleNamespace(
		comment="", musicbrainz_recordingid=None, musicbrainz_artistids=None, musicbrainz_albumid=None,
		replaygain_track_gain=None, replaygain_track_peak=None,
		replaygain_album_gain=None, replaygain_album_peak=None,
	)


def _apply(song: dict) -> SimpleNamespace:
	nt = _track()
	SubsonicService.__new__(SubsonicService)._apply_song_extras(nt, song)
	return nt


def test_maps_comment_mbids_and_replaygain() -> None:
	nt = _apply({
		"comment": "Remastered",
		"musicBrainzId": "rec-1",
		"artists": [{"id": "a1", "name": "A", "musicBrainzId": "art-1"}, {"id": "a2", "name": "B"}],
		"replayGain": {"trackGain": -7.5, "trackPeak": 0.98, "albumGain": -8.1, "albumPeak": 1.02},
	})
	assert nt.comment == "Remastered"
	assert nt.musicbrainz_recordingid == "rec-1"
	assert nt.musicbrainz_artistids == ["art-1"]
	assert (nt.replaygain_track_gain, nt.replaygain_track_peak) == (-7.5, 0.98)
	assert (nt.replaygain_album_gain, nt.replaygain_album_peak) == (-8.1, 1.02)


def test_plain_subsonic_song_leaves_fields_unset() -> None:
	nt = _apply({"id": "1", "title": "x"})
	assert nt.comment == ""
	assert nt.musicbrainz_recordingid is None
	assert nt.musicbrainz_artistids is None
	assert nt.replaygain_track_gain is None
	assert nt.replaygain_album_gain is None


def test_zero_placeholders_are_treated_as_missing() -> None:
	# Untagged files can come back as all zeros rather than omitted
	nt = _apply({"replayGain": {"trackGain": 0, "trackPeak": 0, "albumGain": 0, "albumPeak": 0}})
	assert nt.replaygain_track_gain is None
	assert nt.replaygain_track_peak is None
	assert nt.replaygain_album_gain is None
	assert nt.replaygain_album_peak is None


def test_real_zero_gain_with_peak_is_kept() -> None:
	nt = _apply({"replayGain": {"trackGain": 0, "trackPeak": 0.9}})
	assert (nt.replaygain_track_gain, nt.replaygain_track_peak) == (0.0, 0.9)


def test_album_only_replaygain() -> None:
	nt = _apply({"replayGain": {"albumGain": -6.0}})
	assert nt.replaygain_track_gain is None
	assert nt.replaygain_album_gain == -6.0
	assert nt.replaygain_album_peak is None


def test_junk_values_are_ignored() -> None:
	nt = _apply({
		"comment": 5, "musicBrainzId": "",
		"replayGain": {"trackGain": "nan", "trackPeak": "x", "albumGain": None, "albumPeak": -1},
	})
	assert nt.comment == ""
	assert nt.musicbrainz_recordingid is None
	assert nt.replaygain_track_gain is None
	assert nt.replaygain_track_peak is None
	assert nt.replaygain_album_gain is None
	assert nt.replaygain_album_peak is None
