## Implemented features:

### Codecs

|     | Playback | Metadata | Picture |
| --- | ---      | ---      | ---     |
| MP3 | Y        | Y        | Y       |
| FLAC| Y        | Y        | Y       |
| APE | Y        | APEv2    | APEv2   |
| WV  | Y        | APEv2    | APEv2   |
| TTA | Y        | APEv2    | APEv2   |
| M4A | Y        | Y        |         |
| OGG | Y        | Y        |         |
| OPUS| Y        | Y        |         |
| WMA | Windows  | Windows  |         |
| WAV | Y        |          |         |
| MPC |          |          |         |
| AIFF|          |          |         |
| CD  |          |          |         |


### UI and Layouts

 - Theme files for changing UI colours (not all elements customisable)
 - Track list
 - Album art
 - Album gallery
 - Basic spectrum visualization and level meter
 - Custom columns with sorting
 - Lyrics display

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

## Other common player features not implemented:

 - Codecs: ALAC, Musepack, TAK
 - Gapless playback (crossfade is used)
 - Folder tree view
 - Folder monitoring / auto update
 - Skins
 - Customisable keyboard shortcuts
 - Global hotkeys (other than default media keys)
 - High DPI
 - Audio EQ setting
 - DSPs / Audio Plugins
 - Extentions
 - Audiobooks
 - Tag editing
 - Ratings
 - Read from archive (auto extract zip function exists)
 - Artist/metadata scraping
 - All tag metadata
 - A-B repreat
 - Bookmarks
 - Various playlist formats
 - Audio CD
 - Auto DJ
 - Timer / Alarm
