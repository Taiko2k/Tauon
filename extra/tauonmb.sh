#!/usr/bin/env bash

RESTORE=$(echo -en '\033[0m')
RED=$(echo -en '\033[00;31m')
GREEN=$(echo -en '\033[00;32m')
YELLOW=$(echo -en '\033[00;33m')
BLUE=$(echo -en '\033[00;34m')
MAGENTA=$(echo -en '\033[00;35m')
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

${BLUE}Example:${RESTORE} $(basename "$0") playpause
EOF
  exit 0
}

while [[ "$#" -gt 0 ]]; do
  case $1 in
  -h | --help) usage ;;
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
  exec tauonmb "$@"
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
