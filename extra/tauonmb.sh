#!/bin/bash
python3 /opt/tauon-music-box/tauon.py "$@"
if [ $? -eq 139 ]; then
	echo "SEGV, relaunching"
	python3 /opt/tauon-music-box/tauon.py
fi
echo $?

