#!/usr/bin/env bash
set -euo pipefail

# Bootstraps native Android dependencies for the Phazor p4a recipe.
#
# Default output layout from the repository root:
#   ./android-deps/<abi>/{include,lib}
#
# The current Phazor recipe expects these shared libraries:
#   libFLAC.so libopusfile.so libvorbisfile.so libwavpack.so
#   libopenmpt.so libgme.so libsamplerate.so libmpg123.so
#
# Notes:
# - This script is best-effort and intentionally verbose so failures are easy to diagnose.
# - It prefers SDL3_mixer vendored source trees from an existing .buildozer checkout.
# - It falls back to upstream release archives when vendored sources are unavailable.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/../.." && pwd)"

ABI="${ABI:-arm64-v8a}"
API="${API:-24}"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 4)}"
DEPS_ROOT="${DEPS_ROOT:-$ROOT_DIR/android-deps}"
PREFIX="${DEPS_ROOT}/${ABI}"
BUILD_ROOT="${BUILD_ROOT:-$ROOT_DIR/build/android-deps/${ABI}}"
SRC_CACHE="${SRC_CACHE:-$BUILD_ROOT/src}"
DOWNLOADS_DIR="${DOWNLOADS_DIR:-$BUILD_ROOT/downloads}"

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

require_cmd curl
require_cmd tar
require_cmd cmake
require_cmd ninja
require_cmd make

find_ndk_root() {
  local cand
  for cand in \
    "${NDK:-}" \
    "$ROOT_DIR/.buildozer/android/platform/android-ndk-r28c" \
    "$HOME/.buildozer/android/platform/android-ndk-r28c" \
    "$HOME/Android/Sdk/ndk/28.2.13676358" \
    "$HOME/Android/Sdk/ndk-bundle"
  do
    [ -n "$cand" ] || continue
    if [ -x "$cand/toolchains/llvm/prebuilt/linux-x86_64/bin/clang" ]; then
      echo "$cand"
      return 0
    fi
  done
  return 1
}

NDK_ROOT="$(find_ndk_root || true)"
if [ -z "$NDK_ROOT" ]; then
  echo "Could not locate an Android NDK. Set NDK=/path/to/android-ndk." >&2
  exit 1
fi

TOOLCHAIN="$NDK_ROOT/toolchains/llvm/prebuilt/linux-x86_64"
SYSROOT="$TOOLCHAIN/sysroot"
CMAKE_TOOLCHAIN_FILE="$NDK_ROOT/build/cmake/android.toolchain.cmake"

case "$ABI" in
  arm64-v8a)
    TARGET_TRIPLE="aarch64-linux-android"
    TOOLCHAIN_TRIPLE="aarch64-linux-android"
    ;;
  armeabi-v7a)
    TARGET_TRIPLE="armv7a-linux-androideabi"
    TOOLCHAIN_TRIPLE="arm-linux-androideabi"
    ;;
  x86_64)
    TARGET_TRIPLE="x86_64-linux-android"
    TOOLCHAIN_TRIPLE="x86_64-linux-android"
    ;;
  x86)
    TARGET_TRIPLE="i686-linux-android"
    TOOLCHAIN_TRIPLE="i686-linux-android"
    ;;
  *)
    echo "Unsupported ABI: $ABI" >&2
    exit 1
    ;;
esac

export CC="$TOOLCHAIN/bin/clang --target=${TARGET_TRIPLE}${API}"
export CXX="$TOOLCHAIN/bin/clang++ --target=${TARGET_TRIPLE}${API}"
export AR="$TOOLCHAIN/bin/llvm-ar"
export AS="$TOOLCHAIN/bin/llvm-as"
export LD="$TOOLCHAIN/bin/ld"
export RANLIB="$TOOLCHAIN/bin/llvm-ranlib"
export STRIP="$TOOLCHAIN/bin/llvm-strip"
export NM="$TOOLCHAIN/bin/llvm-nm"
export PKG_CONFIG_PATH="$PREFIX/lib/pkgconfig"
export PKG_CONFIG_LIBDIR="$PREFIX/lib/pkgconfig"
export PKG_CONFIG_SYSROOT_DIR="/"
export CFLAGS="${CFLAGS:-} --sysroot=$SYSROOT -fPIC"
export CXXFLAGS="${CXXFLAGS:-} --sysroot=$SYSROOT -fPIC"
export LDFLAGS="${LDFLAGS:-} --sysroot=$SYSROOT -L$PREFIX/lib"
export CPPFLAGS="${CPPFLAGS:-} -I$PREFIX/include"

