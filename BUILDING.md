# Building Tauon

Tauon is a native C++ application that embeds its Python UI. The
`tauon-native` launcher owns SDL, creates the main window and renderer, and
then imports `tauon.__main__` in its embedded CPython interpreter.

One CMake project (`CMakeLists.txt`) builds all native code: the launcher, the
Phazor audio libraries (`phazor`, and `phazor-pw` on Linux when PipeWire is
available) and the compiled translations. `pyproject.toml` drives it through
scikit-build-core, so `pip install .` builds everything and installs:

- the Python package, with `libphazor*` and `locale/` inside `tauon/`
- the launcher as `tauon` in the environment's scripts directory
  (`.venv/bin/tauon`)

An installed launcher finds its Python environment from its own location: one
in a virtual environment's `bin` directory uses that environment, and one in a
system prefix uses that prefix.

Do not launch Tauon with `python -m tauon`, `python src/tauon/__main__.py`, or a
generated Python console script. Those bypass the native SDL owner and are
rejected intentionally.

## Source checkout

Clone the repository with its submodules:

```sh
git clone --recurse-submodules https://github.com/Taiko2k/Tauon.git
cd Tauon
```

For an existing checkout:

```sh
git submodule update --init --recursive
```

Tauon requires Python 3.11 or newer with its development files (including
the shared `libpython` the launcher embeds), CMake 3.20 or newer, a C and
C++17 compiler, pkg-config, SDL3, gettext's `msgfmt`, and the development
libraries used by the Phazor audio backend.

The launcher embeds the interpreter that builds it, so build and run it with
the same Python environment.

## Linux development environment

The package names vary by distribution. On Ubuntu, the development packages
are approximately:

```sh
sudo apt install \
  build-essential cmake gettext gobject-introspection libayatana-appindicator3-dev \
  libcairo2-dev libchromaprint-dev libdbus-1-dev libflac-dev libgirepository-2.0-dev libgme-dev \
  libjxl-dev libmpg123-dev libopenmpt-dev libopusfile-dev \
  libpipewire-0.3-dev libsamplerate0-dev libvorbis-dev libwavpack-dev ninja-build \
  pkg-config python3-dev python3-venv
```

Install SDL3 from your distribution when available. If it is not packaged,
build and install a current SDL3 release into a local prefix, then pass that
prefix through the `CMAKE_PREFIX_PATH` environment variable.

Create the Python environment and install Tauon into it:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install ".[all,dev]" pytest
```

Run the application:

```sh
.venv/bin/tauon
```

### Editable installs

For development, install Tauon in editable mode with a persistent build
directory. Python changes then apply on the next launch, and re-running the
install rebuilds only the native code that changed:

```sh
python -m pip install scikit-build-core
python -m pip install --no-build-isolation -C build-dir=build/editable -e ".[all,dev]"
.venv/bin/tauon
```

`./run.sh` wraps these steps. When the launcher lives inside a source checkout
(as `.venv/bin/tauon` does), Linux builds keep user data in the checkout's
`user-data` directory rather than `~/.local/share/TauonMusicBox`.

Editable installs read translations from the build output. Running
`python -m tools.i18n.compile_translations` writes them into
`src/tauon/locale` instead, which takes precedence.

Extra CMake options can be passed through pip, for example
`-C cmake.define.CMAKE_PREFIX_PATH=/path/to/sdl3` or
`-C cmake.build-type=Debug`.

## macOS development environment

Install the native dependencies with Homebrew:

```sh
brew install \
  chromaprint cmake ffmpeg game-music-emu gettext gobject-introspection jpeg-xl \
  libopenmpt libsamplerate librsvg ninja opusfile pango pkg-config python@3.15 \
  sdl3 wavpack
```

Then use the Linux commands above, creating the virtual environment with the
Homebrew interpreter:

```sh
$(brew --prefix python@3.15)/libexec/bin/python -m venv .venv
source .venv/bin/activate
```

If CMake cannot locate SDL3 or Python, set:

```sh
export CMAKE_PREFIX_PATH="$(brew --prefix)"
```

## Windows development environment

The supported Windows toolchain is MSYS2 UCRT64. From an MSYS2 UCRT64
shell, install the packages listed in `extra/msyspac.txt`, then create the
virtual environment:

```sh
pacman -S --needed $(tr '\n' ' ' < extra/msyspac.txt)
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
export CMAKE_PREFIX_PATH=/ucrt64
python -m pip install ".[all,dev]" pytest
.venv/bin/tauon.exe
```

## Tests and smoke checks

Run Python tests without launching the application:

```sh
PYTHONPATH=src python -m pytest src/tauon/tests
python -m py_compile src/tauon/t_modules/t_main.py
```

Exercise the embedded bridge and native-created SDL objects:

```sh
.venv/bin/tauon --tray --native-smoke-test
```

On a headless Linux machine, run the smoke test through `xvfb-run`.

## Release-style bundles

Bundles are staged from a virtual environment where Tauon was installed with
`pip install .` (not an editable install). Example for Linux:

```sh
python -m pip install ".[all]"
python tools/package_bundle.py --platform linux --portable
```

Use `--platform windows` or `--platform macos` on those operating systems.
`--projectm PATH` adds the platform's projectM shared library. The bundle is
written to `dist/package` unless `--output` says otherwise, and uses the
environment's installed `tauon` launcher unless `--native` names another. The
staging tool copies a private Python standard library and site-packages tree,
collects native dependencies, and creates the layout expected by the launcher.

The `portable` marker belongs beside the native executable. When present,
Tauon writes user data to `user-data` beside the executable. Installer builds
must omit that marker.

The bundles are architecture-specific. The current macOS workflow produces an
arm64 app, the Windows workflow produces x86-64, and the Linux workflow
produces both x86-64 and arm64 archives. Each Linux archive is
portable across distributions only to the extent allowed by the CI runner's
glibc baseline; build it on the oldest Linux base that the project intends to
support. The staging tool leaves the libraries on the AppImage project's
exclude list to the host, along with anything only they depend on. That covers
glibc and the dynamic loader, the C++ runtime, OpenGL/EGL, DRM, X11/xcb and
Wayland client libraries, ALSA, JACK, PipeWire, and fontconfig with
FreeType and HarfBuzz, so that they match the host's drivers, sound server,
plugins and configuration files. The list is vendored in
`tools/package_bundle.py`, which describes how to refresh it.

Arch Linux and Flatpak packaging are maintained outside this repository. Their
recipes should build the wheel (`python -m build --wheel`) and install it into
the system prefix (`/usr` or `/app`), which places the launcher at `bin/tauon`,
and invoke that directly.
