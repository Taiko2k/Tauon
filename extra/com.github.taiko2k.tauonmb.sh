#!/usr/bin/env bash
set -euo pipefail

RESTORE=$(echo -en '\033[0m')
RED=$(echo -en '\033[00;31m')
GREEN=$(echo -en '\033[00;32m')
YELLOW=$(echo -en '\033[00;33m')
BLUE=$(echo -en '\033[00;34m')
MAGENTA=$(echo -en '\033[00;35m')
BOLD=$(echo -en '\033[1m')

BASE_URL="http://127.0.0.1:7813"

usage() {
	cat <<EOF
${YELLOW}Usage:${RESTORE} $(basename "$0") [options] <command>

${BOLD}${MAGENTA}Commands:${RESTORE}
  ${GREEN}--play${RESTORE}          Starts playback
  ${GREEN}--pause${RESTORE}         Pauses playback
  ${GREEN}--playpause${RESTORE}     Toggle Play/Pause
  ${GREEN}--stop${RESTORE}          Stops playback entirely
  ${GREEN}--next${RESTORE}          Skips to the next track
  ${GREEN}--previous${RESTORE}      Skips to the previous track
  ${GREEN}--raise${RESTORE}         Brings the Tauon window to focus
  ${GREEN}--reloadtheme${RESTORE}   Reloads the active UI theme
  ${GREEN}--shuffle${RESTORE}       Toggles shuffle mode
  ${GREEN}--repeat${RESTORE}        Toggles repeat mode

${BOLD}${MAGENTA}Options:${RESTORE}
  ${YELLOW}-h, --help${RESTORE}    Show this help message

${BLUE}Example:${RESTORE} $(basename "$0") --playpause
EOF
	exit 0
}

while [[ -n ${1-} ]]; do
	case ${1} in
		-h | --help)
			usage
			;;
		--play | --pause | --playpause | --stop | --next | --previous | --raise | --reloadtheme | --shuffle | --repeat)
			if ! RESPONSE=$(curl --fail --silent --show-error --output /dev/null --write-out "%{http_code}" "${BASE_URL}/${1#--}"); then
				if [[ "${RESPONSE}" -ne 200 ]]; then
					echo -e "${RED}${BOLD}Error:${RESTORE} Could not connect to Tauon. HTTP Status: ${RESPONSE}" >&2
					echo -e "${YELLOW}Hint:${RESTORE} Make sure Tauon is running." >&2
					exit 1
				else
					echo -e "${RED}${BOLD}Error:${RESTORE} Curl failed despite HTTP status 200 - THIS SHOULD NOT HAPPEN" >&2
					exit 1
				fi
			fi
			;;
		*)
			exec python3 /app/bin/src/tauon/__main__.py "$@"
			;;
	esac
done

exec python3 /app/bin/src/tauon/__main__.py "$@"
