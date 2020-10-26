#!/bin/bash
if [ "$1" == "--no-start" ]; then
	if [ "$2" == "--play" ]; then curl http://localhost:7813/play/
	elif [ "$2" == "--play-pause" ]; then curl http://localhost:7813/playpause/
	elif [ "$2" == "--pause" ]; then curl http://localhost:7813/pause/
	elif [ "$2" == "--stop" ]; then curl http://localhost:7813/stop/
	elif [ "$2" == "--next" ]; then curl http://localhost:7813/next/
	elif [ "$2" == "--previous" ]; then curl http://localhost:7813/previous/
	else python3 /opt/tauon-music-box/tauon.py "$@";
	fi
else
	echo "two"
	python3 /opt/tauon-music-box/tauon.py "$@"
fi

