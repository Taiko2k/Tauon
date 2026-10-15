"""Read window button layout, theme and subpixel order from the desktop's GNOME settings"""

from __future__ import annotations

import ast
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass

WM_SCHEMA = "org.gnome.desktop.wm.preferences"
INTERFACE_SCHEMA = "org.gnome.desktop.interface"
KEYS = {
	WM_SCHEMA: ("button-layout",),
	INTERFACE_SCHEMA: ("gtk-theme", "font-antialiasing", "font-rgba-order"),
}
# GNOME's own default. Elsewhere it's only meaningful when the desktop syncs its
# layout into the key (as KDE does); otherwise keep every button, like GTK did.
GNOME_DEFAULT_LAYOUT = "appmenu:close"


@dataclass
class DesktopSettings:
	draw_min_button: bool = True
	draw_max_button: bool = True
	left_window_control: bool = False
	theme_name: str = ""
	subpixel_rgb: bool = False


def read_portal() -> dict[str, dict[str, object]]:
	"""Read the keys through the settings portal, the only view of the host's settings inside Flatpak"""
	import dbus  # noqa: PLC0415

	# A private connection, so the shared bus is still created with t_dbus's main loop
	bus = dbus.SessionBus(private=True)
	try:
		portal = bus.get_object("org.freedesktop.portal.Desktop", "/org/freedesktop/portal/desktop", introspect=False)
		reply = portal.ReadAll(list(KEYS), dbus_interface="org.freedesktop.portal.Settings", timeout=0.5)
	finally:
		bus.close()
	return {str(schema): {str(k): str(v) for k, v in values.items()} for schema, values in reply.items()}


def parse_gvariant_string(text: str) -> str:
	"""Unquote a GVariant text-format string such as 'appmenu:close'"""
	try:
		value = ast.literal_eval(text)
	except (ValueError, SyntaxError):
		return text
	return value if isinstance(value, str) else text


def read_gsettings() -> dict[str, dict[str, object]]:
	values: dict[str, dict[str, object]] = {}
	gsettings = shutil.which("gsettings")
	if gsettings is None:
		return values
	# One process per schema, run concurrently; a missing schema just exits non-zero
	procs = {
		schema_id: subprocess.Popen(
			[gsettings, "list-recursively", schema_id],
			stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
		)
		for schema_id in KEYS
	}
	for schema_id, proc in procs.items():
		try:
			out, _ = proc.communicate(timeout=2)
		except subprocess.TimeoutExpired:
			proc.kill()
			proc.communicate()
			continue
		if proc.returncode != 0:
			continue
		found: dict[str, object] = {}
		for line in out.splitlines():
			parts = line.split(" ", 2)
			if len(parts) == 3 and parts[1] in KEYS[schema_id]:
				found[parts[1]] = parse_gvariant_string(parts[2])
		values[schema_id] = found
	return values


def read_desktop_settings(desktop: str | None) -> DesktopSettings:
	result = DesktopSettings()
	try:
		values = read_portal() if os.path.exists("/.flatpak-info") else read_gsettings()
	except Exception as e:
		logging.warning(f"Could not read desktop settings: {e}")
		return result

	interface = values.get(INTERFACE_SCHEMA, {})
	result.theme_name = str(interface.get("gtk-theme", "")).lower()
	result.subpixel_rgb = interface.get("font-antialiasing") == "rgba" and interface.get("font-rgba-order") == "rgb"

	layout = values.get(WM_SCHEMA, {}).get("button-layout")
	if isinstance(layout, str) and (layout != GNOME_DEFAULT_LAYOUT or "GNOME" in (desktop or "")):
		result.draw_min_button = "minimize" in layout
		result.draw_max_button = "maximize" in layout
		result.left_window_control = "close" in layout.split(":")[0]
	return result
