"""Shared test setup.

The tauon_native bridge is built into the tauon-native executable and does not
exist in a plain Python test run. With src on sys.path, `import tauon_native`
would otherwise find the C++ source directory as an empty namespace package.
Tests never draw, so stand in a mock for the bridge before anything imports it.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

if not hasattr(sys.modules.get("tauon_native"), "poll_events"):
	bridge = MagicMock(name="tauon_native")
	bridge.is_active.return_value = False
	sys.modules["tauon_native"] = bridge