if [ "$ABI" = "arm64-v8a" ]; then
  export CFLAGS="$CFLAGS -mno-outline-atomics"
  export CXXFLAGS="$CXXFLAGS -mno-outline-atomics"
fi

mkdir -p \
  "$PREFIX" \
  "$PREFIX/include" \
  "$PREFIX/lib" \
  "$PREFIX/lib/pkgconfig" \
  "$BUILD_ROOT" \
  "$SRC_CACHE" \
  "$DOWNLOADS_DIR"

echo "Using NDK:      $NDK_ROOT"
echo "Using ABI:      $ABI"
echo "Using API:      $API"
echo "Install prefix: $PREFIX"
echo "Build root:     $BUILD_ROOT"

sdl_vendor_root() {
  local root="$ROOT_DIR/.buildozer/android/platform/build-${ABI}/build/bootstrap_builds/sdl3/jni/SDL3_mixer"
  [ -d "$root" ] && printf '%s\n' "$root"
}

download_and_extract() {
  local name="$1"
  local url="$2"
  local filename="${url##*/}"
  local archive="$DOWNLOADS_DIR/${filename}"
  local dst="$SRC_CACHE/${name}"

  if [ ! -f "$archive" ]; then
    echo "Downloading $name" >&2
    curl -L --fail --retry 3 -o "$archive" "$url"
  fi

  if [ ! -d "$dst" ]; then
    rm -rf "$BUILD_ROOT/.extract-${name}" "$dst"
    mkdir -p "$BUILD_ROOT/.extract-${name}"
    tar -xf "$archive" -C "$BUILD_ROOT/.extract-${name}"
    local extracted
    extracted="$(find "$BUILD_ROOT/.extract-${name}" -mindepth 1 -maxdepth 1 -type d | head -n 1)"
    mv "$extracted" "$dst"
  fi

  printf '%s\n' "$dst"
}

source_dir_for() {
  local name="$1"
  local vendored_root
  vendored_root="$(sdl_vendor_root || true)"
  if [ -n "$vendored_root" ]; then
    case "$name" in
      ogg)
        [ -d "$vendored_root/external/ogg" ] && printf '%s\n' "$vendored_root/external/ogg" && return 0
        ;;
      vorbis)
        [ -d "$vendored_root/external/vorbis" ] && printf '%s\n' "$vendored_root/external/vorbis" && return 0
        ;;
      opus)
        [ -d "$vendored_root/external/opus" ] && printf '%s\n' "$vendored_root/external/opus" && return 0
        ;;
      opusfile)
        [ -d "$vendored_root/external/opusfile" ] && printf '%s\n' "$vendored_root/external/opusfile" && return 0
        ;;
      flac)
        [ -d "$vendored_root/external/flac" ] && printf '%s\n' "$vendored_root/external/flac" && return 0
        ;;
      wavpack)
        [ -d "$vendored_root/external/wavpack" ] && printf '%s\n' "$vendored_root/external/wavpack" && return 0
        ;;
      libgme)
        [ -d "$vendored_root/external/libgme" ] && printf '%s\n' "$vendored_root/external/libgme" && return 0
        ;;
    esac
  fi

  case "$name" in
    ogg) download_and_extract "$name" "https://downloads.xiph.org/releases/ogg/libogg-1.3.5.tar.gz" ;;
    vorbis) download_and_extract "$name" "https://downloads.xiph.org/releases/vorbis/libvorbis-1.3.7.tar.gz" ;;
    opus) download_and_extract "$name" "https://downloads.xiph.org/releases/opus/opus-1.5.2.tar.gz" ;;
    opusfile) download_and_extract "$name" "https://downloads.xiph.org/releases/opus/opusfile-0.12.tar.gz" ;;
    flac) download_and_extract "$name" "https://downloads.xiph.org/releases/flac/flac-1.4.3.tar.xz" ;;
    wavpack) download_and_extract "$name" "https://github.com/dbry/WavPack/releases/download/5.8.1/wavpack-5.8.1.tar.xz" ;;
    libgme) download_and_extract "$name" "https://github.com/libgme/game-music-emu/archive/refs/tags/0.6.3.tar.gz" ;;
    libsamplerate) download_and_extract "$name" "https://github.com/libsndfile/libsamplerate/releases/download/0.2.2/libsamplerate-0.2.2.tar.xz" ;;
    libopenmpt) download_and_extract "$name" "https://lib.openmpt.org/files/libopenmpt/src/libopenmpt-0.7.13+release.autotools.tar.gz" ;;
    mpg123) download_and_extract "$name" "https://downloads.sourceforge.net/project/mpg123/mpg123/1.32.9/mpg123-1.32.9.tar.bz2" ;;
    *)
      echo "Unknown dependency source: $name" >&2
      exit 1
      ;;
  esac
}

