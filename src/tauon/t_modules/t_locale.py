# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com

"""Select display languages for gettext"""

import ctypes
import logging
import os
import sys

MUI_LANGUAGE_NAME = 0x8
LANGUAGE_ENV_VARS = ("LANGUAGE", "LC_ALL", "LC_MESSAGES", "LANG")


def _windows_ui_languages() -> list[str] | None:
	"""Read the user's ordered Windows display languages"""
	try:
		get_languages = ctypes.WinDLL("kernel32").GetUserPreferredUILanguages
		get_languages.argtypes = [
			ctypes.c_ulong,
			ctypes.POINTER(ctypes.c_ulong),
			ctypes.POINTER(ctypes.c_wchar),
			ctypes.POINTER(ctypes.c_ulong),
		]
		get_languages.restype = ctypes.c_int
		count = ctypes.c_ulong()
		size = ctypes.c_ulong()
		if not get_languages(MUI_LANGUAGE_NAME, ctypes.byref(count), None, ctypes.byref(size)):
			logging.warning("Could not query Windows display language buffer size")
			return None
		if not size.value:
			return None
		buffer = ctypes.create_unicode_buffer(size.value)
		if not get_languages(MUI_LANGUAGE_NAME, ctypes.byref(count), buffer, ctypes.byref(size)):
			logging.warning("Could not read Windows display languages")
			return None
		languages = [name.replace("-", "_") for name in buffer[: size.value].split("\0") if name]
		# English has no catalog; C stops gettext from selecting a later language.
		return ["C" if name.split("_", 1)[0] == "en" else name for name in languages] or None
	except (AttributeError, OSError):
		logging.warning("Failed to detect Windows display languages", exc_info=True)
		return None


def get_translation_languages(ui_lang: str) -> list[str] | None:
	"""Keep explicit overrides, otherwise detect Windows display languages"""
	if ui_lang != "auto":
		return [ui_lang]
	if sys.platform != "win32" or any(os.environ.get(name) for name in LANGUAGE_ENV_VARS):
		return None
	return _windows_ui_languages()
