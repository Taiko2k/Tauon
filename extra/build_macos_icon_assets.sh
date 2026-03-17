#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "Error: $*" >&2
  exit 1
}

set_plist_string() {
  local plist_path="$1"
  local key="$2"
  local value="$3"

  if /usr/libexec/PlistBuddy -c "Print :${key}" "$plist_path" >/dev/null 2>&1; then
    /usr/libexec/PlistBuddy -c "Set :${key} ${value}" "$plist_path"
  else
    /usr/libexec/PlistBuddy -c "Add :${key} string ${value}" "$plist_path"
  fi
}

here="$(cd "$(dirname "$0")" && pwd)"
repo_root="$(cd "$here/.." && pwd)"

app_path="${1:-$repo_root/dist/Tauon.app}"
icon_source="${2:-$repo_root/src/tauon/assets/tau.icon}"
deployment_target="${MACOSX_DEPLOYMENT_TARGET:-11.0}"
icon_name="$(basename "$icon_source" .icon)"

[[ -d "$app_path" ]] || fail "App bundle not found: $app_path"
[[ -d "$icon_source" ]] || fail "Icon source not found: $icon_source"

resources_dir="$app_path/Contents/Resources"
info_plist="$app_path/Contents/Info.plist"

[[ -f "$info_plist" ]] || fail "Info.plist not found: $info_plist"
mkdir -p "$resources_dir"

work_dir="$(mktemp -d "${TMPDIR:-/tmp}/tauon-icon-assets.XXXXXX")"
cleanup() {
  rm -rf "$work_dir"
}
trap cleanup EXIT

mkdir -p "$work_dir/Assets.xcassets"
cp -R "$icon_source" "$work_dir/${icon_name}.icon"

partial_plist="$work_dir/icon-partial.plist"

xcrun actool \
  "$work_dir/${icon_name}.icon" \
  "$work_dir/Assets.xcassets" \
  --compile "$resources_dir" \
  --app-icon "$icon_name" \
  --include-all-app-icons \
  --minimum-deployment-target "$deployment_target" \
  --output-format human-readable-text \
  --notices \
  --warnings \
  --output-partial-info-plist "$partial_plist" \
  --platform macosx \
  --target-device mac

[[ -f "$partial_plist" ]] || fail "actool did not produce a partial plist"
[[ -f "$resources_dir/Assets.car" ]] || fail "actool did not produce Assets.car"

/usr/libexec/PlistBuddy -c "Merge $partial_plist" "$info_plist"
set_plist_string "$info_plist" "CFBundleIconName" "$icon_name"

if [[ -f "$resources_dir/${icon_name}.icns" ]]; then
  set_plist_string "$info_plist" "CFBundleIconFile" "$icon_name"
fi

plutil -lint "$info_plist" >/dev/null

echo "Compiled ${icon_source} into ${resources_dir}/Assets.car and updated ${info_plist}"