cmake_build() {
  local name="$1"
  local src="$2"
  shift 2
  local build_dir="$BUILD_ROOT/${name}-build"

  echo "Building $name (cmake)"
  rm -rf "$build_dir"
  cmake -S "$src" -B "$build_dir" -G Ninja \
    -DCMAKE_TOOLCHAIN_FILE="$CMAKE_TOOLCHAIN_FILE" \
    -DANDROID_ABI="$ABI" \
    -DANDROID_PLATFORM="android-$API" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="$PREFIX" \
    -DCMAKE_PREFIX_PATH="$PREFIX" \
    -DCMAKE_FIND_ROOT_PATH="$PREFIX" \
    -DCMAKE_POSITION_INDEPENDENT_CODE=ON \
    -DCMAKE_INSTALL_LIBDIR=lib \
    "$@"

  cmake --build "$build_dir" --parallel "$JOBS"
  cmake --install "$build_dir"
}

autotools_build() {
  local name="$1"
  local src="$2"
  shift 2
  local build_dir="$BUILD_ROOT/${name}-build"

  echo "Building $name (autotools)"
  rm -rf "$build_dir"
  mkdir -p "$build_dir"

  (
    cd "$build_dir"
    "$src/configure" \
      --host="$TOOLCHAIN_TRIPLE" \
      --prefix="$PREFIX" \
      --enable-shared \
      --disable-static \
      "$@"
    make -j"$JOBS"
    make install
  )
}

write_pkg_config_override() {
  local name="$1"
  local libs="$2"
  cat > "$PREFIX/lib/pkgconfig/${name}.pc" <<EOF
prefix=$PREFIX
exec_prefix=\${prefix}
libdir=\${prefix}/lib
includedir=\${prefix}/include

Name: $name
Description: local override for Android bootstrap
Version: 1
Libs: $libs
Cflags: -I\${includedir}
EOF
}

build_ogg() {
  local src
  local build_dir="$BUILD_ROOT/ogg-build"
  src="$(source_dir_for ogg)"
  cmake_build ogg "$src" \
    -DBUILD_SHARED_LIBS=ON \
    -DINSTALL_DOCS=OFF \
    -DINSTALL_CMAKE_PACKAGE_MODULE=OFF

  mkdir -p "$PREFIX/include/ogg"
  if [ -f "$src/include/ogg/ogg.h" ] && [ ! -f "$PREFIX/include/ogg/ogg.h" ]; then
    cp "$src/include/ogg/"*.h "$PREFIX/include/ogg/"
  fi
  if [ -f "$build_dir/include/ogg/config_types.h" ] && [ ! -f "$PREFIX/include/ogg/config_types.h" ]; then
    cp "$build_dir/include/ogg/config_types.h" "$PREFIX/include/ogg/config_types.h"
  fi
}

