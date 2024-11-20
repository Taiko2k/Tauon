from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from t_modules.t_main import GuiVar, PlayerCtl, Tauon, TDraw

_ = lambda m: m
class Launch:
	def __init__(self, tauon: Tauon, pctl: PlayerCtl, gui: GuiVar, ddt: TDraw) -> None:
		self.tauon = tauon
		self.pctl = pctl
		self.gui = gui
		self.ddt = ddt

	def render(self) -> None:
		pass
