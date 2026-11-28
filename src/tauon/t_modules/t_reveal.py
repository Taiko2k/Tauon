"""Show a file selected in the desktop's file manager on Linux, inside Flatpak or not"""

# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

from __future__ import annotations

import logging
import os
import subprocess
import threading
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from types import ModuleType

	from dbus.bus import BusConnection

PORTAL_NAME = "org.freedesktop.portal.Desktop"
PORTAL_PATH = "/org/freedesktop/portal/desktop"
OPEN_URI = "org.freedesktop.portal.OpenURI"
FILE_MANAGER_NAME = "org.freedesktop.FileManager1"
FILE_MANAGER_PATH = "/org/freedesktop/FileManager1"

# Long enough for a cold start of the portal or file manager. Blocks a worker thread only.
CHECK_TIMEOUT = 5
OPEN_TIMEOUT = 10

# The request may still be delivered, so falling back would open a second window
TIMEOUT_ERRORS = ("org.freedesktop.DBus.Error.NoReply", "org.freedesktop.DBus.Error.Timeout")

# One reveal at a time, so repeat clicks don't queue up behind a slow one
busy = threading.Lock()


def name_available(bus: BusConnection, name: str) -> bool:
	"""True if something owns the bus name or D-Bus can start it"""
	return bool(bus.name_has_owner(name)) or name in bus.list_activatable_names()


def via_portal(dbus: ModuleType, bus: BusConnection, path: str, token: str | None = None) -> bool:
	"""OpenURI.OpenDirectory, which the portal turns into ShowItems on the host"""
	if not name_available(bus, PORTAL_NAME):
		return False
	portal = bus.get_object(PORTAL_NAME, PORTAL_PATH, introspect=False)
	version = portal.Get(OPEN_URI, "version", dbus_interface="org.freedesktop.DBus.Properties", timeout=CHECK_TIMEOUT)
	# OpenDirectory arrived in version 3
	if int(version) < 3:
		return False
	# Older portals ignore option keys they don't know
	options = {"activation_token": token} if token else {}
	fd = os.open(path, os.O_RDONLY | os.O_CLOEXEC)
	try:
		portal.OpenDirectory(
			"", dbus.types.UnixFd(fd), dbus.Dictionary(options, signature="sv"),
			dbus_interface=OPEN_URI, timeout=OPEN_TIMEOUT)
	finally:
		os.close(fd)
	return True


def via_file_manager(bus: BusConnection, path: str, token: str | None = None) -> bool:
	"""FileManager1.ShowItems, implemented by Nautilus, Dolphin, Nemo, Thunar and others"""
	if not name_available(bus, FILE_MANAGER_NAME):
		return False
	manager = bus.get_object(FILE_MANAGER_NAME, FILE_MANAGER_PATH, introspect=False)
	# The startup id carries the activation token on Wayland
	manager.ShowItems([Path(path).absolute().as_uri()], token or "", dbus_interface=FILE_MANAGER_NAME, timeout=OPEN_TIMEOUT)
	return True


def open_parent(path: str, token: str | None = None) -> None:
	# A copied environment, as setenv isn't thread-safe
	env = {**os.environ, "XDG_ACTIVATION_TOKEN": token} if token else None
	subprocess.Popen(["xdg-open", os.path.dirname(path) + "/"], env=env)


def reveal_file(path: str, token: str | None = None, sandboxed: bool = False) -> str:
	"""Try FileManager1, the portal, then plain xdg-open. Blocking; call from a thread. Returns the method used.

	token is an xdg-activation token (t_wayland_activation) so the file manager may take focus on Wayland.
	Outside a sandbox FileManager1 goes first: the portal deadlocks for 25 s while it activates the
	file manager (xdg-desktop-portal#2093, fixed after 1.22.1). In Flatpak only the portal is reachable.
	"""
	if not busy.acquire(blocking=False):
		logging.info("Already revealing a file, ignoring")
		return "busy"
	try:
		return reveal(path, token, sandboxed)
	finally:
		busy.release()


def reveal(path: str, token: str | None, sandboxed: bool) -> str:
	if not os.path.isfile(path):
		open_parent(path, token)
		return "xdg-open"
	try:
		import dbus  # noqa: PLC0415
		# A private connection, so the shared bus is still created with t_dbus's main loop
		bus = dbus.SessionBus(private=True)
	except Exception:
		logging.exception("No session bus to reveal a file")
		open_parent(path, token)
		return "xdg-open"
	attempts = [
		("FileManager1", lambda: via_file_manager(bus, path, token)),
		("portal", lambda: via_portal(dbus, bus, path, token)),
	]
	if sandboxed:
		attempts.reverse()
	try:
		for name, attempt in attempts:
			try:
				if attempt():
					return name
			except dbus.exceptions.DBusException as e:
				if e.get_dbus_name() in TIMEOUT_ERRORS:
					logging.warning("Revealing a file through %s timed out, not trying further", name)
					return "timeout"
				logging.exception("Revealing a file through %s failed", name)
			except (OSError, ValueError, TypeError):
				logging.exception("Revealing a file through %s failed", name)
	finally:
		bus.close()
	open_parent(path, token)
	return "xdg-open"
