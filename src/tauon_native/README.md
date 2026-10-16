# Tauon native bootstrap

`tauon-native` is the C++17 entrypoint for Tauon. It owns SDL initialisation,
the main window, the renderer, the first loading-screen frame, and final SDL
shutdown. The window is created hidden, painted, explicitly shown, and
synchronized with the platform compositor before it embeds CPython and
executes `tauon.__main__`.

The built-in `tauon_native` Python module exposes native event, window,
renderer, texture, tray, cursor, clipboard, and text-input operations to the
existing Python UI. Python never loads SDL itself and must not destroy the main
window, renderer, or SDL runtime.

The native entry point also provides the shell launcher's command and
single-instance forwarding behavior. Playback and control flags are sent
directly to the controller on `127.0.0.1:7813` without starting Python. When
another Tauon instance owns the instance lock, file paths and `file://` URIs
are forwarded through the controller's `/open/` endpoint; otherwise they are
passed to the newly started Python application.

## Building

The top-level `CMakeLists.txt` builds the launcher together with Phazor, and
`pip install .` runs it through scikit-build-core. The launcher is installed as
`tauon` in the environment's scripts directory:

```sh
python -m pip install .
.venv/bin/tauon
```

The launcher finds Python from its own location. In a bundle it uses the
private runtime beside it. Otherwise CPython's path calculation starts from the
launcher, so one in a virtual environment's `bin` directory picks up that
environment's `pyvenv.cfg`, and one in a system prefix uses that prefix.
No paths are compiled in. Outside a bundle, `TAUON_PYTHONPATH` and
`TAUON_PYTHON_SITE_PACKAGES` are available as explicit development and
diagnostic overrides. Bundles ignore them.

See `BUILDING.md` for editable installs, the supported bundle layout and
platform build commands.

For a bridge-only check that does not import the full Tauon application:

```sh
.venv/bin/tauon --tray --native-smoke-test
```

The smoke test exercises the built-in bridge and verifies the C++-created
window, renderer, texture upload, secondary-window lifecycle, and event path.

## Window state

The launcher reads `window-state.json` from Tauon's user-data directory before
creating the window. Python atomically rewrites the same file when application
state is saved. The versioned document contains the restored size, scale,
opacity, border mode, maximized state, and optional `[x, y]` position. Set
`TAUON_USER_DATA_DIR` to override the directory for packaging or testing.

The former Python-pickle `window.p` format is intentionally not read or
migrated.

## Migration boundary

SDL resources cross the Python boundary as opaque, type-checked capsules; raw
pointer integers are not part of the Python API. The one exception is
`get_window_pointer_property()`, which hands platform window handles to the
compositor integrations (background blur) that must call platform APIs.

SDL failures follow SDL's own convention rather than raising: actions return
`True` or `False`, creation calls return `None`, and `get_error()` describes
the last failure. Invalid handles and malformed arguments still raise. The C++ process remains the
sole SDL runtime owner, while Python-owned secondary resources are created and
destroyed through explicit native calls.
