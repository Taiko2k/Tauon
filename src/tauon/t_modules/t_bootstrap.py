from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable
	from io import TextIOWrapper
	from pathlib import Path
	from typing import Any

	from tauon.__main__ import LogHistoryHandler

@dataclass
class Holder:
	"""Class that holds variables for forwarding them from __main__.py to t_main.py"""

	t_window:               Any #= t_window     # SDL_CreateWindow() return type (???)
	renderer:               Any #= renderer     # SDL_CreateRenderer() return type (???)
	logical_size:           list[int] #= logical_size # X Y res
	window_size:            list[int] #= window_size  # X Y res
	maximized:              bool #= maximized
	scale:                  float #= scale
	window_opacity:         float #= window_opacity
	draw_border:            bool #= draw_border
	transfer_args_and_exit: Callable[[]] #= transfer_args_and_exit # transfer_args_and_exit() - TODO(Martin): This should probably be moved to extra module
	old_window_position:    tuple [int, int] | None #= old_window_position    # X Y res
	install_directory:      Path #= install_directory
	user_directory:         Path #= user_directory
	pyinstaller_mode:       bool #= pyinstaller_mode
	phone:                  bool #= phone
	window_default_size:    tuple[int, int] #= window_default_size # X Y res
	window_title:           bytes #= window_title        # t_title.encode("utf-8")
	fs_mode:                bool #= fs_mode
	t_title:                str #= t_title   # "Tauon"
	n_version:              str #= n_version # "7.9.0"
	t_version:              str #= t_version # "v" + n_version
	t_id:                   str #= t_id      # "tauonmb" | "com.github.taiko2k.tauonmb"
	t_agent:                str #= t_agent   # "TauonMusicBox/7.9.0"
	dev_mode:               bool #= dev_mode
	instance_lock:          TextIOWrapper | None #= instance_lock
	log:                    LogHistoryHandler #= log
