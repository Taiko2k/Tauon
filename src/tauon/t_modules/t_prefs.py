from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pathlib import Path

@dataclass
class Prefs:
	"""Used to hold any kind of settings"""

	view_prefs:              dict[str, bool]
	encoder_output:          Path
	window_opacity:          float
	ui_scale:                float
	power_save:              bool
	discord_allow:           bool
	left_window_control:     bool
	macstyle:                bool
	macos:                   bool
	phone:                   bool
	force_subpixel_text:     bool
	dc_device:               bool
	desktop:                 str
	album_mode:              bool = False
	colour_from_image:       bool = False
	dim_art:                 bool = False
	prefer_side:             bool = True  # Saves whether side panel is shown or not
	pause_fade_time:          int = 400
	change_volume_fade_time:  int = 400
	cross_fade_time:          int = 700
	volume_wheel_increment:   int = 2
	rename_folder_template:   str = "<albumartist> - <album>"
	rename_tracks_template:   str = "<tn>. <artist> - <title>.<ext>"

	enable_web:   bool = False
	allow_remote: bool = False
	expose_web:   bool = True

	enable_transcode:    bool = True
	show_rym:            bool = False
	show_band:           bool = False
	show_wiki:           bool = False
	show_transfer:       bool = True
	show_queue:          bool = True
	prefer_bottom_title: bool = True
	append_date:         bool = True

	update_title:  bool = False
	scroll_enable: bool = True
	break_enable:  bool = True

	transcode_codec:   str = "opus"
	transcode_mode:    str = "single"
	transcode_bitrate: int = 64

	#line_style: int = 1
	device:      int = 1
	device_name: str = ""

	cache_gallery:           bool = True
	gallery_row_scroll:      bool = True
	gallery_scroll_wheel_px: int = 90

	playlist_font_size:  int = 15
	playlist_row_height: int = 27

	tag_editor_name:   str = ""
	tag_editor_target: str = ""
	tag_editor_path:   str = ""

	use_title:    bool = False
	auto_extract: bool = False
	auto_del_zip: bool = False
	pl_thumb:     bool = False

	use_custom_fonts:          bool = False
	linux_font:                str = "Noto Sans, Noto Sans CJK JP, Arial,"
	linux_font_semibold:       str = "Noto Sans, Noto Sans CJK JP, Arial, Medium"
	linux_font_bold:           str = "Noto Sans, Noto Sans CJK JP, Bold"
	linux_font_condensed:      str = "Noto Sans, Extra-Condensed"
	linux_font_condensed_bold: str = "Noto Sans, Extra-Condensed Bold"

	spec2_scroll: bool = True

	spec2_p_base:     list[float] = field(default_factory=lambda: [10, 10, 100])
	spec2_p_multiply: list[float] = field(default_factory=lambda: [0.5, 1, 1])

	spec2_base:           list[float] = field(default_factory=lambda: [10, 10, 100])
	spec2_multiply:       list[float] = field(default_factory=lambda: [0.5, 1, 1])
	spec2_colour_setting: str = "custom"

	auto_lfm:      bool = False
	scrobble_mark: bool = False
	enable_mpris:  bool = True

	replay_gain:       int  = 0  # 0=off 1=track 2=album
	replay_preamp:     int  = 0  # db
	radio_page_lyrics: bool = True

	show_gimage:      bool = False
	end_setting:      str  = "stop"
	show_gen:         bool = False
	show_lyrics_side: bool = True

	log_vol: bool = False

	transcode_opus_as: bool = False

	discord_active:     bool = False
	discord_ready:      bool = False
	disconnect_discord: bool = False

	monitor_downloads: bool = True
	extract_to_music:  bool = False

	enable_lb: bool = False
	lb_token:  str  = ""

	use_jump_crossfade:       bool = True
	use_transition_crossfade: bool = False
	use_pause_fade:           bool = True

	show_notifications: bool = True

	true_shuffle:      bool = True
	append_total_time: bool = False
	backend:           int  = 4  # 2 gstreamer, 4 phazor

	album_repeat_mode:  bool = False  # passed to pctl
	album_shuffle_mode: bool = False  # passed to pctl

	finish_current: bool = False  # Finish current album when adding to queue

	reload_play_state: bool = False  # Resume playback on app restart
	resume_play_wake:  bool = False  # Resume playback on wake
	reload_state: tuple[int, float] | None = None

	mono: bool = False

	last_fm_token = None
	last_fm_username = ""

	use_card_style = True

	plex_username = ""
	plex_password = ""
	plex_servername = ""

	koel_username = "admin@example.com"
	koel_password = "admin"
	koel_server_url = "http://localhost:8050"

	auto_lyrics = False  # Function has been disabled
	jelly_username = ""
	jelly_password = ""
	jelly_server_url = "http://localhost:8096"

	auto_lyrics_checked: list = field(default_factory=list)

	show_side_art = True
	always_pin_playlists = True

	gallery_single_click = True
	custom_bg_opacity = 40

	tabs_on_top = True

	showcase_vis = True
	show_lyrics_showcase = True

	spec2_colour_mode = 0

	device_buffer = 80

	eq = [0.0] * 10
	use_eq = False

	bio_large = False
	discord_show = False

	min_to_tray = False

	guitar_chords = False
	prefer_synced_lyrics = True
	sync_lyrics_time_offset = 0

	playback_follow_cursor = False
	short_buffer = False

	gst_output = "rgvolume pre-amp=-2 fallback-gain=-6 ! autoaudiosink"

	art_bg = False
	art_bg_stronger = 1
	art_bg_opacity = 10
	art_bg_blur = 9
	art_bg_always_blur = False

	random_mode = False
	repeat_mode = False

	failed_artists: list = field(default_factory=list)
	failed_background_artists: list = field(default_factory=list)

	artist_list = False
	auto_sort = False

	transcode_inplace = False

	bg_showcase_only = False

	lyrics_enables: list = field(default_factory=list)

	fatvap = "6b2a9499238ce6416783fc8129b8ac67"

	fanart_notify = True
	discogs_pat = ""

	artist_list_prefer_album_artist = True

	mini_mode_mode = 0
	dc_device_setting = "on"

	download_dir1 = ""
	dd_index = False

	metadata_page_port = 7590

	custom_encoder_output = ""
	column_aa_fallback_artist = False

	meta_persists_stop = False
	meta_shows_selected = False
	meta_shows_selected_always = False

	left_align_album_artist_title = False
	stop_notifications_mini_mode = False
	scale_want = 1
	x_scale = True
	hide_queue = True
	show_playlist_list = True
	thin_gallery_borders = False
	show_current_on_transition = False

	chart_rows = 3
	chart_columns = 3
	chart_bg: list[int] = field(default_factory=lambda: [7, 7, 7])
	chart_text = True
	chart_font = "Monospace 10"
	chart_tile = False

	chart_cascade = False
	chart_c1 = 5
	chart_c2 = 6
	chart_c3 = 10
	chart_d1 = 2
	chart_d2 = 2
	chart_d3 = 2

	art_in_top_panel = True
	always_art_header = False

	# center_bg = True
	ui_lang: str = "auto"
	side_panel_layout = 0
	use_absolute_track_index = False

	hide_bottom_title = True
	auto_goto_playing = False

	diacritic_search = True
	increase_gallery_row_spacing = False
	center_gallery_text = False

	tracklist_y_text_offset = 0
	theme: int = 7
	theme_name = "Turbo"
	transparent_mode: int = 0
	left_panel_mode = "playlist"

	folder_tree_codec_colours = False

	network_stream_bitrate = 0  # 0 is off

	show_side_lyrics_art_panel = True

	gst_use_custom_output = False

	notify_include_album = True

	auto_dl_artist_data = False

	enable_fanart_artist = False
	enable_fanart_bg = False
	enable_fanart_cover = False

	always_auto_update_playlists = False

	subsonic_server = "http://localhost:4040"
	subsonic_user = ""
	subsonic_password = ""
	subsonic_password_plain = False

	subsonic_playlists = {}

	write_ratings = False
	rating_playtime_stars = False

	lyrics_subs = {}

	radio_urls: list = field(default_factory=list)

	lyric_metadata_panel_top = False
	showcase_overlay_texture = False

	sync_target = ""
	sync_deletes = False
	sync_playlist: int | None = None
	download_playlist: int | None = None

	sep_genre_multi = False
	topchart_sorts_played = True

	spot_client = ""
	spot_secret = ""
	spot_username = ""
	spot_password = ""
	spot_mode = False
	launch_spotify_web = False
	launch_spotify_local = False
	remove_network_tracks = False
	bypass_transcode = False
	force_hide_max_button = False
	zoom_art = False
	auto_rec = False
	radio_record_codec = "OPUS"
	pa_fast_seek = False
	precache = False
	# TODO(Martin): cache_list isn't really used anywhere and will always be empty?
	cache_list: list[str] = field(default_factory=list)
	cache_limit = 2000  # in mb
	save_window_position = True
	spotify_token = ""
	always_ffmpeg = False

	use_libre_fm = False
	back_restarts = False

	old_playlist_box_position = 0
	listenbrainz_url = ""
	maloja_enable = False
	maloja_url = ""
	maloja_key = ""

	scrobble_hold = False

	artist_list_sort_mode = "alpha"

	phazor_device_selected = "Default"
	phazor_devices = ["Default"]
	bg_flips = set()
	use_tray = False
	tray_show_title = False
	drag_to_unpin = True
	enable_remote = False

	artist_list_style = 1
	discord_enable = False
	stop_end_queue = False

	block_suspend = False
	smart_bypass = True
	seek_interval = 15
	shuffle_lock = False
	album_shuffle_lock_mode = False
	premium = False
	radio_thumb_bans: list = field(default_factory=list)
	show_nag = False

	playlist_exports = {}
	show_chromecast = False

	samplerate = 48000
	resample = 1
	volume_power = 2

	tmp_cache = True

	sat_url = ""
	lyrics_font_size = 15

	use_gamepad = True
	avoid_resampling = False
	use_scancodes = False

	artist_list_threshold = 4
	allow_video_formats = True
	mini_mode_on_top = True
	tray_theme = "pink"

	lastfm_pull_love = False
	row_title_format = 1
	row_title_genre = False
	row_title_separator_type = 1
	search_on_letter = True

	gallery_combine_disc = False
	pipewire = False
	tidal_quality = 1

	jump_start = True
