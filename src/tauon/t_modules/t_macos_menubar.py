from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import AppKit
import objc

from tauon.t_modules.t_enums import PlayingState

if TYPE_CHECKING:
	from tauon.t_modules.t_main import Tauon


def _menu_state(active: bool) -> int:
	return AppKit.NSControlStateValueOn if active else AppKit.NSControlStateValueOff


class _MenuTarget(AppKit.NSObject):

	def initWithController_(self, controller: MacMenuBar) -> _MenuTarget | None:
		self = objc.super(_MenuTarget, self).init()
		if self is None:
			return None
		self.controller = controller
		return self

	@objc.IBAction
	def openSettings_(self, _: object) -> None:
		self.controller.open_settings()

	@objc.IBAction
	def openTracksArt_(self, _: object) -> None:
		self.controller.open_tracks_art()

	@objc.IBAction
	def importFolderToCurrentPlaylist_(self, _: object) -> None:
		self.controller.import_folder_to_current_playlist()

	@objc.IBAction
	def clearCurrentPlaylist_(self, _: object) -> None:
		self.controller.clear_current_playlist()

	@objc.IBAction
	def openGallery_(self, _: object) -> None:
		self.controller.open_gallery()

	@objc.IBAction
	def openTracksOnly_(self, _: object) -> None:
		self.controller.open_tracks_only()

	@objc.IBAction
	def openShowcase_(self, _: object) -> None:
		self.controller.open_showcase()

	@objc.IBAction
	def openRadio_(self, _: object) -> None:
		self.controller.open_radio()

	@objc.IBAction
	def toggleColumns_(self, _: object) -> None:
		self.controller.toggle_columns()

	@objc.IBAction
	def setTrackShuffle_(self, _: object) -> None:
		self.controller.set_track_shuffle()

	@objc.IBAction
	def setAlbumShuffle_(self, _: object) -> None:
		self.controller.set_album_shuffle()

	@objc.IBAction
	def setShuffleOff_(self, _: object) -> None:
		self.controller.set_shuffle_off()

	@objc.IBAction
	def setRepeatTrack_(self, _: object) -> None:
		self.controller.set_repeat_track()

	@objc.IBAction
	def setRepeatAlbum_(self, _: object) -> None:
		self.controller.set_repeat_album()

	@objc.IBAction
	def setRepeatOff_(self, _: object) -> None:
		self.controller.set_repeat_off()

	@objc.IBAction
	def setShuffleLockdown_(self, _: object) -> None:
		self.controller.set_shuffle_lockdown()

	@objc.IBAction
	def setShuffleLockdownAlbums_(self, _: object) -> None:
		self.controller.set_shuffle_lockdown_albums()

	@objc.IBAction
	def exitShuffleLockdown_(self, _: object) -> None:
		self.controller.exit_shuffle_lockdown()

	@objc.IBAction
	def play_(self, _: object) -> None:
		self.controller.play()

	@objc.IBAction
	def pause_(self, _: object) -> None:
		self.controller.pause()

	@objc.IBAction
	def stop_(self, _: object) -> None:
		self.controller.stop()

	@objc.IBAction
	def loveTrack_(self, _: object) -> None:
		self.controller.love_track()

	@objc.IBAction
	def randomTrack_(self, _: object) -> None:
		self.controller.random_track()

	@objc.IBAction
	def radioRandom_(self, _: object) -> None:
		self.controller.radio_random()

	@objc.IBAction
	def goToPlaying_(self, _: object) -> None:
		self.controller.go_to_playing()

	@objc.IBAction
	def openAbout_(self, _: object) -> None:
		self.controller.open_about()

	@objc.IBAction
	def openOnlineManual_(self, _: object) -> None:
		self.controller.open_online_manual()

	def menuNeedsUpdate_(self, _: AppKit.NSMenu) -> None:
		self.controller.refresh_states()

	def menuWillOpen_(self, _: AppKit.NSMenu) -> None:
		self.controller.refresh_states()


