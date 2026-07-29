# Building Tauon

Tauon is a native C++ application that embeds its Python UI. The
`tauon-native` executable owns SDL, creates the main window and renderer, and
then imports `tauon.__main__` in its embedded CPython interpreter.

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

Tauon requires Python 3.10 or newer, its matching Python development files,
CMake 3.20 or newer, a C++17 compiler, SDL3, and the development libraries used
by the Phazor audio backend.

The Python interpreter used to build `tauon-native` must have the same minor
version and ABI as the Python environment containing Tauon and its compiled
extensions.

## Linux development environment

The package names vary by distribution. On Ubuntu, the development packages
are approximately:

```sh
sudo apt install \
  build-essential cmake gettext gobject-introspection libayatana-appindicator3-dev \
  libcairo2-dev libdbus-1-dev libflac-dev libgirepository-2.0-dev libgme-dev \
  libgtk-3-dev libjxl-dev libmpg123-dev libopenmpt-dev libopusfile-dev \
  libpipewire-0.3-dev libsamplerate0-dev libvorbis-dev libwavpack-dev ninja-build \
  pkg-config python3-dev python3-venv
```

Install SDL3 from your distribution when available. If it is not packaged,
build and install a current SDL3 release into a local prefix, then pass that
prefix through `CMAKE_PREFIX_PATH`.

Create the Python environment and build Tauon:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements_devel.txt build pytest
python -m tools.i18n.compile_translations
python -m build --wheel
python -m pip install --no-deps --force-reinstall dist/*.whl

cmake -S . -B build/native -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DPython3_EXECUTABLE="$PWD/.venv/bin/python" \
  -DTAUON_DEVELOPMENT_BUILD=ON
cmake --build build/native --parallel
```

Run the application:

```sh
./build/native/tauon-native
```

## macOS development environment

Install the native dependencies with Homebrew:

```sh
brew install \
  cmake ffmpeg game-music-emu gettext gobject-introspection gtk+3 jpeg-xl \
  libopenmpt libsamplerate librsvg ninja opusfile pkg-config python@3.14 \
  sdl3 wavpack
```

Then use the Linux commands above, creating the virtual environment with the
Homebrew interpreter:

```sh
$(brew --prefix python@3.14)/libexec/bin/python -m venv .venv
source .venv/bin/activate
```

If CMake cannot locate SDL3, add:

```sh
-DCMAKE_PREFIX_PATH="$(brew --prefix)"
```

## Windows development environment

The supported Windows toolchain is MSYS2 MinGW-w64. From an MSYS2 MINGW64
shell, install the packages listed in `extra/msyspac.txt`, then create the
virtual environment:

```sh
pacman -S --needed $(tr '\n' ' ' < extra/msyspac.txt)
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt -r requirements_devel.txt build pytest
python -m tools.i18n.compile_translations
python -m build --wheel
python -m pip install --no-deps --force-reinstall dist/*.whl
```

Build the native launcher:

```sh
cmake -S . -B build/native -G Ninja \
  -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_PREFIX_PATH=/mingw64 \
  -DPython3_EXECUTABLE="$PWD/.venv/bin/python" \
  -DTAUON_DEVELOPMENT_BUILD=ON
cmake --build build/native --parallel
./build/native/tauon-native.exe
```

## Tests and smoke checks

Run Python tests without launching the application:

```sh
PYTHONPATH=src python -m pytest src/tauon/tests
python -m py_compile src/tauon/t_modules/t_main.py
```

Exercise the embedded bridge and native-created SDL objects:

```sh
./build/native/tauon-native --tray --native-smoke-test
```

On a headless Linux machine, run the smoke test through `xvfb-run`.

## Release-style bundles

Release builds must disable development paths:

```sh
cmake -S . -B build/native-release -G Ninja \
  -DCMAKE_BUILD_TYPE=Release \
  -DPython3_EXECUTABLE="$PWD/.venv/bin/python" \
  -DTAUON_DEVELOPMENT_BUILD=OFF
cmake --build build/native-release --parallel
```

The active virtual environment must contain the freshly built Tauon wheel
before running the staging tool. Example for Linux:

```sh
python tools/package_bundle.py \
  --platform linux \
  --native build/native-release/tauon-native \
  --output dist/package \
  --portable
```

Use `--platform windows` or `--platform macos` on those operating systems.
`--projectm PATH` adds the platform's projectM shared library. The staging tool
copies a private Python standard library and site-packages tree, collects
native dependencies, and creates the layout expected by `tauon-native`.

The `portable` marker belongs beside the native executable. When present,
Tauon writes user data to `user-data` beside the executable. Installer builds
must omit that marker.

The bundles are architecture-specific. The current macOS workflow produces an
arm64 app, and the Windows workflow produces x86-64. The Linux archive is
portable across distributions only to the extent allowed by the CI runner's
glibc baseline; build it on the oldest Linux base that the project intends to
support. The staging tool deliberately leaves glibc and the dynamic loader to
the host instead of trying to ship them.

Arch Linux and Flatpak packaging are maintained outside this repository. Their
recipes should build the wheel and `tauon-native` separately, install both into
the system prefix (`/usr` or `/app`), install the native executable as
`bin/tauon`, and invoke it directly.
