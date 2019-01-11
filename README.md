# Tauon Music Box

<img src="https://user-images.githubusercontent.com/17271572/41101848-6ccf4ed0-6ab9-11e8-8ce8-7f62060b39c9.png" align="left" height="50px" hspace="0px" vspace="20px">

A desktop music player for playback of local audio files.
Designed to be simple and streamlined while putting the user in control of their music collection. Uses the proprietary BASS audio library for playback.

### Screenshot

<img src="https://user-images.githubusercontent.com/17271572/48976940-492ade00-f0f5-11e8-9e93-b8dcb9cdbd8c.jpg" hspace="0px" vspace="60px">


## Features :sparkles:

  - Import tracks and create playlist's by simple **drag and drop**. Ready to go out the box.
  - Support for **gapless playback** and **ReplayGain**.
  - Batch [transcode folders](https://github.com/Taiko2k/tauonmb/wiki/Transcoding-for-PMP-DAP-Smartphone) to an output folder for easy and compact copying to a portable device.
  - Last.fm **scrobbling** with track love support.
  - **Lyrics** display with support for fetching lyrics from LyricWiki.
  - Edit tags with MusicBrainz **Picard** (when also installed).
  - Keep track of play counts. Visualise these so you always know which tracks were your favorite.
  - Shortcuts for searching artists on Rate Your Music and tracks on Genius.
  - Auto extract archives on import.
 

### File type compatibility :milky_way:

#### Audio

- [x] FLAC 
- [x] APE, TTA, WV
- [x] MP3, M4A(aac, alac)
- [x] OGG, OPUS

#### Other

- [x] XSPF
- [x] CUE (automatic detection)

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

> **Note:** These packages are for x86_64 only
___

For further documentation see the [wiki](https://github.com/Taiko2k/tauonmb/wiki/Basic-Use-Guide).

Feel free to submit any issues or suggestions. I'd love to hear your feedback.

[![Maintenance](https://img.shields.io/maintenance/yes/2019.svg?style=flat-square)](https://github.com/Taiko2k/tauonmb/releases) [![GitHub release](https://img.shields.io/github/release/taiko2k/tauonmb.svg?style=flat-square&colorB=ff69b4)](https://github.com/Taiko2k/tauonmb/releases)
