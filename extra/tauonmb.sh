#!/bin/sh
if [ "$1" = '--no-start' ]; then
	case "$2" in
		--play)       exec curl http://localhost:7813/play/;;
		--play-pause) exec curl http://localhost:7813/playpause/;;
		--pause)      exec curl http://localhost:7813/pause/;;
		--stopcurl)   exec curl http://localhost:7813/stop/;;
		--next)       exec curl http://localhost:7813/next/;;
		--previous)   exec curl http://localhost:7813/previous/;;
	esac
fi
exec tauonmb "$@"
