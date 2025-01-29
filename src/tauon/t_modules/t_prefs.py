from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pathlib import Path

	import gi
	gi.require_version("Gtk", "3.0")
	from gi.repository import Gtk

class Prefs:
	"""Used to hold any kind of settings"""

	def __init__(
		self, *, user_directory: Path, music_directory: Path | None, cache_directory: Path,
		macos: bool, phone: bool, left_window_control: bool, detect_macstyle: bool,
		gtk_settings: Gtk.Settings | None, discord_allow: bool,
		flatpak_mode: bool, desktop: str | None, window_opacity: float, scale: float,
	) -> None:
		self.colour_from_image:       bool = False
		self.dim_art:                 bool = False
		self.prefer_side:             bool = True  # Saves whether side panel is shown or not
		self.pause_fade_time:          int = 400
		self.change_volume_fade_time:  int = 400
		self.cross_fade_time:          int = 700
		self.volume_wheel_increment:   int = 2
		self.encoder_output:          Path = user_directory / "encoder"
		if music_directory is not None:
			self.encoder_output:        Path = music_directory / "encode-output"
		self.rename_folder_template:   str = "<albumartist> - <album>"
		self.rename_tracks_template:   str = "<tn>. <artist> - <title>.<ext>"

		self.enable_web:   bool = False
		self.allow_remote: bool = False
		self.expose_web:   bool = True

		self.enable_transcode:    bool = True
		self.show_rym:            bool = False
		self.show_band:           bool = False
		self.show_wiki:           bool = False
		self.show_transfer:       bool = True
		self.show_queue:          bool = True
		self.prefer_bottom_title: bool = True
		self.append_date:         bool = True

		self.transcode_codec:   str = "opus"
		self.transcode_mode:    str = "single"
		self.transcode_bitrate: int = 64

		# self.line_style: int = 1
		self.device:      int = 1
		self.device_name: str = ""

		self.cache_gallery:           bool = True
		self.gallery_row_scroll:      bool = True
		self.gallery_scroll_wheel_px: int = 90

		self.playlist_font_size:  int = 15
		self.playlist_row_height: int = 27

		self.tag_editor_name:   str = ""
		self.tag_editor_target: str = ""
		self.tag_editor_path:   str = ""

		self.use_title:    bool = False
		self.auto_extract: bool = False
		self.auto_del_zip: bool = False
		self.pl_thumb:     bool = False

		self.use_custom_fonts:          bool = False
		self.linux_font:                str = "Noto Sans, Noto Sans CJK JP, Arial,"
		self.linux_font_semibold:       str = "Noto Sans, Noto Sans CJK JP, Arial, Medium"
		self.linux_font_bold:           str = "Noto Sans, Noto Sans CJK JP, Bold"
		self.linux_font_condensed:      str = "Noto Sans, Extra-Condensed"
		self.linux_font_condensed_bold: str = "Noto Sans, Extra-Condensed Bold"

		self.spec2_scroll: bool = True

		self.spec2_p_base:     list[float] = [10, 10, 100]
		self.spec2_p_multiply: list[float] = [0.5, 1, 1]

		self.spec2_base:           list[float] = [10, 10, 100]
		self.spec2_multiply:       list[float] = [0.5, 1, 1]
		self.spec2_colour_setting: str = "custom"

		self.auto_lfm:      bool = False
		self.scrobble_mark: bool = False
		self.enable_mpris:  bool = True

		self.replay_gain:       int  = 0  # 0=off 1=track 2=album
		self.replay_preamp:     int  = 0  # db
		self.radio_page_lyrics: bool = True

		self.show_gimage:      bool = False
		self.end_setting:      str  = "stop"
		self.show_gen:         bool = False
		self.show_lyrics_side: bool = True

		self.log_vol: bool = False

		self.ui_scale: float = scale

		# if flatpak_mode:

		self.transcode_opus_as: bool = False

		self.discord_active:     bool = False
		self.discord_ready:      bool = False
		self.disconnect_discord: bool = False

		self.monitor_downloads: bool = True
		self.extract_to_music:  bool = False

		self.enable_lb: bool = False
		self.lb_token:  str  = ""

		self.use_jump_crossfade:       bool = True
		self.use_transition_crossfade: bool = False
		self.use_pause_fade:           bool = True

		self.show_notifications: bool = True

		self.true_shuffle:      bool = True
		self.append_total_time: bool = False
		self.backend:           int  = 4  # 2 gstreamer, 4 phazor

		self.album_repeat_mode:  bool = False  # passed to pctl
		self.album_shuffle_mode: bool = False  # passed to pctl

		self.finish_current: bool = False  # Finish current album when adding to queue

		self.reload_play_state: bool = False  # Resume playback on app restart
		self.resume_play_wake:  bool = False  # Resume playback on wake
		self.reload_state: tuple[int, float] | None = None

		self.mono: bool = False

		self.last_fm_token = None
		self.last_fm_username = ""

		self.use_card_style = True

		self.plex_username = ""
		self.plex_password = ""
		self.plex_servername = ""

		self.koel_username = "admin@example.com"
		self.koel_password = "admin"
		self.koel_server_url = "http://localhost:8050"

		self.auto_lyrics = False  # Function has been disabled
		self.jelly_username = ""
		self.jelly_password = ""
		self.jelly_server_url = "http://localhost:8096"

		self.auto_lyrics_checked = []

		self.show_side_art = True
		self.always_pin_playlists = True

		self.user_directory:  Path = user_directory
		self.cache_directory: Path = cache_directory

		self.window_opacity = window_opacity
		self.gallery_single_click = True
		self.custom_bg_opacity = 40

		self.tabs_on_top = True
		self.desktop = desktop

		self.dc_device = False  # (BASS) Disconnect device on pause
		if desktop == "KDE":
			self.dc_device = True

		self.showcase_vis = True
		self.show_lyrics_showcase = True

		self.spec2_colour_mode = 0
		self.flatpak_mode = flatpak_mode

		self.device_buffer = 80

		self.eq = [0.0] * 10
		self.use_eq = False

		self.bio_large = False
		self.discord_allow = discord_allow
		self.discord_show = False

		self.min_to_tray = False

		self.guitar_chords = False
		self.prefer_synced_lyrics = True
		self.sync_lyrics_time_offset = 0

		self.playback_follow_cursor = False
		self.short_buffer = False

		self.gst_output = "rgvolume pre-amp=-2 fallback-gain=-6 ! autoaudiosink"

		self.art_bg = False
		self.art_bg_stronger = 1
		self.art_bg_opacity = 10
		self.art_bg_blur = 9
		self.art_bg_always_blur = False

		self.random_mode = False
		self.repeat_mode = False

		self.failed_artists = []
		self.failed_background_artists = []

		self.artist_list = False
		self.auto_sort = False

		self.transcode_inplace = False

		self.bg_showcase_only = False

		self.lyrics_enables = []

		self.fatvap = "6b2a9499238ce6416783fc8129b8ac67"

		self.fanart_notify = True
		self.discogs_pat = ""

		self.artist_list_prefer_album_artist = True

		self.mini_mode_mode = 0
		self.dc_device_setting = "on"

		self.download_dir1 = ""
		self.dd_index = False

		self.metadata_page_port = 7590

		self.custom_encoder_output = ""
		self.column_aa_fallback_artist = False

		self.meta_persists_stop = False
		self.meta_shows_selected = False
		self.meta_shows_selected_always = False

		self.left_align_album_artist_title = False
		self.stop_notifications_mini_mode = False
		self.scale_want = 1
		self.x_scale = True
		self.hide_queue = True
		self.show_playlist_list = True
		self.thin_gallery_borders = False
		self.show_current_on_transition = False

		self.force_subpixel_text = False
		if gtk_settings and gtk_settings.get_property("gtk-xft-rgba") == "rgb":
			self.force_subpixel_text = True

		self.chart_rows = 3
		self.chart_columns = 3
		self.chart_bg = [7, 7, 7]
		self.chart_text = True
		self.chart_font = "Monospace 10"
		self.chart_tile = False

		self.chart_cascade = False
		self.chart_c1 = 5
		self.chart_c2 = 6
		self.chart_c3 = 10
		self.chart_d1 = 2
		self.chart_d2 = 2
		self.chart_d3 = 2

		self.art_in_top_panel = True
		self.always_art_header = False

		# self.center_bg = True
		self.ui_lang: str = "auto"
		self.side_panel_layout = 0
		self.use_absolute_track_index = False

		self.hide_bottom_title = True
		self.auto_goto_playing = False

		self.diacritic_search = True
		self.increase_gallery_row_spacing = False
		self.center_gallery_text = False

		self.tracklist_y_text_offset = 0
		self.theme_name = "Turbo"
		self.left_panel_mode = "playlist"

		self.folder_tree_codec_colours = False

		self.network_stream_bitrate = 0  # 0 is off

		self.show_side_lyrics_art_panel = True

		self.gst_use_custom_output = False

		self.notify_include_album = True

		self.auto_dl_artist_data = False

		self.enable_fanart_artist = False
		self.enable_fanart_bg = False
		self.enable_fanart_cover = False

		self.always_auto_update_playlists = False

		self.subsonic_server = "http://localhost:4040"
		self.subsonic_user = ""
		self.subsonic_password = ""
		self.subsonic_password_plain = False

		self.subsonic_playlists = {}

		self.write_ratings = False
		self.rating_playtime_stars = False

		self.lyrics_subs = {}

		self.radio_urls = []

		self.lyric_metadata_panel_top = False
		self.showcase_overlay_texture = False

		self.sync_target = ""
		self.sync_deletes = False
		self.sync_playlist: int | None = None
		self.download_playlist: int | None = None

		self.sep_genre_multi = False
		self.topchart_sorts_played = True

		self.spot_client = ""
		self.spot_secret = ""
		self.spot_username = ""
		self.spot_password = ""
		self.spot_mode = False
		self.launch_spotify_web = False
		self.launch_spotify_local = False
		self.remove_network_tracks = False
		self.bypass_transcode = False
		self.force_hide_max_button = False
		self.zoom_art = False
		self.auto_rec = False
		self.radio_record_codec = "OPUS"
		self.pa_fast_seek = False
		self.precache = False
		# TODO(Martin): cache_list isn't really used anywhere and will always be empty?
		self.cache_list: list[str] = []
		self.cache_limit = 2000  # in mb
		self.save_window_position = True
		self.spotify_token = ""
		self.always_ffmpeg = False

		self.use_libre_fm = False
		self.back_restarts = False

		self.old_playlist_box_position = 0
		self.listenbrainz_url = ""
		self.maloja_enable = False
		self.maloja_url = ""
		self.maloja_key = ""

		self.scrobble_hold = False

		self.artist_list_sort_mode = "alpha"

		self.phazor_device_selected = "Default"
		self.phazor_devices = ["Default"]
		self.bg_flips = set()
		self.use_tray = False
		self.tray_show_title = False
		self.drag_to_unpin = True
		self.enable_remote = False

		self.artist_list_style = 1
		self.discord_enable = False
		self.stop_end_queue = False

		self.block_suspend = False
		self.smart_bypass = True
		self.seek_interval = 15
		self.shuffle_lock = False
		self.album_shuffle_lock_mode = False
		self.premium = False
		self.power_save = False
		if macos or phone:
			self.power_save = True
		self.left_window_control = macos or left_window_control
		self.macstyle = macos or detect_macstyle
		self.radio_thumb_bans = []
		self.show_nag = False

		self.playlist_exports = {}
		self.show_chromecast = False

		self.samplerate = 48000
		self.resample = 1
		self.volume_power = 2

		self.tmp_cache = True

		self.sat_url = ""
		self.lyrics_font_size = 15

		self.use_gamepad = True
		self.avoid_resampling = False
		self.use_scancodes = False

		self.artist_list_threshold = 4
		self.allow_video_formats = True
		self.mini_mode_on_top = True
		self.tray_theme = "pink"

		self.lastfm_pull_love = False
		self.row_title_format = 1
		self.row_title_genre = False
		self.row_title_separator_type = 1
		self.search_on_letter = True

		self.gallery_combine_disc = False
		self.pipewire = False
		self.tidal_quality = 1
