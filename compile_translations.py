"""Compile language files from ./locale"""
import os
import subprocess
from pathlib import Path


def main() -> None:
	locale_folder = "locale"
	languages = os.listdir(locale_folder)

	for lang_file in languages:

		if lang_file == "messages.pot":
			continue

		po_path = Path(locale_folder) / lang_file / "LC_MESSAGES" / "tauon.po"
		mo_path = Path(locale_folder) / lang_file / "LC_MESSAGES" / "tauon.mo"

		if Path(po_path).exists():
			subprocess.run(["msgfmt", "-o", mo_path, po_path])
			print(f"Compiled: {lang_file}")

		else:
			print(f"Missing po file: {po_path}")

	print("Done")

if __name__ == "__main__":
	main()
