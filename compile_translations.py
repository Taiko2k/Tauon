"""Compile language files from ./locale"""
import logging
import os
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
	locale_folder = "locale"
	languages = os.listdir(locale_folder)

	for lang_file in languages:

		if lang_file == "messages.pot":
			continue

		po_path = Path(locale_folder) / lang_file / "LC_MESSAGES" / "tauon.po"
		mo_path = Path(locale_folder) / lang_file / "LC_MESSAGES" / "tauon.mo"

		if Path(po_path).exists():
			subprocess.run(["msgfmt", "-o", mo_path, po_path], check=True)
			logging.info(f"Compiled: {lang_file}")

		else:
			logging.critical(f"Missing po file: {po_path}")

	logging.info("Done")

if __name__ == "__main__":
	main()
