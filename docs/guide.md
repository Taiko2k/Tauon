Basic usage manual. Updated for v2.6.2
===========

Player is based around disposable playlists, and makes the assumption that folders are albums. Searching, sorting and filtering is applied to individual playlists and not from the whole database.

For best experience you will need an organized and structured music library, ideally with each album in its own folder.

If you have a large and varied music library I recommend keeping albums in respective folders based on genre in order to keep like albums together.

### Importing Music

 - Drag and drop files and folders from your file manager.

Tip: Try importing all your music to a single playlist to get started

### Updating Library

 - Clear playlist and re-import. It should be faster the second time.

### Track Navigation

 - 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist.
 - With random mode on, 'Back' plays songs from playback history.
 - Right click the 'Play' button to jump playlist to the playing track.

  This will search the currently open playlist for a matching track and make it the playing track if found.


### Panel Buttons

   ![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)


### Playlist Scrolling

 - The playlist scroll bar is to the left of the playlist, hidden until moused over.
 - Click above or below the scroll bar to scroll quickly in that direction.
 - Right click anywhere in the scroll field to jump immediately to that location.

### Gallery View

 - To enter gallery view, click VIEW->(Upper right icon) or press mouse button 4 (if you have a 5 button mouse).
 - Clicking an album plays it.
 - Right clicking an album shows its position in the playlist.
 - To select an album using the keyboard, press tab to toggle keyboard control mode.

### Quick Search

1. Use LEFT and RIGHT keys to switch to the playlist containing the track you wish to search for.
2. Press the backslash key or Ctrl+F to open the search box.
3. Type word fragments separated by spaces. For example, to locate a track named 'Coldplay - Clocks' you could try enter the search text 'col clo'.

 - Use UP and DOWN keys to navigate any matching results in the playlist. Press enter key to play the selected track.
 - Press Shift+Enter to create a new playlist of all matching results
 - Press Shift+A to search currently playing artist name

##### New Playlist from folder path fragment:

This function filters tracks to a new playlist that only contains tracks that have a given folder name fragment in their file path.

1. Press the backslash key '\' or Ctrl+F to open search entry.
2. Begin text with a forward slash '/', then type part of a folder path to filter for. (Capitalization will be ignored but used for playlist title)
3. Press Enter to create the new playlist.

__Tip__: End the search text with another forward slash to search just for folders with that name. For example, entering '/Pop' may bring up results for J-Pop and K-Pop, however '/Pop/' will only return folders with that exact name.


### Moving Playlist Tabs

 - Playlist tabs can be rearranged by dragging them onto one another.
 - If shift is held when dragging, the playlist will be merged and appended.

### Moving Tracks

 - A single track can be quickly copied to the end of another playlist by dragging it onto a playlist tab.
 - Single tracks can be repositioned within a playlist by holding shift while dragging
 - To move a block selection, click and drag.
 - To make a selection, click the first track, then hold shift and click the last track. Alternatively just click a block title to select that block.

### Modify Folder Function

Access by right clicking track; _TRACK MENU -> META... -> MODIFY FOLDER..._  OR  _right click folder title; SELECTION MENU -> MODIFY FOLDER..._

***Rename*** - Renames the folder of the track to given template format. The template that this defaults to can be changed in the config.txt file.  

***Delete*** - Deletes the folder and all containing files and folders. Use with caution!

***Compact*** - If the upper containing folder contains no other folders or files, this function will eliminate that folder by moving the lower folder up 2 levels and deleting the old containing folder.

***Clean*** - Deletes the following OS related items in the folder: 'desktop.ini', 'Thumbs.db', Windows Media Player generated thumbnail images, Mac OS related '.DS_Store' and 'MACOSX' files/folders.

Warning: Although there are some checks in place it may still be possible to cause bad things to happen. Best not to use this function around files or folders you cannot afford to lose.

### Modifying Album Art

 - To quickly add album art to a folder, images from a web browser can be dragged onto the side panel canvas. (HTTP only) (Linux only, not working on Windows)
 - If you add or change album art, use MENU -> DATABASE -> RESET IMAGE CACHE to update this without needing to restart.

### Quirks

 - Program data is only saved once the program is exited cleanly and not in the case of a force close or crash (Shutting system down while the player is open is a force close). Play times are periodically saved however.

### Extra Shortcuts


| Function                    | Key         |
| -------------               |:-------------:|
| ***Search***                | Backslash or Ctrl + F  |
|***Toggle playlist breaks*** | F1   
|***Cycle theme***            | F2   
|***Show encoding output folder*** | F9  
|***Cycle Playlists***        | Left and Right
|***Seek***                   | + and -  
|***Delete current playlist***| Ctrl + W  
|***Undo playlist delete***   | Ctrl + Z
|***Back and Advance***       | Shift + Left/Right
|***Back and Advance***       | Home and End
|***Play/Stop/Back/Advance*** | Media keys (global)
|***Toggle gallery keyboard mode***| Tab  
|***Toggle gallery view***    | Mouse button 4


### Inbound Streaming

Compatible with HTTP streams (Shoutcast, Icecast etc). To open a stream:

