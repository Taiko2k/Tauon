# Tauon Music Box

Tauon Music Box is a desktop music player for playback of local audio files.
Designed to be simple and streamlined while puting the user in control of their music library.

### Features :sparkles:


<img src="https://cloud.githubusercontent.com/assets/17271572/25081441/88abb624-239e-11e7-9ba8-d51bc015b168.jpg" align="right" height="200px" hspace="0px" vspace="0px">


<img src="docs/scrn1.jpg" align="right" height="179px" hspace="0px" vspace="20px">

  - Plays most common codecs including MP3 and FLAC.
  - Simple drag and drop track importing.
  - Fast and responsive UI.
  - Playlist oriented search and sorting.
  - Keep track of play counts, even when file location changes.
  - Automatic CUE sheet detection.
  - Transcode folders while keeping album art. Useful for copying to DAP's.
  - Last.fm scrobbling.
  - Lyrics display with support for fetching lyrics from LyricWiki.
  - Open Icecast/Shoutcast streams from URL. Record streams with automatic tagging and splitting.
  - Outbound radio broadcasting. Streams playlist in background without affecting local playback.

### What makes this project different? :lemon: :zap:

I started this project because I was unsatisfied with existing music players, especially ones avaliable for linux. You may find this program different in the following design choices:

 - Focus on playlists and drag and drop functions.
 - Always assumes folders are albums, organised by underlying folder structure.
 - Keeps track of play counts by file name rather than the full path.
 - Provides a streamlined interface out of the box, designed for dark themes.
 - Doesn't modify the users library in the background.
 - Seamless transition between playlist and gallery layouts.
 
#### :broken_heart: However this program may not be for you if:

 - Your music library is sourced from online streaming services.
 - You have an unorganised library and perfer your player to organise it for you.
 - You perfer a customisable user interface, or one that uses the system theme.

### Getting Started :dizzy:

For __Windows__, download latest installer from [releases](https://github.com/Taiko2k/tauonmb/releases) section.

For __Arch Linux__, install from the AUR:  

    $ yaourt -S tauon-music-box


For further documentation see [guide](docs/guide.md).

Feel free to submit any issues or suggestions.
