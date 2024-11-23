"""Update language files from ./locale"""
import os
import subprocess
import sys
from pathlib import Path


def main() -> None:
	if not Path("pygettext.py").is_file():
		print("ERROR: Please add a copy of pygettext.py to this dir from the Python Tools dir")
		sys.exit()

	locale_folder = "locale"
	pot_path = Path(locale_folder) / "messages.pot"

	print("Generate template")

	root_dir = "src"
	# Collect all .py file paths
	py_files = []
	for dirpath, _, filenames in os.walk(root_dir):
		py_files.extend(os.path.join(dirpath, file) for file in filenames if file.endswith(".py"))
	# Run pygettext.py with all .py files as arguments
	if py_files:
		subprocess.run(["python", "pygettext.py", *py_files], check=True)

	print("Copy template")
	subprocess.run(["cp", "messages.pot", pot_path])
	subprocess.run(["rm", "messages.pot"])

	languages = os.listdir(locale_folder)

	for lang_file in languages:
		if lang_file == "messages.pot":
			continue

		po_path = Path(locale_folder) / lang_file / "LC_MESSAGES" / "tauon.po"

		if Path(po_path).exists():
			subprocess.run(["msgmerge", "-U", po_path, pot_path])

			print(f"Updated: {lang_file}")

		else:
			print(f"Missing po file: {po_path}")

	print("Done")

if __name__ == "__main__":
	main()
