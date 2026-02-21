"""Upgrade from older versions"""

from __future__ import annotations

import copy
import logging
from pathlib import Path
from typing import TYPE_CHECKING

from tauon.t_modules.t_extra import RadioPlaylist, RadioStation, StarRecord, TauonPlaylist, TauonQueueItem

if TYPE_CHECKING:
	from tauon.t_modules.t_main import GuiVar, Prefs, StarStore, Tauon, TrackClass

def migrate_star_store_71(tauon: Tauon) -> None:
	import pickle  # noqa: PLC0415

	backup_star_db = tauon.user_directory / "star.p.bak71"
	if not backup_star_db.exists():
		logging.info("Creating a backup Star database star.p.bak71")
		with backup_star_db.open("wb") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)

	new_starstore_db: dict[tuple[str, str, str], StarRecord] = {}
	old_record: list[int | str] = []  # Here just for typing
	for key, old_record in tauon.star_store.db.items():
		if isinstance(old_record, StarRecord):
			logging.warning(
				f"Record {old_record} was already a StarRecord, skipping this migration over…"
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
		tauon.star_store.db = new_starstore_db
		logging.info("Saving newly migrated StarStore db…")
		with (tauon.user_directory / "star.p").open("wb") as file:
			pickle.dump(tauon.star_store.db, file, protocol=pickle.HIGHEST_PROTOCOL)


def database_migrate(
	*,
	tauon: Tauon,
	db_version: float,
	master_library: dict[int, TrackClass],
	install_mode: bool,
	multi_playlist: list[str | int | bool] | list[TauonPlaylist],
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
	list[TauonQueueItem],
	int,
	Prefs,
	GuiVar,
	dict[int, str],
	list[RadioPlaylist],
]:
	"""Migrate database to a newer version if we're behind

	Returns all the objects that could've been possibly changed:
		master_library, multi_playlist, p_force_queue, theme, prefs, gui, gen_codes, radio_playlists
	"""
	if db_version <= 0:
		logging.error("Called database_migrate with db_version equal to or below 0!")
		raise ValueError

	logging.warning(f"Running migrations as DB version was {db_version}!")

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
		for key, value in tauon.star_store.db.items():
			if len(value) == 3:
				value.append(0)
				tauon.star_store.db[key] = value

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
		migrate_star_store_71(tauon)

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

	if db_version <= 73:  # noqa: PLR2004
		logging.info("Updating database to version 74")
		for playlist in multi_playlist:
			if not isinstance(playlist, TauonPlaylist):
				continue

			last_folder = playlist.last_folder
			if isinstance(last_folder, str):
				playlist.last_folder = [last_folder] if last_folder else []
			elif last_folder is None:
				playlist.last_folder = []
			elif isinstance(last_folder, list):
				playlist.last_folder = [str(path) for path in last_folder if path]
			else:
				try:
					playlist.last_folder = [str(path) for path in last_folder if path]
				except TypeError:
					playlist.last_folder = [str(last_folder)] if last_folder else []

	return master_library, multi_playlist, p_force_queue, theme, prefs, gui, gen_codes, radio_playlists
