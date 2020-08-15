#!/bin/sh
for i in {0..9}; do
    test -S $XDG_RUNTIME_DIR/discord-ipc-$i || ln -sf {app/com.discordapp.Discord,$XDG_RUNTIME_DIR}/discord-ipc-$i;
done
python3 /app/bin/tauon.py "$@"
if [ $? -eq 139 ]; then
	echo "SEGV, relaunching"
	python3 /app/bin/tauon.py
fi
echo $?

