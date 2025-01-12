from __future__ import annotations

#from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable
	from io import TextIOWrapper
	from pathlib import Path
	from typing import Any

	from tauon.__main__ import LogHistoryHandler

#@dataclass
class Holder:
	"""Class that holds variables for forwarding them from __main__.py to t_main.py"""

	def __init__(
		self, t_window: Any, renderer: Any, logical_size: list[int], window_size: list[int], maximized: bool,
		scale: float, window_opacity: float, draw_border: bool, transfer_args_and_exit: Callable[[]],
		old_window_position: tuple [int, int] | None, install_directory: Path, user_directory: Path,
		pyinstaller_mode: bool, phone: bool, window_default_size: tuple[int, int], window_title: bytes,
		fs_mode: bool, t_title: str, n_version: str, t_version: str, t_id: str, t_agent: str, dev_mode: bool,
		instance_lock: TextIOWrapper | None, log: LogHistoryHandler,
	) -> None:
		self.t_window = t_window     # SDL_CreateWindow() return type (???)
		self.renderer               = renderer     # SDL_CreateRenderer() return type (???)
		self.logical_size           = logical_size # X Y res
		self.window_size            = window_size  # X Y res
		self.maximized              = maximized
		self.scale                  = scale
		self.window_opacity         = window_opacity
		self.draw_border            = draw_border
		self.transfer_args_and_exit = transfer_args_and_exit # transfer_args_and_exit() - TODO(Martin): This should probably be moved to extra module
		self.old_window_position    = old_window_position    # X Y res
		self.install_directory      = install_directory
		self.user_directory         = user_directory
		self.pyinstaller_mode       = pyinstaller_mode
		self.phone                  = phone
		self.window_default_size    = window_default_size # X Y res
		self.window_title           = window_title        # t_title.encode("utf-8")
		self.fs_mode                = fs_mode
		self.t_title                = t_title   # "Tauon"
		self.n_version              = n_version # "7.9.0"
		self.t_version              = t_version # "v" + n_version
		self.t_id                   = t_id      # "tauonmb" | "com.github.taiko2k.tauonmb"
		self.t_agent                = t_agent   # "TauonMusicBox/7.9.0"
		self.dev_mode               = dev_mode
		self.instance_lock          = instance_lock
		self.log                    = log
