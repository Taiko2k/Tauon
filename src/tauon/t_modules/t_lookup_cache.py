# Copyright © 2026, Tauon contributors

"""Bounded, session-only caches for file fingerprints and lookup responses."""

from __future__ import annotations

import copy
import hashlib
import json
import threading
from collections import OrderedDict

CACHE_LIMIT = 300


def cache_key(parts: object) -> str:
	"""Normalize request parameters and keep credentials out of cache keys."""
	return hashlib.sha256(json.dumps(parts, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class LookupCache:
	def __init__(self) -> None:
		self.lock = threading.Lock()
		self.values: dict[str, OrderedDict[str, str | dict]] = {
			"fingerprint": OrderedDict(),
			"request": OrderedDict(),
		}

	def get(self, kind: str, key: str) -> str | dict | None:
		with self.lock:
			cache = self.values[kind]
			if key not in cache:
				return None
			cache.move_to_end(key)
			return copy.deepcopy(cache[key])

	def put(self, kind: str, key: str, value: str | dict) -> None:
		with self.lock:
			cache = self.values[kind]
			cache[key] = copy.deepcopy(value)
			cache.move_to_end(key)
			while len(cache) > CACHE_LIMIT:
				cache.popitem(last=False)
