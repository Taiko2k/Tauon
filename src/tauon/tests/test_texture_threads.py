"""SDL textures are only freed on the UI thread, and never while a caller still holds them."""

import logging
import threading
from queue import SimpleQueue
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tauon.t_modules import t_main, t_native
from tauon.t_modules.t_main import ArtistList, GallClass, StyleOverlay, Tauon


class Track:
	parent_folder_path = "/music/album"
	index = 7


@pytest.fixture
def destroyed(monkeypatch: pytest.MonkeyPatch) -> list:
	freed: list = []
	monkeypatch.setattr(t_native, "destroy_texture", freed.append)
	return freed


def run_in_thread(fn) -> None:
	thread = threading.Thread(target=fn)
	thread.start()
	thread.join()


def make_tauon(tmp_path, track: Track) -> Tauon:
	tauon = Tauon.__new__(Tauon)
	tauon.gui = MagicMock(halt_image_rendering=False)
	tauon.g_cache_directory = tmp_path
	tauon.gall_ren = SimpleNamespace(
		queue=[], key_list=[(track, 100, 0)], gall={(track, 100, 0): [3, None, "thumb", None]})
	tauon.album_art_gen = MagicMock()
	tauon.pending_image_clears = SimpleQueue()
	return tauon


def test_art_download_thread_defers_texture_frees(tmp_path, destroyed: list) -> None:
	track = Track()
	tauon = make_tauon(tmp_path, track)

	run_in_thread(lambda: tauon.clear_track_image_cache(track))
	assert destroyed == []
	tauon.album_art_gen.clear_cache.assert_not_called()
	assert (track, 100, 0) in tauon.gall_ren.gall

	tauon.drop_pending_image_clears()
	assert destroyed == ["thumb"]
	assert tauon.gall_ren.gall == {}
	assert tauon.gall_ren.key_list == []
	tauon.album_art_gen.clear_cache.assert_called_once()


def test_image_clear_on_ui_thread_is_immediate(tmp_path, destroyed: list) -> None:
	track = Track()
	tauon = make_tauon(tmp_path, track)

	tauon.clear_track_image_cache(track)
	assert destroyed == ["thumb"]
	assert tauon.pending_image_clears.empty()


def make_overlay() -> StyleOverlay:
	overlay = StyleOverlay.__new__(StyleOverlay)
	overlay.gui = MagicMock()
	overlay.thread_manager = MagicMock()
	overlay.min_on_timer = MagicMock()
	overlay.min_on_timer.get.return_value = -1
	overlay.a_texture = "front"
	overlay.b_texture = "back"
	overlay.surface = None
	overlay.textures_stale = False
	return overlay


def test_overlay_worker_flush_leaves_textures_to_display(destroyed: list) -> None:
	overlay = make_overlay()

	run_in_thread(overlay.flush)
	assert destroyed == []
	assert overlay.textures_stale

	overlay.display()
	assert destroyed == ["front", "back"]
	assert overlay.a_texture is None
	assert overlay.b_texture is None
	assert not overlay.textures_stale


def test_overlay_flush_on_ui_thread_is_immediate(destroyed: list) -> None:
	overlay = make_overlay()
	overlay.flush()
	assert destroyed == ["front", "back"]


def test_artist_thumb_invalidation_frees_texture_on_ui_thread(destroyed: list) -> None:
	box = ArtistList.__new__(ArtistList)
	box.gui = MagicMock()
	box.stale_thumbs = SimpleQueue()
	box.thumb_cache = {"Artist": ["texture", None], "Missing": None}

	run_in_thread(lambda: box.invalidate_thumb("Artist"))
	run_in_thread(lambda: box.invalidate_thumb("Missing"))
	assert "Artist" in box.thumb_cache
	assert destroyed == []

	box.drop_stale_thumbs()
	assert box.thumb_cache == {}
	assert destroyed == ["texture"]


def make_gallery(tracks: list[Track]) -> GallClass:
	gall = GallClass.__new__(GallClass)
	gall.tauon = SimpleNamespace(gallery_load_delay=SimpleNamespace(get=lambda: 1))
	gall.gui = MagicMock()
	gall.size = 100
	gall.folder_image_offsets = {}
	gall.frame = 0
	gall.frame_stamp = {}
	gall.frame_used = set()
	gall.limit = 2
	gall.key_list = []
	gall.gall = {
		(track, 100, 0): [3, None, f"tex{n}", SimpleNamespace(x=0, y=0, w=100, h=100), (1, 2, 3)]
		for n, track in enumerate(tracks)
	}
	return gall


def test_gallery_keeps_textures_handed_out_this_frame(destroyed: list) -> None:
	tracks = [Track(), Track(), Track()]
	gall = make_gallery(tracks)

	# Like the albumflow widget: collect more textures than the cache limit, then draw
	gall.new_frame()
	held = [gall.render(track, (0, 0), return_texture=True)[0] for track in tracks]
	assert held == ["tex0", "tex1", "tex2"]
	assert destroyed == []

	# Next frame the oldest unused entry can go
	gall.new_frame()
	gall.render(tracks[2], (0, 0), return_texture=True)
	assert destroyed == ["tex0"]
	assert (tracks[0], 100, 0) not in gall.gall


def test_destroy_texture_logs_off_ui_thread(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
	native = MagicMock()
	monkeypatch.setattr(t_native, "tauon_native", native)

	with caplog.at_level(logging.ERROR):
		t_native.destroy_texture("ui")
		assert not caplog.records
		run_in_thread(lambda: t_native.destroy_texture("worker"))

	assert [record.message for record in caplog.records] == ["destroy_texture called off the UI thread"]
	assert native.destroy_texture.call_count == 2


def test_main_module_frees_through_facade() -> None:
	# The checks above patch t_native; t_main must resolve it at call time
	assert t_main.sdl3 is t_native
