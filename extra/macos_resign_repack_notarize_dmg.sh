#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  macos_resign_repack_notarize_dmg.sh --input-dmg PATH --identity "Developer ID Application: ..." [options]

Unpacks a CI-built DMG, deep-signs the .app bundle, rebuilds the DMG using the same
create-dmg layout settings used in .github/workflows/build_and_release.yaml, then
notarizes and staples the rebuilt DMG.

Options:
  --input-dmg PATH        Source DMG from CI (required)
  --output-dmg PATH       Output DMG path (default: alongside input as *-signed.dmg)
  --identity NAME         Developer ID Application signing identity
                          (default: $CODESIGN_IDENTITY)
  --entitlements PATH     Entitlements plist for codesign
                          (default: $CODESIGN_ENTITLEMENTS or repo extra/entitlements.plist)
  --app-name NAME         App bundle name without .app (default: auto-detect from DMG)
  --notary-profile NAME   notarytool keychain profile (default: $NOTARYTOOL_PROFILE)
  --skip-notarize         Rebuild/sign only; skip notarization + stapling
  --keep-temp             Keep temp working directory for debugging
  -h, --help              Show this help

Notarization auth (choose one):
  1) --notary-profile / $NOTARYTOOL_PROFILE
  2) Apple ID env vars for xcrun notarytool:
       APPLE_ID
       APPLE_TEAM_ID
       APPLE_APP_PASSWORD (or APPLE_APP_SPECIFIC_PASSWORD)

Requirements:
  macOS command-line tools: hdiutil, codesign, xcrun, ditto
  create-dmg (same tool used by the GitHub workflow)
  python3 (optional, used to generate the custom DMG background if available)
EOF
}

log() {
  printf '[%s] %s\n' "$(date '+%H:%M:%S')" "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

regularize_file_if_symlink() {
  local path="$1"
  local tmp

  [[ -L "$path" ]] || return 0

  tmp="${path}.codex-regularized"
  rm -f "$tmp"
  cp -pL "$path" "$tmp"
  mv -f "$tmp" "$path"
  log "Replaced symlink with regular file for codesign: $path"
}

bundle_exec_name() {
  local info_plist="$1"
  local exec_name=""

  if command -v plutil >/dev/null 2>&1; then
    exec_name="$(plutil -extract CFBundleExecutable raw -o - "$info_plist" 2>/dev/null || true)"
  fi

  if [[ -z "$exec_name" ]] && command -v /usr/libexec/PlistBuddy >/dev/null 2>&1; then
    exec_name="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$info_plist" 2>/dev/null || true)"
  fi

  printf '%s' "$exec_name"
}

regularize_nested_bundle_symlinks() {
  local app_path="$1"
  local top_info="$app_path/Contents/Info.plist"
  local top_exec_name=""
  local top_exec=""
  local info=""
  local bundle_dir=""
  local exec_name=""
  local exec_path=""

  log "Normalizing symlinked bundle metadata/executables before signing"

  regularize_file_if_symlink "$top_info"
  top_exec_name="$(bundle_exec_name "$top_info" || true)"
  if [[ -n "$top_exec_name" ]]; then
    top_exec="$app_path/Contents/MacOS/$top_exec_name"
    regularize_file_if_symlink "$top_exec"
  fi

  while IFS= read -r -d '' info; do
    bundle_dir="${info%/Contents/Info.plist}"
    [[ "$bundle_dir" == "$app_path" ]] && continue

    regularize_file_if_symlink "$info"

    exec_name="$(bundle_exec_name "$info" || true)"
    if [[ -n "$exec_name" ]]; then
      exec_path="$bundle_dir/Contents/MacOS/$exec_name"
      regularize_file_if_symlink "$exec_path"
    fi
  done < <(find "$app_path" -path '*/Contents/Info.plist' -print0 2>/dev/null)
}