build_vorbis() {
  cmake_build vorbis "$(source_dir_for vorbis)" \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF \
    -DOGG_ROOT="$PREFIX" \
    -DOGG_INCLUDE_DIR="$PREFIX/include" \
    -DOGG_LIBRARIES="$PREFIX/lib/libogg.so"
}

build_opus() {
  local src
  src="$(source_dir_for opus)"
  cmake_build opus "$src" \
    -DBUILD_SHARED_LIBS=ON \
    -DOPUS_BUILD_PROGRAMS=OFF \
    -DOPUS_BUILD_TESTING=OFF \
    -DOPUS_DISABLE_DOCS=ON

  mkdir -p "$PREFIX/include/opus"
  if [ -d "$src/include/opus" ]; then
    cp "$src/include/opus/"*.h "$PREFIX/include/opus/" 2>/dev/null || true
    cp "$src/include/opus/"*.h "$PREFIX/include/" 2>/dev/null || true
  fi
  if [ -f "$src/include/opus.h" ]; then
    cp "$src/include/"*.h "$PREFIX/include/opus/" 2>/dev/null || true
    cp "$src/include/"*.h "$PREFIX/include/" 2>/dev/null || true
  fi
}

build_opusfile() {
  local src
  src="$(source_dir_for opusfile)"
  cmake_build opusfile "$src" \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF \
    -DBUILD_PROGRAMS=OFF \
    -DINSTALL_PKG_CONFIG_MODULE=ON \
    -DOP_DISABLE_EXAMPLES=ON \
    -DOP_DISABLE_HTTP=ON \
    -DOP_DISABLE_DOCS=ON \
    -DOGG_INCLUDE_DIR="$PREFIX/include" \
    -DOGG_LIBRARY="$PREFIX/lib/libogg.so" \
    -DOPUS_INCLUDE_DIR="$PREFIX/include" \
    -DOPUS_LIBRARY="$PREFIX/lib/libopus.so"

  mkdir -p "$PREFIX/include/opus"
  if [ -f "$src/include/opusfile.h" ]; then
    cp "$src/include/opusfile.h" "$PREFIX/include/opusfile.h" 2>/dev/null || true
    cp "$src/include/opusfile.h" "$PREFIX/include/opus/opusfile.h" 2>/dev/null || true
  fi
}

build_flac() {
  cmake_build flac "$(source_dir_for flac)" \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_PROGRAMS=OFF \
    -DBUILD_EXAMPLES=OFF \
    -DBUILD_TESTING=OFF \
    -DBUILD_DOCS=OFF \
    -DBUILD_CXXLIBS=OFF \
    -DINSTALL_MANPAGES=OFF \
    -DWITH_OGG=ON \
    -DOGG_INCLUDE_DIR="$PREFIX/include" \
    -DOGG_LIBRARY="$PREFIX/lib/libogg.so"
}

build_wavpack() {
  local src
  src="$(source_dir_for wavpack)"
  cmake_build wavpack "$src" \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_PROGRAMS=OFF \
    -DBUILD_TESTING=OFF

  mkdir -p "$PREFIX/include/wavpack"
  if [ -f "$src/include/wavpack.h" ]; then
    cp "$src/include/wavpack.h" "$PREFIX/include/wavpack.h" 2>/dev/null || true
    cp "$src/include/wavpack.h" "$PREFIX/include/wavpack/wavpack.h" 2>/dev/null || true
  fi
}

build_libgme() {
  cmake_build libgme "$(source_dir_for libgme)" \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF \
    -DENABLE_UBSAN=OFF
}

build_libsamplerate() {
  cmake_build libsamplerate "$(source_dir_for libsamplerate)" \
    -DBUILD_SHARED_LIBS=ON \
    -DBUILD_TESTING=OFF \
    -DLIBSAMPLERATE_EXAMPLES=OFF \
    -DCMAKE_POLICY_VERSION_MINIMUM=3.5
}

build_mpg123() {
  local src
  src="$(source_dir_for mpg123)"
  autotools_build mpg123 "$src" \
    --with-cpu=generic_fpu \
    --with-audio=dummy \
    --enable-int-quality \
    --disable-debug \
    --disable-components \
    --enable-libmpg123 \
    --with-default-audio=dummy

  if [ -f "$src/src/include/mpg123.h" ]; then
    install -Dm644 "$src/src/include/mpg123.h" "$PREFIX/include/mpg123.h"
  elif [ -f "$src/android/mpg123.h" ]; then
    install -Dm644 "$src/android/mpg123.h" "$PREFIX/include/mpg123.h"
  fi
}

