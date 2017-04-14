# Tauon Music Box

Tauon Music Box is a desktop music player for playback of local audio files.
Designed for ease of use and simplicity with minimal configuration required.
Uses BASS audio library. Target supported platforms are Windows 10 and Arch Linux.

### Features :sparkles:

  - Playback support for most common codecs including MP3, FLAC, OGG, OPUS, and APE
  - Simple drag and drop track importing
  - Playlist oriented search and sorting
  - Keep track of play counts, even when file location changes
  - Large album art display
  - Automatic CUE sheet detection
  - Transcode folders while keeping album art. Useful for copying to DAP's with limited storage / codec support.
  - Last.fm scrobbling with love track function
  - Lyrics display with support for fetching lyrics from LyricWiki
  - Save and load playlists in the XSPF file format
  - Open Icecast/Shoutcast streams from URL. Record streams with automatic tagging and splitting
  - Outbound radio streaming to Icecast. Streams playlist in background without affecting local playback.
  
### Screenshot :star2:


<img src="https://cloud.githubusercontent.com/assets/17271572/21793801/736fa45a-d759-11e6-8e97-be58e2e7bcac.jpg" alt="Standard View" width=910px />

<img src="https://cloud.githubusercontent.com/assets/17271572/17890552/e0c9985e-698a-11e6-8a3c-1b49570e6619.jpg" alt="Standard View" width=690px />


### Getting Started :dizzy:

For __Windows__, download latest installer from [releases](https://github.com/Taiko2k/tauonmb/releases) section.
 
For __Arch Linux__, download pkgbuild from releases section. Use an AUR manager to install or install dependencies manually (check list of dependencies inside pkgbuild), navigate terminal to download location and run:  
  
    $ makepkg
    $ sudo pacman -U tauon-music-box-2.3.5-1-x86_64.pkg.tar


For further documentation see [guide](docs/guide.md). For detailed feature status see [features](docs/features.md).




