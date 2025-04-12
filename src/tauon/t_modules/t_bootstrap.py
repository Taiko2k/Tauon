from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable
	from io import TextIOWrapper
	from pathlib import Path
	from sdl3 import LP_SDL_Renderer, LP_SDL_Window

	from tauon.__main__ import LogHistoryHandler

@dataclass
class Holder:
	"""Class that holds variables for forwarding them from __main__.py to t_main.py"""

	t_window:               LP_SDL_Window
	renderer:               LP_SDL_Renderer
	logical_size:           list[int] # X Y res
	window_size:            list[int] # X Y res
	maximized:              bool
	scale:                  float
	window_opacity:         float
	draw_border:            bool
	transfer_args_and_exit: Callable[[]] # transfer_args_and_exit() - TODO(Martin): This should probably be moved to extra module
	old_window_position:    tuple[int, int] | None # X Y res
	install_directory:      Path
	user_directory:         Path
	pyinstaller_mode:       bool
	phone:                  bool
	window_default_size:    tuple[int, int] # X Y res
	window_title:           bytes # t_title.encode("utf-8")
	fs_mode:                bool
	t_title:                str # "Tauon"
	n_version:              str # "7.9.0"
	t_version:              str # "v" + n_version
	t_id:                   str # "tauonmb" | "com.github.taiko2k.tauonmb"
	t_agent:                str # "TauonMusicBox/7.9.0"
	dev_mode:               bool
	instance_lock:          TextIOWrapper | None
	log:                    LogHistoryHandler
