# Tauon native bootstrap

`tauon-native` is the C++17 entrypoint for Tauon. It owns SDL initialisation,
the main window, the renderer, the first loading-screen frame, and final SDL
shutdown. The window is created hidden, painted, explicitly shown, and
synchronized with the platform compositor before it embeds CPython and
executes `tauon.__main__`.

The built-in `tauon_native` Python module exposes the bootstrap window and
renderer to the existing Python UI. PySDL3 is still used as a transitional
compatibility layer, but the launcher forces it to resolve symbols from the
same SDL shared library as the native executable. Python must not destroy the
main window, renderer, or SDL runtime when `Holder.native_bootstrap` is true.

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

The smoke test imports PySDL3, reconstructs its typed pointers to the
C++-created window and renderer, and verifies both handles through SDL.

## Window state

The launcher reads `window-state.json` from Tauon's user-data directory before
creating the window. Python atomically rewrites the same file when application
state is saved. The versioned document contains the restored size, scale,
opacity, border mode, maximized state, and optional `[x, y]` position. Set
`TAUON_USER_DATA_DIR` to override the directory for packaging or testing.

The former Python-pickle `window.p` format is intentionally not read or
migrated.

## Migration boundary

The integer address functions in `tauon_native` are deliberately transitional
and private to the bootstrap. Native `Window`, `Renderer`, `Texture`, and
`Event` Python types should replace them as SDL call sites are migrated. The
C++ process remains the sole lifetime owner throughout the transition.
