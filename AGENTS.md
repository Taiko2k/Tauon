# AGENTS.md

## Purpose

This repository is Tauon, a desktop music player with a large Python/SDL UI layer.

## Big Picture

- Main Python package: `src/tauon`
- Main entrypoint: `src/tauon/__main__.py`
- Main UI/application logic: `src/tauon/t_modules/t_main.py`
- Preferences and persisted settings: `src/tauon/t_modules/t_prefs.py`
- Native audio backend implementation: `src/phazor/phazor.c`
- Integration modules live in `src/tauon/t_modules/`:
  - `t_discord.py`
  - `t_jellyfin.py`
  - `t_subsonic.py`
  - `t_tidal.py`
  - `t_webserve.py`
  - `t_lyrics.py`
  - `t_phazor.py`

## Project-Specific Rules

- Do not shadow `_`. It is treated as the translation builtin in this project.

Fast syntax check:

```bash
python3 -m py_compile src/tauon/t_modules/t_main.py
```
