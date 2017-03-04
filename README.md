# Tauon Music Box

Tauon Music Box is a desktop music player for playback of local audio files.
Designed for ease of use and simplicity with minimal configuration required.
Uses BASS audio library. Target supported platforms are Windows 10 and Arch Linux.

### Features :sparkles:

  - Playback support for most common codecs including MP3, FLAC, OGG, OPUS, and APE
  - Dark themed, minimal user interface
  - Includes large album art and gallery views
  - Simple drag and drop track importing
  - Automatic CUE sheet detection and integration
  - Batch transcode folders of tracks to save space when copying to portable devices
  - Quick search
  - Playlist sorting
  - Last.fm scrobbling
  - Outbound streaming via Icecast

### Screenshot :star2:


<img src="https://cloud.githubusercontent.com/assets/17271572/21793801/736fa45a-d759-11e6-8e97-be58e2e7bcac.jpg" alt="Standard View" width=910px />

<img src="https://cloud.githubusercontent.com/assets/17271572/17890552/e0c9985e-698a-11e6-8a3c-1b49570e6619.jpg" alt="Standard View" width=690px />

Note: Screenshots taken under Windows 10 using Metro X theme 

### Getting Started :dizzy:

For __Windows__, download latest installer from [releases](https://github.com/Taiko2k/tauonmb/releases) section.
 
For __Arch Linux__, download pkgbuild from releases section and install.  
Warning: The currently required package python-cairo-git may cause other packages to break. (known conflict with lollypop)

Using Yaourt, navigate terminal to download location and run:  
Update: There appeares to be a bug using this method in the current release of yaourt, you may need to install dependencies manually, or update to the dev version of yaourt (yaourt-git). Note that the dependency python-cairo-git is avaliable in the AUR  

    $ yaourt -Pi


For further documentation see [guide](docs/guide.md). For detailed feature status see [features](docs/features.md).




