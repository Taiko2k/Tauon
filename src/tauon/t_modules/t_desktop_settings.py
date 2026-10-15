"""Read window button layout, theme and subpixel order from the desktop via GIO"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

from gi.repository import Gio, GLib

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
	bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
	reply = bus.call_sync(
		"org.freedesktop.portal.Desktop",
		"/org/freedesktop/portal/desktop",
		"org.freedesktop.portal.Settings",
		"ReadAll",
		GLib.Variant("(as)", (list(KEYS),)),
		GLib.VariantType("(a{sa{sv}})"),
		Gio.DBusCallFlags.NONE,
		500,
		None,
	)
	return reply.unpack()[0]


def read_gsettings() -> dict[str, dict[str, object]]:
	values: dict[str, dict[str, object]] = {}
	source = Gio.SettingsSchemaSource.get_default()
	if source is None:
		return values
	for schema_id, keys in KEYS.items():
		# Gio.Settings aborts the process on a missing schema, so look it up first
		schema = source.lookup(schema_id, True)
		if schema is None:
			continue
		settings = Gio.Settings.new_full(schema, None, None)
		values[schema_id] = {key: settings.get_value(key).unpack() for key in keys if schema.has_key(key)}
	return values


def read_desktop_settings(desktop: str | None) -> DesktopSettings:
	result = DesktopSettings()
	try:
		values = read_portal() if os.path.exists("/.flatpak-info") else read_gsettings()
	except GLib.Error as e:
		logging.warning(f"Could not read desktop settings: {e.message}")
		return result
	except Exception:
		logging.exception("Error reading desktop settings")
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
