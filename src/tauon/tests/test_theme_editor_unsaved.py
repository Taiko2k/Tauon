# Copyright © 2015-2026, Taiko2k captain(dot)gxj(at)gmail.com
"""Unsaved theme editor changes survive closing and reopening the editor.

Closing the editor without saving leaves the edited colours applied, so
reopening it on the same theme should pick the draft back up and still show
"Unsaved changes!" (issue #2275).
"""

from __future__ import annotations

import os

os.environ["SDL_DISABLE_METADATA"] = "1"  # Disable metadata method
os.environ["SDL_DOC_GENERATOR"]    = "0"  # Disable doc generation

from pathlib import Path
from types import SimpleNamespace

from tauon.t_modules import t_main


class FakeOver:
	"""Just the parts of Over that the theme editor open/close flow touches."""

	begin_theme_editor = t_main.Over.begin_theme_editor
	clear_theme_editor_state = t_main.Over.clear_theme_editor_state
	resume_theme_editor = t_main.Over.resume_theme_editor
	close_theme_editor = t_main.Over.close_theme_editor
	open_theme_editor = t_main.Over.open_theme_editor
	apply_theme_editor_colour = t_main.Over.apply_theme_editor_colour
	theme_editor_current_colour = t_main.Over.theme_editor_current_colour

	def __init__(self) -> None:
		colours = t_main.ColoursClass()
		colours.side_panel_background = t_main.ColourRGBA(10, 10, 10, 255)
		fader = SimpleNamespace(fall=lambda: None, rise=lambda: None)
		self.tauon = SimpleNamespace(colours=colours, fader=fader)
		self.gui = SimpleNamespace(theme_name="Mindaro Copy", update_layout=False)
		self.prefs = SimpleNamespace(theme=1)
		self.enabled = True
		self.theme_path = Path("theme/Mindaro Copy.ttheme")
		self.theme_editor_enabled = False
		self.theme_editor_selected_attr = "side_panel_background"
		self.theme_editor_title_box = SimpleNamespace(
			text="", cursor_position=0, selection=0, set_text=lambda _text: None)
		self.theme_editor_draft_colours = None
		self.theme_editor_original_colours = None
		self.theme_editor_target_path = None
		self.theme_editor_dirty = False

	def active_theme_is_user_editable(self) -> bool:
		return True

	def active_theme_path(self) -> Path:
		return self.theme_path

	def apply_theme_preview_colours(self, source: t_main.ColoursClass) -> None:
		self.tauon.colours = t_main.clone_theme_colours(source)

	def sync_theme_editor_controls_from_current_colour(self) -> None:
		pass

	def destroy_theme_editor_gradient_textures(self) -> None:
		pass

	def destroy_settings_texture(self) -> None:
		pass


def edit_and_close(over: FakeOver) -> None:
	over.open_theme_editor()
	over.apply_theme_editor_colour(("side_panel_background",), t_main.ColourRGBA(200, 0, 0, 255))
	assert over.theme_editor_dirty
	over.close_theme_editor()


def test_reopening_keeps_unsaved_changes() -> None:
	over = FakeOver()
	edit_and_close(over)

	over.open_theme_editor()

	assert over.theme_editor_enabled
	assert over.theme_editor_dirty
	assert over.theme_editor_current_colour() == t_main.ColourRGBA(200, 0, 0, 255)
	assert over.theme_editor_original_colours.side_panel_background == t_main.ColourRGBA(10, 10, 10, 255)


def test_reopening_after_theme_reload_restores_draft() -> None:
	over = FakeOver()
	edit_and_close(over)
	# Switching themes away and back reloads the saved colours from disk
	over.tauon.colours.side_panel_background = t_main.ColourRGBA(10, 10, 10, 255)

	over.open_theme_editor()

	assert over.theme_editor_dirty
	assert over.tauon.colours.side_panel_background == t_main.ColourRGBA(200, 0, 0, 255)


def test_other_theme_starts_fresh() -> None:
	over = FakeOver()
	edit_and_close(over)
	over.theme_path = Path("theme/Other.ttheme")

	over.open_theme_editor()

	assert not over.theme_editor_dirty
	assert over.theme_editor_target_path == over.theme_path


def test_closing_without_changes_clears_draft() -> None:
	over = FakeOver()
	over.open_theme_editor()
	over.close_theme_editor()

	assert over.theme_editor_draft_colours is None
	assert over.theme_editor_target_path is None
