#!/usr/bin/env python3
"""Assemble relocatable Tauon bundles around the native launcher."""

from __future__ import annotations

import argparse
import os
import plistlib
import re
import shutil
import stat
import subprocess
import sys
import sysconfig
from collections import deque
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON_TOOL_PACKAGES = {
	"-distutils-hack",
	"-pytest",
	"build",
	"cython",
	"iniconfig",
	"pip",
	"pkg-resources",
	"pyproject-hooks",
	"pytest",
	"setuptools",
	"wheel",
}
STDLIB_EXCLUDES = {
	"__pycache__",
	"ensurepip",
	"idlelib",
	"lib2to3",
	"site-packages",
	"test",
	"tests",
	"tkinter",
	"turtledemo",
	"venv",
}
LINUX_SYSTEM_LIBRARIES = {
	"ld-linux-aarch64.so.1",
	"ld-linux-x86-64.so.2",
	"libBrokenLocale.so.1",
	"libanl.so.1",
	"libc.so.6",
	"libdl.so.2",
	"libm.so.6",
	"libnss_compat.so.2",
	"libnss_dns.so.2",
	"libnss_files.so.2",
	"libnss_hesiod.so.2",
	"libpthread.so.0",
	"libresolv.so.2",
	"librt.so.1",
	"libutil.so.1",
}
GI_NAMESPACES = (
	("Gtk", "3.0"),
	("GdkPixbuf", "2.0"),
	("Pango", "1.0"),
	("PangoCairo", "1.0"),
	("Rsvg", "2.0"),
	("Notify", "0.8"),
	("Notify", "0.7"),
)


