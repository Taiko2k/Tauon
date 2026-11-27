# Copyright © 2026, Tauon contributors

from collections.abc import Callable

import mutagen
import pytest
from mutagen.mp4 import MP4FreeForm

from tauon.t_modules import t_main
from tauon.t_modules.t_tagscan import read_mp4_tags
from tauon.tests import test_tagedit

audio_files = test_tagedit.audio_files
make_audio = test_tagedit.make_audio


@pytest.mark.parametrize("case", [str.upper, str.lower, lambda name: name])
def test_mp4_freeform_tags_ignore_case(make_audio: Callable, case: Callable[[str], str]) -> None:
	# rsgain writes REPLAYGAIN_* in upper case (#2451)
	values = {
		"replaygain_track_gain": b"3.76 dB",
		"replaygain_track_peak": b"0.131104",
		"replaygain_album_gain": b"-1.50 dB",
		"replaygain_album_peak": b"0.5",
		"MusicBrainz Track Id": b"rec-id",
		"MusicBrainz Artist Id": b"artist-id",
		"DISCSUBTITLE": b"Side B",
		"SYNCEDLYRICS": b"[00:01.00]Hi",
	}
	path = make_audio("m4a")
	audio = mutagen.File(path)
	for name, value in values.items():
		audio.tags["----:com.apple.iTunes:" + case(name)] = [MP4FreeForm(value)]
	audio.save()

	track = t_main.TrackClass()
	read_mp4_tags(mutagen.File(path).tags, track)
	assert track.replaygain_track_gain == pytest.approx(3.76)
	assert track.replaygain_track_peak == pytest.approx(0.131104)
	assert track.replaygain_album_gain == pytest.approx(-1.5)
	assert track.replaygain_album_peak == pytest.approx(0.5)
	assert track.musicbrainz_recordingid == "rec-id"
	assert track.musicbrainz_artistids == ["artist-id"]
	assert track.disc_subtitle == "Side B"
	assert track.synced == "[00:01.00]Hi"
