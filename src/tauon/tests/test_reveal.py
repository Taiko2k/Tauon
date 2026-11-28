"""Fallback order of t_reveal: FileManager1 then portal (reversed in Flatpak), then xdg-open"""

from __future__ import annotations

import sys
import types

import pytest

from tauon.t_modules import t_reveal


NO_REPLY = "org.freedesktop.DBus.Error.NoReply"


class FakeDBusException(Exception):
	def __init__(self, message, name="org.freedesktop.DBus.Error.Failed"):
		super().__init__(message)
		self.name = name

	def get_dbus_name(self):
		return self.name


class FakeObject:
	def __init__(self, bus, name):
		self.bus = bus
		self.name = name

	def Get(self, interface, prop, **_kw):
		if self.bus.portal_error:
			raise FakeDBusException("portal broken", self.bus.portal_error)
		return self.bus.portal_version

	def OpenDirectory(self, parent, fd, options, **_kw):
		self.bus.calls.append(("OpenDirectory", parent))
		self.bus.options.append(options)

	def ShowItems(self, uris, startup_id, **_kw):
		if self.bus.manager_error:
			raise FakeDBusException("manager broken", self.bus.manager_error)
		self.bus.calls.append(("ShowItems", uris))
		self.bus.startup_ids.append(startup_id)


class FakeBus:
	def __init__(self, names, portal_version=4, portal_error=None, manager_error=None):
		self.names = names
		self.portal_version = portal_version
		self.portal_error = portal_error
		self.manager_error = manager_error
		self.calls = []
		self.options = []
		self.startup_ids = []
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
	monkeypatch.setattr(t_reveal, "open_parent", lambda path, token=None: opened.append(path))

	def use(bus):
		fake = types.ModuleType("dbus")
		fake.SessionBus = lambda private=False: bus
		fake.types = types.SimpleNamespace(UnixFd=lambda fd: fd)
		fake.Dictionary = lambda value, signature=None: value
		fake.exceptions = types.SimpleNamespace(DBusException=FakeDBusException)
		monkeypatch.setitem(sys.modules, "dbus", fake)

	return str(track), opened, use


def uri(path):
	return f"file://{path.replace(' ', '%20')}"


def test_file_manager_first(setup):
	path, opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME})
	use(bus)
	assert t_reveal.reveal_file(path) == "FileManager1"
	assert bus.calls == [("ShowItems", [uri(path)])]
	assert opened == []
	assert bus.closed


def test_portal_first_in_flatpak(setup):
	path, opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME})
	use(bus)
	assert t_reveal.reveal_file(path, sandboxed=True) == "portal"
	assert bus.calls == [("OpenDirectory", "")]
	assert opened == []


@pytest.mark.parametrize("bus_kw", [
	{"names": {t_reveal.PORTAL_NAME}},
	{"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "manager_error": "org.freedesktop.DBus.Error.Failed"},
])
def test_portal_when_file_manager_unusable(setup, bus_kw):
	path, opened, use = setup
	bus = FakeBus(**bus_kw)
	use(bus)
	assert t_reveal.reveal_file(path) == "portal"
	assert bus.calls == [("OpenDirectory", "")]
	assert opened == []


@pytest.mark.parametrize("bus_kw", [
	{"names": {t_reveal.FILE_MANAGER_NAME}},
	{"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "portal_version": 2},
	{"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "portal_error": "org.freedesktop.DBus.Error.Failed"},
])
def test_file_manager_when_portal_unusable_in_flatpak(setup, bus_kw):
	path, opened, use = setup
	bus = FakeBus(**bus_kw)
	use(bus)
	assert t_reveal.reveal_file(path, sandboxed=True) == "FileManager1"
	assert bus.calls == [("ShowItems", [uri(path)])]
	assert opened == []


@pytest.mark.parametrize("bus_kw", [
	{"names": set()},
	{"names": {t_reveal.FILE_MANAGER_NAME}, "manager_error": "org.freedesktop.DBus.Error.Failed"},
])
def test_xdg_open_last(setup, bus_kw):
	path, opened, use = setup
	use(FakeBus(**bus_kw))
	assert t_reveal.reveal_file(path) == "xdg-open"
	assert opened == [path]


@pytest.mark.parametrize(("bus_kw", "sandboxed"), [
	({"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "manager_error": NO_REPLY}, False),
	({"names": {t_reveal.PORTAL_NAME, t_reveal.FILE_MANAGER_NAME}, "portal_error": NO_REPLY}, True),
])
def test_timeout_stops_fallback(setup, bus_kw, sandboxed):
	path, opened, use = setup
	bus = FakeBus(**bus_kw)
	use(bus)
	assert t_reveal.reveal_file(path, sandboxed=sandboxed) == "timeout"
	assert bus.calls == []
	assert opened == []
	assert bus.closed


def test_ignored_while_busy(setup):
	path, opened, use = setup
	bus = FakeBus({t_reveal.FILE_MANAGER_NAME})
	use(bus)
	with t_reveal.busy:
		assert t_reveal.reveal_file(path) == "busy"
	assert bus.calls == []
	assert t_reveal.reveal_file(path) == "FileManager1"


def test_missing_file_skips_dbus(setup):
	path, opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME})
	use(bus)
	assert t_reveal.reveal_file(path + ".gone") == "xdg-open"
	assert bus.calls == []


def test_token_reaches_portal_and_file_manager(setup):
	path, _opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME})
	use(bus)
	t_reveal.reveal_file(path, "tok-1")
	assert bus.options == [{"activation_token": "tok-1"}]

	bus = FakeBus({t_reveal.FILE_MANAGER_NAME})
	use(bus)
	t_reveal.reveal_file(path, "tok-2")
	assert bus.startup_ids == ["tok-2"]


def test_no_token_sends_empty_values(setup):
	path, _opened, use = setup
	bus = FakeBus({t_reveal.PORTAL_NAME})
	use(bus)
	t_reveal.reveal_file(path)
	assert bus.options == [{}]


def test_xdg_open_gets_token_in_env(monkeypatch, tmp_path):
	launched = []
	monkeypatch.setattr(t_reveal.subprocess, "Popen", lambda args, env=None: launched.append((args, env)))
	t_reveal.open_parent(str(tmp_path / "a.flac"), "tok-3")
	t_reveal.open_parent(str(tmp_path / "a.flac"))
	assert launched[0][1]["XDG_ACTIVATION_TOKEN"] == "tok-3"
	assert launched[1][1] is None
