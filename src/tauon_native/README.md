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

## Development build

SDL3, CMake 3.20 or later, a C++17 compiler, and the Python development files
for Tauon's environment are required.

```sh
cmake -S . -B build/native \
  -DPython3_EXECUTABLE="$PWD/.venv/bin/python" \
  -DCMAKE_BUILD_TYPE=Debug
cmake --build build/native --parallel
./build/native/tauon-native
```

The build embeds the source and Python site-packages locations selected by
CMake. Packaging can override them at runtime with `TAUON_PYTHONPATH` and
`TAUON_PYTHON_SITE_PACKAGES`.

For a bridge-only check that does not import the full Tauon application:

```sh
./build/native/tauon-native --tray --native-smoke-test
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

The integer handles in `tauon_native` are deliberately private to the bridge.
The C++ process remains the sole SDL runtime owner, while Python-owned
secondary resources are created and destroyed through explicit native calls.