build_libopenmpt() {
  local src
  src="$(source_dir_for libopenmpt)"
  autotools_build libopenmpt "$src" \
    --disable-static \
    --enable-shared \
    --disable-openmpt123 \
    --disable-examples \
    --disable-tests \
    --disable-doxygen-doc \
    --without-zlib \
    --without-portaudio \
    --without-portaudiocpp \
    --without-sndfile \
    --without-flac \
    --without-mpg123
}

post_install_fixes() {
  mkdir -p "$PREFIX/include/opus" "$PREFIX/include/vorbis" "$PREFIX/include/wavpack" "$PREFIX/include/gme"

  if [ -f "$PREFIX/include/opusfile.h" ] && [ ! -f "$PREFIX/include/opus/opusfile.h" ]; then
    cp "$PREFIX/include/opusfile.h" "$PREFIX/include/opus/opusfile.h"
  fi
  if [ -f "$PREFIX/include/vorbisfile.h" ] && [ ! -f "$PREFIX/include/vorbis/vorbisfile.h" ]; then
    cp "$PREFIX/include/vorbisfile.h" "$PREFIX/include/vorbis/vorbisfile.h"
  fi
  if [ -f "$PREFIX/include/wavpack.h" ] && [ ! -f "$PREFIX/include/wavpack/wavpack.h" ]; then
    cp "$PREFIX/include/wavpack.h" "$PREFIX/include/wavpack/wavpack.h"
  fi
  if [ -f "$PREFIX/include/gme.h" ] && [ ! -f "$PREFIX/include/gme/gme.h" ]; then
    cp "$PREFIX/include/gme.h" "$PREFIX/include/gme/gme.h"
  fi

  write_pkg_config_override opusfile "-L\${libdir} -lopusfile -lopus -logg"
  write_pkg_config_override vorbisfile "-L\${libdir} -lvorbisfile -lvorbis -logg"
}

verify_outputs() {
  local missing=0
  local paths=(
    "$PREFIX/include/FLAC/stream_decoder.h"
    "$PREFIX/include/opus/opusfile.h"
    "$PREFIX/include/vorbis/vorbisfile.h"
    "$PREFIX/include/wavpack/wavpack.h"
    "$PREFIX/include/libopenmpt/libopenmpt.h"
    "$PREFIX/include/gme/gme.h"
    "$PREFIX/include/samplerate.h"
    "$PREFIX/include/mpg123.h"
    "$PREFIX/lib/libFLAC.so"
    "$PREFIX/lib/libopusfile.so"
    "$PREFIX/lib/libvorbisfile.so"
    "$PREFIX/lib/libwavpack.so"
    "$PREFIX/lib/libopenmpt.so"
    "$PREFIX/lib/libgme.so"
    "$PREFIX/lib/libsamplerate.so"
    "$PREFIX/lib/libmpg123.so"
  )

  for path in "${paths[@]}"; do
    if [ ! -e "$path" ]; then
      echo "Missing expected output: $path" >&2
      missing=1
    fi
  done

  if [ "$missing" -ne 0 ]; then
    echo "One or more dependency outputs are missing." >&2
    exit 1
  fi
}

build_ogg
build_vorbis
build_opus
build_opusfile
build_flac
build_wavpack
build_libgme
build_libsamplerate
build_mpg123
build_libopenmpt
post_install_fixes
verify_outputs

cat <<EOF

Android dependency bootstrap complete.

Output prefix:
  $PREFIX

Next steps:
  export PHAZOR_ANDROID_DEPS_PREFIX="$DEPS_ROOT"
  buildozer -f packaging/android/buildozer.spec android debug

Because buildozer.spec now packages android-deps/${ABI}/lib/*.so, the shared
libraries from this prefix will be copied into the APK for ${ABI}.
EOF