class MacMenuBar:

	def __init__(self, tauon: Tauon) -> None:
		self.tauon = tauon
		self.target = _MenuTarget.alloc().initWithController_(self)
		self.installed = False
		self.items: dict[str, AppKit.NSMenuItem] = {}

	def install(self) -> bool:
		if self.installed:
			self.refresh_states()
			return True

		app = AppKit.NSApp() or AppKit.NSApplication.sharedApplication()
		main_menu = app.mainMenu()
		if main_menu is None:
			main_menu = AppKit.NSMenu.alloc().initWithTitle_("")
			app.setMainMenu_(main_menu)

		self._install_app_menu(main_menu)
		self._install_menu(
			main_menu,
			"File",
			[
				(
					"file_import_folder_to_current_playlist",
					"Import Folder to Current Playlist",
					"importFolderToCurrentPlaylist:",
					"",
					0,
				),
				(
					"file_clear_current_playlist",
					"Clear Current Playlist",
					"clearCurrentPlaylist:",
					"",
					0,
				),
			],
			insert_at=1,
		)
		self._install_menu(
			main_menu,
			"Navigation",
			[
				("navigation_tracks_art", "Tracks & Art", "openTracksArt:", "", 0),
				("navigation_gallery", "Gallery", "openGallery:", "", 0),
				("navigation_tracks_only", "Tracks Only", "openTracksOnly:", "", 0),
				("navigation_showcase", "Showcase", "openShowcase:", "", 0),
				("navigation_radio", "Radio", "openRadio:", "", 0),
				("columns_toggle", "Columns Toggle", "toggleColumns:", "", 0),
			],
		)
		self._install_menu(
			main_menu,
			"Modes",
			[
				("shuffle_track", "Track shuffle", "setTrackShuffle:", "", 0),
				("shuffle_album", "Album shuffle", "setAlbumShuffle:", "", 0),
				("shuffle_off", "Shuffle Off", "setShuffleOff:", "", 0),
				None,
				("repeat_track", "Repeat Track", "setRepeatTrack:", "", 0),
				("repeat_album", "Repeat Album", "setRepeatAlbum:", "", 0),
				("repeat_off", "Repeat Off", "setRepeatOff:", "", 0),
				None,
				("lockdown_track", "Shuffle Lockdown", "setShuffleLockdown:", "", 0),
				("lockdown_album", "Shuffle Lockdown Albums", "setShuffleLockdownAlbums:", "", 0),
				("lockdown_exit", "Exit Shuffle Lockdown", "exitShuffleLockdown:", "", 0),
			],
		)
		self._install_menu(
			main_menu,
			"Playback",
			[
				("play", "Play", "play:", "", 0),
				("pause", "Pause", "pause:", "", 0),
				("stop", "Stop", "stop:", "", 0),
			],
		)
		self._install_menu(
			main_menu,
			"Track",
			[
				("love_track", "Love Playing Track", "loveTrack:", "", 0),
				("random_track", "Random Track", "randomTrack:", "", 0),
				("radio_random", "Radio Random", "radioRandom:", "", 0),
				("go_to_playing", "Go to Playing", "goToPlaying:", "", 0),
			],
		)
		help_menu = self._install_menu(
			main_menu,
			"Help",
			[
				("about", "About", "openAbout:", "", 0),
				("online_manual", "Online Manual", "openOnlineManual:", "", 0),
			],
		)
		self._move_window_menu_before_help(app, main_menu, help_menu)
		app.setHelpMenu_(help_menu)

		self.installed = True
		self.refresh_states()
		return True

	def _install_app_menu(self, main_menu: AppKit.NSMenu) -> None:
		if main_menu.numberOfItems() <= 0:
			return

		app_menu_item = main_menu.itemAtIndex_(0)
		app_menu = app_menu_item.submenu()
		if app_menu is None:
			return

		existing_settings_item = self._find_settings_item(app_menu)
		if existing_settings_item is not None:
			existing_settings_item.setTarget_(self.target)
			existing_settings_item.setAction_("openSettings:")
			return

		insert_at = min(1, app_menu.numberOfItems())
		settings_item = self._make_item("Settings", "openSettings:", ",", AppKit.NSEventModifierFlagCommand)
		app_menu.insertItem_atIndex_(settings_item, insert_at)

		next_index = insert_at + 1
		if next_index < app_menu.numberOfItems():
			next_item = app_menu.itemAtIndex_(next_index)
			if next_item is not None and not next_item.isSeparatorItem():
				app_menu.insertItem_atIndex_(AppKit.NSMenuItem.separatorItem(), next_index)

	def _install_menu(
		self,
		main_menu: AppKit.NSMenu,
		title: str,
		items: list[tuple[str, str, str, str, int] | None],
		insert_at: int | None = None,
	) -> AppKit.NSMenu:
		existing = self._find_item(main_menu, title)
		if existing is not None:
			main_menu.removeItem_(existing)

		menu = AppKit.NSMenu.alloc().initWithTitle_(title)
		menu.setAutoenablesItems_(False)
		menu.setDelegate_(self.target)

		for item_info in items:
			if item_info is None:
				menu.addItem_(AppKit.NSMenuItem.separatorItem())
				continue

			key, label, action, key_equivalent, modifiers = item_info
			item = self._make_item(label, action, key_equivalent, modifiers)
			menu.addItem_(item)
			self.items[key] = item

		menu_item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, None, "")
		menu_item.setSubmenu_(menu)
		if insert_at is None:
			main_menu.addItem_(menu_item)
		else:
			main_menu.insertItem_atIndex_(menu_item, min(insert_at, main_menu.numberOfItems()))
		return menu

	def _move_window_menu_before_help(
		self,
		app: AppKit.NSApplication,
		main_menu: AppKit.NSMenu,
		help_menu: AppKit.NSMenu,
	) -> None:
		window_item = self._find_window_menu_item(app, main_menu)
		help_item = self._find_item_by_submenu(main_menu, help_menu)
		if window_item is None or help_item is None or window_item == help_item:
			return

		help_index = main_menu.indexOfItem_(help_item)
		window_index = main_menu.indexOfItem_(window_item)
		if help_index < 0 or window_index < 0:
			return
		if window_index == help_index - 1:
			return

		main_menu.removeItem_(window_item)
		help_index = main_menu.indexOfItem_(help_item)
		if help_index < 0:
			main_menu.addItem_(window_item)
			return
		main_menu.insertItem_atIndex_(window_item, help_index)

	def _make_item(self, title: str, action: str, key_equivalent: str, modifiers: int) -> AppKit.NSMenuItem:
		item = AppKit.NSMenuItem.alloc().initWithTitle_action_keyEquivalent_(title, action, key_equivalent)
		item.setTarget_(self.target)
		if modifiers:
			item.setKeyEquivalentModifierMask_(modifiers)
		return item

	def _find_item(self, menu: AppKit.NSMenu, title: str) -> AppKit.NSMenuItem | None:
		for index in range(menu.numberOfItems()):
			item = menu.itemAtIndex_(index)
			if item is not None and item.title() == title:
				return item
		return None

	def _find_item_by_submenu(self, menu: AppKit.NSMenu, submenu: AppKit.NSMenu) -> AppKit.NSMenuItem | None:
		for index in range(menu.numberOfItems()):
			item = menu.itemAtIndex_(index)
			if item is not None and item.submenu() == submenu:
				return item
		return None

	def _find_window_menu_item(self, app: AppKit.NSApplication, main_menu: AppKit.NSMenu) -> AppKit.NSMenuItem | None:
		window_menu = app.windowsMenu()
		if window_menu is not None:
			item = self._find_item_by_submenu(main_menu, window_menu)
			if item is not None:
				return item
		return self._find_item(main_menu, "Window")

	def _find_settings_item(self, menu: AppKit.NSMenu) -> AppKit.NSMenuItem | None:
		for index in range(menu.numberOfItems()):
			item = menu.itemAtIndex_(index)
			if item is None or item.isSeparatorItem():
				continue

			if item.keyEquivalent() == "," and item.keyEquivalentModifierMask() == AppKit.NSEventModifierFlagCommand:
				return item

			title = item.title()
			if title in {"Settings", "Settings…", "Preferences", "Preferences…"}:
				return item
		return None

	def refresh_states(self) -> None:
		try:
			view_box = self.tauon.view_box
			pctl = self.tauon.pctl
			prefs = self.tauon.prefs
		except Exception:
			logging.exception("Failed reading Tauon state for macOS menu bar")
			return

		self._set_state("navigation_tracks_art", bool(view_box.side()))
		self._set_state("navigation_gallery", bool(view_box.gallery1()))
		self._set_state("navigation_tracks_only", bool(view_box.tracks()))
		self._set_state("navigation_showcase", bool(view_box.lyrics()))
		self._set_state("navigation_radio", bool(view_box.radio()))
		self._set_state("columns_toggle", bool(view_box.col()))

		self._set_state("shuffle_track", pctl.random_mode and not pctl.album_shuffle_mode)
		self._set_state("shuffle_album", pctl.random_mode and pctl.album_shuffle_mode)
		self._set_state("shuffle_off", not pctl.random_mode)

		self._set_state("repeat_track", pctl.repeat_mode and not pctl.album_repeat_mode)
		self._set_state("repeat_album", pctl.repeat_mode and pctl.album_repeat_mode)
		self._set_state("repeat_off", not pctl.repeat_mode)

		self._set_state("lockdown_track", prefs.shuffle_lock and not prefs.album_shuffle_lock_mode)
		self._set_state("lockdown_album", prefs.shuffle_lock and prefs.album_shuffle_lock_mode)
		self._set_state("lockdown_exit", not prefs.shuffle_lock)

		navigation_enabled = not prefs.shuffle_lock
		for key in (
			"navigation_tracks_art",
			"navigation_gallery",
			"navigation_tracks_only",
			"navigation_showcase",
			"navigation_radio",
			"columns_toggle",
		):
			self._set_enabled(key, navigation_enabled)

		mode_controls_enabled = not prefs.shuffle_lock
		for key in (
			"shuffle_track",
			"shuffle_album",
			"shuffle_off",
			"repeat_track",
			"repeat_album",
			"repeat_off",
		):
			self._set_enabled(key, mode_controls_enabled)

		self._set_enabled("lockdown_track", True)
		self._set_enabled("lockdown_album", True)
		self._set_enabled("lockdown_exit", True)

		play_state = pctl.playing_state
		current_playlist_locked = self.tauon.pl_is_locked(pctl.active_playlist_viewing)
		current_track_available = bool(pctl.track_queue)
		playlist_available = bool(pctl.multi_playlist[pctl.active_playlist_playing].playlist_ids)
		love_track_title = "Love Playing Track"
		if play_state in (PlayingState.PLAYING, PlayingState.PAUSED) and self.tauon.love(False):
			love_track_title = "Unlove Playing Track"

		self._set_title("love_track", love_track_title)
		self._set_enabled("file_import_folder_to_current_playlist", not current_playlist_locked)
		self._set_enabled("file_clear_current_playlist", not current_playlist_locked)
		self._set_enabled("play", play_state in (PlayingState.STOPPED, PlayingState.PAUSED))
		self._set_enabled("pause", play_state == PlayingState.PLAYING)
		self._set_enabled("stop", play_state != PlayingState.STOPPED)
		self._set_enabled("love_track", play_state in (PlayingState.PLAYING, PlayingState.PAUSED))
		self._set_enabled("random_track", playlist_available)
		self._set_enabled("radio_random", True)
		self._set_enabled("go_to_playing", current_track_available)
		self._set_enabled("about", True)
		self._set_enabled("online_manual", True)

	def _set_state(self, key: str, active: bool) -> None:
		item = self.items.get(key)
		if item is not None:
			item.setState_(_menu_state(active))

	def _set_enabled(self, key: str, enabled: bool) -> None:
		item = self.items.get(key)
		if item is not None:
			item.setEnabled_(enabled)

	def _set_title(self, key: str, title: str) -> None:
		item = self.items.get(key)
		if item is not None and item.title() != title:
			item.setTitle_(title)

	def import_folder_to_current_playlist(self) -> None:
		panel = AppKit.NSOpenPanel.openPanel()
		panel.setCanChooseFiles_(False)
		panel.setCanChooseDirectories_(True)
		panel.setAllowsMultipleSelection_(False)
		panel.setCanCreateDirectories_(False)
		panel.setMessage_("Choose a folder to import into the current playlist.")
		panel.setPrompt_("Import")
		panel.setDirectoryURL_(AppKit.NSURL.fileURLWithPath_(str(self.tauon.music_directory)))
		if panel.runModal() != AppKit.NSModalResponseOK:
			return

		url = panel.URL()
		if url is None:
			return
		path = url.path()
		if not path:
			return

		self.tauon.import_folder_to_current_playlist(path)
		self.refresh_states()

	def clear_current_playlist(self) -> None:
		self.tauon.clear_current_playlist()
		self.refresh_states()

	def open_settings(self) -> None:
		self.tauon.activate_info_box()
		self.tauon.gui.update = 2
		self.refresh_states()

	def open_tracks_art(self) -> None:
		self.tauon.view_standard_meta()
		self.refresh_states()

	def open_gallery(self) -> None:
		self.tauon.force_album_view()
		self.refresh_states()

	def open_tracks_only(self) -> None:
		self.tauon.view_tracks()
		self.refresh_states()

	def open_showcase(self) -> None:
		self.tauon.enter_showcase_view()
		self.refresh_states()

	def open_radio(self) -> None:
		self.tauon.enter_radio_view()
		self.refresh_states()

	def toggle_columns(self) -> None:
		self.tauon.view_box.col(hit=True)
		self.refresh_states()

	def set_track_shuffle(self) -> None:
		self.tauon.menu_set_random()
		self.refresh_states()

	def set_album_shuffle(self) -> None:
		self.tauon.menu_album_random()
		self.refresh_states()

	def set_shuffle_off(self) -> None:
		self.tauon.menu_shuffle_off()
		self.refresh_states()

	def set_repeat_track(self) -> None:
		self.tauon.menu_set_repeat()
		self.refresh_states()

	def set_repeat_album(self) -> None:
		self.tauon.menu_album_repeat()
		self.refresh_states()

	def set_repeat_off(self) -> None:
		self.tauon.menu_repeat_off()
		self.refresh_states()

	def set_shuffle_lockdown(self) -> None:
		if not self.tauon.prefs.shuffle_lock:
			self.tauon.toggle_shuffle_layout()
		elif self.tauon.prefs.album_shuffle_lock_mode:
			self.tauon.prefs.album_shuffle_lock_mode = False
			self.tauon.gui.update = 2
		self.refresh_states()

	def set_shuffle_lockdown_albums(self) -> None:
		if not self.tauon.prefs.shuffle_lock:
			self.tauon.toggle_shuffle_layout_albums()
		elif not self.tauon.prefs.album_shuffle_lock_mode:
			self.tauon.prefs.album_shuffle_lock_mode = True
			self.tauon.gui.update = 2
		self.refresh_states()

	def exit_shuffle_lockdown(self) -> None:
		if self.tauon.prefs.shuffle_lock:
			self.tauon.toggle_shuffle_layout()
		self.refresh_states()

	def play(self) -> None:
		self.tauon.pctl.play()
		self.refresh_states()

	def pause(self) -> None:
		self.tauon.pctl.pause_only()
		self.refresh_states()

	def stop(self) -> None:
		self.tauon.stop()
		self.refresh_states()

	def love_track(self) -> None:
		self.tauon.bar_love_notify()
		self.refresh_states()

	def random_track(self) -> None:
		self.tauon.random_track()
		self.refresh_states()

	def radio_random(self) -> None:
		self.tauon.radio_random()
		self.refresh_states()

	def go_to_playing(self) -> None:
		self.tauon.goto_playing_extra()
		self.refresh_states()

	def open_about(self) -> None:
		self.tauon.activate_info_box()
		self.tauon.pref_box.tab_active = len(self.tauon.pref_box.tabs) - 1
		self.tauon.pref_box.scroll = 0
		self.tauon.gui.update = 2
		self.refresh_states()

	def open_online_manual(self) -> None:
		self.tauon.open_manual_link()
		self.refresh_states()
