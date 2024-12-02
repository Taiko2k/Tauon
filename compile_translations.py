"""Compile language files from ./locale"""
import logging
import subprocess
from pathlib import Path


# TODO(Martin): import this class from tauon.py instead
class CustomLoggingFormatter(logging.Formatter):
	"""Nicely format logging.loglevel logs"""

	grey        = "\x1b[38;20m"
	grey_bold   = "\x1b[38;1m"
	yellow      = "\x1b[33;20m"
	yellow_bold = "\x1b[33;1m"
	red         = "\x1b[31;20m"
	bold_red    = "\x1b[31;1m"
	reset       = "\x1b[0m"
	format         = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s"
	format_verbose = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s (%(filename)s:%(lineno)d)"

	FORMATS = {
		logging.DEBUG:    grey_bold   + format_verbose + reset,
		logging.INFO:     yellow      + format         + reset,
		logging.WARNING:  yellow_bold + format         + reset,
		logging.ERROR:    red         + format         + reset,
		logging.CRITICAL: bold_red    + format_verbose + reset,
	}

	def format(self, record: dict) -> str:
		log_fmt = self.FORMATS.get(record.levelno)
		# Remove the miliseconds(%f) from the default string
		date_fmt = "%Y-%m-%d %H:%M:%S"
		formatter = logging.Formatter(log_fmt, date_fmt)
		# Center align + min length things to prevent logs jumping around when switching between different values
		record.levelname = f"{record.levelname:^7}"
		record.module = f"{record.module:^10}"
		return formatter.format(record)

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
	script_dir = Path(__file__).parent
	locale_folder = script_dir / "locale"
	languages = locale_folder.iterdir()

	for lang_file in languages:

		if lang_file.name == "messages.pot":
			continue

		po_path = locale_folder / lang_file.name / "LC_MESSAGES" / "tauon.po"
#		mo_path = locale_folder / lang_file.name / "LC_MESSAGES" / "tauon.mo"
		mo_dirpath = script_dir / "src" / "tauon" / "locale" / lang_file.name / "LC_MESSAGES"
		mo_path = mo_dirpath / "tauon.mo"

		if not mo_path.exists():
			(mo_dirpath).mkdir(parents=True)

		if po_path.exists():
			try:
				subprocess.run(["/usr/bin/msgfmt", "-o", mo_path, po_path], check=True)
			except Exception:
				# Don't log the exception to make the build log clear
				logging.error(f"Failed to compile translations for {lang_file.name}")
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
