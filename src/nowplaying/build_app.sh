#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
out_dir="$here/build"
app_dir="$out_dir/TauonNowPlaying.app"

mkdir -p "$out_dir"

# Build the binary
xcrun swiftc \
  "$here/TauonNowPlaying.swift" \
  -O \
  -o "$out_dir/TauonNowPlaying" \
  -framework AppKit \
  -framework MediaPlayer

# Create .app bundle
rm -rf "$app_dir"
mkdir -p "$app_dir/Contents/MacOS" "$app_dir/Contents/Resources"

cp "$out_dir/TauonNowPlaying" "$app_dir/Contents/MacOS/TauonNowPlaying"
cp "$here/Info.plist" "$app_dir/Contents/Info.plist"

echo "Built: $app_dir"
