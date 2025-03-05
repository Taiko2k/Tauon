
Changelog
---------

### v8.0.0

 - **Added** Transparent accent theme mode
 - **Added** Drag and drop from file zone highlight
 - **Added** Lyric provider "LRCLIB" including synced lyrics
 - **Added** Theme Charmed as built in
 - **Fixed** Mini mode always on top not working on Wayland
 - **Fixed** Drag and drop feedback when dragging external file
 - **Fixed** Various crash and other bugs
 - **Tweaked** Shuffle lockdown shortcut added to main menu
 - **Tweaked** Theme Ash colours
 - **Restored** guitar chords, including support for new guitarchords.com API
 

### v7.9.0

- **Added** TIDAL support
- **Added** Linux/macOS/Windows CI builds, restoring Windows and macOS build support
- **Fixed** crashes related to PipeWire [#1250](https://github.com/Taiko2k/Tauon/issues/1250)
- **Fixed** audio cutting out on the PipeWire backend with specific custom quantum settings [#1245](https://github.com/Taiko2k/Tauon/issues/1245)
- **Fixed** wrong encoding used for some tags in XSPF exports [#1331](https://github.com/Taiko2k/Tauon/issues/1331)
- **Fixed** Spotify local audio playback. User Spotify password entry no longer required
- **Fixed** gensokyoradio.net radio fallback URL
- **Fixed** mishandling display change event, this fixes the "Grr" errors in the log
- **Fixed** loading configuration with negative integers, this fixes setting a negative baseline offset
- **Fixed** playlist being able to skip to next song even when current song was looped due to a race condition
- **Fixed** leaking Resource handlers, this may fix potential memory leaks
- **Improved** Jellyfin integration - cover art now loads even for albumless tracks
- **Improved** Various changes to build system, Migrated to pyproject.toml
- ***Removed*** guitar chords feature - api.guitarchords.com it partially relied on is dead, replaced by newer API that would need implementing, and the chords feature was unmaintained
- ***Removed*** Spotify recommendations feature (API deprecated by Spotify)
- Many other bug fixes and code refactors [Special thanks to @C0rn3j for a lot of these]

### v7.8.3

- **Fixed** crash when using IME

### v7.8.2

- **Fixed** M4A and AIFF not importing bug introduced by 7.8.1

### v7.8.1

- **Added** Pipewire native output option (Linux only)
- **Added** setting in UI to disable gamepad
- **Added** support for importing files with .AIFF extension
- **Fixed** IME candidate list position when using UI scaling
- **Tweaked** standard sort to avoid merging albums
- **Improved** Jellyfin import speed and track details
- **Improved** CUE sheet read specification compliance
- **Improved** Discord RPC update speed

### v7.8.0

- **Added** support for various game music file types
- **Added** gallery setting to combine discs
- **Tweaked** shuffle mode for stricter repeat avoidance
- **Improved** encoding detection for CUE sheets
- **Fixed** duplicate highlight album in gallery bug

### v7.7.2

- **Added** album art for Discord rich presence
- Show error message when Airsonic auth fails

### v7.7.1

- **Added** Chinese script conversion to global search
- **Tweaked** CUE scan to scan audio file for additional metadata
- **Tweaked** global search to include artist sort order tag
- **Tweaked** MPRIS and notifications to fallback to filename if metadata missing
- **Tweaked** folder title to only show year in date
- **Fixed** a repeat of first part of track when in an album queue
- **Fixed** replay gain preamp setting not persisting
- ***Deprecated*** koel support

### v7.7.0

- **Added** new interactive icons for shuffle and repeat (Thanks @skylineone044 for help with that)
- **Added** last.fm artist image scraping for artist backgrounds
- **Added** setting for condensed fonts
- **Moved** artist background setting to theme settings tab
- ***Reverted*** change to last.fm album artist detection
- **Fixed** a possible crash with queue open
- **Fixed** a possible crash dragging tracks
- **Fixed** an issue with fanart.tv artist images

### v7.6.7

- **Added** various options for tracklist row title format
- **Added** feature to set playlist to use persistent time positions
- **Added** setting to disable activate search on letter key press
- **Fixed** handling of non-utf8 filenames
- **Fixed** crash when pressing Get Scrobble Counts while not logged in

### v7.6.6

- **Fixed** bug with radio not playing

### v7.6.5

- **Added** setting "Pull loves" for last.fm
- **Added** monochrome tray icon option (linux only)
- **Added** HLS compatibility for internet radio
- **Added** rescan all folders function to MENU > Database
- **Added** "disc number" and "has cue sheet" columns
- **Added** "sort by imported folders" sorting option
- **Moved** some add column functions to submenu
- **Tweaked** sort track number function to better sort multi disc albums
- **Tweaked** UI Spotify track indication
- **Improved** Spotify playback reliability
- **Improved** handling of unplayable Spotify tracks
- **Fixed** replay gain transition volume

### v7.6.4

- **Added** loved playlist ordering by timestamp (not retroactive)
- **Restored** device buffer setting in config file
- **Fixed** APE tag scan time duration reading zero
- **Fixed** an issue with not being able to switch output device
- **Fixed** switch artist in artist list not resetting to first album
- **Fixed** spotify startup info message persisting
- **Fixed** drag on top bar for new playlist now working under Wayland

### v7.6.3

- **Tweaked** search overly
- **Fixed** a crash when resizing window narrow
- **Fixed** an issue with submenus after setting UI scale
- **Fixed** background art not reloading on window resize

### v7.6.2

- **Fixed** Spotify auth not working

### v7.6.1

- **Fixed** black bars in slate mini mode
- **Fixed** high CPU in slate mini mode
- **Tweaked** to rescan files when duration is zero

### v7.6.0

- **Added** rework of broadcast feature
- **Added** new mini mode "Slate"
- **Added** mini-mode always-on-top feature
- **Added** function to import POPM ratings from tags
- **Added** FMPS_Rating write support for OGG files
- **Added** lookup artist on Spotify function to track menu
- **Added** confirmation to embedded art delete
- **Added** Spotify get recommended tracks feature
- **Tweaked** search overlay to show thumbnails for track results
- **Tweaked** spotify artist lookup to give more accurate results
- **Tweaked** artist panel click to locate behavior
- **Tweaked** esc shortcut to exit radio and showcase views
- **Updated** built in radio list
- **Fixed** radio view not exiting on search result activate
- **Fixed** some internet features on Windows build not working
- **Fixed** APE tag reading in various cases
- **Fixed** playback not resumable on device reconnect [Thanks @dannysu]
- **Fixed** compatibility with some FLAC files with ID3 tags
- ***Removed*** "restore window position" setting from GUI

### v7.5.0

- **Added** Windows SMTC support
- **Added** "show all" artists toggle to artist list menu
- **Added** Spotify audio passthrough support
- **Added** Spotify append track to playlist empty area menu
- **Added** Spotify import artist, album and context functions
- **Added** Spotify love heart icon to track row
- **Added** Spotify like track to track context menu
- **Moved** Spotify import library functions to playback menu
- **Moved** lyrics toggle synced button to lyrics context menu
- **Tweaked** auto theme colours in radio view
- **Tweaked** auto output to stay open on pause
- **Fixed** tag scan and write functions blocking UI
- **Fixed** conformation dialog scaling
- **Fixed** shuffle breaking after folder rescan
- **Fixed** tray text not updating with internet radio
- **Fixed** Spotify artist import not working

### v7.4.7

- **Enabled** OSS support
- **Fixed** internet radio incorrect playback speed bug
- **Fixed** scrobble on repeat
- **Fixed** tracks not starting at 0 with "avoid resampling" on
- **Fixed** crash with theme Mindaro

### v7.4.6

- **Added** theme entries for menu and corner buttons
- **Added** UI scale safety auto fallback
- **Fixed** crash when auto-theme enabled
- **Fixed** un-maximize button in fullscreen

### v7.4.4

- **Added** file size approximation for CUE tracks
- **Added** image submenu to gallery menu
- **Added** image load error fallback
- **Enabled** importing of various additional tracker formats
- **Tweaked** folder navigator to reload on imports
- **Tweaked** CUE scan to inherit metadata from source file
- **Tweaked** CUE scan to add disc numbers
- **Tweaked** artist list to ignore "the" prefix for sorting
- **Tweaked** confirm box to yes/no model
- **Fixed** various track transition issues
- **Fixed** auto scan lyrics not working with centered style side panel
- **Fixed** a rare bug that could cause local tracks to not play
- **Fixed** loading icon hidpi scaling
- **Fixed** some bugs with artist list playlist filtering
- **Fixed** artist list panel not highlighting track on playback

### v7.4.3

- **Added** window control context menu to top panel
- **Added** middle click top panel to minimize
- **Added** bit depth metadata for Jellyfin tracks
- **Fixed** import stall with non utf8 filenames
- **Fixed** CUE tracks re-importing with rescan folders
- **Fixed** bitrate/samplerate column for Jellyfin tracks
- **Fixed** artist info panel toggle in settings
- **[Windows] Fixed** missing ffprobe import

### v7.4.2

- **Fixed** min window size on HiDPI
- **Fixed** cursor size on Wayland
- **Fixed** spotify remote pause/next/previous control
- **Fixed** spotify icon colour in menus
- **Enabled** ID3 scanning on WAVE files
- **Marked** tray menu strings for translation


### v7.4.1

- **Added** jellyfin playlist import and uploading
- **Added** jellyfin file metadata info
- **Added** shortcuts-ignore-keymap setting
- **Fixed** generator playlists with network playlists
- **Fixed** crash on exit on Wayland
- **Fixed** corner resize cursors

### v7.4.0

- **Added** revised Chromecast mode
- **Added** non-resampling mode
- **Added** disc change indicator line in tracklist
- **Added** prompt to clear generator on dnd
- **Changed** keyboard shortcuts to use scancodes
- **Workaround** cursor theme issue on GNOME Wayland
- **Fixed** folder rescan on Windows
- **Fixed** garbled audio on RPi
- **Fixed** missing duration on some files


### v7.3.2

- **Fixed** possible tick on track crossfade
- **Fixed** mpris and media keys

### v7.3.1

- **Fixed** distortion on track start (regression)

### v7.3.0

- **Added** Tauon to Tauon interconnect feature
- **Added** transcode of network tracks
- **Added** transcoded track network fallback feature
- **Added** lastfm artist image scraper to artist info panel
- **Added** config setting to disable gamepad
- **Added** hex code compatibility to theme files
- **Improved** "transfer playtime to" function
- **Improved** transition and track timing
- **Updated** Windows support
- **Tweaked** various default keyboard shortcuts
- **Tweaked** the lock playlist feature to be hidden behind shift
- **Fixed** high CPU usage with radio (again)
- **Fixed** toggle-showcase from radio view
- **Fixed** background art to work with radio stations
- **Fixed** non-responsive window on long init
- ***Removed*** "artist info panel" toggle from view box
- ***Removed*** discogs setting from UI

### v7.2.1

- **Added** option to resume playback on system wake
- **Fixed** an issue with high CPU usage with internet radio
- **Fixed** ctrl+m for mute not working and crashing
- **Fixed** a possible issue with premature end of track with some formats

### v7.2.0

- **Added** cache system option for local files
- **Added** option to use persistent network cache
- **Added** setting to restart on back to UI settings
- **Added** singles folder detection and gallery display
- **Added** generator code 'px' to exclude contents of a playlist
- **Added** escape key to keymaps file
- **Added** toggle mute to keymaps file
- **Added** 'auto' mode for ReplayGain
- **Added** theme mascot extension
- **Added** mini modes to shuffle lockdown mode
- **Fixed** invalid folder name on move
- **Fixed** genre search not detecting semicolon deliminator
- **Fixed** playing track position when items from playlist are deleted
- **Fixed** "Filepath" column sort not working correctly
- **Fixed** some issues with UI scaling in tracks view
- **Tweaked** "Filename" column sort to sort by full filepath
- **Tweaked** play action to resume radio station
- **Tweaked** config file formatting
- **Tweaked** shuffle lockdown to restore on restart
- **Tweaked** restart back threshold time to from 2s to 6s
- **Restored** Spotify button
- **[Phazor] Fixed** audio stall on track jump with delayed IO
- **[Phazor] Fixed** delay/freeze on switching output device
- **[Phazor] Enabled** "cross fade time" setting
- **[Phazor] Added** output-samplerate config setting
- **[Phazor] Added** resample quality config setting
- **[Phazor] Added** setting to always use FFMPEG
- **[Phazor] Added** native Wavpack decode
- **[Phazor] Added** volume curve setting
- ***Removed*** GStreamer backend

### v7.1.3

- **Added** game controller input support
- **Fixed** auto export playlist not working
- **Fixed** mod playback (bug from v7.1.2)

### v7.1.2

- **Fixed** terminal spam on radio playback
- **[Phazor] Fixed** radio stalling in some cases
- **[Phazor] Fixed** some FLAC files not playing


### v7.1.1

- **Added** "Clean Database" prompt function to MENU
- **Added** ctrl text cursor methods
- **Added** automatic scaling between HiDPI monitors (Experimental)
- **Added** playlist tab indicators for track drag
- **Improved** UI scale slider to update without restart
- **Tweaked** internet radio reliability
- **Fixed** radio stream continuing download after using rr/revert
- **Fixed** maloja scrobble not respecting enable setting
- **Fixed** crash when attempting to export an empty playlist
- **Fixed** "zoom art to fix" aspect ratio
- **Fixed** background art not reloading on window resize
- ***Deprecated*** Spotify support (Now hold shift to reveal setting)

### v7.1.0

- **Added** export playlist settings box
- **Added** chromecast support (Experimental)
- **Added** lyric provider lyrics.ovh
- **Added** "albums" mode to shuffle lockdown
- **Added** gen code 'ia' for albums imported
- **Added** flag "--tray" to hide window on startup
- **Fixed** some radio stations not working
- **Fixed** replay gain not being read from MP3
- **[Phazor] Fixed** some file types not playing with network
- ***Removed*** lyric provider LyricWiki

### v7.0.1

- **Fixed** showcase visualiser glitch
- **Fixed** GENRE field in CUE sheet parsing

### v7.0.0

- **Added** track favorite support for Jellyfin
- **Added** M3U support for playlist import/export
- **Added** new radio layout view
- **Added** icon thumbnails to radio stations
- **Added** generator code "find string" fs
- **Added** auto recorded radio tracks import
- **Added** moved exit radio/showcase button to top panel
- **Tweaked** right side panel size behavior on window resize
- **Fixed** toggle background "Blur" setting not triggering update
- **Fixed** radio broadcast page periodically terminating

### v6.8.3

- **Fixed** phazor related bugs related to idling

### v6.8.2

- **Fixed** del key deleting tracks with tag editor box open
- ***Reverted*** natsort filepath change
- **[Phazor] Fixed** a bug where small chance backend crash on seek

### v6.8.1

- **Added** shift + up/down for track selection
- **Moved** ctrl + up/down for volume level
- **Changed** track number column name to #
- **Enabled** open image for embedded
- **Tweaked** filtered artist list to transfer back playing when switching artist
- **Tweaked** bitrate column to show samplerate/bitdepth for lossless
- **Tweaked** filepath sort to use natural sort
- **Fixed** possible UI glitch with some video drivers
- **Fixed** tooltip text on light theme
- **Fixed** mac window tool function order
- **Fixed** RTL language text not rendering (RTL still todo)
- **Fixed** add to queue shortcut in search applying text
- **Fixed** left window control in compact mode
- **[Phazor] Fixed** incorrect playback speed with WAV files
- **[Phazor] Improved** output quality with 24bit tracks

### v6.8.0

- **Added** left window decoration style
- **Added** macOS style window control style
- **Added** option to config file "seek-interval"
- **Added** shuffle lockdown as feature
- **Added** queue and show shortcuts to global search
- **Fixed** album artist field reading for MP3
- **Fixed** crash when displaying filenames with non utf8 data
- **Fixed** gallery add album to queue
- **Fixed** MP3 multi genre scan
- **Fixed** default sorting of imported tracks
- **Fixed** jellyfin album/artist tagging
- **Changed** importer to ignore dotfiles
- **Improved** idle CPU usage further
- **Improved** MPRIS2 compliance
- **Updated** macOS support

### v6.7.1

- **Fixed** mini mode border
- **Fixed** import stalling in some cases

### v6.7.0

- **Added** basic built in tag editor
- **Added** server rating support for Airsonic/Subsonic tracks
- **Added** image remove support for M4A, FLAC (now built in)
- **Added** MBID reading for M4A
- **Changed** date display to use original date
- **Improved** window startup speed
- **Improved** idle performance
- **Tweaked** defaults of some settings
- **Fixed** a bug with text highlighting
- **Fixed** an issue with CUE importing
- **Fixed** replay-gain slider setting movement
- **Fixed** a possible issue with Airsonic import stalling
- **Fixed** UI scaling of some border elements
- **Workaround** for a rendering bug in SDL 2.0.16
- ***Replaced*** Hsaudiotag and Stagger with Mutagen

### v6.6.1

- **Added** Jellyfin playback status update
- **Added** get scrobble counts from Maloja
- **Added** keyboard shortcut to transfer playtimes between tracks
- **Tweaked** default font behavior
- **Enabled** "rescan folder" menu entry for album in folder navigator
- **Enabled** WavePack decode with Phazor (via ffmpeg)
- **Fixed** rescan folder function moving folder to end of playlist when scanning the first
- ***Removed*** text RGB AA override (now auto detected)
- **[Flatpak] Removed** supplementary CJK font

### v6.6.0

- **Restored** spectrum visualisers (Phazor only)
- **Added** "Filename" type column
- **Added** relative volume adjust remote API point
- **Added** help link for Discord RP with Flatpak
- **Added** auto pause on suspend
- **Added** auto write db changes on shutdown
- **Added** option to block suspend during playback
- **Improved** radio stream fail error reporting detail
- **Tweaked** search goto to pulse highlight album in gallery
- **Tweaked** last.fm scrobble to include album-artist
- **Fixed** some shortcuts being possible while text input is active
- **Fixed** discord RPC not working when album is a single letter
- **Fixed** CUE sheet parsing missing composer and album artist fields
- **Fixed** click not registering after restore from tray
- **Fixed** some MP3 fields not parsing
- **Fixed** gallery not updating after column sort

### v6.5.4

- **Added** support for .WAV metadata
- **Added** setting to auto-stop on queue final track
- **Re-enabled** auto search lyrics feature (moved setting to config file)
- **Fixed** crash on reload metadata on removed file
- **Fixed** a rare possible crash when tag scanning MP3 files
- **Fixed** MPRIS not updating on CUE track transition
- **Tweaked** 8 star playtime balance
- **[Phazor] Fixed** an issue with FLAC + CUE position when previous track had different samplerate
- **[Phazor] Fixed** loading of some types of .WAV files (24bit still unsupported)

### v6.5.3

- **Changed** Discord presence control to persistent setting
- **Changed** Spotify auth to use user provided ID
- **Changed** Genius track lookup to fallback to standard search page
- **Fixed** rare crash when importing certain Spotify tracks
- **Fixed** click on focus on working
- **Fixed** folder navigator not updating on regenerate

### v6.5.2

- **Fixed** widget drag in some locations
- **Fixed** repeat icon alignment with UI scaling

### v6.5.1

- **Simplified** Spotify setup / remove need for key
- **Added** album info to global search track results
- **Added** import all spotify playlist button
- **[Phazor] Fixed** CUE sheets with FLAC

### v6.5.0

- **Added** support for playback of tracker files
- **Fixed** background art on window resize
- **Added** listen/scrobble support for Airsonic
- **Added** path metadata to plex tracks
- **Improved** Airsonic import speed
- **[GStreamer] Tweaked** network transition behaviour
- **[Phazor] Tweaked** network download behaviour

### v6.4.9

- **Added** export playlist albums as CSV
- **Added** button conformation to delete playlist on middle click
- **Improved** export database CSV format
- **Fixed** a bug with flickering album art in gallery on large screens
- **Fixed** high CPU on mouse down
- **Fixed** a bug with system tray when using GStreamer backend
- **Fixed** crash when drop files on tab

### v6.4.8

- **Added** Jellyfin streaming support
- **Added** delete playlist confirmation
- **Added** keyboard shortcuts "Clear Queue" and "Regenerate Playlist"
- Various fixes for keyboard control
- **Tweaked** global generator playlists to ignore other generator playlists
- **Fixed** keyboard shortcut trigger on window tab
- **Fixed** wrong radio URL displayed in compact view title
- **Fixed** slow backend switching
- **Fixed** delay in track change response near end of track [Phazor]

### v6.4.7

- **Improved** File Modified sorter to better group albums
- **Fixed** radio recording not working on Flatpak
- **Fixed** an issue with artist list wont goto multi-artist
- **Fixed** window not restoring when relaunching while in tray

### v6.4.6

- **Fixed** a possible bug with Spotify playback

### v6.4.5

- **Added** text only view to artist list
- **Added** buffering animation to seek bar
- **Added** alpha remote API
- ***Replaced*** Apiseeds lyric provider with Happi
- **Fixed** drag and drop from pantheon not working
- **Fixed** a bug with tracks skipping when using radio random
- ***Removed*** "Auto search lyrics" option

### v6.4.4

- **Added** track title to tray tooltip
- **Added** buffering progress indicator (Phazor)
- **Added** setting to use plain text airsonic authentication (For Nextcloud)
- **Added** volume control on scroll on tray
- **Changed** minimize to tray to close to tray
- **Fixed** UI scaling issue with settings tabs on top
- ***Removed*** "Reset missing flags" function (now automatic)
- **[Phazor] Fixed** an issue where rapidly pressing pause was cause jam
- **[Phazor] Added** resampling for MP3, Vorbis and Opus

### v6.4.3

- **Added** system tray support (AppIndicator)
- **Tweaked** track info Spotify icon colour
- **Fixed** spotify resume after long pause
- **Fixed** a bug where radio art would not reload on resuming stream

### v6.4.2

- **[Phazor] Fixed** radio stations not playing

### v6.4.1

- **Added** option to use artist backgrounds (Accounts > Fanart.tv)
- **Added** desktop launcher actions for play/pause, next and previous
- **Added** command line control arguments
- **Added** spotify icon button to track info box
- **Moved** MB4 and MB5 shortcuts to input config
- **Improved** ReplayGain support
- **Improved** Airsonic scan error handling
- **Fixed** issue with exported thumbnail collisions
- **Fixed** GStreamer EQ invert slider bug (workaround)
- **Fixed** GStreamer backend playing wrong track when switching fast
- **Fixed** a possible crash with malformed generator codes
- ***Set*** Phazor as default backend over GStreamer
- ***Set*** global search to locate artist with shift + enter
- ***Set*** transcode output .opus.ogg extension to just .ogg
- ***Removed*** download URL feature
- **[Phazor] Added** resampling for FLAC files
- **[Phazor] Fixed** slow seeking with some formats

### v6.4.0

- **Added** artist list sorting options
- **Added** Maloja scrobble support
- **Added** function to import scrobble counts and column to display
- **Added** custom Listenbrainz server option
- **Added** "Launching Spotfiy" status text
- **Added** new sorting option "Sort by Imported"
- **Tweaked** playlists stats readout
- **Tweaked** artist list appearance
- **Tweaked** settings function tab page layout
- **Tweaked** playlist list to remember scroll position over restart
- **Tweaked** album art display to prioritise "folder.*" over other names
- **Fixed** compact mode play/pause button order
- **Fixed** column bar peak position
- **Fixed** a case where Spotify monitoring would stall
- **Fixed** UI draw when using "Return" from showcase view
- **Fixed** a bug with seek bar display when using "radio random"
- **Fixed** radio type album art not showing in compact layout
- **[Phazor] Added** pulseaudio output selector
- **[Phazor] Added** "Fade on pause/stop" setting
- **[Phazor] Added** "Fade on jump" setting
- **[Phazor] Added** OGG metadata parsing for internet radio
- **[Phazor] Fixed** a crash when attempting to play mono FLACs
- **[Phazor] Fixed** FFMPEG processes not being cleaned up

### v6.3.3

- **Added** config option to restart track on back press
- **Added** option to scrobble to Libre.fm instead of Last.fm
- **Added** regenerate network collections functionality
- ***Set*** default keybind for "love playing" as Ctrl+Shift+L
- ***Set*** auto regen playlist setting default to on
- **Enabled** option to disable "transcode folder" menu entry
- **Added** ctrl click to add track to selection
- **Added** "Add to Queue" to selection menu
- **Added** toast for love track shortcut
- **Added** counter to Airsonic library import
- **Tweaked** lyrics to use as sycned if detected
- **Tweaked** synced lyrics synchronisation accuracy
- **Tweaked** auto regenerate playlists behaviour
- **Improved** PLEX import speed
- **Fixed** a possible stall when importing corrupted flac files
- **Fixed** down key on search overly advancing past results
- **Fixed** bottom panel title hiding
- **Fixed** no lyric menu when only synced lyrics showing
- **Fixed** menu click triggering seek bar when over
- **Fixed** column sorting by filepath
- **Fixed** possible crash when loading network track with Phazor

### v6.3.2

- **Improved** broadcast page
  - **Redesigned** layout to a centered style
  - **Added** metadata delay to improve perceived synchronisation
  - **Added** sourcing lyrics from lrc files (static)
  - **Fixed** no spaces in text bug
- **Fixed** global search crash with Spotify when not enabled
- **Fixed** delay when restarting broadcast

### v6.3.1

- **Enabled** picture menu for showcase album art
- **Fixed** borked radio metadata page
- **Fixed** process not closing with active broadcast connection
- Phazor:
  - **Fixed** audio not fading out on app exit
  - **Fixed** no audio when start after pause
  - **Reduced** possible glitches

### v6.3.0

- **Added** option to restore window position on restart
- **Fixed** spotify auth not working with tekore v3

### v6.2.6

- **Fixed** an upgrading issue causing some tracks to stall
- **Fixed** a crash when using copy in an empty playlist
- **Fixed** an issue with playback stalling after missing track or jump during transition

### v6.2.5

- **Fixed** Spotify remote not progressing

### v6.2.4

- **Restored** device selector

### v6.2.2

- ***Disabled*** device selector
- **Fixed** freeze on audio setting change
- ***Removed*** python-discogs_client dependency

### v6.2.1

- **Improved** internet radio
  - **Improved** buffering and reliability
  - **Added** drag to re-arrange for saved stations
  - **Added** option for search type
  - **Added** radio output codec setting in config file

### v6.2.0

- **Added** station search browser for internet radio
- **Added** detection of OGA file extension
- **Added** support pasting list of Spotify links
- **Added** support for pasting Spotify URI type
- **Added** radio stream metadata display
- **Changed** radio recording from button to setting
- **Improved** koel library import speed
- **Fixed** Spotify playlists not being imported in full
- **Fixed** some misc UI elements with scaling
- **Fixed** a crash when reading malformed lyrics files
- **Fixed** disabled menu items icon colour
- **Fixed** radio artist and title display for some cases
- **Workaround** for memory leak crash on startup
- ***Replaced*** BASS based broadcast backend with custom backend
- **Improved** GStreamer backend
  - **Added** level meter visualiser
  - **Added** audio equalizer
  - **Added** pause/resume/volume fade
  - **Workaround** for some network tracks not being seekable
  - **Workaround** for poor audio quality on some radio streams
  - **Fixed** start of CUE file audible on track jump
  - **Fixed** a bug where playback would immediately jump to next track
  - **Fixed** a possible crash on startup
  - ***Removed*** auto output device option
- ***Removed*** BASS backend
  - ***Lost*** spectrum visualiser

### v6.1.3

- **Improved** Spotify support
  - **Added** support for saving albums to library
  - **Added** regenerate library albums and liked track playlists
  - **Improved** Spotify playback synchronisation
  - **Fixed** un-like track not working

### v6.1.2

- **Added** "--nogdk" to bypass possible crash
- **Fixed** sync not working with first ordered playlist

### v6.1.1

- **Added** workaround for crash on KDE + Flatpak

### v6.1.0

- **Added** maximize window button
- **Added** setting "Zoom album art to fit"
- **Added** "Add Spotify album" function to end of playlist menu
- **Added** import and upload Spotify playlist functions
- **Added** import and search Spotify track function
- **Added** exit app keyboard shortcut as Ctrl + Q
- **Moved** "add to queue" shortcut to Alt + Q
- **Fixed** a possible crash when using artist info panel
- **Fixed** transcode status not showing correct remaining during sync
- **Fixed** synced lyrics not word wrapping
- **Fixed** pressing play button not un-pausing with Spotify
- **Changed** "remove network tracks" to not remove Spotify tracks
- **Changed** left panel button to exit showcase view

### v6.0.3

- **Added** UI scale slider in settings
- **Added** auto-scale based on xft dpi setting
- **Added** playlist setting "Set as downloads playlist"
- **Fixed** network track pausing with BASS
- **Fixed** crash on rescan music folder
- **Fixed** Spotify remote mode not showing track date
- **Reduced** chance of playtime database corruption
- **Changed** cover art downloader to abort if non-album folder

### v6.0.2

- **Improved** Airsonic library import
- **Fixed** lyrics searching all providers even if one was successful

### v6.0.1

- **Added** option to bypass transcode on sync
- **Improved** "set as sync playlist" function to be un-settable
- **Fixed** folder rescan to be able to rescan multiple imported folders
- **Fixed** import PLEX tracks not working
- **Fixed** setting account passwords not being hidden
- **Fixed** Spotify library import limit

### v6.0.0

- **Added** Spotify integration
- **Added** "Transcode and Sync" function
- **Added** Bandcamp artist search function
- **Added** visual theme selector to settings
- **Added** input fields for network accounts in settings
- **Added** setting for separate multi-value genre results (default is now off)
- **Added** "sort by top played" setting to chart generator
- **Added** "comment" and "genre" properties for MPRIS2
- **Added** "Remove Network Tracks" function in database menu
- **Added** custom controls to broadcast landing page
- **Improved** transcode handling of multi disc albums
- **Improved** genre result names for some genres
- **Improved** caching for network sourced album art
- **Improved** hidden columns bar to peak on mouse over
- **Tweaked** old playtime star colour
- **Tweaked** layout and description of various settings
- **Tweaked** tab double click to play click timing
- **Fixed** genius lyrics scrape for new layout version
- **Fixed** tracks showing as drop-able into a generator playlist
- **Fixed** dropping tracks then clicking playlist triggering play
- **Fixed** favicon not showing in broadcast page
- **Fixed** broadcast page not working without outside connection
- **Fixed** animation stutter when opening settings box
- **Fixed** global search scroll wheel behavior
- **Fixed** right click copy with text input fields
- **Fixed** artist image loading for some artist names
- ***Removed*** "auto update generated playlists" from in-app settings

### v5.5.5

- **Added** feature "Playlist gallery quick add mode"
- **Changed** about title font style
- **Changed** show minimize button to follow GTK setting
- **Fixed** a bug with radio page not loading album art
- **Fixed** a case with "Transcode All" resulting in stall
- Various fixes for custom light themes
- Various Windows fixes for use with MSYS

### v5.5.4

- **Added** "Find incomplete albums" function
- **Fixed** metadata not being read from some FLAC files
- **Fixed** crash when selecting GStreamer output device

### v5.5.3

- **Fixed** window opacity not persisting on restart
- **Fixed** auto theme colours on track switch sometimes not working
- **Fixed** double notification on playlist repeat
- **Improved** permission error message with Snap

### v5.5.2

- **Fixed** menu closing after using layout shortcut
- **Fixed** side panel synced lyrics scroll hitbox
- **Fixed** possible crash when using "remove missing tracks" or "edit with picard"
- **Fixed** a crash when using "vacuum playtimes"

### v5.5.1

- **Fixed** possible crash when auto lyrics enabled

### v5.5.0

- **Added** new theme "Neon Love"
- **Added** new theme "Sunken"
- **Added** "queue only" left panel type
- **Added** overflow menus for top panel tabs
- **Added** playlist results to global search
- **Added** playlist number keyboard shortcuts
- **Added** double click playlist to play
- **Restored** "gallery only" view layout (click gallery button twice)
- **Improved** "showcase only" background art compositing
- **Improved** colour blending with custom themes
- **Changed** playlist list layout to alt style
- **Changed** playlist lock indicator to pin indicator
- **Fixed** text with mascot bg in columns view
- **Fixed** lyrics source entries not showing asterisk
- **Fixed** rendering during view change click
- **Fixed** gallery jumping to top when deleting another playlist
- **Fixed** a bug where showcase would exit when switching track
- **Fixed** queue panel colours for non-dark themes
- **Fixed** audio device list not accepting mouse scrolling
- **Fixed** playtime not counting near end of track
- **Fixed** a bug where listenbrainz wouldn't work if last.fm was disabled
- **Fixed** a case where listenbrainz submission would fail (requires tag rescan)
- **Fixed** lyrics auto download not working if right panel was in centered mode
- **Fixed** a possible crash loading lrc files
- ***Removed*** config option "show playlist list" (now redundant)
- ***Removed*** playlist "auto" indicator
- ***Removed*** playlist pin buttons
- ***Removed*** bg art option "always center" (now automatic)

### v5.4.3

- **Added** Portuguese translation
- **Added** generator code "f" for find
- **Added** option to place lyrics metadata panel on top
- **Added** the following functions to keymap file: new-generator-playlist, edit-generator,
   search-lyrics-selected and substitute-search-selected
- **Changed** folder path generator code from 'f' to 'p'
- **Tweaked** appearance of micro mini-mode
- **Tweaked** colours of some UI elements
- **Tweaked** theme files to specify bottom panel title text colour
- **Improved** adding column to add at selected location
- **Fixed** new-playlist shortcut not being re-bindable
- **Fixed** a possible crash after using "Remove missing tracks"
- **Fixed** background art not returning after playing a track with no album art (regression fix)
- **Fixed** IME input (regression fix + improvement)
- **Fixed** some .lrc files not loading
- ***Removed*** config option "Always show seek bar in mini-mode micro" (now always on)

### v5.4.2

- **Added** swedish translation
- ***Set*** love-selected default shortcut as ctrl+l
- **Tweaked** folder navigator panel to auto adjust size
- **Fixed** add to queue shortcut

### v5.4.1

- **Fixed** a possible crash if track has lyrics but no album art
- **Fixed** gallery arrow key control
- **Fixed** an issue where embedded album art sometimes wouldn't load

### v5.4.0

- **Added** reading of pls/m3u/xspf files for radios
- **Added** "Copy to clipboard" function to bottom panel area menu
- **Added** click column title to sort. Removed menu entries.
- **Redesigned** "open http stream box"
- **Restored** drag tab to end duplicate tab function (hold ctrl)
- **Enabled** http stream on GStreamer backend
- **Enabled** scrobbling for internet radio
- **Fixed** view jump on queue advance
- **Fixed** warning message on visualiser enable
- **Fixed** end of tracks being cut off when on repeat
- **Fixed** time counter not advancing when playing internet stream
- **Fixed** mini-mode with internet radio
- **Fixed** an issue with pasting tracks using ctrl+v
- **Fixed** not being able to use add to queue shortcut with quick find box open
- **Fixed** clear playlist not resetting view position
- **Fixed** paste menu function not working with external folder paste
- **Fixed** external folder paste not working from some file managers (Nemo)
- **Fixed** playlist paste menu non-activation zone being too large
- **Fixed** showcase view not being restored on app restart

### v5.3.1

- **Added** Genius lyrics scrape
- **Added** substitute lyric search function
- **Added** "Remove duplicates" function
- **Added** "Edit generator" shortcut function
- **Added** instructions to edit generator box
- **Added** 'auto' indicator to playlist list
- **Added** "Make playlist auto sorting" function
- **Added** column, 'comment', 'today', 'self' and 'path' generator codes
- **Added** easter egg 0401-2020
- **Improved** generator code entry to update on type
- **Improved** scroll edge animation
- **Tweaked** behavior of 'auto' generator code to also apply on track drag and drop
- **Tweaked** light theme and auto theme colours
- **Tweaked** auto show playing on track transition behavior
- **Enabled** synced lyrics in lyrics side panel
- **Fixed** generator code year filter
- **Fixed** cycle-playlist-left/right not being rebind-able
- **Fixed** transition fade not being disabled on previous
- **Fixed** mascot position in "tracks only" view
- **Fixed** click on menu break causing menu to close
- **Fixed** toast text sometimes overflowing box
- **Fixed** rating star colours when using auto theme
- **Fixed** text colour in lyrics metadata panel with auto theme
- ***Removed*** restriction on enabling both auto theme and background art

### v5.3.0

- **Added** user track ratings
- **Added** regenerate function to playlist tab menu
- **Added** playlist generator strings
- **Added** backup database file saving
- **Added** subsonic streaming support
- **Tweaked** search results to show more folders
- **Changed** love heart column title from emoji to icon
- **Enabled** network sources with GStreamer backend
- **Moved** last.fm error message to top panel
- **Fixed** XSPF importing filenames with certain characters
- **Fixed** XSPF importing not reporting errors on 2nd try
- **Fixed** column sorting not ignoring case
- **Fixed** column sort ascending not maintaining track order
- **Fixed** drag and dropping folders as new tab not working if top panel was full
- **Fixed** icons not reverting size when changing ui-scale back to 1.0
- **Fixed** a crash in showcase view with large portrait window size
- **Fixed** tracks not being marked as missing when broadcasting
- **Fixed** empty visualisers showing in GStreamer mode
- **Fixed** settings box buttons UI scaling
- **Fixed** playlist list not scrolling with arrow key navigation
- **Fixed** crash on exit on some desktops

### v5.2.1

- **Tweaked** layout of settings to allow for localisation
- **Updated** Discord RP with fixed app icon
- **Fixed** crash with remove embed image function
- **Fixed** system language detection

### v5.2.0

- **Added** global search filter keywords: composer, year, album
- **Added** border to artist thumbnail hover preview
- **Added** "lock folder tree to playlist" hidden menu option
- **Improved** global search speed
- **Improved** CUE sheet compatibility for multiple target file CUE sheets
- **Improved** "sort year per artist" function to consider album-artist tag
- **Moved** various options to config file
- **Moved** "lyrics side info panel" toggle setting to menu
- **Fixed** restore to maximized on app open smoothness
- **Fixed** mouse over state when mouse leaves window at non edge
- **Fixed** CUE sheet imports with APE files sometimes importing duplicate
- **Fixed** a bug with artist titles sometimes not appearing in gallery
- ***Removed*** option to disable diacritic mode searching
- ***Removed*** search images on Google function
- ***Removed*** lyrics function "Split Lines"

### v5.1.4

- **Added** toggle of automatic artist data downloading
- **Added** manual trigger for artist bio download to menu
- **Added** toggles for fanart.tv sourcing
- **Added** "Enqueue album next" entry to gallery menu
- **Changed** artist image preview to activate on hover
- **Tweaked** folder nodes in tree to be bold if contains many sub items
- **Fixed** crash on select GStreamer custom output setting
- **Fixed** artist bio panel not reducing to small size
- **Fixed** playlist tabs being incorrectly dragged during UI stall

### v5.1.3

- **Fixed** crash with renaming tracks

### v5.1.2

- **Added** toggle to show album title in notification
- **Added** loading screen on app start
- **Added** picture preview to artist list
- **Fixed** some UI scale issues

### v5.1.1

- **Tweaked** mini mode appearance
- **Fixed** artist text not appearing in gallery after import
- **Fixed** GStreamer backend performing gapless transition with user jump
- **Fixed** delete folder not immediately redrawing playlist
- **Fixed** a crash when opening gallery

### v5.1.0

- **Added** "Collapse All" function to folder tree
- **Added** BASS library downloader function
- **Added** device selection and replay gain to GStreamer backend
- **Tweaked** middle click right side panel to also cycle lyrics view
- **Fixed** album grid drag and drop
- **Fixed** compact view gallery exit field with panel open
- **Fixed** folder tree scroll position after collapsing
- **Fixed** cursor setting to left drag type on startup

### v5.0.4

- **Fixed** a rendering performance issue
- **Fixed** paste not updating playlist immediately
- **Fixed** text not truncating in lyric metadata box
- **Tweaked** global search input control behavior

### v5.0.3

- **Changed** "Broadcast This" to allow starting a broadcast
- **Fixed** background art not functioning

### v5.0.2

- **Added** click "now streaming" to show broadcast track in playlist
- **Added** port setting for broadcast page
- **Added** cascade in lyrics menu
- **Fixed** folder tree view scroll position when showing playing
- **Fixed** scrobble queue no working
- **Fixed** text box text exceeding bounds
- **Fixed** text box shortcuts not functioning
- **Fixed** search overlay text box cursor bug
- **Fixed** broadcast listener count not resetting on start
- **Fixed** edit tags with selection menu sometimes causing crash
- **Fixed** genre search results with multiple genres and capitalisaton
- **Tweaked** global search performance
- **Tweaked** mini mode colours
- **Improved** gallery loading performance
- **Moved** "Toggle art" function to ctrl+h shortcut
- ***Removed*** lyrics under art feature

### v5.0.1

- **Fixed** an issue with continuous high CPU usage with gallery layout

### v5.0.0

- **Added** new folder tree type view to left side panel
- **Added** koel streaming support
- **Added** icon for menu item "Filter to new playlist"
- **Added** change right side panel layout by middle click shortcut
- **Added** middle click left panel button to switch to preview view
- **Improved** artist list to handle separate artists by colon
- **Improved** left side panel to always show playlists+queue when dragging
- **Tweaked** mini mode background colour
- **Tweaked** side panel show lyrics menu button behavior
- **Tweaked** artist list to allow middle click to filter to new playlist
- **Tweaked** left side panel mode switcher button menu to hide items already open
- **Tweaked** youtube downloader to place items in a subfolder
- **Tweaked** cycle playlist by keyboard behavior to skip hidden playlists
- **Moved** "Transfer Folder" function to folder navigator
- **Fixed** add queue toast possibly changing on queue re-order
- **Fixed** track title not appearing in bottom panel if track had no metadata
- **Fixed** open track URI from external not working while window was lowered
- **Fixed** artwork with network tracks not showing after resizing side panel
- **Fixed** pageup/down not selecting track

### v4.8.2

- **Added** gallery option "Center text"
- **Added** queue panel peak behavior when empty
- **Added** hold ctrl to add album to queue ungrouped
- **Added** download progress to seek bar for network tracks (PLEX)
- **Tweaked** gallery text colour
- **Tweaked** drag side panel to full size art to snap in place
- **Tweaked** tracklist to show filename when title missing
- **Tweaked** app icon to eliminate drop shadow
- **Tweaked** config to automatically reload when closing settings box
- **Tweaked** "Sky" theme bottom panel colours
- **Improved** UI scaling to accept any fractional value
- **Improved** full art lock size reliability
- **Improved** queue "Add album after current" to add after all playing album tracks
- **Improved** theme setting retention, now added to config file
- **Improved** album art to avoid blocking when downloading from network (PLEX)
- **Fixed** text input dropping letters while under load
- **Fixed** side panel center mode text position with small window
- **Fixed** showcase lyrics jumping position slightly when entering view
- **Fixed** extra empty playlist when dropping xspf onto left side panel
- **Fixed** lyrics scrolling when using volume change shortcut
- **Fixed** artist list key shortcuts not working with filtered playlist
- **Fixed** start of CUE based file playing briefly when switching tracks
- **Fixed** exit showcase button transferring click to side panel
- **Fixed** view box button off colour in Lavender Light theme
- **Moved** device buffer setting to config file
- ***Renamed*** META in global search to FOLDER
- ***Removed*** "Copy artist- album" from track menu and "Copy artist" from folder menu
- ***Removed*** "Forget import folder" function

### v4.8.1

- **Added** diacritic search
- **Added** cursor change on mouse-over to window resize hotspots
- **Added** option to always show title in bottom panel
- **Added** "Composer" and "Comment" as possible fields for rename tracks function
- **Added** "Locate Artist" function to bottom panel menu
- **Added** context menu to gallery power bar
- **Added** "Move playing folder here" function to power bar menu
- **Added** config option "Auto show playing"
- **Improved** colour blending for some elements in custom theme
- **Improved** rename track box to allow single tracks only (hold shift)
- **Improved** notifications to show app icon (KDE Plasma)
- **Tweaked** right side panel behavior to lock with full size art
- **Tweaked** open gallery behavior to open at selected rather than playing track
- **Fixed** text in bottom panel showing with center style side panel
- **Fixed** sub-menus possibly overlapping view box in compact view
- **Fixed** repeat button alpha overlap in Carbon theme
- **Fixed** gallery scroll bar sliding view past bounds
- **Fixed** a possible crash when resizing window with artist bio panel open
- **Fixed** launching under KDE causing screen flicker

### v4.8.0

- **Added** Japanese translation (Partial machine translation)
- **Added** Chinese Simplified translation (Contributed by tyzmodo)
- **Added** "Always center" option for art background function
- **Added** menu icon for Discord
- **Added** alternate right side panel layout
- **Added** toast for scrolling to hidden playlist on top bar
- **Added** compact artist list for compact mode
- **Added** config option for absolute track indices in titles disabled playlists
- **Improved** thumbnail generating while scrolling gallery
- **Improved** search progress indicator to animate
- **Improved** gallery power bar to create new playlist on wheel click
- **Enabled** showcase visualiser in compact mode
- **Tweaked** gallery scroll bar to reveal when scrolling by wheel
- **Tweaked** go-to-playing behavior to align album with top
- **Tweaked** Lavender Light theme colours
- **Tweaked** artist bio image size in compact view
- **Tweaked** font sizes in showcase view
- **Fixed** right-click not closing file/folder rename box's
- **Fixed** thread crash with old data files
- **Fixed** artist info panel staying open when in compact gallery view
- **Fixed** side panel metadata not respecting "always show selected" setting
- **Fixed** minimum window size with UI scaling
- **Fixed** playlist panel text colours in auto theme mode

### v4.7.1

- **Added** URL download function
- **Added** support for multiple artist comments in Vorbis tags
- **Added** frame to album art in showcase/lyrics view
- **Added** missing functionality for MPRIS2: Shuffle, LoopStatus and OpenURI
- **Added** scroll bar to gallery
- **Added** lightning button to enable power bar
- **Moved** sort functions to submenu
- **Tweaked** scroll speed of various elements
- **Fixed** bug with scrobble marker not hiding while listenbrainz enabled
- **Fixed** a crash when deleting a track while gallery open
- **Fixed** MPRIS2 non-compliance causing failure on KDE Plasma
- **Fixed** crash on select FLAC transcode option

### v4.7.0

- **Added** improved compact UI (when window is narrow)
  - **Added** new header bar style
  - **Added** compact volume control
  - **Added** hide tracklist in gallery
  - Adjust play button to play/pause
  - Adjust tracklist width to full window
  - Adjust settings to show tabs on top
  - **Fixed** showcase/lyrics view
  - **Fixed** menu positioning with window edge
- **Improved** appearance of playtime stars
- **Tweaked** tracklist row height default setting to large preset
- **Tweaked** view layout box to close on click on some buttons
- **Fixed** last.fm not respecting disable option
- **Fixed** right click mode menu triggering show current
- **Fixed** notification text not updating if no track name metadata
- **Fixed** an issue where playlist tabs may not be drawn after wide hidden tabs
- **Fixed** an issue where albums would become dragged while dragging panel

### v4.6.3

- **Improved** gallery to allow drag and drop to rearrange
  - **Tweaked** single click to play to trigger on mouse up
- **Improved** chart generator
  - **Added** cascade style option
  - **Added** no padding mode
  - **Added** two column text fallback
  - **Improved** thumbnails to crop and zoom to full square
  - **Improved** error handling
- **Improved** XSPF importing compatibility
- **Fixed** click transferring into mini-modes
- **Tweaked** size of thick track row height preset
- **Tweaked** settings check box appearance
- **Tweaked** save to disk to wait until window is unfocused
- **Moved** EQ settings to audio tab and theme settings to new theme tab

### v4.6.2

- **Fixed** numpad return key not being registered
- **Fixed** chart text grouping
- **Fixed** a change that caused artist list names being lowercase and not registering on click
- **Fixed** replay gain applying after song start

### v4.6.1

- **Fixed** startup crash if music directory was not found
- **Fixed** MP3 files using ID3v2.3 tags scanning incorrect date format
- **Fixed** import stalling when encountering folders with invalid permission
- **Fixed** freeze on restore with newer versions of SDL2

### v4.6.0

- **Added** new theme: Carbon
- **Added** album chart generator
- **Improved** startup speed slightly
- **Fixed** auto-theme not applying when in "tracks only" or "gallery" views
- **Fixed** gallery scroll position sliding slightly when re-entering gallery at top
- **Fixed** gap between hitboxes in tracklist (again)
- **Fixed** seeking beyond current track causing position to jump backwards instead of advance
- **Fixed** gallery jumping to beginning when re-entering on non-playing playlist
- **[Windows] Fixed** a text rendering issue in some cases with text on coloured backgrounds
- **[Linux] Tweaked** transcode finished desktop notification to emit even when window focused
- **[Linux] Fixed** music and download folders not following xdg-dirs
- **[Linux] Fixed** application not appearing in desktop default application list

### v4.5.2

- **Added** setting "Force subpixel text rendering"
- **Added** "Add to queue" toast box
- **Fixed** gallery not correctly shifting when clicking on top row when out of alignment
- **Fixed** tracklist truncating end track position if only tracks were listed
- **Fixed** bug causing global search crashing in some cases
- **Tweaked** gallery to remember scroll position on restart
- **Tweaked** gallery tag bar to not activate when window not focused
- ***Disabled*** thin gallery border setting for large art sizes (temporary bug mitigation)

### v4.5.1

- **Added** "artist " search prefex to search overly to only search artists
- **Added** config option "show-current-on-transition"
- **Extended** mpris2 with LovePlaying and UnLovePlaying methods
- **Fixed** random track shortcut behavior when random albums mode was set
- **Fixed** notification text for KDE Plasma update
- **Fixed** gallery cache being unnecessarily cleared when using certain functions
- **Improved** middle click add to queue to select track
- **Improved** micro mode seek bar click area for restarting track
- **Tweaked** search overlay result rankings
- **Tweaked** showcase view artist line font size

### v4.5.0

- **Split** import scanning into two stages, allowing tracks to be played before scan.
- **Added** setting "Prefer thinner borders" for gallery
- **Added** keyboard shortcut for loving selected track (unbound)
- **Added** year results to global search
- **Added** random load effect to gallery for small gallery thumbnails
- **Added** two side panel settings to "view" tab in settings
- **Improved** gallery cache loading speed
- **Improved** MP3 genre code detection
- **Tweaked** mini mode menu for simplification
- **Tweaked** love track to display instantly when no last.fm account
- **Tweaked** "View" settings layout
- **Tweaked** minimum gallery art size (can now go smaller)
- **Tweaked** column view auto deactivation on open gallery space checking
- **Tweaked** album count algorithm on stats view
- **Tweaked** gallery to group multi-cd albums
- **Fixed** length of rendered tracklist (now more accurate and consistent)
- **Fixed** UI stutter when changing gallery art size
- **Fixed** performance issue when loading gallery image from cache
- **Fixed** scrobble pause not affecting listenbrainz
- **Fixed** scrobble of last.fm/listenbrainz being resubmitted if type of other failed
- **Fixed** queue album not finishing if last album in playlist
- **Fixed** queue album possibly playing next track in playlist after album
- **Fixed** gallery thumbnailer crashing if loading an image failed
- **Fixed** gallery scroll markers not hiding when mouse leaves right edge of window
- **Fixed** scrobble retries not using original time stamp
- **Fixed** hearts possibly being rendered behind text in tracklist
- **Fixed** gallery shifting position slightly when jumping to end row
- **Fixed** playlist list scrolling
- **Fixed** scroll pulse animation showing if playlist was empty
- **Fixed** delay in tracklist selection rendering
- **Fixed** track notification being sent when auto-stop was enabled
- **Fixed** fix advance when paused playing old track when disconnect-pause setting was active
- **Fixed** a crash with showcase view if playing folder was removed
- **Fixed** column top bar possibly rendering over into gallery area
- **Fixed** hide column bar default setting
- **Fixed** hide column bar setting in settings not properly updating UI
- **Fixed** crash when enabling auto theme

### v4.4.1

- **Added** Ctrl-click to global search to add items to current playlist
- **Added** setting to hide side panel queue when empty
- **Added** setting to show playlist list in left side panel
- **Added** reload bio option to bio panel (hold shift in context menu)
- **Tweaked** queue menu "Except for This" to only reveal on shift hold
- **Fixed** crash on upgrade when items were in queue
- **Fixed** playlist list scroll bar possibly not appearing when needed
- **Fixed** queue track count text jumping position when clicking last item in queue

### v4.4.0

- **Added** "Composer" field to track box
- **Added** "Album-Artist", "Composer" and "Comment" to columns mode
- **Added** per column colours to theme files
- **Added** config option to show selected track in side panel when stopped
- **Added** config option to stop track change notifications while git in Mini Mode
- **Added** seek bar to mini mode micro
- **Added** shortcut to cycle between mini mode square and micro (shift click and wheel click)
- **Added** track menu function to add track to beginning of queue (hold shift to show)
- **Added** queue option to play item immediately
- **Added** queue option to crop to selected track only
- **Added** keybinds global-search, cycle-theme-reverse and reload-theme
- **Added** track sum and total duration to queue panel
- **Added** on-the-fly backend switching
- **Added** tool-tips to fields in columns mode (Linux only)
- **Added** MP3 genre code detection to tag scanner
- **Added** drag from playlist to insert in queue functionality
- **Added** "Queue to New Playlist" function
- **Improved** config file to be programmatically generated
- **Improved** "delete embedded image" function to only remove from single file when shift key down
- **Improved** search to make album-artist and composer fields searchable
- **Improved** columns 'Hide bar' mode to persist, is now restored using a right click context menu
- **Improved** last.fm love scanner to ignore case
- **Improved** desktop icon size to better fit GNOME guidelines
- **Improved** scrobble toggle function to use ListenBrainz branding if enabled and Last.fm is disabled
- **Tweaked** auto-stop behavior with queue, now added per item toggle, no longer always ignores when queue active
- **Tweaked** main scroll bar background for transparency, restored size in column mode
- **Tweaked** transcode output setting text for better clarity
- **Tweaked** bottom panel title to always show if window is large
- **Tweaked** artist list to show all artists if playlist is not large
- **Tweaked** mini mode seek bar to trigger on mouse up rather than down
- **Tweaked** window button colours for better visibility in mini-mode
- **Tweaked** auto-stop behavior to stop with next track ready
- **Tweaked** desktop notification text layout. Notification is now withdrawn after time
- **Tweaked** left panel to always show queue under playlist list
- **Moved** "prefer using album-artist in artist list panel" setting to config file
- **Moved** "double digit" setting to config file
- **Moved** listenbrainz and discogs token storage to config file
- **Moved** UI scale setting to config file
- **Fixed** and enabled mini mode with maximizing
- **Fixed** a bug that caused FLAC pictures to not be detected on rare occasion
- **Fixed** artist list sorting with case sensitivity
- **Fixed** artist list sort by album-artist setting not remembering on restart
- **Fixed** setting fonts in config file
- **Fixed** subtle text rendering issue on some settings buttons
- **Fixed** column drag tag text positioning
- **Fixed** "album artist" track box field always showing tooltip on hover
- **Fixed** "sort by filepath" not ignoring case
- **Fixed** progress bar not resetting with auto-stop when using GStreamer backend
- **Fixed** single track albums in queue playing next track after
- **Fixed** gallery and artist list thumbnail background colours with light theme
- **Fixed** queue panel infini scrolling
- **Fixed** scrobble toggle not showing if only ListenBrains was active
- **[Wayland] Fixed** scroll bars not functioning (partially)

### v4.3.1

- **Added** mini mode selector menu with new options
- **Added** restore button to mini mode
- **Added** option to prefer using album-artist in artist list panel
- **Tweaked** mini mode controls to always display when cursor enters panel
- **Fixed** gallery not jumping to artist when using artist list
- **Fixed** cached last.fm artist images not appearing in artist bio panel

### v4.3.0

- **Added** quick cover art download feature
- **Added** input config file. Many keyboard shortcuts can now be remapped
- **Added** various key functions for switching layouts and for "Toggle Broadcast"
- **Added** setting to apply art background to showcase view only
- **Added** lyric provider Apiseeds
- **Added** lyrics settings button to settings
- **Added** artist image sources farnart.tv and Discogs
- **Added** delete image function
- **Enabled** artist image downloading and artist panel
- ***Disabled*** tooltip for forward button (was annoying)
- **Added** mini mode background colour to theme files
- **Tweaked** discord RP to show album field
- **Improved** accounts settings tab layout
- **Improved** discord RP to suspend when idle
- **Improved** "Open with Picard" button to work with selections (and single tracks using shift)
- **Fixed** album art cycle to ignore click on window focus
- **Fixed** top row heart tooltip position
- **Fixed** a possible crash when using gallery key control mode
- **Fixed** reload metadata function not functioning for whole album when triggered manually

### v4.2.3

- **Fixed** startup crash when non en locale detected

### v4.2.2

- **Fixed** playtimes doubling when using edit with Picard
- **Fixed** metadata reload with Picard not working when switching playlist before closing
- **Fixed** tracks in folder with other folders not being sorted together
- **Tweaked** artist list click hkighlight animation time
- **Tweaked** artist list to open on playing artist is possible
- **Changed** artist list click to cycle artist blocks in playlist
- **Changed** reset image cache to partial reset artist thumbnails
- ***Disabled*** artist image downloading
- ***Disabled*** artist info panel


### v4.2.1

- **Added** loading of user artist thumbnails from "artist-pictures" folder
- **Changed** artist filter playlists to link to parent
- **Tweaked** artist list scroll bar behavior
- **Fixed** album image cache resets clearing artist thumbnails
- **Fixed** background skin not changing on singles
- **Fixed** crash when using gallery and 1.25x scaling with background skin on


### v4.2.0

- **Added** artist list to left side panel
- **Added** skin background using album art function
- **Added** setting "Auto sort on import"
- **Added** feature to transcode single tracks at a time
- **Added** setting to transcode files inplace
- **Tweaked** behavior when launching with file
- **Fixed** "Stop" function in Windows tray not working
- **Fixed** click not working after minimize and raise
- **Fixed** open with not working with some file managers
- **Fixed** repeat album mode not working with "playback follows cursor"
- **Fixed** repeat and shuffle settings not persisting on app restart
- **Fixed** gallery and lyrics not having scrolling bounds
- **Fixed** bug with side panel toggling in lyrics showcase view
- **Fixed** scroll with chord lyrics applying to whole window
- **Fixed** scroll bar jitter when mouse held down on bar center

### v4.1.1

- **Added** progress bar for transcoding
- **Fixed** transcode stalling when duplicate tracks present
- **Fixed** transcode not producing thumbnail
- **Fixed** being able to enter mini-mode in full-screen
- **Added** config option to use small file buffering
- **Improved** MP3 encoding to not require separate LAME encoder

### v4.1.0

- **Added** playback setting "Playback follows cursor"
- **Added** support for displaying timed lyrics from .lrc files
- **Added** feature to display guitar chord lyrics
- **Added** fetch guitar chord lyrics from GuitarParty
- **[Windows] Added** system tray with min to tray option
- **Changed** portable mode to use a subfolder for user data
- **Fixed** audio timing (for real this time)
- **Fixed** showcase title text position when using GStreamer
- **Fixed** scrobble marker jumping on first tick
- **Fixed** love heart text alignment when at left side of playlist
- **Fixed** album art display not preferring upper level files (thanks gSilas for fix)
- **Fixed** click on folder title causing unnecessary processing
- Possible fix for inaccurate mouse click positioning
- **Increased** file buffer for audio to reduce stuttering
- **Improved** shuffling to update when tracks are added to playlist
- **Improved** time display at end of track with CUE tracks
- **Moved** "Resume playback on launch" option to config file
- **Moved** "Import PLEX music" to "Accounts" tab
- ***Removed*** "Shuffle avoids repeats" option (now always on)

### v4.0.0

- **Added** lock icon and indicator for locked playlists
- **Fixed** animation jitter with drop tracks on tab
- **Fixed** drop files not saving state
- **Fixed** artist bio scroll bar possibly not scrolling full height
- ***Reverted*** some buffer changes for more accurate time positioning
- **Restored** Windows support
- **Fixed** crash when transcoding with gallery open first time
- **Fixed** crash when using folder mover
- **Fixed** playlist status text position not respecting artist info box
- **[Flatpak] Improved** fontconfg detection

### v3.9.1

- **Fixed** crash when deleting track using delete key
- **Fixed** track drag to playlist not working when tabs disabled
- **Fixed** track drag to viewed playlist not triggering redraw
- ***Set*** default settings panel to "Function"

### v3.9.0

- **Added** EQ control
- **Added** function to delete individual tracks physically
- **Added** setting to change device buffer length
- **Added** function to lock playlists from accidental deletion
- **Added** menu function to make artist panel larger
- **Re-Added** function to allow importing via copy and paste
- **Tweaked** file buffers to be larger and enabled async loading
- **Tweaked** disc number detection to better handle case of inconsistent tagging
- **Tweaked** playlist scroll wheel speed with low vertical space
- **Improved** data saving to write to disk immediately on many more functions that modify data
- **Improved** Discord rich presence to allow disconnecting (still broken on flatpak)
- **Improved** GNOME media key support
- **Increased** showcase visualiser frame rate
- **Fixed** showcase visualiser low frame rate when changing volume
- **Fixed** not force showing lyrics when using "Lyrics" button
- **Fixed** animations malfunctioning on clock changes
- **Fixed** PLEX function caching in data instead of cache directory
- **Fixed** and improved symbolic icon
- **Fixed** artist info panel sometimes showing previous bio when changing fast
- **Fixed** not showing track in MPRIS on startup
- **Fixed** some possible crashes with blank slate

### v3.8.1

- **Tweaked** rename tracks to ignore bad file renames
- **Tweaked** showcase visualiser to activate more in upper ranges
- **Tweaked** showcase visualiser colourisation
- **Tweaked** spectrogram to toggle colours on re-select
- **Improved** mini-mode and queue-box to show filename if metadata missing
- **Fixed** enable move folder setting persisting
- **Fixed** rename tracks default template
- **Fixed** a possible crash when importing tracks with stats tab open
- **Fixed** clicking between buttons in view box causing it to close
- ***Removed*** spectrogram colour config

### v3.8.0

- **Added** mini mode UI
- **Added** visualizer to showcase view
- **Added** option to disable tabs on top panel
- **Added** keyboard shortcut for adding to queue (ctrl + q)
- **Added** support for user folder themes
- **Added** menu function to hide lyrics in "Lyrics showcase" view
- **Tweaked** playing highlight in some themes
- **Tweaked** drag sensitivity for dragging tabs in playlist side panel (reduced)
- **Tweaked** tab dragging to toggle hidden if dragged between top or side panel
- **Changed** tab drag to end function to move instead of duplicate
- **Improved** device switching to allow switching while playing
- **Improved** compatibility with KDE to detach audio when paused
- **Improved** playlist side panel to allow direct file dropping
- **Improved** showcase title text to scale with text length
- **Fixed** not being able to restart app immediately
- **Fixed** image menu incorrectly showing items as greyed
- **Fixed** PLEX scan status text persisting if failed
- **Fixed** crash on F12 press
- **Fixed** light mode galley text rendering with auto theme
- **Fixed** showcase view text colours with auto theme
- ***Removed*** F10 to toggle decorations
- ***Removed*** gallery card style option (now always on)
- ***Removed*** jump on stall detection

### v3.7.0

- **Added** integrated PLEX streaming support
- **Added** setting to automatically search LyricWiki
- **Added** setting to hide album art box
- **Added** link to lyrics view in metadata box
- **Added** keyboard shortcuts to show track info box
- **Added** playlist background mascot feature
- **Added** key to change window opacity
- **Added** option to toggle gallery single/double click to play
- **Improved** importing to always auto-name new playlists
- **Improved** listenbrainz to submit track ID data
- **Improved** menu sub position to start at parent location
- **Improved** transcode finish notification to provide button to open folder
- **Improved** artist bio panel resize performance
- **Improved** internationalisation for various number displays
- **Tweaked** artist bio status font
- **Tweaked** artist bio rate limiting (reduced)
- **Tweaked** notification timing at end of track
- **Fixed** a crash when resizing window small before playing
- **Fixed** a crash when pressing back on an empty playlist
- **Fixed** audio device list not being contained to box / not being scrollable
- **Fixed** direction keys changing playlist when a modifier key was held
- **Fixed** listenbrainz profile url link cursor hit box
- **Fixed** side panel lyrics being wrong colour on auto theme
- **Fixed** notification not showing correctly when no album field
- **Fixed** tag scanner including date format data in date field for M4A
- **Fixed** inconsistent / wrong behavior when adding album to queue
- **Fixed** / workaround for lyricwiki instrumental pages
- **Fixed** window drag border being active when maximized
- **Fixed** a crash when navigating through gallery very fast
- **Fixed** pressing up to first gallery album not working
- ***Removed*** "Finish current" and "Automatically finish current album" options

### v3.6.0

- **Added** new theme "Lavender Light"
- **Added** setting to change gallery tile to card style (Light mode only)
- **Redesigned** app icon
- **Redesigned** rename playlist box
- **Improved** last.fm login to use web authorisation method
- **Improved** gallery text colour for light backgrounds
- **Restored** "Large row preset" button
- **Tweaked** transcoder to use original folder name when tracks from multiple albums are detected
- **Tweaked** positioning of various elements in settings box
- **Tweaked** folder transfer safety check
- **Tweaked** playlist side bar tab
- **Tweaked** playlist text positioning in 1.25x mode
- **Fixed** quick find box font positioning
- **Fixed** a bug where "disk total" field would not show for some formats
- **Fixed** missing HiDPI icons for Sonemic and Picard
- **Fixed** queue thumbnails not respecting UI scale
- **Fixed** crash if enter pressed with empty playlist
- **Fixed** playlist side bar titles not updating immediately after drag
- ***Removed*** folder transfer show option (reverted to always on)
- ***Removed*** web remote interface

### v3.5.4

- **Added** settings option to resume playback on app restart
- **Added** settings option to finish currently playing album when queuing an album
- **Added** config option to force mono audio (bass only)
- **Improved** playback modes to remember setting after restart
- **Improved** download monitor archive contents detection
- **Tweaked** playlist panel highlight colour slightly
- **Fixed** a crash when double clicking item in queue
- **Fixed** a crash if adding item to queue with blank slate
- **Fixed** download monitor indicator being delayed on startup
- **Fixed** crash on starting inbound stream
- **Fixed** radio random and revert causing seek bar to visually momentarily jump to zero
- **Fixed** case where using revert function to missing file could cause next track to not start at beginning
- **[GStreamer] Fixed** radio random and revert not setting start time

### v3.5.3

- **Fixed** track info genre field showing last field
- **Fixed** a possible crash during database clean

### v3.5.2

- **Added** setting to switch audio playback backend to GStreamer
- **Added** hidden function to find lost playtimes (Hold shift in folder menu)
- **Added** 7z support to archive extractor
- **Added** button in settings to cycle to previous theme
- **Tweaked** gallery jumping when only one item in view
- **Tweaked** mode buttons disappearing in small window
- **Tweaked** rename playlist box to open with text highlighted
- **Tweaked** archive app detection with Flatpak
- **Restored** option to not delete archives on extraction
- **Fixed** archive monitor activating when target folder already exists
- **Fixed** 'open with picard' losing track of playtimes if filename was changed
- **Fixed** replay gain indicator not offsetting position on full time indicator
- **Fixed** time indicator possibly updating irregularly
- **Fixed** "Fetching image" text rendering.
- **Fixed** "Show Current" not jumping when track just out of view
- **Fixed** image details showing ERROR with cached files
- **Fixed** tag bar on 1.25x UI scaling
- **Fixed** wide art mode not locking ratio to less wide art then previous
- **Fixed** wide art mode lock position being slightly incorrect
- **[GStreamer] Fixed** loading file paths with certain characters in name
- **[GStreamer] Fixed** last.fm not scrobbling in gstreamer mode
- **[GStreamer] Fixed** tracks not being marked when missing

### v3.5.1

- **Added** function to MENU for importing home music folder to new playlist
- **Added** setting to disable fade of track pause
- **Added** option to show total folder duration in folder title
- **Enhanced** re-import function, moved to main playlist menu
- **Changed** last.fm to submit album-artist on "feat." detect
- **Added** removing embedded images support for FLAC
- **Fixed** return to maximized state on restart
- **Tweaked** window title drag zone to be closer to MENU

### v3.5.0

- **Added** folder/album queueing
- **Added** queuing inspector to left side panel
- **Added** option to pause force queue
- **Added** gallery wheel click to add album to queue
- **Added** menus to repeat and shuffle buttons for better usability
- **Added** random albums as playback mode
- **Changed** "stop at end" to have lower priority than force queue
- **Changed** force queue to persist over restart
- **Changed** last.fm scrobbler to not disable on failure
- **Tweaked** gallery artist font
- **Fixed** power bar and scroll field overlapping
- **Fixed** pausing with gstreamer fallback
- **Fixed** crash when queued track is removed from playlist
- **Fixed** crash when queued track was removed using clean database function
- **Fixed** a possible crash caused by playlist scroll bar
- ***Removed*** option to toggle "Add to queue" in menus

### v3.4.0

- **Added** "Add to queue" to track context menu
- **Added** "Open folder" to gallery context menu
- **Added** support for side bar extending on wide album art
- **Changed** folder transfer to require enabling in settings with warning
- **Changed** 'cycle' and 'repeat' playlist functions to ignore hidden playlist's
- **Changed** clicking bottom row in gallery to bring row into full view
- **Changed** gallery hit boxes to exclude titles
- **Fixed** scroll bar jumping direction with few tracks, fixed possible crash
- **Fixed** pause command de-syncing if clicked quickly
- **Fixed** area of rename playlist box not being selectable
- **Fixed** dragging to re-arrange tracks in playlist not correctly updating gallery
- **Fixed** cycle all playlist setting not having effect
- **Fixed** possible race condition causing playback thread to crash
- **Fixed** gallery moving relative position when toggling "Show titles in gallery"
- **Fixed** column mode not showing after restart (for real this time)
- **Fixed** slide cursor showing after moving mouse past side bar while mouse down
- **Fixed** fade transition to not wait for IO
- **Fixed** column drag hit fields slightly overlapping
- **Fixed** right side panel to drag by offset rather than absolute click position
- **Tweaked** column title font
- **Tweaked** default gallery titles to on
- **Improved** column dragging visual feedback
- **Improved** gallery scroll arrows to highlight on mouse over
- **Improved** love indicator to display in a constant time then revert if failed
- **Restored** rudimentary Windows support

### v3.3.3

- **Fixed** possible playback stall, partially
- **Fixed** tag editor launching from Flatpak

### v3.3.2

- **Fixed** incorrect end of playlist notification

### v3.3.1

- **Fixed** "Use crossfades when jumping tracks" being disabled causing gapless transitions to fail

### v3.3.0

- **Added** gapless playback
- **Added** secret credits page
- **Changed** rename templates to full words with angle brackets
- **Tweaked** folder/album title text to truncate separately to date
- **Tweaked** playlist side bar text truncation
- **Tweaked** search to skip playlist's with angle brackets in name
- **Fixed** incorrect length calculation of ogg vorbis files
- **Fixed** folder/album titles not truncating
- **Fixed** scrobbles not waiting until end of track to be submitted
- **Fixed** limit on number of friend hearts displayed
- **Fixed** auto theme not persisting in gallery view
- **Fixed** gallery jumping to wrong position on playlist switch if position was at top
- **Fixed** a case where playlist would change vew position when deleting another playlist
- **Fixed** a possible issue where playback would stall at end of a long track
- **Fixed** end lines possibly missing from lyrics views
- **Fixed** side panel closing if application restarted while in lyrics view
- **Fixed** fade time setting affecting gapless transition
- **Fixed** tag scan not forcing redraw on metadata update
- ***Removed*** rename box's template hints
- ***Removed*** template defaults from config file

### v3.2.4

- **Added** new theme Astro
- **Added** meta folders to search overlay results
- **Added** track menu shortcut to view track in lyrics view
- **Added** tooltips to 'modify folder' buttons
- **Added** icon to rename tracks menu label
- **Added** warning protection to clear all loves button
- **Fixed** app not starting if a locale had not been configured
- **Fixed** year sorter menu labeling being incorrect
- **Fixed** a bug with file rename function where unintended tracks from other folders could be modified
- **Fixed** file rename function sometimes failing to show warning on missing metadata
- **Fixed** search result right click marking track as playing position
- **Fixed** gallery position not staying when using move folder function
- **Fixed** a case where folder break would not distinguish between different folders with same name
- **Fixed** reload metadata function not detecting file extension changes
- **Fixed** notification display at end of playlist
- **Fixed** a crash when playing a CUE sheet track at the end of a playlist
- **Fixed** column mode not using natural sort for track numbers
- **Fixed** UI not remembering being in column view on restart
- **Fixed** column view not using new heart icons
- **Fixed** seek bar not updating while volume bar was held
- **Fixed** heart name text rendering with light playlist background colour
- **Improved** gallery to remember view position when switching playlists quickly
- **Improved** search algorithm to better handle fragmented search terms for albums
- **Improved** power tag bar to better adapt to different library sizes and available window space
- **Improved** playlist tab panel text readability on light backgrounds
- **Tweaked** file rename box appearance to better match folder modification box
- **Tweaked** track notification text order
- **Tweaked** search overlay to better fit results to window height
- **Moved** rename template hints to a hover over question mark
- ***Removed*** remains of broadcast sync feature
- **[Wayland native] Fixed** files not importing on drag and drop

### v3.2.3

- **Added** album repeat mode
- **Added** shuffle within album mode
- **Added** option for true shuffling
- **Added** right click menu to close artist info panel
- **Fixed** transcode stalling on filepaths containing double-quotes
- **Fixed** possible issue and crash when playing CUE sheet tracks and switching playlist
- **Fixed** 'hi' notification when track had no metadata
- **Fixed** some draw positioning in search overlay
- **Tweaked** playlist panel toggle to open on drag over
- **Added** DE whitelist for notification support as workaround for mpris commands failing
- ***Removed*** file corruption warnings due to many false positives

### v3.2.2

- **Added** option to show desktop notifications for playing track
- **Added** ctrl+z undo steps for undoing track deletes
- **Improved** handling and feedback of corrupt files
- **Tweaked** artist bio font size to be larger
- **Tweaked** artist bio fetching to have lower rate limit
- **Fixed** player sometimes stalling on transition with fade off
- **Fixed** missing truncation tooltip for filepath in track box
- **Fixed** undo 'clear playlist' not restoring inplace
- **Fixed** artist bio scroll bar not recalculating on panel resize
- **[Flatpak] Fixed** output audio device switching
- **[Flatpak] Added** possible workaround for poor font rendering

### v3.2.1

- **Added** embedded picture support for OGG and OPUS tags
- **Added** options to turn off crossfading
- **Improved** error feedback when importing an archive
- **Tweaked** pre-import counter to favor speed over accuracy
- **Tweaked** track import sorting algorithm to better handle inconsistent disc number tagging
- **Tweaked** find box to close on backspace
- **Tweaked** search overlay to require more mouse movement before registering
- ***Reverted*** some track info box fonts
- ***Reverted*** album search return behavior to auto-play
- **Fixed** delayed gallery rendering when player was stopped
- **Fixed** artist info links possibly containing a period
- **Fixed** enter key possibly registering when using a window switcher
- **Fixed** possible crash when using fractional scaling and artist info panel
- **[Flatpak] Added** workaround for possible issue causing crash on start


### v3.2.0

- **Added** context menu to gallery album right click
- **Added** sorting option 'Reversed Folders'
- **Added** audio bit-depth display to track box (FLAC, APE, TTA)
- **Added** tool-tips for truncated text in track info box
- **Added** function to duplicate playlist by dragging tab to end
- **Added** highlight for transcoded albums in gallery while transcoding
- **Added** cursor tab drag indicator
- **Improved** error feedback for 'Start Broadcast' when there are no tracks
- **Improved** folder mover to remove old track entries
- **Improved** stat tab codec chart to generate a playlist on click
- **Improved** playlist side panel to include the 'sort' sub menu
- **Tweaked** 'rename playlist' box size
- **Tweaked** track box fonts and colour
- **Tweaked** folder mover menu text and behavior
- **Tweaked** 'duplicate playlist' function to modify the new title with a hint
- **Tweaked** playlist tabs to allow dragging between side panel and top panel
- **Tweaked** folder delete function to move to trash by default
- **Tweaked** download indicator to allow dismissal of watched items
- **Tweaked** scroll bars to highlight on click
- **Fixed** download indicator staying on if file was removed
- **Fixed** gallery thumbnails to match side bar cycling without needing to reset (again)
- **Fixed** delete option causing gallery to jump position to selected
- **Fixed** possible unexpected behavior when modifying playlist with a menu open
- **Fixed** error handling with last.fm love sync
- **Fixed** top bar metadata for small window positioning
- **Fixed** window not raising on extra instance launch
- **Fixed** lyrics view not returning to gallery from track box button
- **Fixed** duplicate playlist undo backups
- **Fixed** possible losing focus of playing playlist if a playlist was deleted
- **Fixed** a crash if a playlist was deleted then back button was pressed twice
- **Fixed** album artist text in info box overlapping album art thumbnail
- **Fixed** resulting album from search not aligning to top of playlist
- **Fixed** tracks with no metadata showing as blank in search results
- **Fixed** unstable text positioning in track box with fractional scaling
- **Fixed** some menu entries not greying out
- **Fixed** an issue with playing position after deleting tracks
- **Fixed** an issue where submenus might not position within window
- **Fixed** search overlay 'show only' function sometimes showing the playing track instead
- **Fixed** subsequent searches not resetting view to top
- **Fixed** scrobble marker show while player was paused
- **Fixed** lyrics display being truncated with long lyrics
- ***Removed*** 'cut' menu option

### v3.1.2

- **Added** 1.25x UI scaling option
- **Fixed** artist info panel not scaling with UI scaling setting (partial)
- **Fixed** 'next theme' button positioning
- **Fixed** crash on change time mode with clean slate
- **Fixed** scroll area on gallery being too large with few albums

### v3.1.1

- **Fixed** crash on clear playlist [critical]
- **Fixed** queue not overriding repeat setting
- **Fixed** 'new playlist' menu appearing on scroll bar right click
- **Fixed** typing in rename folder box activating search overlay
- **Improved** rename files and folders, added 'default' button, now saves template on restart.


### v3.1.0

- **Added** new 'folder tag' feature to gallery
- **Added** album counts to stats tab
- **Improved** ctrl-Z function; can now undo multiple playlist deletes
- **Changed** transcode files opus extension to use '.opus.ogg'
- **Changed** left clicking play button while playing now jumps view to playing track
- **Changed** behavior of enter key on album search result now just shows instead of playing
- **Tweaked** search algorithm to better return exact phrase matches
- **Tweaked** playlist scroll bar appearance
- **Tweaked** side panel lyrics positioning
- **Tweaked** settings to warn if LAME is not installed when selecting MP3 for encoding
- **Fixed** a VRAM memory leak.
- **Fixed** gallery not updating on inplace sort functions.
- **Fixed** a stall on importing some XSPF playlist's
- **Fixed** a crash when holding shift and scrolling
- **Fixed** playlist switch on delete not setting gallery position
- **Fixed** a possible crash when changing volume with clean state
- **Fixed** a crash when deleting final playlist with gallery open
- **Fixed** genres not showing in search results
- **Fixed** 'sort year per artist' sort function truncating the end artist
- **Fixed** XSPF inter-app compatibility
- **Fixed** track text in playlist not truncating if space was negative
- ***Removed*** option to hide transcode function from menu

### v3.0.2

- **Fixed** low quality thumbnail caching
- **Fixed** an issue where a drag and drop action could trigger on track load
- **Fixed** an issue where an empty folder would cause the download indicator to stay on
- **Fixed** clicking next to minimize button changing visualiser
- **Improved** some scroll-bars to highlight on mouse over
- **Changed** folder copy/move function to move only. Removed some menu entries.
- **Changed** theme default
- **Tweaked** sub-menu appearance
- **Added** menu icon for Picard
- Dropping an album onto playlist bar now gives the new playlist the title of the album
- **Added** preliminary support for multi-language / translations
- ***Removed*** 'playback follows playlist' setting, now always off.

### v3.0.1

- **Simplified** last.fm scrobble settings
- **Added** ListenBrainz support
- **Added** button to open app data folder
- **Improved** text positioning for customised font
- **Improved** queue display indication
- **Improved** artist bio link buttons to show hand cursor
- **Fixed** about title showing playlist name after using folder filter
- **Fixed** scroll on top bar not respecting hidden playlist's
- **Fixed** last track in playlist not showing as playing in gallery
- **Fixed** UI slowdown when playing title is long
- **Fixed** queue not working for end of track advancing
- **Fixed** playing highlight to show only playing instance
- **Fixed** showcase lyrics not resetting scroll position after using lyric search
- **Fixed** crash on start broadcast (critical bug)
- **Fixed** an issue where scrobbling could not be paused if a track had not yet been playing
- Partial fixes to 2x scaling
- Partial fixes to auto theme mode
- **Tweaked** tooltip display to be slightly larger
- **Tweaked** layout setting defaults: CSD on, default window size, side panel on
- **Tweaked** audio archive detection to be more relaxed
- **Tweaked** shift image metadata to show full resolution information
- **Changed** default audio encoder output directory to ~/Music/encode-output/

### v3.0.0

- **Added** artist info panel (gets data from last fm)
- **Added** playlist selector side panel
- **Added** playlist hide feature (hides individual playlist tabs from top panel)
- **Added** download monitor indicator to top panel (replaces previous F8 function)
- **Added** setting to extract archives to music folder
- **Added** scroll bar to side panel lyrics
- **Moved** 'search image on google' function to picture menu
- **Moved** 'show lyrics in side panel' setting from settings box to lyric menu
- ***Removed*** Windows operating system support
- ***Removed*** previous playlist selector box
- ***Removed*** playlist selector box's left click to quick add track feature
- ***Removed*** playlist selector box's direct set playlist playing feature
- ***Removed*** 'dim gallery' function and setting
- ***Removed*** 'always use folder names' setting (now always off)
- ***Removed*** setting for gallery disk caching (now always on)
- ***Removed*** setting for showing lyrics in radio web page (now always on)
- ***Removed*** setting for deleting archives (now always on)
- ***Removed*** UI colour theme 'Deep'
- **Tweaked** delete archive function to move files to trash
- **Tweaked** search overlay search algorithm
- **Tweaked** mouse side button functions for more obvious behavior
- **Tweaked** show hearts setting to be allowed in addition to stars and lines
- **Improved** search overlay to allow scrolling by scroll wheel
- **Changed** user config, cache, and data folder locations to Linux appropriate ones
- **Fixed** track special indicator lengths in playlist only view
- **Fixed** extra track being selected if mouse moved quickly
- **Fixed** previous selected track temporarily remaining highlighted after right click
- **Fixed** border being active when window maximized
- **Fixed** duplicate tracks appearing in search overlay
- **Fixed** words not truncating properly (bug from v2.8.3)
- **Fixed** window minimum size not being enforced

### v2.8.3

- **Added** 'love track' option to track menu
- **Added** show love hearts for loved tracks display option
- **Added** function to show last.fm friends loves in heart display
- **Added** function to fetch loved tracks from last.fm
- **Added** functions to clear loved tracks from db
- **Added** new quick import function to key F8
- **Added** warning when attempting to love track while not connected to last.fm
- **[Linux] Added** function to show playing track name in Discord
- **[Linux] Added** auto extract rar archive support when 'unrar' is available
- **Tweaked** 'show columns' button to switch view when on showcase view
- Web server can now be stated and stopped without restart
- **Fixed** folder title hit area overlapping scroll area
- **Fixed** tracks not scrobbling on repeats
- **Fixed** track love function blocking main UI
- **Fixed** crash when broadcast advances track after deleting playlists
- **Fixed** right end of broadcast seek bar not being clickable
- **Fixed** possible case causing subroutine crash
- **Fixed** rename box triggering search overlay
- **[Linux only] Fixed** performance slowdown when truncating text
- **Moved** documentation to Github wiki


### v2.8.0

- **Added** new global search function
- **Added** time display mode for total album time
- **Added** embedded image support for M4A files
- **Extended** metadata support for M4A: album-artist, disc number and lyrics
- **Bound** space-bar key to pause and resume playback
- **Improved** device selection UI feedback
- **Improved** delete playlist function to try return view to previous playlist
- **Improved** importer to ignore MACOSX folders and DOT files
- **Improved** 'get lyrics' function to not block main UI
- **Fixed** gallery hit boxes being too large when titles are disabled
- **Fixed** playlist default setting not matching original default
- **Fixed** transcode cancel menu overlapping window drag area
- **Fixed** fixed message box not clearing after continued keyboard input
- [Linux] Filename changes are now tracked when editing tags with Picard
- **Bound** F5 key to toggle lyrics view


### v2.7.0

- **Added** transcode option 'Save opus as ogg file extension' (for Android compatibility)
- **Added** 'return' button to lyrics showcase view
- **Added** background fade effect for opening settings box
- **Added** new error icon to some error messages
- ***Removed*** 'gallery only' view layout
- ***Removed*** 'album art plus tracks' view layout
- ***Removed*** 'scan rym db' function
- **Combined** main and view menu
- **Changed** lyrics showcase button to function as a toggle
- **Changed** view buttons to not close on click
- **Changed** transcode image thumbnail names to "cover.jpg" only (for improved compatibility)
- ***Set*** new defaults: visualiser enabled, row size larger
- **Improved** error feedback for changing output devices
- **Fixed** replay-gain db indicator not being truncated
- **Fixed** bug with side panel lyric setting
- **Fixed** output sound device not being remembered on restart
- **Fixed** gallery setting not being remembered on restart
- **Fixed** remove embed function causing crash
- **Fixed** showcase view not showing radio metadata, not showing title when missing metadata
- **Fixed** cursor flicker on column drag
- **[Windows] Fixed** non ascii device names causing playback to fail


### v2.6.4

- **Added** right click menu for canceling imports and transcodes
- **Improved** quick playing artist search function, moved shortcut to F4
- **Improved** error handling for folder mover function
- **Added** size limit for folder delete function
- **Fixed** not being able to step further back in random mode if previous track were missing
- **Fixed** stream recording incorrectly giving an error message
- **Fixed** folder mover not using album-artist as title
- **Fixed** crash when left clicking empty album art
- **Fixed** case in track info box where comment text would overlap thumbnail
- **Fixed** file not being importable after linked cue file
- **Fixed** default row size setting mismatch
- **Fixed** track info box WAV tag having bad rendering
- **Allowed** last.fm module to be optional
- **[Linux] Fixed** dragging volume bar causing unstable rendering


### v2.6.3

- **Added** support for embedded CUE sheets in Flac files (Vorbis type)
- **Added** 'Next' and 'Previous' function to picture menu
- **Added** config file option for logarithmic volume control
- **Added** function to sort albums by year per artist
- **Added** feedback animation for when dropping files on tabs
- **Improved** search to re-scan on playlist switch
- **Improved** search to indicate when top or bottom of playlist is reached
- **Tweaked** search box appearance
- **Tweaked** alignment of 3 digit track indices
- **Fixed** genre field not being imported from CUE sheets
- **Fixed** search text entry lag when nothing was already found
- **Fixed** tracks only view track highlight not matching width when column mode is on
- **Fixed** crash when right clicking empty album art
- **Fixed** playlist panel context menu not taking mouse focus
- **Fixed** 'fix mojibake' not immediately updating playlist
- **Fixed** radio metadata not showing if the previous track had lyrics
- **Fixed** show playing jumping to wrong track when playlist has duplicates
- **[Linux] Fixed** application preventing monitor sleep

### v2.6.2

- **Added** tool tips to view menu and mode buttons
- **Added** option to show lyrics in side panel (enabled by default)
- **Added** function to split lyric sentences into new lines
- **Added** animation to playlist and gallery to show when scrolling at top
- **Added** side spacing to 'playlist only' view
- **Improved** image download function to no longer block the UI (Linux)
- **Unified** image right click functions to a single menu
- Transcode can now be canceled with Ctrl+C shortcut
- Transcode now sends system notification when transcode has finished (Linux)
- ***Removed*** support for fonts other than Arial (Windows)
- **Fixed** lyrics only pasting to playing track
- **Fixed** lyrics not updating after pasting
- **Fixed** bug where sometimes switching playlist would change the current view

### v2.6.1

- **Fixed** tracks advancing too early (critical)
- ***Set*** database to save to disk after imports

### v2.6.0

- **Added** time cursor to seek bar on wheel click
- **Added** sorting function for album duration
- **Added** new view switcher box
- **Moved** 'copy lyrics' function to lyrics menu
- **Moved** 'toggle breaks' function to tab menu
- **Changed** track info box's lyrics label to a button that shows lyrics in lyrics view
- **Changed** behavior of search box to close on return
- **Changed** folder menu to include the transcode folder function
- **Changed** gallery highlight to animate on 'show playing'
- ***Removed*** detection of mp4 files
- ***Removed*** optional speedup module
- ***Removed*** 'Return to standard' view function
- **Fixed** scrollbar scrolling past bottom panel
- **Fixed** track box attribute hit boxes being slightly off
- **Fixed** show playing in Art+Tracks view having incorrect alignment on last album
- **Fixed** drag mode being activated on track menu click in Art+Track view
- **Fixed** art+tracks view crashing if the play queue was empty
- **[Linux] Fixed** some errors that were reported on console
- **[Linux] Fixed** crash on start on Openbox
- **[Linux] Fixed** gstreamer mode not advancing tracks

### v2.5.2

- **Added** track menu button to show album in gallery
- **Added** 3 new level meter colour modes (set new default to orange)
- **Added** window outline in borderless mode
- **Added** option to disable deleting for zip extract function
- **Added** text field menu for copy and paste, removed buttons from url entry box
- **Tweaked** 'view' button hitbox to be smaller
- **Fixed** text field pasting at cursor position
- **Fixed** bug with transcode selecting all folders with same name
- **Fixed** rare bug with multiple tracks showing as selected on click
- **Fixed** menu activation hitbox overlapping scroll bar in Art + Tracks view
- **Fixed** error messages appearing behind url box
- **Fixed** gallery view input visual feedback delay when selecting
- **Fixed** template settings in config file not having effect
- **[Windows] Fixed** buttons in settings having overhanging text
- **[Linux] Added** 2x UI display setting for HiDPI displays (testing)
- **[Linux] Added** symbolic icon for improved desktop integration
- **[Linux] Fixed** rare display corruption when showing level meter
- **[Linux] Fixed** media keys not working with new version of Gnome (3.26)
- **[Linux] Improved** integration with budgie desktop
- **[Linux] Improved** volume bar sliding performance under some configurations


### v2.5.1

- **Moved** 'art + tracks' view scroll bar to right side of window
- **Fixed** visualiser showing occasional corruption (linux)
- **Fixed** IME input not working
- **Fixed** url encoding with search on Sonemic function
- **Fixed** bad font rending in about box under some themes
- **Fixed** crash when using 'go to playing' on first played track
- **Tweaked** some fonts and colours
- ***Removed*** reset window shortcut


### v2.5.0

- **Added** button for saving URL's in open stream box
- **Added** icons to various menu elements
- **Added** playlist repeat option
- **Added** function to move folders to different library locations
- **Added** menu link to search images on google
- **Added** functionality for dropping links onto album canvas to download album art (linux)
- **Added** keyboard navigation to gallery view (via tab key)
- **Added** Shift-A search box shortcut to search for playing artist name
- **Added** text editing cursor to text fields
- **Added** search track on Genius menu option
- **Added** links to web server pages in settings
- **Improved** transition gap timing consistency
- **Improved** message box appearance and expanded various error messages
- **Improved** track menu settings to no longer require restart to change
- **Changed** folder delete function to no longer require shift key held down
- **Split** selection context menu into separate selection and folder menus
- **Tweaked** various UI elements
- **Tweaked** window draggable area during broadcast
- **Fixed** replay gain not consistently applying
- **Fixed** playback stall if stop and play clicked in quick succession
- **Fixed** crashes when using clean database function under certain circumstances
- **Fixed** reload metadata failing when used for a selection
- **Fixed** menu elements activating after click but before menu close
- **Fixed** stream metadata parsing
- **Fixed** newlines being allowed in text boxes



### v2.4.1

- **Added** 'file modified' sorting option
- **Added** cursor indicator to show when tracks are being dragged
- **Added** animated indicator to show number of tracks dropped onto a tab
- **Added** progress indicator for clean database function
- **Added** option to show lyrics in radio page
- **Fixed** thumbnail generator for MPRIS failing in some cases (linux)
- **Fixed** playing track not stopping if end track in playlist was missing
- **Fixed** visual glitch when moving playlist tabs
- **Fixed** show license button not working (linux)
- **Fixed** break title having bad rendering when selected while on coloured background
- **Fixed** backend crash when attempting to play a missing track first
- **Fixed** clean database function causing double memory usage
- **Fixed** clicks to rename tracks box clicking through
- **Fixed** TTA files not playing (linux)
- **Tweaked** selections to deselect when track clicked on
- **Tweaked** single track drag to allow moving via shift after drag has begun
- **Tweaked** double click timing to be tighter
- **Tweaked** auto theme text legibility for some cases
- **Tweaked** cross-fade to not apply to auto-stop function

### v2.4.0

- **Added** MPRIS interface support (Linux)
- **Added** ReplayGain support for tracks with supporting track/album metadata
- **Added** append playlist by drag tab and hold shift functionality
- **Added** indicator when broadcasting to show number of listeners
- **Added** html audio player to radio page
- **Fixed** window video corruption on start (Linux)
- **Fixed** stream recording causing crash on track change (Linux)
- **Fixed** comment text not being properly truncated (Linux)
- **Fixed** search term not found indication not deactivating correctly
- **Fixed** search box text having bad rendering
- **Fixed** crossfade being applied to end of last track in playlist and causing slight cutoff
- **Fixed** UI not updating when end of playlist is reached
- **Tweaked** vertical positioning of text with large characters (Linux)
- **Changed** drag over indicator to bar type
- **Simplified** media key setting in config file
- ***Removed*** system clipboard file copy function
- ***Removed*** MP3 support in broadcasting
- ***Removed*** icecast support. Broadcasting now uses internal server

### v2.3.6

- **Added** seek bars and auto updating to web interface
- Lost some web interface features
- ***Removed*** sample re-encode function
- **Fixed** minor bug with track group selection
- **Fixed** gallery view not updating when deleting folder
- **Fixed** rare crash with track info (Linux)
- **Fixed** tab menu not registering when clicked over drag area (Linux)

### v2.3.5

- **Added** image metadata via shift key
- **Added** monthly backuping of play count database
- **Added** indicator for tab dragging
- **Added** label for unloaded album art in gallery when titles set to off
- **Tweaked** font configuration
- **Tweaked** some labels
- **Tweaked** track move indicator
- **Fixed** sorting another playlist by filepath overwriting current
- **Fixed** first title cut off in art + tracks view
- **Fixed** codec ratio bar not correctly updating for new imports
- **Fixed** lucky random filter causing crash
- ***Removed*** transparency on image metadata box
- ***Removed*** themes Citrus and Smoke
- ***Removed*** reset play count option
- ***Removed*** fix mojibake manual function
- ***Removed*** folder browser and importer
- ***Removed*** global title break setting
- ***Removed*** reset layout button from settings
- ***Removed*** bottom bar album art
- ***Removed*** title in top panel setting
- ***Removed*** 'Has Comment' filter option


### v2.3.1

- **Added** delete folder function
- **Changed** play history playlist order. Extended history to 250
- **Fixed** rename folder function causing tracks to move in playlist
- **Fixed** show album art in bottom panel not correctly updating on toggle
- **Fixed** mouse button 4 gallery shortcut not working
- **Fixed** visualiser not activating from menu when off
- ***Removed*** toggle random and repeat entries from playback menu


### v2.3.0

- **Added** function to fetch lyrics from LyricWiki
- **Added** function to paste and clear lyrics
- **Added** track love function with last.fm submission
- **Added** bar chart of codec ratios to stats tab
- **Added** right click menu for changing visualiser
- **Added** option to automatically connect to last.fm
- **Added** folder rename function
- **Added** folder compacter function to folder rename box
- **Added** auto-resuming for functions that interrupt playback
- **Added** text cursor positioning, selection, copy, paste and cut for rename input boxes
- **Expanded** selection menu items
- **Redesigned** number change settings widget
- **Moved** and updated folder clean function to folder rename box
- **Moved** 'remove embedded image from mp3' function to picture context menu
- **Moved** scrobble mark setting from config file to UI settings
- ***Set*** duration field in track info box as copyable
- ***Set*** imported tracks to be sorted by default
- **Changed** labels in view menu, removed 'Full Art' shortcut
- **Changed** 'go to playing' function to always find any available track
- **Changed** layout of album title in 'art + tracks' view
- **Fixed** scroll on panels in showcase view also scrolling lyrics
- **Fixed** playback buttons not changing colour between themes
- **Fixed** playtime inflation when modifying metadata
- **Fixed** play count duping on tracks with same filename but different artist
- **Fixed** bug where cached last.fm hash would not update when entering new password
- **Fixed** dim mode not applying to playlist
- **Fixed** rename tracks not showing result message
- **Fixed** stats genre list not splitting multiple genres
- **Fixed** tracks not being ordered correctly in certain cases with inconsistent tagging
- **Fixed** mouse not releasing outside of window
- ***Removed*** themes 'ice' and 'orange'
- **[Linux] Fixed** gallery view and visualiser showing corrupted graphics with some video drivers
- **[Linux] Fixed** erratic rendering when visualiser is on with some video drivers

### v2.1.5

- **Added** stars playtime representation
- **Added** mini spectrogram visualiser
- **Added** native clipboard integration
- **Added** stream recording function (re-encoded as ogg)
- **Added** play history to playlist function
- **Added** setting to hide text in gallery view
- **Added** cut/copy/paste keyboard shortcuts for tracks
- **Added** menu shortcut for search
- **Added** option to show album art in bottom panel
- [Broadcasting] Song can now be seeked by clicking on progress display in top panel
- **Fixed** missing playback support for ALAC codec M4A files under Linux
- **Fixed** delayed UI update on media key press
- **Fixed** play time line positioning
- **Fixed** single instancing when web server is disabled
- **Fixed** quick drag to playlist not working from folder title
- **Fixed** menu shortcut hint colour blending
- **Fixed** left shift key not applying to some shortcuts
- **Fixed** window title on Gnome showing as Python
- **Fixed** text slightly overlapping playtime line
- **Fixed** radio metadata being truncated
- **Fixed** transcoding files to ogg producing corrupted output in some cases
- **Fixed** mp3 encoding not working
- **Added** auto detect Gnome desktop environment for media keys
- **Added** label in transcode settings showing when ffmpeg is missing
- **Reduced** idle cpu usage
- **Improved** selecting and dragging operations
- **Improved** text truncating in column mode
- **Improved** text cursor animation
- **Simplified** copy/paste functions
- **Moved** 'Playlist Stats' function to tab menu
- **Bound** 'Random Track' to semicolon key
- **Bound** End key to 'Next Track'
- **Bound** Home key to restart track / back
- **Bound** show end/start of playlist to Shift + Home/End keys
- ***Set*** defaults: web interface as disabled, RYM search as disabled
- ***Removed*** 'shift' track sub menu

### v2.1.0

- **Added** auto extract zip archive option
- **Added** native text rendering on windows (windows only)
- **Added** cairo as text renderer on linux (experimental, linux only)
- **Added** auto theme option to settings
- **Added** hide column bar option to menu
- **Fixed** title bar text updating
- **Fixed** poor album art image display quality
- **Fixed** double digit setting not applying in some cases
- **Fixed** top bar entering compact mode when title is displayed in bottom bar
- **Fixed** quick drag sometimes being triggered after UI lag
- **Fixed** playlist row size settings not applying to combo view
- **Improved** sidebar drag area to show drag cursor
- **Improved** auto theme mode
- **Improved** playlist selection box, bound to tilde key
- **Tweaked** column grip area
- **Changed** font configuration setting
- **Changed** default font on windows to Meiryo, fallback to Arial
- **Changed** default font on linux to Noto Sans
- ***Removed*** cycle list format option

### v2.0.0

- **Added** customisable playlist column layout with sorting
- **Added** customisation of playlist row size
- **Added** visual subgroups in menus
- **Added** re-import function
- **Added** output device selection to system settings tab
- **Added** menu shortcut for toggling playlist breaks
- **Added** search artist on Wikipeida track menu entry
- **Added** auto fix mojibake function
- **Bound** F9 key to open encode output
- **Bound** r-shift + slash to revert
- **Tweaked** scrobble marker appearance
- **Improved** error feedback for broadcasting
- **Fixed** edit tags externally sometimes including other folders
- **Fixed** volume not being affected by windows volume mixer
- **Fixed** messages not disappearing while settings box was open
- **Fixed** dragging tracks sometimes not applying
- ***Removed*** 'most skipped' and 'empty playlist' playlist filters

### v1.9.2

- **Added** new lyrics view
- **Added** support for WavPack (.wv) files
- **Added** tag reading support for APEv2 tags (APE, TTA and WavPack files)
- **Added** 'has lyrics' filter option
- **Added** GStreamer fallback on linux with basic functionality
- **Added** home holder user files location when detected as installed
- **Added** rescan tags option for playlists
- **Tweaked** playlist rename input box to apply input on click out, not just enter key.
- **Fixed** not being able to delete or arrange playlist while importing
- **Fixed** tracks importing to playlist that already have cue sheets (folders only, again)
- **Fixed** wav tracks duration not being detected on import
- **Fixed** delete key not working on single track
- **Fixed** stats open (this time for sure)
- **Fixed** art+tracks view tracks for up to 100 tracks per album
- **Fixed** page up/down keys not working for art+tracks view
- **Fixed** comment field only being read from MP3 files
- **Fixed** lyrics field not being read from MP3 files

### v1.9.0

- **Added** 'most played albums' sorting option
- **Added** functionality for quick dragging tracks onto top panel to send to new playlist
- **Added** disc number tag reading for OPUS, OGG, MP3 and FLAC. Updated sorting function to recognise this.
- **Added** disc total and track total display to track info box.
- **Added** 'paste' and 'clear' buttons to URL input box
- **Added** web track sample link generating function (experimental feature)
- **Added** colourise from album art function (experimental feature, press F3 to activate)
- **Added** bitrate estimation display for FLAC and OPUS in track info box
- **Added** button to copy lyrics to clipboard in track info box. Updated scanner to detect lyrics for FLAC, OPUS and OGG
- **Added** shortcut to open config file from settings box
- **Added** FLAC as folder transcoding option
- **Improved** inbound radio streaming error feedback
- **Improved** transcoding error feedback on linux
- **Tweaked** gallery to no longer jump when track advances automatically
- **Tweaked** scroll bar appearance
- **Tweaked** folder title to select on right click
- **Tweaked** 'copy artist- album' function to prioritise using artist-album field for artist
- **Tweaked** track dragging to no longer require shift to be held to move multiple tracks
- **Tweaked** Go To Playing function to make any matching track in the open playlist the playing track and playlist
- **Fixed** crash when using radio random
- **Fixed** seek bar, track title and playing time display for radio streaming
- **Fixed** player not switching to stopped state when stream ends
- **Fixed** a performance leak in playlist config tab
- **Fixed** fallback text not truncating to correct length
- **Fixed** edge scroll bar hiding on maximised window
- **Fixed** jittery gallery scrolling when running visualiser
- **Fixed** playlist digit setting sometimes not being enforced
- **Fixed** broadcast not sending title and artist to Icecast server on first track
- **Fixed** remote control url to allow trailing forward slash, enabled favicon
- **Fixed** playlist being at end after clear and import
- **Fixed** playlist stats missing file on Linux
- **Fixed** drag dropping import onto panel and tab on Linux
- **Fixed** comment not highlighting https URL links
- Separate oggenc download no longer required for broadcasting

### v1.8.0

- **Added** option to increase playlist font size
- **Added** function to copy fields to clipboard from track info box
- **Added** font options to config file
- **Added** configuration for external tag editor integration
- **Added** function to remove embedded album art from MP3 files
- **Added** minimise and exit icons for borderless mode
- **Added** function to extract and save embedded images from track tags
- **Added** support for reading OPUS metadata
- **Added** album artist field support for OPUS, FLAC, MP3, OGG and CUE
- **Added** cue sheet indicator to track info box
- **Fixed** click on window focus not registering
- **Fixed** some track highlights not being full playlist width
- **Fixed** window flash on focus maximised
- **Tweaked** menu behavior to switch on mouse over

### v1.7.3

- **Added** drop on top panel to import to new playlist functionality
- **Added** 'search term not found' indicator
- **Changed** side panel metadata font and tab font
- **Enabled** fast encoding for OGG codec
- **Increased** number of worker threads
- **Moved** IME edit display location
- **Fixed** reset cache crash
- **Fixed** scroll bar hitbox overlapping play button
- **Fixed** hitbox overlap on tab buttons
- **Fixed** queue highlight area
- **Fixed** transcoding from cue files sometimes failing
- ***Removed*** CUE type encoding option

### v1.7.1

- **Added** setting for disk caching gallery art
- **Added** setting for gallery view scroll speed
- **Added** setting for scrolling gallery view by row
- **Added** scroll controls to gallery view
- **Improved** encoding performance for opus output
- **Fixed** error importing certain tracks
- **Fixed** max CPU usage with level meter
- **Fixed** encode not working with cue files to single tracks
- **Fixed** opus output files not containing track number metadata
- **Fixed** transcoding on Linux

### v1.7.0

- **Added** shortcut hints to various menu entries
- **Added** ctrl+z shortcut to undo last playlist delete
- **Added** ogg support for folder encoding output
- **Added** row formatting cycle button to settings
- **Added** play times to playlist readout
- **Added** comment display to track info box
- **Added** duplicate playlist function
- **Added** new last.fm setup tab in settings
- **Added** support for light background themes
- **Improved** window closing speed
- **Fixed** window showing white during startup
- **Fixed** level visualiser not decaying after stop
- **Tweaked** styling of various interface elements
- **Tweaked** playlist formatting and appearance
- **Tweaked** config file formatting
- **Redesigned** application icon
- ***Set*** UI frame as option in theme files
- ***Removed*** custom playlist row formatting
- ***Removed*** hide scroll bar as option
- ***Removed*** highlight artist as option
- ***Removed*** pause lock option
- ***Removed*** pyperclip as dependency

### v1.6.3

- **Improved** playlist importing speed
- **Added** ctrl+w shortcut to delete playlist
- **Added** ctrl+r shortcut to rename playlist
- **Added** shift+enter to show search results in new playlist
- **Added** shuffle folders function
- **Added** folder path filtering to search function
- **Added** transcoding support for MP3 (requires lame encoder)
- **Added** transcoding support for single tracks
- **Moved** transcoding setting to UI
- **Tweaked** gallery view layout
- **Tweaked** default configuration
- **Fixed** scrolling bug in album combo view

### v1.6.0

- **Added** new formats for play time indicator
- **Added** new menu button to bottom panel
- **Added** gallery only view
- **Added** importing and exporting support for XSPF format playlists
- **Added** clean database function
- **Added** option to show title in bottom panel for some view modes
- **Moved** view modes into new view menu
- **Moved** playback options to new menu
- **Tweaked** bottom panel visual elements
- **Tweaked** gallery album goto function
- **Changed** F1 shortcut to toggle folder breaking for current playlist
- **Fixed** layout reset window size being slightly too small
- **Fixed** rate at which seek bar updates
- **Fixed** drag on tab not working in albums plus tracks view
- **Fixed** images reloading when switching layouts
- **Fixed** image cache for gallery being unlimited
- **Fixed** single track imports sometimes adding to wrong playlist
- **Fixed** issue with pasting tracks
- Other small tweaks and fixes to user interface

### v1.5.2

- **Added** playback menu
- **Added** tracking of track skips
- **Added** new sorting options: by artist, album, reversed, skips and file path
- **Added** new copy/paste menu for selections
- **Added** ctrl-a shortcut to select all tracks in playlist
- **Added** 5 new themes
- **Added** album art + tracks combined view mode
- ***Removed*** genre sorting option
- ***Removed*** last.fm panel indicator
- ***Removed*** shift click to delete playlist function
- ***Removed*** two existing themes
- ***Replaced*** disable scroll bar function with hide scroll bar function
- **Improved** multiple new playlist naming
- **Improved** playlist tab repositioning
- **Improved** gallery view fonts
- **Fixed** slow track number sorting speed
- **Fixed** incorrect seeking after cue based track transition
- **Fixed** moving tracks onto folder title
- **Fixed** seek bar click sometimes wrongly registering
- **Fixed** cursor movement response being delayed
- **Fixed** unicode end characters becoming corrupted
- **Fixed** visualiser clock speed
- **Fixed** tracks with inconsistent file extension case not importing
- **Fixed** un-maximized on start bug
- **Fixed** playlist scroll boundary in gallery view
- Misc UI tweaks
- Misc bug fixes

### v1.4.3

- **Moved** some settings from config file to UI
- **Fixed** bug causing crash when accessing web interface
- Minor performance optimizations
- Various UI tweaks
- Various other bug fixes


### v1.4.2

- **Added** playlist sorting by year
- **Added** option for changing gallery art size
- **Added** embedded image loading from FLAC files
- **Added** a basic playlist selection box
- **Added** an option for showing year in folder title
- **Changed** icon
- **Changed** main font
- **Tweaked** font sizes for playlist
- **Improved** CPU usage with visualiser, slightly
- **Fixed** a bug causing slower scrolling
- **Fixed** gallery view not jumping to first few rows
- **Fixed** Go to Playing function not working on gallery in some situations
- **Fixed** buttons using incorrect theme colour
- ***Disabled*** gallery info bar

### v1.4.0

- **Added** playlist navigation to web interface
- **Added** WMA playback support under Windows
- **Added** reloading artwork function to database menu
- **Added** ability to import to playlist directly by dropping on tab
- **Added** specifying of encoding output directory from config
- **Added** 'open with' support and opening file via cli
- **Added** single instance functionality
- **Added** a basic info panel to gallery view
- **Added** file size information to track info
- **Added** GIF image support
- **Added** OPUS encoding support for broadcasting
- **Added** rudimentary Mac OS X support
- **Tweaked** some menu/GUI elements
- **Tweaked** create playlist behavior to not request input
- **Tweaked** gallery view artist labels to show 'various' label if applicable
- **Fixed** web interface colours
- **Fixed** broadcasting on linux
- **Fixed** console windows appearing when transcoding
- **Fixed** settings taking long to open with large music libraries
- **Fixed** incorrectly displaying song lengths greater than an hour long
- **Fixed** slow re-importing (again)
- **Fixed** cue source file incorrectly importing (again)
- **Fixed** crash when clearing playlist in gallery view
- **Fixed** some keybinds being active during text input
- **Fixed** gallery view sometimes showing incorrect picture
- **Improved** stability when importing
- **Updated** icon design
- **Bound** shift+up/down keys to volume control
- ***Removed*** disk caching of images for web interface
- ***Removed*** dependence on running from working directory
- **[Note] Changed** database format, reset required if upgrading (delete state.p file)

### v1.3.0

- **Added** hints for empty playlist
- **Added** search on RYM function
- **Tweaked** scrollbar behaviour
- Minor interface tweaks and bug fixes

### v1.2.5

- Minor interface tweaks and string changes
- **Fixed** crash when opening a stream
- **Fixed** crash when deleting a playlist while in gallery view
- **Bound** - and + keys to seek functions
- **Added** radio random function (M3 click forward or comma key)

### v1.2.1

- Cleaner starting when some program files missing
- Galley view now jumps to album when selecting 'back'


### v1.2.0

- **Improved** rendering performance
- **Improved** window drag handling
- **Added** top menu buttons display
- **Fixed** random mode not working with cue tracks
- **Tweaked** interface

### v1.1.6

- Minor interface fixes
- **Improved** re-import performance
- **Added** import progress counter

### v1.1.5

- Minor interface fixes
- **Tweaked** context menu categories
- **Tweaked** selection behavior
- **Tweaked** icon colour
- **Fixed** visual error with shift moving tracks
- **Fixed** a rare crash when clicking album in album view
- **Fixed** a crash when playing a track detected as zero length (windows)
- **Changed** top list to sort by playtime rather than playcount
- **Added** config to disable transcode menu entry
- **Added** time playing colour to themes
- **Added** keybinds for repeat and show playing (. and ' respectively)

### v1.1.0

- **Fixed** high cpu usage when dragging
- **Fixed** black window in some cases
- **Fixed** title bar text not updating in some cases
- **Tweaked** button hitboxes
- **Tweaked** some menu entries
- **Tweaked** track selection behavior
- **Added** thick row option
- **Added** side panel background as themeable

### v1.0.9

- **Fixed** opus+cue encoding on linux
- **Fixed** stream progress bar overlapping level meter
- **Fixed** toggle gallery view not remembering side panel width
- **Moved** sort tracks to playlist menu
- **Tweaked** gallery layout
- **Tweaked** certain themes colors
- **Improved** gallery view performance
- **Added** top genre/album/artist readout
- **Added** playlist filtering by genre to playlist menu
- **Added** spectrum analyzer (may incur high cpu usage)
- **Added** option for player following playlist
- **Added** option for switching to double digit track numbers
- **Added** option for toggling scroll bar
- **Added** option for playlist folder separation
- **Added** jump playlist ability to 'show playing' function
- **Added** taskbar progress on windows
- **Added** Page Up / Page Down function
- **Added** seek bar background and various line colours to themes
- **Added** custom playlist line format option


### v1.0.1

- **Fixed** lastfm scrobbling not submitting album info
- **Fixed** inconsistent track number format
- **Added** opus encoding bitrate to config file
- **Added** transpose playlist option
- **Improved** cue sheet handling when transcoding (still has some limitations)

### v1.0.0

- **Reduced** CPU usage with level meter
- **Improved** level meter animation
- **Fixed** level meter not persisting after restart
- **Fixed** a crash in album view
- **Added** batch encode folder to opus + cue
- **Added** scrobble marker

### v0.9.9

- **Moved** some UI elements to new options frame
- **Added** delete key functionality
- **Added** built in folder picker for importing
- **Added** About panel
- **Added** periodic saving of playtimes to disk
- **Tweaked** scroll bar appearance
- **Tweaked** playlist tab layout to avoid overlapping
- **Tweaked** GUI CPU usage and performance

### v0.9.8

- **Fixed** a bug with broadcasting not playing tracks defined by CUE sheets
- **Fixed** a bug with player taking too long to play again after stopping
- **Fixed** a bug with incorrect selection on playlist change
- **Fixed** opening external images on linux
- **Fixed** some misc crashes
- **Added** support for samplerates other than 44100 to broadcasting
- **Added** experimental web interface (remote control and broadcast album art, enable in config)
- **Added** experimental borderless mode
- **Added** right click seek bar to pause/play
- **Added** support for dragging tracks to other playlists
- **Added** support for renaming playlists
- **Added** fade time setting to config file
- **Moved** renaming tracks function to new modify submenu
- **Moved** csv export to new database submenu
- **Tweaked** playlist generator functions
- **Tweaked** volume and playlist tabs scrollable area
- **Tweaked** album view behavior with track switching
- Minor GUI tweaks
- **Improved** latin character support

### v0.9.5

- **Improved** gallery view switching and layout
- **Improved** image compatibility
- ***Removed*** and altered various menu options
- **Added** menu box for changing settings
- **Added** hidden command for exporting database to csv
- **Added** hidden dialog for renaming files
- **Added** 'copy' for multiple track selection

### v0.9.0

- **Redesigned** context menu
- **Fixed** album art resize scaling
- **Fixed** colour flickering on single track playlists
- **Expanded** colourable items
- **Expanded** image subfolder search names
- **Updated** track number colour to dark if track missing
- **Tweaked** art counter box
- Player now saves window size on reset
- **Added** Partial multi select and drag to reorder (hold shift)
- **Moved** built in theme to file
- **Added** seek during pause as config option
- **Added** reset missing flag function to menu
- **Added** right click to toggle mute volume bar
- **Added** mouse scroll to seek bar
- **Added** right click play button to show now playing

### v0.8.5

- Bottom bar colour can now be defined in theme file
- **Added** mediakey toggle to config

### v0.8.0

- **Added** album view (experimental)
- **Enhanced** scrolling performance
- **Reworked** menu system
- **Added** copy/paste like functionality for tracks and folders in playlists
- Minor UI and usability alterations

### v0.7.5

- **Fixed** bug with some cue sheets not loading
- Moderate performance optimizations

### v0.7

- **Fixed** window not rendering on certain video drivers (Linux)
- **Changed** media key detection to use Dbus for better Gnome integration (Linux)
- **Added** a track information box option to context menu
- Minor UI tweaks, removed some redundant options
- **Moved** some options to new playlist context menu
- **Improved** IME support
- **Improved** search reliability
- **Added** text cursor animation
- Small performance tweaks

### v0.6.5 (First public release)

- **Fixed** bug with not being able to rearrange playlists
- **Improved** theme loading
