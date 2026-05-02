#!/usr/bin/env python
"""Update language files from the repository locale directory."""
import logging
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def existing_path(path: Path) -> Path | None:
	return path if path.exists() else None


def homebrew_prefixes() -> list[Path]:
	"""Return possible Homebrew prefixes on macOS."""
	prefixes: list[Path] = []
	brew = shutil.which("brew")
	if brew:
		try:
			result = subprocess.run([brew, "--prefix"], capture_output=True, check=True, text=True)  # noqa: S603
		except (OSError, subprocess.CalledProcessError):
			pass
		else:
			prefix = Path(result.stdout.strip())
			if prefix.exists():
				prefixes.append(prefix)

	for path in (Path("/opt/homebrew"), Path("/usr/local")):
		if path.exists() and path not in prefixes:
			prefixes.append(path)

	return prefixes


def homebrew_pygettext_candidates() -> list[Path]:
	"""Find pygettext.py in Homebrew Python installs."""
	candidates: list[Path] = []
	for prefix in homebrew_prefixes():
		for base in (prefix / "opt", prefix / "Cellar"):
			if not base.exists():
				continue
			candidates.extend(base.glob("python*/**/Tools/i18n/pygettext.py"))
			candidates.extend(base.glob("python*/**/examples/Tools/i18n/pygettext.py"))
	return candidates


def find_executable(name: str) -> Path | None:
	"""Find an executable on PATH or in common Homebrew locations."""
	path = shutil.which(name)
	if path:
		return Path(path)

	if sys.platform == "darwin":
		for prefix in homebrew_prefixes():
			for candidate in (
				prefix / "bin" / name,
				prefix / "opt" / "gettext" / "bin" / name,
			):
				if candidate.exists():
					return candidate

	return None


def find_pygettext() -> Path | None:
	"""Find pygettext.py locally, on PATH, in stdlib, or in Homebrew Python."""
	path = existing_path(REPO_ROOT / "pygettext.py")
	if path:
		return path

	path_on_path = shutil.which("pygettext.py")
	if path_on_path:
		return Path(path_on_path)

	stdlib = sysconfig.get_path("stdlib")
	path = Path(stdlib) / "Tools" / "i18n" / "pygettext.py"
	if path.exists():
		return path

	if sys.platform == "darwin":
		for path in homebrew_pygettext_candidates():
			if path.exists():
				return path

	return None

def main() -> None:
	pygettext_path = find_pygettext()
	if not pygettext_path:
		logging.error("Please add a copy of pygettext.py to the repository root from the Python Tools dir")
		sys.exit()
	msgmerge_path = find_executable("msgmerge")
	if not msgmerge_path:
		logging.error("Unable to find msgmerge. Please install gettext and ensure msgmerge is on PATH")
		sys.exit()

	locale_folder = REPO_ROOT / "locale"
	pot_path = locale_folder / "messages.pot"

	logging.info("Generate template")

	root_dir = REPO_ROOT / "src"
	# Collect all .py file paths
	py_files: list[str] = []
	for dirpath, _, filenames in os.walk(root_dir):
		py_files.extend(str((Path(dirpath) / file).relative_to(REPO_ROOT)) for file in filenames if file.endswith(".py"))
	# Run pygettext.py with all .py files as arguments
	if py_files:
		_ = subprocess.run([sys.executable, str(pygettext_path), *py_files], check=True, cwd=REPO_ROOT)  # noqa: S603

	logging.info("Copy template")
	(REPO_ROOT / "messages.pot").replace(pot_path)

	languages = locale_folder.iterdir()

	for lang_file in languages:
		if lang_file.name == "messages.pot":
			continue

		po_path = locale_folder / lang_file.name / "LC_MESSAGES" / "tauon.po"

		if po_path.exists():
			_ = subprocess.run([str(msgmerge_path), "-U", str(po_path), str(pot_path)], check=True)  # noqa: S603

			logging.info(f"Updated: {lang_file.name}")

		else:
			logging.warning(f"Missing po file: {po_path}")

	logging.info("Done")

if __name__ == "__main__":
	main()
