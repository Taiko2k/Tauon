"""Upgrade from older versions"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from tauon.t_modules.t_extra import RadioPlaylist, RadioStation, StarRecord, TauonPlaylist, TauonQueueItem

if TYPE_CHECKING:
	from tauon.t_modules.t_main import GuiVar, Prefs, StarStore, Tauon, TrackClass


def database_migrate(
	*,
	tauon: Tauon,
	db_version: float,
	master_library: dict[int, TrackClass],
	install_mode: bool,
	multi_playlist: list[str | int | bool] | list[TauonPlaylist],
	star_store: StarStore,
	a_cache_dir: str,
	cache_directory: Path,
	config_directory: Path,
	install_directory: Path,
	user_directory: Path,
	gui: GuiVar,
	gen_codes: dict[int, str],
	prefs: Prefs,
	radio_playlists: list[dict[str, int | str | list[dict[str, str]]]] | list[RadioPlaylist],
	p_force_queue: list[int | bool] | list[TauonQueueItem],
	theme: int,
) -> tuple[
	dict[int, TrackClass],
	list[TauonPlaylist],
	StarStore,
	list[TauonQueueItem],
	int,
	Prefs,
	GuiVar,
	dict[int, str],
	list[RadioPlaylist],
]:
	"""Migrate database to a newer version if we're behind

	Returns all the objects that could've been possibly changed:
		master_library, multi_playlist, star_store, p_force_queue, theme, prefs, gui, gen_codes, radio_playlists
	"""
	from tauon.t_modules.t_main import uid_gen

	show_message = tauon.show_message

	if db_version <= 0:
		logging.error("Called database_migrate with db_version equal to or below 0!")
		raise ValueError

	logging.warning(f"Running migrations as DB version was {db_version}!")
	if db_version <= 0.8:  # noqa: PLR2004
		logging.info("Updating database from version 0.8 to 0.9")
		for key, value in master_library.items():
			setattr(master_library[key], "skips", 0)

	if db_version <= 0.9:  # noqa: PLR2004
		logging.info("Updating database from version 0.9 to 1.1")
		for key, value in master_library.items():
			setattr(master_library[key], "comment", "")

	if db_version <= 1.1:  # noqa: PLR2004
		logging.info("Updating database from version 1.1 to 1.2")
		for key, value in master_library.items():
			setattr(master_library[key], "album_artist", "")

	if db_version <= 1.2:  # noqa: PLR2004
		logging.info("Updating database to version 1.3")
		for key, value in master_library.items():
			setattr(master_library[key], "disc_number", "")
			setattr(master_library[key], "disc_total", "")

	if db_version <= 1.3:  # noqa: PLR2004
		logging.info("Updating database to version 1.4")
		for key, value in master_library.items():
			setattr(master_library[key], "lyrics", "")
			setattr(master_library[key], "track_total", "")
		show_message(
			"Upgrade complete. Note: New attributes such as disk number won't show for existing tracks (delete state.p to reset)"
		)

	if db_version <= 1.4:  # noqa: PLR2004
		logging.info("Updating database to version 1.5")
		for playlist in multi_playlist:
			playlist.append(uid_gen())

	if db_version <= 1.5:  # noqa: PLR2004
		logging.info("Updating database to version 1.6")
		for i in range(len(multi_playlist)):
			if len(multi_playlist[i]) == 7:
				multi_playlist[i].append("")

	if db_version <= 1.6:  # noqa: PLR2004
		logging.info("Updating preferences to 1.7")
		# gui.show_stars = False
		if install_mode:
			# shutil.copy(install_directory / "config.txt", user_directory)
			logging.info("Rewrote user config file")

	if db_version <= 1.7:  # noqa: PLR2004
		logging.info("Updating database to version 1.8")
		if install_mode:
			logging.info(".... Overwriting user config file")
			# shutil.copy(install_directory / "config.txt", user_directory)

		try:
			logging.info(".... Updating playtime database")

			old = star_store.db
			# perf_timer.set()
			old_total = sum(old.values())
			# logging.info(perf_timer.get())
			logging.info(f"Old total: {old_total}")
			star_store.db = {}

			new = {}
			for track in master_library.values():
				key = track.title + track.filename
				if key in old:
					n_value = [old[key], ""]
					n_key = star_store.object_key(track)
					star_store.db[n_key] = n_value

			diff = old_total - star_store.get_total()
			logging.info(
				f"New total: {int(diff)} Seconds could not be matched to tracks. Total playtime won't be affected"
			)
			star_store.db[("", "", "LOST")] = [diff, ""]
			logging.info("Upgrade Complete")
		except Exception:
			logging.exception("Error upgrading database")
			show_message(_("Error loading old database, did the program not exit properly after updating? Oh well."))

	if db_version <= 1.8:  # noqa: PLR2004
		logging.info("Updating database to 1.9")
		for key, value in master_library.items():
			setattr(master_library[key], "track_gain", None)
			setattr(master_library[key], "album_gain", None)
		show_message(_("Upgrade complete. Run a tag rescan if you want enable ReplayGain"))

	if db_version <= 1.9:  # noqa: PLR2004
		logging.info("Updating database to version 2.0")
		for key, value in master_library.items():
			setattr(master_library[key], "modified_time", 0)
		show_message(_("Upgrade complete. New sorting option may require tag rescan."))

	if db_version <= 2.0:  # noqa: PLR2004
		logging.info("Updating database to version 2.1")
		for key, value in master_library.items():
			setattr(master_library[key], "is_embed_cue", False)
			setattr(master_library[key], "cue_sheet", "")
		show_message(_("Updated to v2.6.3"))

	if db_version <= 2.1:  # noqa: PLR2004
		logging.info("Updating database to version 2.1")
		for key, value in master_library.items():
			setattr(master_library[key], "lfm_friend_likes", set())

	if db_version <= 2.2:  # noqa: PLR2004
		for i in range(len(multi_playlist)):
			if len(multi_playlist[i]) < 9:
				multi_playlist[i].append(True)

	if db_version <= 2.3:  # noqa: PLR2004
		logging.info("Updating database to version 2.4")
		for key, value in master_library.items():
			setattr(master_library[key], "bit_depth", 0)

	if db_version <= 2.4:  # noqa: PLR2004
		if theme > 0:
			theme += 1

	if db_version <= 2.5:  # noqa: PLR2004
		logging.info("Updating database to version 2.6")
		for key, value in master_library.items():
			setattr(master_library[key], "is_network", False)
		# for i in range(len(multi_playlist)):
		# 	if len(multi_playlist[i]) < 10:
		# 		multi_playlist[i].append(False)

	if db_version <= 26:  # noqa: PLR2004
		logging.info("Updating database to version 27")
		for i in range(len(multi_playlist)):
			if len(multi_playlist[i]) == 9:
				multi_playlist[i].append(False)

	if db_version <= 27:  # noqa: PLR2004
		logging.info("Updating database to version 28")
		for i in range(len(multi_playlist)):
			if len(multi_playlist[i]) <= 10:
				multi_playlist[i].append("")

	if db_version <= 29:  # noqa: PLR2004
		logging.info("Updating database to version 30")
		for key, value in master_library.items():
			setattr(master_library[key], "composer", "")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with Path(config_directory / "input.txt").open("a") as f:
				f.write("global-search G Ctrl\n")
				f.write("cycle-theme-reverse\n")
				f.write("reload-theme F10\n")

		show_message(_("Welcome to v4.4.0. Run a tag rescan if you want enable Composer metadata."))

	if db_version <= 30:  # noqa: PLR2004
		for i, item in enumerate(p_force_queue):
			try:
				assert item[6]
			except Exception:
				logging.exception("Error asserting item[6]")
				p_force_queue[i].append(False)

	if db_version <= 31:  # noqa: PLR2004
		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with Path(config_directory / "input.txt").open("a") as f:
				f.write("love-selected\n")
		gui.set_bar = True

	if db_version <= 32 and theme > 1:  # noqa: PLR2004
		theme += 1

	if db_version <= 33:  # noqa: PLR2004
		logging.info("Update to db 34")
		for key, value in master_library.items():
			if not hasattr(master_library[key], "misc"):
				setattr(master_library[key], "misc", {})

	if db_version <= 34:  # noqa: PLR2004
		logging.info("Update to dv 35")
		# Moved to after config load

	if db_version <= 35:  # noqa: PLR2004
		logging.info("Updating database to version 36")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with Path(config_directory / "input.txt").open("a") as f:
				f.write("toggle-show-art H Ctrl\n")

	if db_version <= 37:  # noqa: PLR2004
		logging.info("Updating database to version 38")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with Path(config_directory / "input.txt").open("a") as f:
				f.write("toggle-console `\n")

	if db_version <= 38:  # noqa: PLR2004
		logging.info("Updating database to version 39")

		for key, value in star_store.db.items():
			logging.info(value)
			if len(value) == 2:
				value.append(0)
				star_store.db[key] = value

	if db_version <= 39:  # noqa: PLR2004
		logging.info("Updating database to version 40")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			f = (config_directory / "input.txt").open("r")
			text = f.read()
			f.close()
			lines = text.splitlines()
			if "l ctrl" not in text.lower():
				f = (config_directory / "input.txt").open("w", encoding="utf-8")
				for line in lines:
					line = line.strip()
					if line == "love-selected":
						line = "love-selected L Ctrl"
					f.write(line + "\n")
				f.close()

	if db_version <= 40:  # noqa: PLR2004
		logging.info("Updating database to version 41")
		old = copy.deepcopy(prefs.lyrics_enables)
		prefs.lyrics_enables.clear()
		if "apiseeds" in old:
			prefs.lyrics_enables.append("Apiseeds")
		if "lyricwiki" in old:
			prefs.lyrics_enables.append("LyricWiki")
		if "genius" in old:
			prefs.lyrics_enables.append("Genius")

	if db_version <= 41:  # noqa: PLR2004
		logging.info("Updating database to version 42")

		for key, value in gen_codes.items():
			gen_codes[key] = value.replace('f"', 'p"')

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			f = (config_directory / "input.txt").open("r")
			text = f.read()
			f.close()
			lines = text.splitlines()

			f = Path(config_directory / "input.txt").open("w", encoding="utf-8")
			for line in lines:
				line = line.strip()
				if "rename-playlist" in line:
					f.write(line + "\n")

					line = "new-playlist T Ctrl\n"
					f.write(line)

					line = "\nnew-generator-playlist\n"
					f.write(line)
					if "e ctrl" in text.lower():
						line = "edit-generator\n\n"
					else:
						line = "edit-generator E Ctrl\n\n"
					f.write(line)

					line = "search-lyrics-selected\n"
					f.write(line)
					line = "substitute-search-selected"

				f.write(line + "\n")

			f.close()

	if db_version <= 42:  # noqa: PLR2004
		logging.info("Updating database to version 43")

	if db_version <= 43:  # noqa: PLR2004
		logging.info("Updating database to version 44")
		# Repair db
		for key, value in star_store.db.items():
			if len(value) == 2:
				value.append(0)
				star_store.db[key] = value

	if db_version <= 44:  # noqa: PLR2004
		logging.info("Updating database to version 45")
		logging.info("Cleaning cache directory")
		for item in cache_directory.iterdir():
			path = cache_directory / item
			if "-lfm." in str(item) or "-ftv." in str(item) or "-dcg." in str(item):
				path.rename(a_cache_dir / item)
		for item in cache_directory.iterdir():
			path = cache_directory / item
			if path.is_file():
				path.unlink()

	if db_version <= 45:  # noqa: PLR2004
		logging.info("Updating database to version 46")
		for p in multi_playlist:
			if type(p[7]) != list:
				p[7] = [p[7]]

	if db_version <= 46:  # noqa: PLR2004
		logging.info("Updating database to version 47")
		for p in multi_playlist:
			if type(p[7]) != list:
				p[7] = [p[7]]

	if db_version <= 47:  # noqa: PLR2004
		logging.info("Updating database to version 48")
		if (user_directory / "spot-r-token").is_file():
			show_message(
				_("Welcome to v6.1.0. Due to changes, please re-authorise Spotify"),
				_("You can do this by clicking 'Forget Account', then 'Authroise' in Settings > Accounts > Spotify"),
			)

	if db_version <= 48:  # noqa: PLR2004
		logging.info("Fix bad upgrade, now 49")
		for key, value in master_library.items():
			if not hasattr(master_library[key], "url_key"):
				setattr(master_library[key], "url_key", "")
			if not hasattr(master_library[key], "art_url_key"):
				setattr(master_library[key], "art_url_key", "")

	if db_version <= 49:  # noqa: PLR2004
		logging.info("Updating database to version 50")
		if (user_directory / "spot-r-token").is_file():
			show_message(
				_("Welcome to v6.3.0. Due to an upgrade, please re-authorise Spotify"),
				_("You can do this by clicking 'Authroise' in Settings > Accounts > Spotify"),
			)
			(user_directory / "spot-r-token").unlink()

	if db_version <= 54:  # noqa: PLR2004
		logging.info("Updating database to version 55")
		for key, value in master_library.items():
			setattr(master_library[key], "lfm_scrobbles", 0)

	if db_version <= 55:  # noqa: PLR2004
		logging.info("Update to db 56")
		for key, value in master_library.items():
			if hasattr(value, "track_gain"):
				if value.track_gain != 0:
					value.misc["replaygain_track_gain"] = value.track_gain
				del value.track_gain

			if hasattr(value, "album_gain"):
				if value.album_gain != 0:
					value.misc["replaygain_album_gain"] = value.album_gain
				del value.album_gain

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("a") as f:
				f.write("toggle-right-panel MB5\n")
				f.write("toggle-gallery MB4\n")

	if db_version <= 56:  # noqa: PLR2004
		logging.info("Update to db 57")
		if "Apiseeds" in prefs.lyrics_enables:
			prefs.lyrics_enables.remove("Apiseeds")
			prefs.lyrics_enables.append("Happi")

	if db_version <= 57:  # noqa: PLR2004
		logging.info("Updating database to version 58")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("a") as f:
				f.write("\nregenerate-playlist R Alt\n")
				f.write("clear-queue Q Shift Alt\n")
				f.write("resize-window-16:9 F11 Alt\n")
				f.write("delete-playlist-force W Shift Ctrl\n")

	if db_version <= 58:  # noqa: PLR2004
		logging.info("Updating database to version 59")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("a") as f:
				f.write("\nrandom-album ; Alt\n")

	if db_version <= 59:  # noqa: PLR2004
		logging.info("Updating database to version 60")

		if prefs.spotify_token:
			show_message(
				_("Upgrade to v6.5.1. It looks like you are using Spotify."),
				_("Please click 'Authorise' again in the settings"),
			)
		prefs.spotify_token = ""

	if db_version <= 60:  # noqa: PLR2004
		logging.info("Updating database to version 61")

		token_path = user_directory / "spot-token-pkce"
		if token_path.exists():
			prefs.spotify_token = ""
			token_path.unlink()
			show_message(
				_("Upgrade to v6.5.3 complete"),
				_("It looks like you are using Spotify. Please re-setup Spotify again in the settings"),
			)

	if db_version <= 61:  # noqa: PLR2004
		logging.info("Updating database to version 62")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("a") as f:
				f.write("\ntransfer-playtime-to P Ctrl Shift\n")

	if db_version <= 62:  # noqa: PLR2004
		logging.info("Updating database to version 63")
		for item in gui.pl_st:
			if item[0] == "T":
				item[0] = "#"

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("r") as f:
				lines = f.readlines()
			with (config_directory / "input.txt").open("w", encoding="utf-8") as f:
				for line in lines:
					if line == "vol-up Up Shift\n" or line == "vol-down Down Shift\n":
						continue
					f.write(line)
				f.write("\n")
				f.write("shift-up Up Shift\n")
				f.write("shift-down Down Shift\n")
				f.write("vol-up Up Ctrl\n")
				f.write("vol-down Down Ctrl\n")

	if db_version <= 63:  # noqa: PLR2004
		logging.info("Updating database to version 64")
		if prefs.radio_urls:
			radio_playlists[0]["items"].extend(prefs.radio_urls)
			prefs.radio_urls = []
		# prefs.show_nag = True

	if db_version <= 64:  # noqa: PLR2004
		logging.info("Updating database to version 65")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("a") as f:
				f.write("\nescape Escape\n")
				f.write("toggle-mute M Ctrl\n")

	if db_version <= 65:  # noqa: PLR2004
		logging.info("Updating database to version 66")

		if install_directory != config_directory and (config_directory / "input.txt").is_file():
			with (config_directory / "input.txt").open("a") as f:
				f.write("\ntoggle-artistinfo O Ctrl\n")
				f.write("cycle-theme ] Ctrl\n")
				f.write("cycle-theme-reverse [ Ctrl\n")

	if db_version <= 66:  # noqa: PLR2004
		logging.info("Updating database to version 67")
		for key, value in star_store.db.items():
			if len(value) == 3:
				value.append(0)
				star_store.db[key] = value

	if db_version <= 67:  # noqa: PLR2004
		logging.info("Updating database to version 68")
		for p in multi_playlist:
			if len(p) == 11:
				p.append(False)

	if db_version <= 68:  # noqa: PLR2004
		logging.info("Updating database to version 69")
		new_multi_playlist: list[TauonPlaylist] = []
		new_queue: list[TauonQueueItem] = []
		for playlist in multi_playlist:
			new_multi_playlist.append(
				TauonPlaylist(
					title=playlist[0],
					playing=playlist[1],
					playlist_ids=playlist[2],
					position=playlist[3],
					hide_title=playlist[4],
					selected=playlist[5],
					uuid_int=playlist[6],
					last_folder=playlist[7],
					hidden=playlist[8],
					locked=playlist[9],
					parent_playlist_id=playlist[10],
					persist_time_positioning=playlist[11],
				)
			)
		for queue in p_force_queue:
			new_queue.append(
				TauonQueueItem(
					track_id=queue[0],
					position=queue[1],
					playlist_id=queue[2],
					type=queue[3],
					album_stage=queue[4],
					uuid_int=queue[5],
					auto_stop=queue[6],
				)
			)
		multi_playlist = new_multi_playlist
		p_force_queue = new_queue

	if db_version <= 69:  # noqa: PLR2004
		logging.info("Updating database to version 70")
		new_radio_playlists: list[RadioPlaylist] = []
		for playlist in radio_playlists:
			stations: list[RadioStation] = []

			for station in playlist["items"]:
				stations.append(
					RadioStation(
						title=station["title"],
						stream_url=station["stream_url"],
						country=station.get("country", ""),
						website_url=station.get("website_url", ""),
						icon=station.get("icon", ""),
						stream_url_fallback=station.get("stream_url_unresolved", ""),
					)
				)
			new_radio_playlists.append(
				RadioPlaylist(
					uid=playlist["uid"], name=playlist["name"], scroll=playlist.get("scroll", 0), stations=stations
				)
			)
		radio_playlists = new_radio_playlists

	if db_version <= 71:  # This migration used both 71 and 72  # noqa: PLR2004
		logging.info("Updating database to version 72")
		logging.info("Creating a backup Star database star.p.bak71")
		import pickle  # noqa: PLC0415

		backup_star_db = user_directory / "star.p.bak71"
		if not backup_star_db.exists():
			with backup_star_db.open("wb") as file:
				pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

		new_starstore_db: dict[tuple[str, str, str], StarRecord] = {}
		old_record: list[int | str] = []  # Here just for typing
		for key, old_record in star_store.db.items():
			if isinstance(old_record, StarRecord):
				logging.warning(
					"Record {old_record} was already a StarRecord, likely half-failed earlier migration, skipping this migration over…"
				)
				break
			new_record = StarRecord()
			new_record.playtime = old_record[0]
			new_record.loved = "L" in old_record[1]
			new_record.rating = old_record[2]
			# There was a bug where the fourth element was not set
			if len(old_record) == 4:
				new_record.loved_timestamp = old_record[3]
			new_starstore_db[key] = new_record
		else:
			star_store.db = new_starstore_db
			logging.info("Saving newly migrated StarStore db…")
			with (user_directory / "star.p").open("wb") as file:
				pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

	if db_version <= 72:  # noqa: PLR2004
		# prefs.playlist_exports = save[168]
		logging.info("Updating database to version 73")
		for key, item in prefs.playlist_exports.items():
			playlist = None
			for p in multi_playlist:
				if p.uuid_int == key:
					playlist = p
					break
			else:
				continue

			if item.get("auto"):
				playlist.auto_export = True

			path = item.get("path")
			if path:
				if not path.endswith("/") and not path.endswith("\\"):
					path = path + "/"
				playlist.playlist_file = path

			type = item.get("type")
			if type:
				playlist.export_type = type

			relative = item.get("relative")
			if relative:
				playlist.relative_export = relative

	return master_library, multi_playlist, star_store, p_force_queue, theme, prefs, gui, gen_codes, radio_playlists
