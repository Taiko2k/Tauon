#!/usr/bin/env python
"""Update language files from ./locale"""
import logging
import os
import subprocess
import sys
import sysconfig
from pathlib import Path


def find_pygettext() -> Path | None:
	"""Find pygettext.py, either in the standard stdlib dir or locally in the project"""
	stdlib = sysconfig.get_path("stdlib")
	path = Path(stdlib) / "Tools" / "i18n" / "pygettext.py"
	if path.exists():
		return path

	path = Path.cwd() / "pygettext.py"
	if path.exists():
		return path

	return None

def main() -> None:
	pygettext_path = find_pygettext()
	if not pygettext_path:
		logging.error("Please add a copy of pygettext.py to this dir from the Python Tools dir")
		sys.exit()

	locale_folder = Path("locale")
	pot_path = locale_folder / "messages.pot"

	logging.info("Generate template")

	root_dir = "src"
	# Collect all .py file paths
	py_files: list[str] = []
	for dirpath, _, filenames in os.walk(root_dir):
		py_files.extend(str(Path(dirpath) / file) for file in filenames if file.endswith(".py"))
	# Run pygettext.py with all .py files as arguments
	if py_files:
		_ = subprocess.run(["/usr/bin/python", str(pygettext_path), *py_files], check=True)  # noqa: S603

	logging.info("Copy template")
	_ = subprocess.run(["/usr/bin/cp", "messages.pot", pot_path], check=True)  # noqa: S603
	_ = subprocess.run(["/usr/bin/rm", "messages.pot"], check=True)

	languages = locale_folder.iterdir()

	for lang_file in languages:
		if lang_file.name == "messages.pot":
			continue

		po_path = locale_folder / lang_file.name / "LC_MESSAGES" / "tauon.po"

		if Path(po_path).exists():
			_ = subprocess.run(["/usr/bin/msgmerge", "-U", po_path, pot_path], check=True)  # noqa: S603

			logging.info(f"Updated: {lang_file.name}")

		else:
			logging.warning(f"Missing po file: {po_path}")

	logging.info("Done")

if __name__ == "__main__":
	main()
