
<img src="https://user-images.githubusercontent.com/17271572/51743494-a2b58600-2101-11e9-9e90-9c7c6c3394eb.png" align="left" height="157px" hspace="0px" vspace="20px">

## Tauon Music Box

A desktop music player for playback of local audio files.
Designed to be simple and streamlined while putting the user in control of their music collection. Uses BASS audio library for playback (proprietary).

<img src="https://user-images.githubusercontent.com/17271572/51741796-c6c29880-20fc-11e9-9507-c1681c0f03b1.jpg" hspace="0px" vspace="160px">

## Features :sparkles:

  - Import tracks and create playlists by simple **drag and drop**.
  - Support for **gapless playback**.
  - Batch [transcode folders](https://github.com/Taiko2k/tauonmb/wiki/Transcoding-for-PMP-DAP-Smartphone) of music for easy copying to a PMP.
  - Last.fm **scrobbling** with track love support :heart:. See which of your tracks your friends loved too! :purple_heart:
  - **Lyrics** display with support for fetching lyrics from LyricWiki.
  - Edit tags with MusicBrainz **Picard** (when also installed).
  - Keep track of play counts. Visualise these so you always know which tracks were your favorite.
  - Shortcuts for searching artists on Rate Your Music and tracks on Genius.
  - Desktop integration with MPRIS2
  - **Extract archives** and import your music downloads in **one click**! :zap:


#### File type compatibility :milky_way:

- [x] FLAC, APE, TTA, WV, MP3, M4A(aac, alac), OGG, OPUS
- [x] XSPF, CUE (automatic detection)

#### Not supported

- [ ] M3U, PLS, WMA, CD, MOD, AIFF

## Download and Install :dizzy:

For __Arch Linux__ based distros, install is avaliable from the [AUR](https://aur.archlinux.org/packages/tauon-music-box/).

For __Other Linux distributions__, a standalone **Flatpak** package is available.

 - After downloading *tauon.flatpak* from lastest [release](https://github.com/Taiko2k/tauonmb/releases):    

     - Install using: `sudo flatpak install tauon.flatpak`

     - To uninstall run: `sudo flatpak uninstall com.github.taiko2k.tauonmb`

     >**Note:** This standalone Flatpak package won't auto update. You'll need to check back here for updates.

     >**Troubleshooting:** If you're having issues installing, try make sure you have installed and configured Flatpak for your distro as described on https://flatpak.org/setup/. Make sure you have the flathub repo added using `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo` as this is needed to download the runtimes.

___

For further documentation see the [wiki](https://github.com/Taiko2k/tauonmb/wiki/Basic-Use-Guide).

Feel free to submit any issues or suggestions. I'd love to hear your feedback.

[![Maintenance](https://img.shields.io/maintenance/yes/2019.svg?style=for-the-badge)](https://github.com/Taiko2k/tauonmb/releases) [![GitHub release](https://img.shields.io/github/release/taiko2k/tauonmb.svg?style=for-the-badge&colorB=ff69b4)](https://github.com/Taiko2k/tauonmb/releases) ![test](https://img.shields.io/badge/platform-linux--64-lightgrey.svg?style=for-the-badge)
