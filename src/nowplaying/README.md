# TauonNowPlaying (macOS helper)

This is a small macOS helper app that integrates Tauon with macOS "Now Playing".

- Publishes track metadata via `MPNowPlayingInfoCenter`
- Receives transport commands (play/pause/next/prev/stop) via `MPRemoteCommandCenter`
- Communicates with Tauon over stdin/stdout using newline-delimited JSON

## Build

Requires Xcode Command Line Tools.

```bash
cd src/nowplaying
chmod +x build_app.sh
./build_app.sh
```

Output:
- `src/nowplaying/build/TauonNowPlaying.app`

## IPC protocol (v1)

Helper -> Tauon:
- `{ "type": "ready", "protocol": 1 }`
- `{ "type": "media_key", "name": "PlayPause" }` (also: `Play`, `Pause`, `Next`, `Previous`, `Stop`)
- `{ "type": "seek", "position": 123.45 }` (absolute seek to seconds)
- `{ "type": "seek_relative", "delta": 15 }` (relative seek in seconds; negative for rewind; optional)

Tauon -> Helper:
- `{ "type": "update", "title": "...", "artist": "...", "album": "...", "state": 1, "art_path": "/path/to/image.png" }`
  - `state`: `0` stopped, `1` playing, `2` paused
  - Optional: `duration` (seconds), `elapsed` (seconds), `playing` (bool)
  - Optional: `art_path` (absolute path to an image file)
- `{ "type": "clear" }`
- `{ "type": "quit" }`
- `{ "type": "ping" }` -> `{ "type": "pong" }`
