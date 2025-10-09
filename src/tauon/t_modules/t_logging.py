import logging
from logging import LogRecord
from typing import override


class CustomLoggingFormatter(logging.Formatter):
	"""Nicely format logging.loglevel logs"""

	# fmt:off
	grey        = "\x1b[0;20m"
	grey_bold   = "\x1b[0;1m"
	yellow      = "\x1b[33;20m"
	yellow_bold = "\x1b[33;1m"
	red         = "\x1b[31;20m"
	bold_red    = "\x1b[31;1m"
	purple      = "\x1b[0;35m"
	reset       = "\x1b[0m"
	format_simple  = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s"
	format_verbose = "%(asctime)s [%(levelname)s] [%(module)s] %(message)s (%(filename)s:%(lineno)d)"
	# fmt:on

	def __init__(self, color: bool = True):
		super().__init__()
		self.color = color

		# TODO(Martin): Add a way in which devel mode uses everything verbose
		# fmt:off
		if color:
			self.FORMATS = {
				logging.DEBUG:    self.grey_bold   + self.format_verbose + self.reset,
				logging.INFO:     self.grey        + self.format_simple  + self.reset,
				logging.WARNING:  self.purple      + self.format_verbose + self.reset,
				logging.ERROR:    self.red         + self.format_verbose + self.reset,
				logging.CRITICAL: self.bold_red    + self.format_verbose + self.reset,
			}
		else:
			self.FORMATS = {
				logging.DEBUG:    self.format_verbose,
				logging.INFO:     self.format_simple,
				logging.WARNING:  self.format_verbose,
				logging.ERROR:    self.format_verbose,
				logging.CRITICAL: self.format_verbose,
			}
		# fmt:on

	@override
	def format(self, record: LogRecord) -> str:
		log_fmt = self.FORMATS.get(record.levelno)
		# Remove the miliseconds(%f) from the default string
		date_fmt = "%Y-%m-%d %H:%M:%S"
		formatter = logging.Formatter(log_fmt, date_fmt)
		# Center align + min length things to prevent logs jumping around when switching between different values
		record.levelname = f"{record.levelname:^7}"
		record.module = f"{record.module:^10}"
		return formatter.format(record)


class LogHistoryHandler(logging.Handler):
	def __init__(self) -> None:
		super().__init__()
		self.log_history: list[LogRecord] = []

	@override
	def emit(self, record: LogRecord) -> None:
		self.log_history.append(record)
		if len(self.log_history) > 50:
			del self.log_history[0]
