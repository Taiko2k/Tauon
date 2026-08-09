"""Small structural boundaries shared by integration and leaf modules."""

from __future__ import annotations

from typing import Any, Protocol


class AppLike(Protocol):
	"""The stable application surface used by leaf modules.

	Most Tauon services still access feature-specific attributes. Keeping those
	attributes structural lets them retain their existing behavior without
	pulling the application coordinator into static analysis.
	"""

	pctl: Any
	gui: Any
	prefs: Any
	inp: Any
	renderer: Any
	window_size: Any
	dirs: Any
	ddt: Any
	fields: Any
	coll: Any

	def __getattr__(self, name: str) -> Any: ...


class StringsLike(Protocol):
	"""Structural type for the localized string container."""

	def __getattr__(self, name: str) -> str: ...
