# Tauon Music Box

<img src="https://user-images.githubusercontent.com/17271572/41101848-6ccf4ed0-6ab9-11e8-8ce8-7f62060b39c9.png" align="left" height="50px" hspace="0px" vspace="20px">

A desktop music player for playback of local audio files.
Designed to be simple and streamlined while putting the user in control of their music collection. Uses the proprietary BASS audio library for playback.

### Screenshot

<img src="https://user-images.githubusercontent.com/17271572/48309413-8912a100-e5de-11e8-9323-8a3713469419.jpg" hspace="0px" vspace="60px">


## Features :sparkles:

  - Import tracks and create playlist's by simple **drag and drop**. Ready to go out the box.
  - Batch [transcode folders](https://github.com/Taiko2k/tauonmb/wiki/Transcoding-for-PMP-DAP-Smartphone) to a single output folder for easy and compact copying to a portable device.
  - Last.fm **scrobbling** with track love support.
  - Support for **gapless playback** and **ReplayGain**.
  - **Lyrics** display with support for fetching lyrics from LyricWiki.
  - See your album art how it was meant to with a large album art display.
  - Outbound [radio broadcasting](https://github.com/Taiko2k/tauonmb/wiki/Outbound-Broadcasting). Streams a playlist in the background without affecting local playback.
  - Edit tags with MusicBrainz **Picard** (when also installed).
  - Keep track of play counts. Visualise these as stars so you always know tracks were your favorite.
  - Shortcuts for searching artists on Rate Your Music and tracks on Genius.
  - Auto extract archives on import.
  
  <img src="https://user-images.githubusercontent.com/17271572/43353750-94d68a0e-9293-11e8-9a80-bd15146f06eb.jpg" hspace="0px" vspace="0px" width="320"> | <img src="https://user-images.githubusercontent.com/17271572/40102029-768ed298-593d-11e8-9ec0-2d39873fd8a4.png" hspace="0px" vspace="0px" width="450"> | <img src="https://user-images.githubusercontent.com/17271572/43353964-d9725eec-9296-11e8-9a77-3de33040c9de.jpg" hspace="0px" vspace="0px" width="350">
  --- | --- | ---
  **Rich search. :mag: Find tracks, albums and artists at the speed of sound.** [<sup>?</sup>](https://github.com/Taiko2k/tauonmb/wiki/Find-and-Search) | **See your loved tracks, and your friends loves too!** :sparkling_heart: | **Download monitor. :doughnut: Import your downloaded music in one click!**
  <img src="https://user-images.githubusercontent.com/17271572/43353986-8719114e-9297-11e8-8028-adb9e5ad1247.jpg" hspace="0px" vspace="0px" width="320"> | <img src="https://user-images.githubusercontent.com/17271572/43353819-f9f2e580-9294-11e8-9e00-1921de2e6442.jpg" hspace="0px" vspace="0px" width="320"> | <img src="https://user-images.githubusercontent.com/17271572/43354043-e5e718d2-9298-11e8-8a6d-8539f5a8d56c.jpg" hspace="0px" vspace="0px" width="320">
  **Your music in your control, with built in folder renaming and deleting.** :pencil2: | **Navigate between your organised collections at lighting speed.** [<sup>?</sup>](https://github.com/Taiko2k/tauonmb/wiki/Meta-Folders) :rocket: | **Jump in and out of the integrated album gallery.**


### File type compatibility :milky_way:

#### Audio

- [x] FLAC 
- [x] APE, TTA, WV
- [x] MP3, M4A
- [x] OGG, OPUS
- [ ] WMA, CD, MOD, AIFF

#### Other

- [x] XSPF
- [x] CUE (automatic detection)
- [ ] M3U, PLS

## Download and Install :dizzy:

For __Arch Linux__, install is avaliable from the [AUR](https://aur.archlinux.org/packages/tauon-music-box/).

For __Other Linux distributions__, a standalone **Flatpak** package is available.
 
 1. If you have not already, make sure you have correctly installed and configured Flatpak for your distro. See https://flatpak.org/setup/. Specificaly you will need to have the flathub repo added:
 
     `flatpak remote-add --if-not-exists flathub https://flathub.org/repo/flathub.flatpakrepo`
 
 2. After downloading *tauon.flatpak* from lastest [release](https://github.com/Taiko2k/tauonmb/releases).    
     
     - Install using: `sudo flatpak install tauon.flatpak`
         
     - To uninstall run: `sudo flatpak uninstall com.github.taiko2k.tauonmb`
 
     >**Note:** This standalone Flatpak package won't auto update. You'll need to check back here for updates.
     
     >**Note:** Only host installed Picard/tag-editors are supported.
___

For further documentation see the [wiki](https://github.com/Taiko2k/tauonmb/wiki/Basic-Use-Guide).

Feel free to submit any issues or suggestions. I'd love to hear your feedback.

[![Maintenance](https://img.shields.io/maintenance/yes/2018.svg?style=flat-square)](https://github.com/Taiko2k/tauonmb/releases) [![GitHub release](https://img.shields.io/github/release/taiko2k/tauonmb.svg?style=flat-square&colorB=ff69b4)](https://github.com/Taiko2k/tauonmb/releases)
