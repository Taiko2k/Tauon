# Building Tauon

Tauon is a C++ launcher that owns SDL, creates the window and renderer, and
runs the Python UI in an embedded CPython. One CMake project builds the
launcher, the Phazor audio libraries (plus `phazor-pw` on Linux with PipeWire)
and the translations; scikit-build-core drives it, so `pip install .` builds
everything and installs the launcher as `.venv/bin/tauon`.

The launcher embeds the Python that built it and uses the environment it is
installed in. `python -m tauon`, `python src/tauon/__main__.py` and Python
console scripts bypass it and are rejected on purpose.

## Requirements

Python 3.11+ with development files and a shared `libpython`, CMake 3.20+, a
C/C++17 compiler, pkg-config, SDL3, gettext's `msgfmt`, and the Phazor codec
libraries. Clone with submodules:

```sh
git clone --recurse-submodules https://github.com/Taiko2k/Tauon.git
# or, in an existing checkout:
git submodule update --init --recursive
```

**Linux** (Ubuntu package names; SDL3 may need building into a prefix named
by `CMAKE_PREFIX_PATH`):

```sh
sudo apt install \
  build-essential cmake gettext gobject-introspection libayatana-appindicator3-dev \
  libcairo2-dev libchromaprint-dev libdbus-1-dev libflac-dev libgirepository-2.0-dev libgme-dev \
  libjxl-dev libmpg123-dev libopenmpt-dev libopusfile-dev \
  libpipewire-0.3-dev libsamplerate0-dev libvorbis-dev libwavpack-dev ninja-build \
  pkg-config python3-dev python3-venv
python3 -m venv .venv
```

**macOS** (create the venv with Homebrew's Python, and set
`CMAKE_PREFIX_PATH="$(brew --prefix)"` if CMake can't find SDL3 or Python):

```sh
brew install \
  chromaprint cmake ffmpeg game-music-emu gettext gobject-introspection jpeg-xl \
  libopenmpt libsamplerate librsvg ninja opusfile pango pkg-config python@3.15 \
  sdl3 wavpack
$(brew --prefix python@3.15)/libexec/bin/python -m venv .venv
```

**Windows** (MSYS2 CLANG64 shell; the launcher is `.venv/bin/tauon.exe`):

```sh
pacman -S --needed $(tr '\n' ' ' < extra/msyspac.txt)
python -m venv .venv
export CMAKE_PREFIX_PATH="${MSYSTEM_PREFIX}"
```

## Install and run

```sh
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[all,dev]" pytest
.venv/bin/tauon
```

For development, use an editable install with a persistent build directory
(`./run.sh` wraps this). Python changes apply on the next launch; re-running
the install rebuilds only the native code that changed:

```sh
python -m pip install scikit-build-core
python -m pip install --no-build-isolation -C build-dir=build/editable -e ".[all,dev]"
```

- Pass CMake options through pip, e.g. `-C cmake.build-type=Debug` or
  `-C cmake.define.CMAKE_PREFIX_PATH=/path/to/sdl3`.
- Editable installs read translations from the build output;
  `python -m tools.i18n.compile_translations` writes them to
  `src/tauon/locale`, which takes precedence.
- On Linux, a launcher inside a source checkout keeps user data in the
  checkout's `user-data` directory instead of `~/.local/share/TauonMusicBox`.

## Tests

```sh
PYTHONPATH=src python -m pytest src/tauon/tests
python -m py_compile src/tauon/t_modules/t_main.py
.venv/bin/tauon --tray --native-smoke-test   # use xvfb-run on headless Linux
```

## Bundles

Stage a bundle from a non-editable `pip install ".[all]"`:

```sh
python tools/package_bundle.py --platform linux --portable   # or windows, macos
```

The bundle goes to `dist/package` (`--output` to change). `--projectm PATH`
adds projectM, and `--native PATH` picks a launcher other than the installed
one. The tool copies a private Python runtime and collects native
dependencies.

`--portable` puts a `portable` marker beside the executable, which keeps user
data in `user-data` next to it. Installer builds must not include it. The
launcher moves data left in `_internal/user-data` by older (PyInstaller)
portable builds there on first launch, and still honours their
`_internal/portable` marker.

Bundles are per-architecture: CI builds macOS arm64, Windows x86-64, and Linux
x86-64 and arm64. A Linux bundle runs only on hosts with at least the build
machine's glibc, so build on the oldest base you support. Libraries that must
match the host (glibc, the C++ runtime, GL/EGL, X11/Wayland, ALSA, JACK,
PipeWire, fontconfig, FreeType, HarfBuzz) are left to the host, following the
AppImage exclude list vendored in `tools/package_bundle.py`.

Arch Linux and Flatpak packaging live outside this repository. Their recipes
should build a wheel (`python -m build --wheel`), install it into the system
prefix (`/usr` or `/app`) and run `bin/tauon`.
