from enum import IntEnum


class LoaderCommand(IntEnum):
	NONE = 0
	DONE = 1
	FOLDER = 2
	FILE = 3
