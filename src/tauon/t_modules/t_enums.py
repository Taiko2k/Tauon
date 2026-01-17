from enum import IntEnum


class LoaderCommand(IntEnum):
	NONE = 0
	DONE = 1
	FOLDER = 2
	FILE = 3


class PlayerState(IntEnum):
	STOPPED = 0
	PLAYING = 1
	PAUSED = 2
	URL_STREAM = 3
	SPOTIFY_MODE = 4


class PlayingState(IntEnum):
	STOPPED = 0
	PLAYING = 1
	PAUSED = 2
	URL_STREAM = 3


class StopMode(IntEnum):
	OFF = 0
	TRACK = 1
	ALBUM = 2
	TRACK_PERSIST = 3
	ALBUM_PERSIST = 4


class Backend(IntEnum):
	NONE = 0
	GSTREAMER = 2
	PHAZOR = 4
