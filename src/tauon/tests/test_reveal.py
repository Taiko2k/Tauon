"""Fallback order of t_reveal: portal, then FileManager1, then xdg-open"""

from __future__ import annotations

import sys
import types

import pytest

from tauon.t_modules import t_reveal


class FakeDBusException(Exception):
	pass


class FakeObject:
	def __init__(self, bus, name):
		self.bus = bus
		self.name = name

	def Get(self, interface, prop, **_kw):
		if self.bus.portal_error:
			raise FakeDBusException("portal broken")
		return self.bus.portal_version

	def OpenDirectory(self, parent, fd, options, **_kw):
		self.bus.calls.append(("OpenDirectory", parent))

	def ShowItems(self, uris, startup_id, **_kw):
		if self.bus.manager_error:
			raise FakeDBusException("no reply")
		self.bus.calls.append(("ShowItems", uris))


class FakeBus:
	def __init__(self, names, portal_version=4, portal_error=False, manager_error=False):
		self.names = names
		self.portal_version = portal_version
		self.portal_error = portal_error
		self.manager_error = manager_error
		self.calls = []
		self.closed = False

	def name_has_owner(self, name):
		return name in self.names

	def list_activatable_names(self):
		return []

	def get_object(self, name, _path, introspect=True):
		return FakeObject(self, name)

	def close(self):
		self.closed = True


@pytest.fixture
def setup(monkeypatch, tmp_path):
	track = tmp_path / "Album" / "01 song.flac"
	track.parent.mkdir()
	track.write_bytes(b"x")
	opened = []
	monkeypatch.setattr(t_reveal, "open_parent", lambda path: opened.append(path))

	def use(bus):
		fake = types.ModuleType("dbus")
		fake.SessionBus = lambda private=False: bus
		fake.types = types.SimpleNamespace(UnixFd=lambda fd: fd)
		fake.Dictionary = lambda value, signature=None: value
		fake.exceptions = types.SimpleNamespace(DBusException=FakeDBusException)
		monkeypatch.setitem(sys.modules, "dbus", fake)

	return str(track), opened, use


def test_portal_first(setup):
	path, opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME})
	use(bus)
	assert t_reveal.reveal_file(path) == "portal"
	assert bus.calls == [("OpenDirectory", "")]
	assert opened == []
	assert bus.closed


@pytest.mark.parametrize("bus_kw", [
	{"names": {t_reveal.FILE_MANAGER_NAME}},
	{"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "portal_version": 2},
	{"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "portal_error": True},
])
def test_file_manager_when_portal_unusable(setup, bus_kw):
	path, opened, use = setup
	bus = FakeBus(**bus_kw)
	use(bus)
	assert t_reveal.reveal_file(path) == "FileManager1"
	assert bus.calls == [("ShowItems", [f"file://{path.replace(' ', '%20')}"])]
	assert opened == []


@pytest.mark.parametrize("bus_kw", [
	{"names": set()},
	{"names": {t_reveal.FILE_MANAGER_NAME}, "manager_error": True},
])
def test_xdg_open_last(setup, bus_kw):
	path, opened, use = setup
	use(FakeBus(**bus_kw))
	assert t_reveal.reveal_file(path) == "xdg-open"
	assert opened == [path]


def test_missing_file_skips_dbus(setup):
	path, opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME})
	use(bus)
	assert t_reveal.reveal_file(path + ".gone") == "xdg-open"
	assert bus.calls == []
