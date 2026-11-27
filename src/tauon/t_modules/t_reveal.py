"""Show a file selected in the desktop's file manager on Linux, inside Flatpak or not"""

from __future__ import annotations

import logging
import os
import subprocess
from pathlib import Path

PORTAL_NAME = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
OPEN_URI = "org.freedesktop.portal.OpenURI"
FILE_MANAGER_NAME = "org.freedesktop.FileManager1"
FILE_MANAGER_PATH = "/org/freedesktop/FileManager1"

# Long enough for a cold start of the portal or file manager. Blocks a worker thread only.
CHECK_TIMEOUT = 5
OPEN_TIMEOUT = 10


def name_available(bus, name: str) -> bool:
	"""True if something owns the bus name or D-Bus can start it"""
	return bool(bus.name_has_owner(name)) or name in bus.list_activatable_names()


def via_portal(dbus, bus, path: str) -> bool:
	"""OpenURI.OpenDirectory, which the portal turns into ShowItems on the host"""
	if not name_available(bus, PORTAL_NAME):
		return False
	portal = bus.get_object(PORTAL_NAME, PORTAL_PATH, introspect=False)
	version = portal.Get(OPEN_URI, "version", dbus_interface="org.freedesktop.DBus.Properties", timeout=CHECK_TIMEOUT)
	# OpenDirectory arrived in version 3
	if int(version) < 3:
		return False
	fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
	try:
		portal.OpenDirectory(
			"", dbus.types.UnixFd(fd), dbus.Dictionary({}, signature="sv"),
			dbus_interface=OPEN_URI, timeout=OPEN_TIMEOUT)
	finally:
		os.close(fd)
	return True


def via_file_manager(bus, path: str) -> bool:
	"""FileManager1.ShowItems, implemented by Nautilus, Dolphin, Nemo, Thunar and others"""
	if not name_available(bus, FILE_MANAGER_NAME):
		return False
	manager = bus.get_object(FILE_MANAGER_NAME, FILE_MANAGER_PATH, introspect=False)
	manager.ShowItems([Path(path).absolute().as_uri()], "", dbus_interface=FILE_MANAGER_NAME, timeout=OPEN_TIMEOUT)
	return True


def open_parent(path: str) -> None:
	subprocess.Popen(["xdg-open", os.path.dirname(path) + "/"])


def reveal_file(path: str) -> str:
	"""Try the portal, then FileManager1, then plain xdg-open. Blocking; call from a thread. Returns the method used."""
	if not os.path.isfile(path):
		open_parent(path)
		return "xdg-open"
	try:
		import dbus  # noqa: PLC0415
		# A private connection, so the shared bus is still created with t_dbus's main loop
		bus = dbus.SessionBus(private=True)
	except Exception:
		logging.exception("No session bus to reveal a file")
		open_parent(path)
		return "xdg-open"
	try:
		for name, attempt in (("portal", lambda: via_portal(dbus, bus, path)), ("FileManager1", lambda: via_file_manager(bus, path))):
			try:
				if attempt():
					return name
			except (dbus.exceptions.DBusException, OSError, ValueError, TypeError):
				logging.exception("Revealing a file through %s failed", name)
	finally:
		bus.close()
	open_parent(path)
	return "xdg-open"