1. Go to _MENU -> OPEN STREAM..._
2. Type in address to stream or click paste if link is in clipboard (you can manually copy these URLs out of m3u files if available) (Must start with http:// or ftp://)
3. Click GO

To record a steam, once a stream has been opened, re enter the open stream box and click REC. Recordings are encoded using OGG codec at about 100kbs and are automatically split on metadata change. Press F9 to show output folder.

### Outbound Streaming / Broadcasting

From player top bar click MENU and select 'Start Broadcast'. You should then see a blue highlight that shows the currently streaming track. You can right click a track and select 'Broadcast This' to stream a track immediately.

The stream can be reached at http://localhost:8000. You can connect by opening the link in a media player or web browser (tends to be a little bit unreliable with some browsers, try refreshing the page if playback stalls).

__Note__: The codec used is OGG. Bit-rate can be set in 'config.txt'. Higher bit-rates may help reduce latency. Lower bit-rates will conserve bandwidth at cost of audio quality.

__Note__: Modifying the number of tracks in playlist that appear before the broadcast marker will impact the broadcast position.


### Transcoding albums

Intended to be an easy way to reduce file sizes for copying tracks to devices with limited storage. Results will be of degraded quality (lossy codec) and should not be used for archival.

1. Ensure FFMPEG is avaliable.
 - For Windows, download ffmpeg from https://ffmpeg.org/ and place 'ffmpeg.exe' in encoder directory. To find this folder press F9.
 - For Linux, install ffmpeg using your distro's package manager.
 - If you need MP3 output, repeat above steps for LAME (lame.exe). For Windows you may find lame.exe on the internet. For Linux consult your package manager.

2. Optionally configure settings in MENU -> SETTINGS...-> TRANSCODE
 - 64Kbps OPUS provides good sound quality with small file size, but not many players are compatible with it.
 - 96kbps OGG, or 128kbs MP3 provide comparable quality and are more widely compatible.
 - The FLAC option should only be used to convert other lossless audio files. Note that the generated picture will still be a lossy thumbnail.

3. Right click a track and select, TRACK MENU -> TRANSCODE FOLDER to transcode the the tracks in the folder to which the track resides. Wait for it to finish.
 - If the yellow text in the top panel does not change for an extended amount of time, the transcode may have stalled. In this case you will need to restart the application as there is currently no handling on errors.

4. See result folders in the encoder directory. To open this folder press F9.


### Japanese Mojibake

In case of mojibake (where displayed characters from Japanese language metadata is garbled), the ideal solution is to re-apply tags in a tag editor, preferably using a sane encoding (i.e UTF-8)

As a temporary solution a fix mojibake function is available under TRACK MENU -> META... -> FIX MOJIBAKE

This function will apply changes to all tracks in the folder/album   

__Note__: Changes made by these functions only apply to internal database and are not written back to the tags on disk

__Tip__: To undo these changes and revert to original tags, use TRACK MENU -> META... -> RELOAD METADATA

### Tag Editing

There is currently no built in support for tag editing.

An external tag editor can be used. This is configured for MusicBrainz Picard by default but can be changed in config.txt

To activate use: _TRACK MENU -> META... -> Edit tags with XXXX_

__Note__: While editing tracks externally, make sure not to change the file names. If you wish to change the file names after you have imported them, use the rename tracks function under TRACK MENU -> META... -> RENAME TRACKS.

__Bug__: Picard has a bug that causes it to fail with Unicode paths on windows.


### Importing/Exporting Playlists

Playlists can be backed up, shared and imported using the XSPF playlist file format.


- To export: Right click playlist tab and select Export.

- To import: Drag and drop XSPF playlist file onto program window. (Any playlist files inside folders will be ignored)

  __Important__: You will likely need to use the clean database function beforehand. (_MENU->Database->Find And Remove Dead Tracks_)

  __Note__: Its best to import any corresponding audio files before importing playlists.  


Bug: Some tracks with strange characters in metadata may cause process to fail.  

Tip: Exporting then importing tracks also serves the function of reviving dead tracks when files have been moved. (Provided the 'clean database' function is used before re-import.)


### ReplayGain

Basic support for ReplayGain exists. When enabled, volume will be adjusted according to ReplayGain metadata in track tags.

Only applies to local playback. If no ReplayGain metadata exists, no adjustments will be made.


### Physical Folder Copy and Move / Library Transfer [Experimental]

WARNING: There may be bugs and cases not accounted for. Use with caution and not around data you cannot afford to lose.

The purpose of this function is to facilitate and ease of moving folders between library locations.

Performing this is a two step process:

  1. Right click a folder title of a folder you want to copy or move and select "COPY FOLDER FROM LIBRARY" from the menu.
  2. Find an imported track that exists from a location you wish to copy the folder to. Right click it, and click COPY TO THIS LIBRARY or hold down shift and click MOVE TO THIS LIBRARY to have the original folder deleted after rather than just copying.

This function will attempt to find the upper most directory level that is used for artists. It will then create a directory for the artist and move the folder there.

The resulting path structure will then be ***/folder_with_music(hopefully)/artist/original_folder_name***.

WARNING: The entire source directory will be copied/moved, so make sure it only contains folders and files you want to transfer.


User data files
================

When program is installed to program files via installer, files are kept in a dedicated location. C:\Users\<user>\Music\TauonMusicBox on Windows and ~/.tauonmb-user on Linux.

**state.p** - Contains playlists, track database information and settings. Delete to reset player.

**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by a matching filename, artist and track title. Can be transferred between platforms.


Web components
=================================

**Note**: Currently requires active internet connection in order to fetch jquery.

Enable in MENU -> SETTINGS... -> SYSTEM tab

Warning: Enabling the 'allow external connections' option may pose a security risk.

Warning: Make sure there are no private files in the folders of your music, especially pictures that may inadvertently be sent as an album art thumbnail.

***localhost:7590/remote*** - Remote player control with album art and track info

***localhost:7590/radio*** - Album art and track info for broadcasting

-----------------------------

You made it to the end. Congratulations! I hope that all made sense and you enjoy using Tauon Music Box. Have fun listening!