def run(command: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
	return subprocess.run(command, check=check, capture_output=True, text=True)


def remove_existing(path: Path) -> None:
	if path.is_symlink() or path.is_file():
		path.unlink()
	elif path.is_dir():
		shutil.rmtree(path)


def copy_tree(source: Path, destination: Path, *, ignore=None) -> None:
	if not source.is_dir():
		return
	shutil.copytree(source, destination, dirs_exist_ok=True, symlinks=True, ignore=ignore)


def stdlib_ignore(directory: str, names: list[str]) -> set[str]:
	ignored = {name for name in names if name in STDLIB_EXCLUDES or name.endswith((".pyc", ".pyo"))}
	if Path(directory).name == "__pycache__":
		ignored.update(names)
	return ignored


def site_packages_ignore(directory: str, names: list[str]) -> set[str]:
	ignored = {name for name in names if name == "__pycache__" or name.endswith((".pyc", ".pyo"))}
	for name in names:
		normalized = re.sub(r"[-_.]+", "-", name).lower()
		if normalized in PYTHON_TOOL_PACKAGES or any(
			normalized.startswith(f"{tool_name}-") for tool_name in PYTHON_TOOL_PACKAGES
		):
			ignored.add(name)
	return ignored


def active_site_packages() -> list[Path]:
	paths: list[Path] = []
	for scheme_name in ("purelib", "platlib"):
		value = sysconfig.get_path(scheme_name)
		if value:
			path = Path(value).resolve()
			if path.is_dir() and path not in paths:
				paths.append(path)
	return paths


def copy_python_runtime(python_root: Path) -> Path:
	stdlib_source = Path(sysconfig.get_path("stdlib")).resolve()
	if not (stdlib_source / "encodings").is_dir():
		raise RuntimeError(f"Python standard library is incomplete: {stdlib_source}")
	copy_tree(stdlib_source, python_root / "stdlib", ignore=stdlib_ignore)

	site_destination = python_root / "site-packages"
	for site_source in active_site_packages():
		copy_tree(site_source, site_destination, ignore=site_packages_ignore)

	tauon_package = site_destination / "tauon"
	if not (tauon_package / "__main__.py").is_file():
		raise RuntimeError(
			"Tauon is not installed in the active Python environment; install the freshly built wheel before staging"
		)
	return tauon_package


def copy_optional_file(source: Path, destination: Path, *, executable: bool = False) -> bool:
	if not source.is_file():
		return False
	destination.parent.mkdir(parents=True, exist_ok=True)
	shutil.copy2(source, destination)
	if executable:
		destination.chmod(destination.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
	return True


def copy_application_extras(tauon_package: Path, platform_name: str) -> None:
	copy_tree(REPO_ROOT / "fonts", tauon_package / "fonts")

	solver_name = "lrclib-solver.exe" if platform_name == "windows" else "lrclib-solver"
	copy_optional_file(REPO_ROOT / solver_name, tauon_package / solver_name, executable=True)

	if platform_name == "windows":
		copy_optional_file(REPO_ROOT / "TauonSMTC.dll", tauon_package / "lib" / "TauonSMTC.dll")
	elif platform_name == "macos":
		copy_tree(
			REPO_ROOT / "src" / "nowplaying" / "build" / "TauonNowPlaying.app",
			tauon_package / "lib" / "TauonNowPlaying.app",
		)
		ffmpeg = shutil.which("ffmpeg")
		if ffmpeg:
			copy_optional_file(Path(ffmpeg), tauon_package / "ffmpeg", executable=True)


def copy_runtime_data(internal_root: Path) -> None:
	prefixes = [Path(sys.base_prefix), Path(sys.prefix)]
	typelib_dest = internal_root / "lib" / "girepository-1.0"
	for prefix in prefixes:
		for relative in (
			Path("lib/girepository-1.0"),
			Path("lib64/girepository-1.0"),
			Path("lib/x86_64-linux-gnu/girepository-1.0"),
			Path("lib/aarch64-linux-gnu/girepository-1.0"),
		):
			copy_tree(prefix / relative, typelib_dest)
		copy_tree(prefix / "share" / "glib-2.0" / "schemas", internal_root / "share" / "glib-2.0" / "schemas")
		copy_tree(prefix / "etc" / "fonts", internal_root / "etc" / "fonts")

	try:
		typelib_directory = run(
			["pkg-config", "--variable=typelibdir", "gobject-introspection-1.0"],
			check=False,
		).stdout.strip()
	except FileNotFoundError:
		typelib_directory = ""
	if typelib_directory:
		copy_tree(Path(typelib_directory), typelib_dest)
	try:
		glib_prefix = run(["pkg-config", "--variable=prefix", "glib-2.0"], check=False).stdout.strip()
	except FileNotFoundError:
		glib_prefix = ""
	if glib_prefix:
		prefix = Path(glib_prefix)
		copy_tree(prefix / "share" / "glib-2.0" / "schemas", internal_root / "share" / "glib-2.0" / "schemas")
		copy_tree(prefix / "etc" / "fonts", internal_root / "etc" / "fonts")
	try:
		fontconfig_directory = run(["pkg-config", "--variable=confdir", "fontconfig"], check=False).stdout.strip()
	except FileNotFoundError:
		fontconfig_directory = ""
	if fontconfig_directory:
		copy_tree(Path(fontconfig_directory), internal_root / "etc" / "fonts")


def gi_shared_library_names() -> set[str]:
	inspector = shutil.which("g-ir-inspect")
	if inspector is None:
		return set()
	names: set[str] = set()
	for namespace, version in GI_NAMESPACES:
		result = run(
			[inspector, namespace, f"--version={version}", "--print-shlibs"],
			check=False,
		)
		if result.returncode != 0:
			continue
		for line in result.stdout.splitlines():
			if line.startswith("shlib:"):
				names.update(name.strip() for name in line.removeprefix("shlib:").split(",") if name.strip())
	return names


def library_search_directories() -> list[Path]:
	directories = [
		Path(sys.prefix) / "bin",
		Path(sys.prefix) / "lib",
		Path(sys.base_prefix) / "bin",
		Path(sys.base_prefix) / "lib",
	]
	for package in ("glib-2.0", "gtk+-3.0", "gdk-pixbuf-2.0", "pango", "librsvg-2.0", "libnotify"):
		result = run(["pkg-config", "--variable=prefix", package], check=False)
		if result.returncode == 0 and result.stdout.strip():
			prefix = Path(result.stdout.strip())
			directories.extend((prefix / "bin", prefix / "lib"))
	return list(dict.fromkeys(directory.resolve() for directory in directories if directory.is_dir()))


def locate_shared_library(name: str, search_directories: list[Path]) -> Path | None:
	command_path = shutil.which(name)
	if command_path:
		return Path(command_path).resolve()
	for directory in search_directories:
		candidate = directory / name
		if candidate.is_file():
			return candidate.resolve()
	if sys.platform.startswith("linux"):
		result = run(["ldconfig", "-p"], check=False)
		for line in result.stdout.splitlines():
			match = re.match(rf"\s*{re.escape(name)}\s+.*=>\s+(\S+)", line)
			if match:
				candidate = Path(match.group(1))
				if candidate.is_file():
					return candidate.resolve()
	return None


def copy_gi_shared_libraries(destination: Path) -> None:
	destination.mkdir(parents=True, exist_ok=True)
	search_directories = library_search_directories()
	missing: list[str] = []
	for name in sorted(gi_shared_library_names()):
		source = locate_shared_library(name, search_directories)
		if source is None:
			missing.append(name)
			continue
		shutil.copy2(source, destination / source.name)
	if missing:
		raise RuntimeError(f"unable to locate GI shared libraries: {', '.join(missing)}")


def parse_ldd(binary: Path) -> set[tuple[str, Path]]:
	try:
		result = run(["ldd", str(binary)], check=False)
	except FileNotFoundError:
		return set()
	dependencies: set[tuple[str, Path]] = set()
	for line in result.stdout.splitlines():
		match = re.match(r"\s*(\S+)\s+=>\s+(\S+)\s+\(0x", line)
		if match is not None:
			name = match.group(1)
			path = Path(match.group(2))
		else:
			match = re.match(r"\s*(/\S+)\s+\(0x", line)
			if match is None:
				continue
			path = Path(match.group(1))
			name = path.name
		if path.is_file():
			dependencies.add((name, path.resolve()))
	return dependencies


def windows_imports(binary: Path) -> set[str]:
	try:
		result = run(["objdump", "-p", str(binary)], check=False)
	except FileNotFoundError:
		return set()
	imports: set[str] = set()
	for line in result.stdout.splitlines():
		match = re.match(r"\s*DLL Name:\s*(\S+)", line)
		if match is not None:
			imports.add(match.group(1))
	return imports


def collect_windows_dependencies(bundle_root: Path) -> None:
	queue = deque(
		path
		for path in bundle_root.rglob("*")
		if path.is_file() and path.suffix.lower() in {".exe", ".dll", ".pyd"}
	)
	seen: set[Path] = set()
	search_directories = library_search_directories()
	while queue:
		binary = queue.popleft()
		for name in windows_imports(binary):
			dependency = locate_shared_library(name, search_directories)
			if dependency is None:
				continue
			if dependency in seen:
				continue
			seen.add(dependency)
			dependency_text = dependency.as_posix().lower()
			if "/windows/system32/" in dependency_text or "/windows/syswow64/" in dependency_text:
				continue
			destination = bundle_root / dependency.name
			if not destination.exists():
				shutil.copy2(dependency, destination)
				queue.append(destination)


def elf_files(bundle_root: Path) -> list[Path]:
	files: list[Path] = []
	for path in bundle_root.rglob("*"):
		if not path.is_file() or path.is_symlink():
			continue
		try:
			with path.open("rb") as file_handle:
				header = file_handle.read(18)
			if header[:4] != b"\x7fELF" or len(header) < 18:
				continue
			if header[5] == 1:
				byte_order = "little"
			elif header[5] == 2:
				byte_order = "big"
			else:
				continue
			elf_type = int.from_bytes(header[16:18], byte_order)
			# patchelf can only update executables and shared objects, not
			# relocatable files such as Python's static-library object files.
			if elf_type in {2, 3}:  # ET_EXEC, ET_DYN
				files.append(path)
		except OSError:
			continue
	return files


def collect_linux_dependencies(bundle_root: Path, executable: Path, internal_root: Path) -> None:
	library_directory = internal_root / "lib"
	library_directory.mkdir(parents=True, exist_ok=True)
	queue = deque(elf_files(bundle_root))
	seen: set[tuple[str, Path]] = set()
	while queue:
		binary = queue.popleft()
		for dependency_name, dependency in parse_ldd(binary):
			key = (dependency_name, dependency)
			if key in seen or dependency_name in LINUX_SYSTEM_LIBRARIES:
				continue
			seen.add(key)
			destination = library_directory / dependency_name
			if not destination.exists():
				shutil.copy2(dependency, destination)
				queue.append(destination)

	patchelf = shutil.which("patchelf")
	if patchelf is None:
		raise RuntimeError("patchelf is required to make the Linux bundle relocatable")
	for binary in elf_files(bundle_root):
		if binary == executable:
			rpath = "$ORIGIN/_internal/lib"
		elif binary.parent == library_directory:
			rpath = "$ORIGIN"
		else:
			relative = os.path.relpath(library_directory, binary.parent)
			rpath = f"$ORIGIN/{relative}"
		run([patchelf, "--set-rpath", rpath, str(binary)])


def macho_files(bundle_root: Path) -> list[Path]:
	macho_magics = {
		b"\xbe\xba\xfe\xca",
		b"\xca\xfe\xba\xbe",
		b"\xce\xfa\xed\xfe",
		b"\xcf\xfa\xed\xfe",
		b"\xfe\xed\xfa\xce",
		b"\xfe\xed\xfa\xcf",
	}
	files: list[Path] = []
	for path in bundle_root.rglob("*"):
		if not path.is_file() or path.is_symlink():
			continue
		try:
			with path.open("rb") as file_handle:
				if file_handle.read(4) in macho_magics:
					files.append(path)
		except OSError:
			continue
	return files


def macos_dependencies(binary: Path) -> list[str]:
	result = run(["otool", "-L", str(binary)], check=False)
	dependencies: list[str] = []
	for line in result.stdout.splitlines():
		# Universal binaries repeat an unindented "<path> (architecture ...):"
		# header for each slice. Only the indented rows are load commands.
		if not line[:1].isspace():
			continue
		value = line.strip().split(" (compatibility", 1)[0]
		if value and value not in dependencies:
			dependencies.append(value)
	return dependencies


def macos_rpaths(binary: Path) -> list[str]:
	result = run(["otool", "-l", str(binary)], check=False)
	rpaths: list[str] = []
	expect_path = False
	for line in result.stdout.splitlines():
		stripped = line.strip()
		if stripped == "cmd LC_RPATH":
			expect_path = True
			continue
		if expect_path and stripped.startswith("path "):
			value = stripped.removeprefix("path ").rsplit(" (offset ", 1)[0]
			if value not in rpaths:
				rpaths.append(value)
			expect_path = False
	return rpaths


def resolve_macos_dependency(dependency: str, consumer: Path, search_roots: list[Path]) -> Path | None:
	if dependency.startswith("/"):
		path = Path(dependency)
		if path.exists():
			return path.resolve()
	if dependency.startswith("@loader_path/"):
		path = consumer.parent / dependency.removeprefix("@loader_path/")
		return path.resolve() if path.exists() else None
	if dependency.startswith("@executable_path/"):
		return None
	name = Path(dependency).name
	for root in [consumer.parent, *search_roots]:
		path = root / name
		if path.exists():
			return path.resolve()
	return None


def framework_parts(path: Path) -> tuple[Path, Path] | None:
	parts = path.parts
	for index, part in enumerate(parts):
		if part.endswith(".framework"):
			root = Path(*parts[: index + 1])
			relative = Path(*parts[index:])
			return root, relative
	return None


def python_framework_ignore(directory: str, names: list[str]) -> set[str]:
	if Path(directory).name.startswith("Versions"):
		return set()
	if Path(directory).name == "Resources":
		return {name for name in names if name == "Python.app"}
	return {name for name in names if name in {"Headers", "bin", "include", "lib", "share"}}


def collect_macos_dependencies(app_root: Path, executable: Path, frameworks: Path) -> None:
	frameworks.mkdir(parents=True, exist_ok=True)
	brew_prefix = run(["brew", "--prefix"], check=False).stdout.strip()
	search_roots = [
		frameworks,
		REPO_ROOT / "build" / "projectm" / "lib",
		Path(sys.base_prefix) / "lib",
	]
	if brew_prefix:
		search_roots.append(Path(brew_prefix) / "lib")

	queue = deque(macho_files(app_root))
	seen: set[Path] = set()
	while queue:
		consumer = queue.popleft()
		for dependency in macos_dependencies(consumer):
			if dependency.startswith(("/System/Library/", "/usr/lib/")):
				continue
			source = resolve_macos_dependency(dependency, consumer, search_roots)
			if source is None:
				continue
			source = source.resolve()
			framework = framework_parts(source)
			if framework is not None:
				framework_root, framework_relative = framework
				destination_root = frameworks / framework_root.name
				if not destination_root.exists():
					ignore = python_framework_ignore if framework_root.name == "Python.framework" else None
					copy_tree(framework_root, destination_root, ignore=ignore)
				destination = frameworks / framework_relative
				replacement = f"@rpath/{framework_relative.as_posix()}"
			else:
				destination = frameworks / source.name
				replacement = f"@rpath/{source.name}"
				if not destination.exists():
					shutil.copy2(source, destination)
			if consumer.resolve() in {source.resolve(), destination.resolve()}:
				run(["install_name_tool", "-id", replacement, str(consumer)], check=False)
			else:
				run(["install_name_tool", "-change", dependency, replacement, str(consumer)])
			if destination not in seen:
				seen.add(destination)
				queue.append(destination)

	for binary in macho_files(app_root):
		for rpath in macos_rpaths(binary):
			if rpath.startswith("/"):
				run(["install_name_tool", "-delete_rpath", rpath, str(binary)])
		relative_frameworks = os.path.relpath(frameworks, binary.parent)
		run(
			["install_name_tool", "-add_rpath", f"@loader_path/{relative_frameworks}", str(binary)],
			check=False,
		)
		if binary.parent == frameworks and binary.suffix == ".dylib":
			run(["install_name_tool", "-id", f"@rpath/{binary.name}", str(binary)], check=False)

	for binary in macho_files(app_root):
		for dependency in macos_dependencies(binary):
			if dependency.startswith("/") and not dependency.startswith(("/System/Library/", "/usr/lib/")):
				raise RuntimeError(f"Unrelocated dependency in {binary}: {dependency}")
		for rpath in macos_rpaths(binary):
			if rpath.startswith("/"):
				raise RuntimeError(f"Unrelocated rpath in {binary}: {rpath}")


def ad_hoc_sign_macos(app_root: Path) -> None:
	codesign = shutil.which("codesign")
	if codesign is None:
		raise RuntimeError("codesign is required to make the relocated macOS app runnable")
	for binary in macho_files(app_root):
		run([codesign, "--force", "--sign", "-", str(binary)])
	nested_bundles = sorted(
		(
			path
			for path in app_root.rglob("*")
			if path.is_dir() and path.suffix in {".app", ".framework"}
		),
		key=lambda path: len(path.parts),
		reverse=True,
	)
	for bundle in nested_bundles:
		run([codesign, "--force", "--sign", "-", str(bundle)])
	run([codesign, "--force", "--sign", "-", str(app_root)])


def create_macos_plist(contents: Path, version: str) -> None:
	document = {
		"CFBundleDevelopmentRegion": "en",
		"CFBundleDisplayName": "Tauon",
		"CFBundleExecutable": "Tauon",
		"CFBundleIconFile": "tau-mac.icns",
		"CFBundleIdentifier": "com.github.taiko2k.tauonmb",
		"CFBundleInfoDictionaryVersion": "6.0",
		"CFBundleName": "Tauon",
		"CFBundlePackageType": "APPL",
		"CFBundleShortVersionString": version,
		"CFBundleVersion": version,
		"LSMinimumSystemVersion": "13.0",
		"NSHighResolutionCapable": True,
	}
	with (contents / "Info.plist").open("wb") as file_handle:
		plistlib.dump(document, file_handle)


def read_version() -> str:
	import tomllib

	with (REPO_ROOT / "pyproject.toml").open("rb") as file_handle:
		return str(tomllib.load(file_handle)["project"]["version"])


def stage_bundle(arguments: argparse.Namespace) -> Path:
	output = arguments.output.resolve()
	protected_paths = {
		Path("/"),
		Path.home().resolve(),
		Path.cwd().resolve(),
		REPO_ROOT,
		REPO_ROOT.parent,
	}
	if output in protected_paths:
		raise RuntimeError(f"refusing to replace protected output directory: {output}")
	remove_existing(output)

	if arguments.platform == "macos":
		app_root = output / "Tauon.app"
		contents = app_root / "Contents"
		executable = contents / "MacOS" / "Tauon"
		internal_root = contents / "Resources"
		python_root = internal_root / "python"
		frameworks = contents / "Frameworks"
		executable.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(arguments.native, executable)
		executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
		create_macos_plist(contents, read_version())
		copy_optional_file(
			REPO_ROOT / "src" / "tauon" / "assets" / "tau-mac.icns",
			contents / "Resources" / "tau-mac.icns",
		)
		copy_optional_file(
			REPO_ROOT / "src" / "tauon" / "assets" / "Assets.car",
			contents / "Resources" / "Assets.car",
		)
	else:
		app_root = output / "TauonMusicBox"
		executable_name = "Tauon Music Box.exe" if arguments.platform == "windows" else "tauon"
		executable = app_root / executable_name
		internal_root = app_root / "_internal"
		python_root = internal_root / "python"
		app_root.mkdir(parents=True, exist_ok=True)
		shutil.copy2(arguments.native, executable)
		executable.chmod(executable.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

	tauon_package = copy_python_runtime(python_root)
	copy_application_extras(tauon_package, arguments.platform)
	copy_runtime_data(internal_root)
	if arguments.platform == "macos":
		copy_gi_shared_libraries(frameworks)
	elif arguments.platform == "windows":
		copy_gi_shared_libraries(app_root)
	else:
		copy_gi_shared_libraries(internal_root / "lib")

	if arguments.projectm:
		projectm_name = Path(arguments.projectm).name
		copy_optional_file(Path(arguments.projectm), executable.parent / projectm_name)

	if arguments.portable:
		(executable.parent / "portable").touch()

	if arguments.platform == "windows":
		collect_windows_dependencies(app_root)
	elif arguments.platform == "linux":
		collect_linux_dependencies(app_root, executable, internal_root)
	else:
		collect_macos_dependencies(app_root, executable, frameworks)
		ad_hoc_sign_macos(app_root)

	return app_root


def parse_arguments() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument("--platform", choices=("linux", "macos", "windows"), required=True)
	parser.add_argument("--native", type=Path, required=True, help="Built tauon-native executable")
	parser.add_argument("--output", type=Path, required=True, help="Directory that will receive the bundle")
	parser.add_argument("--projectm", type=Path, help="Optional projectM shared library")
	parser.add_argument("--portable", action="store_true", help="Create a portable marker beside the native executable")
	arguments = parser.parse_args()
	if not arguments.native.is_file():
		parser.error(f"native executable does not exist: {arguments.native}")
	if arguments.projectm and not arguments.projectm.is_file():
		parser.error(f"projectM library does not exist: {arguments.projectm}")
	return arguments


def main() -> int:
	arguments = parse_arguments()
	app_root = stage_bundle(arguments)
	print(app_root)
	return 0


if __name__ == "__main__":
	raise SystemExit(main())
