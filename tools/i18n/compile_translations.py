"""Compile language files from the repository locale directory."""
import logging
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
	sys.path.insert(0, str(REPO_ROOT))

from src.tauon.t_modules.t_logging import CustomLoggingFormatter

# DEBUG+ to file and std_err
logging.basicConfig(
	level=logging.DEBUG,
	handlers=[
		logging.StreamHandler(),
#		logging.FileHandler('/tmp/tauon.log'),
	],
)
# INFO+ to std_err
logging.getLogger().handlers[0].setLevel(logging.INFO)
logging.getLogger().handlers[0].setFormatter(CustomLoggingFormatter())

def main() -> None:
	compile_failure = False
	locale_folder = REPO_ROOT / "locale"
	languages = locale_folder.iterdir()

	for lang_file in languages:

		if lang_file.name in ("messages.pot", ".DS_Store"):
			continue

		po_path = locale_folder / lang_file.name / "LC_MESSAGES" / "tauon.po"
#		mo_path = locale_folder / lang_file.name / "LC_MESSAGES" / "tauon.mo"
		mo_dirpath = REPO_ROOT / "src" / "tauon" / "locale" / lang_file.name / "LC_MESSAGES"
		mo_path = mo_dirpath / "tauon.mo"

		if not mo_path.exists():
			mo_dirpath.mkdir(parents=True)

		if po_path.exists():
			try:
				subprocess.run(["msgfmt", "-o", mo_path, po_path], check=True)
			except Exception:
				logging.exception(f"Failed to compile translations for {lang_file.name}")
				compile_failure = True
			else:
				logging.info(f"Compiled: {lang_file.name}")

		else:
			logging.critical(f"Missing po file: {po_path}")
	if compile_failure:
		raise Exception("Compiling had errors!")
	logging.info("Done")

if __name__ == "__main__":
	main()
