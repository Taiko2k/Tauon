# AGENTS.md

## Purpose

This repository is Tauon, a desktop music player with a large Python/SDL UI layer.

## Big Picture

- Main Python package: `src/tauon`
- Native entrypoint: `src/tauon_native/main.cpp` builds the `tauon` launcher. It owns SDL, the main window and the renderer, embeds CPython, and runs `tauon.__main__`.
- Python entrypoint: `src/tauon/__main__.py`. It raises unless started by the native launcher, so `python -m tauon` doesn't work.
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
- Keep code comments concise.

## Running

Editable install (`./run.sh` wraps it; see `BUILDING.md`). Python changes apply on the next launch; re-run it after changing native code:

```bash
python -m pip install --no-build-isolation -C build-dir=build/editable -e ".[all,dev]"
```

Launch:

```bash
.venv/bin/tauon
```

- Set `TAUON_USER_DATA_DIR=/some/dir` to run against a throwaway profile instead of the real one.
- Folder or file paths passed as arguments are imported, or forwarded to an already running instance.
- `.venv/bin/tauon --tray --native-smoke-test` checks the native bridge without loading the full app.
- Tests run with plain pytest (`.venv/bin/python -m pytest src/tauon/tests`); `conftest.py` mocks the native bridge.

Fast syntax check:

```bash
python3 -m py_compile src/tauon/t_modules/t_main.py
```

## Testing

Test files may not be up to date. Avoid running the full test suite.
