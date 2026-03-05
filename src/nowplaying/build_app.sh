#!/usr/bin/env bash
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
out_dir="$here/build"
app_dir="$out_dir/TauonNowPlaying.app"
icon_src="$here/../tauon/assets/tau-mac.icns"
icon_name="$(basename "$icon_src")"

mkdir -p "$out_dir"

if [[ ! -f "$icon_src" ]]; then
  echo "Missing app icon: $icon_src" >&2
  exit 1
fi

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
cp "$icon_src" "$app_dir/Contents/Resources/$icon_name"

echo "Built: $app_dir"
