## Implemented features:

### Codecs

|     | Playback | Metadata | Picture |
| --- | ---      | ---      | ---     |
| MP3 | Y        | Y        | Y       |
| FLAC| Y        | Y        | Y       |
| APE | Y        | APEv2    | APEv2   |
| WV  | Y        | APEv2    | APEv2   |
| TTA | Y        | APEv2    | APEv2   |
| M4A | Y        | Y        | Y       |
| OGG | Y        | Y        |         |
| OPUS| Y        | Y        |         |
| WMA | Windows  | Windows  |         |
| WAV | Y        |          |         |
| MPC |          |          |         |
| AIFF|          |          |         |
| CD  |          |          |         |
| MOD |          |          |         |


### External service integration

- Last.fm scrobbling
- Get lyrics from LyricWiki

### Other file formats

 - XSPF (import and export) (cross-app compatibility not tested)
 - CUE sheets targeting single files (import only) (automatically read when importing)

### Player features

- Multiple tabbed playlists
- Quick search
- Filter from search to new playlist
- Play count
- Sorting to new playlist
- Web interface (basic playback control)
- Inbound streaming (HTTP, Icecast, Shoutcast)
- Outbound streaming
- Global media keys + some local harcoded keyboard shortcuts
- Output audio device override
- Track love

### Editing

- Folder batch file renaming
- Folder batch transcode (MP3, OGG, OPUS)
- Text Encoding fix (Japanese only, not written back to files)
- External tag editor linking

### Audio

- Volume
- Cross fade (only)
- Replay gain (Track and Album gain from metadata only)

## Other common player features not featured:

 - Codecs: ALAC, Musepack, TAK, MOD
 - Folder monitoring / auto update
 - Global hotkeys (other than default media keys)
 - Audio EQ setting
 - Tag editing (internal)
 - Read from archive (auto extract zip function exists)
 - Artist/metadata scraping
 - All tag metadata
 - A-B repreat
 - Bookmarks
 - Various playlist formats
 - Audio CD
 - Auto DJ
 - Timer / Alarm
 - Genre filtering
 - Per track ratings
 - Folder tree view

## Out of scope

  - Audiobooks
  - Extensions
  - Skins
  - Gapless playback
  - DSPs / Audio Plugins
