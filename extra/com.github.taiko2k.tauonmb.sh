#!/usr/bin/env bash

RESTORE=$(echo -en '\033[0m')
RED=$(echo -en '\033[00;31m')
GREEN=$(echo -en '\033[00;32m')
YELLOW=$(echo -en '\033[00;33m')
BLUE=$(echo -en '\033[00;34m')
MAGENTA=$(echo -en '\033[00;35m')
CYAN=$(echo -en '\033[00;36m')
BOLD=$(echo -en '\033[1m')

CONTROLLER_HOST="127.0.0.1"
CONTROLLER_PORT="7813"
BASE_URL="http://${CONTROLLER_HOST}:${CONTROLLER_PORT}"

usage() {
  cat <<EOF
${YELLOW}Usage:${RESTORE} $(basename "$0") [options] <command>

${BOLD}${MAGENTA}Commands:${RESTORE}
  ${GREEN}play${RESTORE}          Starts playback
  ${GREEN}pause${RESTORE}         Pauses playback
  ${GREEN}playpause${RESTORE}     Toggle Play/Pause
  ${GREEN}stop${RESTORE}          Stops playback entirely
  ${GREEN}next${RESTORE}          Skips to the next track
  ${GREEN}prev${RESTORE}          Skips to the previous track
  ${GREEN}raise${RESTORE}         Brings the Tauon window to focus
  ${GREEN}reloadtheme${RESTORE}   Reloads the active UI theme
  ${GREEN}shuffle${RESTORE}       Toggles shuffle mode
  ${GREEN}repeat${RESTORE}        Toggles repeat mode

${BOLD}${MAGENTA}Options:${RESTORE}
  ${YELLOW}-h, --help${RESTORE}    Show this help message
  ${YELLOW}-v, --version${RESTORE}  Show version information

${BLUE}Example:${RESTORE} $(basename "$0") playpause
EOF
  exit 0
}

while [[ "$#" -gt 0 ]]; do
  case $1 in
  -h | --help) usage ;;
  -v | --version)
    VERSION=$(
      python3 <<'EOF'
import ast
import inspect
import tauon
import sys
try:
    main_py_path = inspect.getfile(tauon).replace("__init__.py", "__main__.py")
    with open(main_py_path, "r", encoding="utf-8") as f:
        source_code = f.read()
    tree = ast.parse(source_code)
    n_version = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "n_version":
                    if isinstance(node.value, ast.Constant):
                        n_version = node.value.value
                        break
    if n_version is not None:
        print(n_version)
    else:
        sys.exit(1)
except Exception as e:
    sys.exit(1)
EOF
    )
    echo -e "${CYAN}tauonmb v${VERSION}${RESTORE}"
    exit 0
    ;;
  -*)
    echo -e "${RED}${BOLD}Error:${RESTORE} Unknown option: $1" >&2
    usage
    ;;
  *)
    COMMAND=$1
    shift
    break
    ;;
  esac
done

if [ -z "$COMMAND" ]; then
  python3 /app/bin/src/tauon/__main__.py "$@"
fi

case "$COMMAND" in
play | pause | playpause | stop | next | prev | raise | reloadtheme | shuffle | repeat)
  [ "$COMMAND" == "prev" ] && API_COMMAND="previous" || API_COMMAND="$COMMAND"

  RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "${BASE_URL}/${API_COMMAND}")

  if [ "$RESPONSE" -ne 200 ]; then
    echo -e "${RED}${BOLD}Error:${RESTORE} Could not connect to Tauon. (HTTP Status: $RESPONSE)" >&2
    echo -e "${YELLOW}Hint:${RESTORE} Make sure Tauon is running." >&2
    exit 1
  fi
  ;;
*)
  echo -e "${RED}${BOLD}Error:${RESTORE} Invalid command -> '$COMMAND'" >&2
  usage
  ;;
esac
