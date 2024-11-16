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
	subprocess.run(["python", "pygettext.py", "t_modules/t_dbus.py", "t_modules/t_extra.py", "t_modules/t_jellyfin.py", "t_modules/t_main.py", "t_modules/t_phazor.py", "t_modules/t_spot.py", "t_modules/t_stream.py", "t_modules/t_tidal.py", "t_modules/t_webserve.py"])
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
