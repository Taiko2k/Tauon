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

# The Tauon application itself, for anything that isn't a remote control command
APP=(python3 /app/bin/src/tauon/__main__.py)

usage() {
	cat <<EOF
${YELLOW}Usage:${RESTORE} $(basename "$0") [options] <command> [files...]

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

The leading dashes are optional.

${BOLD}${MAGENTA}Options:${RESTORE}
  ${YELLOW}-h, --help${RESTORE}    Show this help message

${BLUE}Example:${RESTORE} $(basename "$0") --playpause
EOF
	exit 0
}

# Echo the remote control endpoint for a command argument, or return 1 if the
# argument is not a command. Leading dashes and internal hyphens are ignored.
resolve_command() {
	local arg=${1#--}
	arg=${arg//-/}

	case ${arg} in
		play | pause | playpause | stop | raise | reloadtheme | shuffle | repeat)
			printf '%s' "${arg}"
			;;
		next | advance)
			printf 'next'
			;;
		previous | prev | back)
			printf 'previous'
			;;
		*)
			return 1
			;;
	esac
}

send_command() {
	local response
	if ! response=$(curl --fail --silent --show-error --output /dev/null --write-out "%{http_code}" "${BASE_URL}/${1}"); then
		if [[ "${response}" -ne 200 ]]; then
			echo -e "${RED}${BOLD}Error:${RESTORE} Could not connect to Tauon. HTTP Status: ${response}" >&2
			echo -e "${YELLOW}Hint:${RESTORE} Make sure Tauon is running." >&2
			exit 1
		else
			echo -e "${RED}${BOLD}Error:${RESTORE} Curl failed despite HTTP status 200 - THIS SHOULD NOT HAPPEN" >&2
			exit 1
		fi
	fi
}

handled=0

while [[ -n ${1-} ]]; do
	if [[ ${1} == "-h" || ${1} == "--help" ]]; then
		usage
	fi

	# An existing path or a URI is a file to open, even if it looks like a command
	if [[ -e ${1} || ${1} == file://* ]]; then
		break
	fi

	if COMMAND=$(resolve_command "${1}"); then
		send_command "${COMMAND}"
		handled=1
		shift
		continue
	fi

	# Not a command - hand this and everything after it to the application
	break
done

# Remaining arguments are for the application, e.g. files to open or --tray
if [[ $# -gt 0 ]]; then
	exec "${APP[@]}" "$@"
fi

if [[ ${handled} -eq 1 ]]; then
	exit 0
fi

exec "${APP[@]}"