INPUT_DMG=""
OUTPUT_DMG=""
IDENTITY="${CODESIGN_IDENTITY:-}"
ENTITLEMENTS_PATH="${CODESIGN_ENTITLEMENTS:-}"
APP_NAME=""
NOTARY_PROFILE="${NOTARYTOOL_PROFILE:-}"
SKIP_NOTARIZE=0
KEEP_TEMP=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --input-dmg)
      [[ $# -ge 2 ]] || fail "--input-dmg requires a value"
      INPUT_DMG="$2"
      shift 2
      ;;
    --output-dmg)
      [[ $# -ge 2 ]] || fail "--output-dmg requires a value"
      OUTPUT_DMG="$2"
      shift 2
      ;;
    --identity)
      [[ $# -ge 2 ]] || fail "--identity requires a value"
      IDENTITY="$2"
      shift 2
      ;;
    --entitlements)
      [[ $# -ge 2 ]] || fail "--entitlements requires a value"
      ENTITLEMENTS_PATH="$2"
      shift 2
      ;;
    --app-name)
      [[ $# -ge 2 ]] || fail "--app-name requires a value"
      APP_NAME="$2"
      shift 2
      ;;
    --notary-profile)
      [[ $# -ge 2 ]] || fail "--notary-profile requires a value"
      NOTARY_PROFILE="$2"
      shift 2
      ;;
    --skip-notarize)
      SKIP_NOTARIZE=1
      shift
      ;;
    --keep-temp)
      KEEP_TEMP=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1 (use --help)"
      ;;
  esac
done

[[ -n "$INPUT_DMG" ]] || fail "--input-dmg is required"
[[ -f "$INPUT_DMG" ]] || fail "Input DMG not found: $INPUT_DMG"
[[ -n "$IDENTITY" ]] || fail "Signing identity is required (--identity or \$CODESIGN_IDENTITY)"

require_cmd hdiutil
require_cmd codesign
require_cmd xcrun
require_cmd ditto
require_cmd create-dmg

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
GEN_BG_SCRIPT="$REPO_ROOT/extra/generate_dmg_background.py"
DEFAULT_ENTITLEMENTS_PATH="$REPO_ROOT/extra/entitlements.plist"

if [[ -z "$ENTITLEMENTS_PATH" && -f "$DEFAULT_ENTITLEMENTS_PATH" ]]; then
  ENTITLEMENTS_PATH="$DEFAULT_ENTITLEMENTS_PATH"
fi

if [[ -n "$ENTITLEMENTS_PATH" ]]; then
  [[ -f "$ENTITLEMENTS_PATH" ]] || fail "Entitlements plist not found: $ENTITLEMENTS_PATH"
  if command -v plutil >/dev/null 2>&1; then
    plutil -lint "$ENTITLEMENTS_PATH" >/dev/null
  fi
fi

if [[ -z "$OUTPUT_DMG" ]]; then
  input_dir="$(cd "$(dirname "$INPUT_DMG")" && pwd)"
  input_base="$(basename "$INPUT_DMG" .dmg)"
  OUTPUT_DMG="$input_dir/${input_base}-signed.dmg"
fi

WORK_DIR="$(mktemp -d "${TMPDIR:-/tmp}/tauon-resign-dmg.XXXXXX")"
MOUNT_DIR="$WORK_DIR/mount"
STAGE_DIR="$WORK_DIR/stage"
REPACK_DIR="$WORK_DIR/repack"
BG_PATH="$WORK_DIR/dmg-background.png"
ATTACHED=0

cleanup() {
  local exit_code=$?
  if [[ $ATTACHED -eq 1 ]]; then
    hdiutil detach "$MOUNT_DIR" >/dev/null 2>&1 || hdiutil detach -force "$MOUNT_DIR" >/dev/null 2>&1 || true
  fi
  if [[ $KEEP_TEMP -eq 0 ]]; then
    rm -rf "$WORK_DIR"
  else
    log "Kept temp directory: $WORK_DIR"
  fi
  exit "$exit_code"
}
trap cleanup EXIT

mkdir -p "$MOUNT_DIR" "$STAGE_DIR" "$REPACK_DIR"

log "Mounting input DMG: $INPUT_DMG"
hdiutil attach -readonly -nobrowse -mountpoint "$MOUNT_DIR" "$INPUT_DMG" >/dev/null
ATTACHED=1

if [[ -z "$APP_NAME" ]]; then
  shopt -s nullglob
  apps=( "$MOUNT_DIR"/*.app )
  shopt -u nullglob
  [[ ${#apps[@]} -gt 0 ]] || fail "No .app bundle found at DMG root"
  [[ ${#apps[@]} -eq 1 ]] || fail "Multiple .app bundles found; pass --app-name"
  APP_NAME="$(basename "${apps[0]}" .app)"
fi

SRC_APP="$MOUNT_DIR/$APP_NAME.app"
[[ -d "$SRC_APP" ]] || fail "App bundle not found in DMG: $SRC_APP"

SIGNED_APP="$STAGE_DIR/$APP_NAME.app"
log "Copying app bundle out of DMG"
ditto "$SRC_APP" "$SIGNED_APP"

log "Detaching input DMG"
hdiutil detach "$MOUNT_DIR" >/dev/null
ATTACHED=0

regularize_nested_bundle_symlinks "$SIGNED_APP"

log "Deep-signing app bundle: $SIGNED_APP"
codesign_cmd=(
  codesign
  --force
  --deep
  --timestamp
  --options runtime
  --sign "$IDENTITY"
)
if [[ -n "$ENTITLEMENTS_PATH" ]]; then
  log "Using entitlements: $ENTITLEMENTS_PATH"
  codesign_cmd+=( --entitlements "$ENTITLEMENTS_PATH" )
fi
codesign_cmd+=( "$SIGNED_APP" )
"${codesign_cmd[@]}"

log "Verifying code signature"
codesign --verify --deep --strict --verbose=2 "$SIGNED_APP"
codesign --display --verbose=2 "$SIGNED_APP" >/dev/null

log "Preparing DMG background"
use_background=0
if [[ -f "$GEN_BG_SCRIPT" ]] && command -v python3 >/dev/null 2>&1; then
  if python3 "$GEN_BG_SCRIPT" "$BG_PATH"; then
    use_background=1
  else
    log "Background generation failed; rebuilding DMG without custom background"
  fi
else
  log "Background generator unavailable; rebuilding DMG without custom background"
fi

log "Rebuilding DMG: $OUTPUT_DMG"
rm -f "$OUTPUT_DMG"
ditto "$SIGNED_APP" "$REPACK_DIR/$APP_NAME.app"

create_dmg_once() {
  if [[ $use_background -eq 1 ]]; then
    create-dmg \
      --volname "$APP_NAME" \
      --background "$BG_PATH" \
      --window-pos 200 120 \
      --window-size 540 400 \
      --icon-size 100 \
      --icon "$APP_NAME.app" 150 170 \
      --hide-extension "$APP_NAME.app" \
      --app-drop-link 390 170 \
      "$OUTPUT_DMG" \
      "$REPACK_DIR"
  else
    create-dmg \
      --volname "$APP_NAME" \
      --window-pos 200 120 \
      --window-size 540 400 \
      --icon-size 100 \
      --icon "$APP_NAME.app" 150 170 \
      --hide-extension "$APP_NAME.app" \
      --app-drop-link 390 170 \
      "$OUTPUT_DMG" \
      "$REPACK_DIR"
  fi
}

i=0
until create_dmg_once; do
  if [[ $i -eq 10 ]]; then
    fail "create-dmg did not succeed even after 10 retries"
  fi
  i=$((i + 1))
  rm -f "$OUTPUT_DMG"
  log "create-dmg failed, retrying ($i/10)"
done

if [[ $SKIP_NOTARIZE -eq 1 ]]; then
  log "Skipping notarization as requested"
  log "Finished: $OUTPUT_DMG"
  exit 0
fi

APPLE_PASSWORD="${APPLE_APP_PASSWORD:-${APPLE_APP_SPECIFIC_PASSWORD:-}}"
notary_auth=()

if [[ -n "$NOTARY_PROFILE" ]]; then
  notary_auth=( --keychain-profile "$NOTARY_PROFILE" )
elif [[ -n "${APPLE_ID:-}" && -n "${APPLE_TEAM_ID:-}" && -n "$APPLE_PASSWORD" ]]; then
  notary_auth=(
    --apple-id "$APPLE_ID"
    --team-id "$APPLE_TEAM_ID"
    --password "$APPLE_PASSWORD"
  )
else
  fail "No notarization credentials configured. Set --notary-profile / \$NOTARYTOOL_PROFILE or APPLE_ID + APPLE_TEAM_ID + APPLE_APP_PASSWORD"
fi

log "Submitting DMG for notarization"
xcrun notarytool submit "$OUTPUT_DMG" "${notary_auth[@]}" --wait

log "Stapling notarization ticket to DMG"
xcrun stapler staple -v "$OUTPUT_DMG"
xcrun stapler validate -v "$OUTPUT_DMG"

log "Finished notarized DMG: $OUTPUT_DMG"
