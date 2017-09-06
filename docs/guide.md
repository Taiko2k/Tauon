Basic usage guide. Updated for v2.5.1
===========

Player is based around disposable playlists, and makes the assumption that folders are albums. Searching, sorting and filtering is applied to individual playlists and not from the whole database.

For best experience you will need an organized and structured music library, ideally with each album in its own folder.

I recommend the following file structure: LIBRARY/GENRE/ARTIST/ALBUM/TRACKS. Where GENRE could be any sort of broad categorization you feel is best in order to keep like albums together.

### Importing Music

 - Drag and drop files and folders from your file manager.

Tip: Try importing all your music to a single playlist to get started

### Updating Library

 - Clear playlist and re-import. It should be faster the second time.

### Track Navigation

 - 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist.
 - With random mode on, 'Back' plays songs from playback history.
 - Right click the 'Play' button to jump to / show the playing track. This function will search playlists for a matching track with the following priority:
   1) The currently viewed playlist
   2) The playlist that the playing track is playing from
   3) All other playlists starting from left to right

### Playlist Scrolling

 - The playlist scroll bar is to the left of the playlist, hidden until moused over.
 - Click above or below the scroll bar to scroll quickly in that direction.
 - Right click anywhere in the scroll field to jump immediately to that location.

### Gallery View

 - To enter gallery view, click VIEW-> TRACKS + GALLERY or press mouse button 4 (if you have a 5 button mouse).
 - Clicking an album plays it.
 - Right clicking an album shows its position in the playlist.
 - To select an album using the keyboard, press tab to toggle keyboard control mode.

### Quick Search

1) Use LEFT and RIGHT keys to switch to the playlist containing the track you wish to search for.
2) Press the backslash key or Ctrl+F to open the search box.
3) Type word fragments separated by spaces. For example, to locate a track named 'Coldplay - Clocks' you could try enter the search text 'col clo'.

 - Use UP and DOWN keys to navigate any matching results in the playlist. Press enter key to play selected track.
 - Press Shift+Enter to create a new playlist of all matching results
 - Press Shift+A to search currently playing artist name

### New Playlist from folder path fragment:

This function filters tracks to a new playlist that only contains tracks that have a given folder name fragment in their file path.

1) Press the backslash key '\' or Ctrl+F to open search entry.
2) Begin text with a forward slash '/', then type part of a folder path to search for. (Capitalization will be ignored but used for playlist title)
3) Press Enter to create the new playlist.

Tip: End the search text with another forward slash to search just for folders with that name. For example, entering '/Pop' may bring up results for J-Pop and K-Pop, however '/Pop/' will only return folders with that exact name.

### Panel Buttons

![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)


### Moving Playlist Tabs

 - Playlist tabs can be rearranged by dragging them onto one another.
 - If shift is held when dragging, the playlist will be merged and appended.

### Moving Tracks

 - A single track can be quickly copied to the end of another playlist by dragging it onto a playlist tab.
 - Single tracks can be repositioned within a playlist by holding shift while dragging
 - To move a block selection, click and drag.
 - To make a selection, click the first track, then hold shift and click the last track. Alternatively just click a block title to select that block.

### Modify Folder Function

Access by right clicking track; TRACK MENU -> META... -> MODIFY FOLDER...  OR  right click folder title; SELECTION MENU -> MODIFY FOLDER...

***Rename*** - Renames the folder of the track to given template format. The template that this defaults to can be changed in the config.txt file.  

***Delete*** - Deletes the folder and all containing files and folders. Use with caution!

***Compact*** - If the upper containing folder contains no other folders or files, this function will eliminate that folder by moving the lower folder up 2 levels and deleting the old containing folder.

***Clean*** - Deletes the following OS related items in the folder: 'desktop.ini', 'Thumbs.db', Windows Media Player generated thumbnail images, Mac OS related '.DS_Store' and 'MACOSX' files/folders.

Warning: Although there are some checks in place it may still be possible to cause bad things to happen. Best not to use this function around files or folders you cannot afford to lose.

### Physical Folder Copy and Move / Library Transfer

WARNING: Function is experimental. There may be bugs and and there will be cases not accounted for. Use with caution and not around data you cannot afford to lose.

The purpose of this function is to facilitate and ease of moving folders between library locations.

Performing this is a two step process:

  1) Right click a folder title of a folder you want to copy/move and select "COPY FOLDER FROM LIBRARY" from the menu.
  2) Find an imported track that exists form a location you wish to copy the folder to. Right click it, and click COPY TO THIS LIBRARY or hold down shift and click MOVE TO THIS LIBRARY to have the original folder deleted after rather than just copying.

This function will attempt to find the upper most directory level that is used for artists. It will then create a directory for the artist and move the folder there.

The resulting path structure will then be ***/folder_with_music(hopefully)/artist/original_folder_name***.

WARNING: The entire source directory will be copied/moved, so make sure it only contains folders and files you want to transfer.


### Modifying Album Art

 - To quickly add album art to a folder, images from a web browser can be dragged onto the side panel canvas. (HTTP only) (Linux only, not working on Windows)
 - If you add or change album art, use MENU -> DATABASE -> RESET IMAGE CACHE to update this without needing to restart.

### Quirks

 - Program data is only saved once the program is exited cleanly and not in the case of a force close or crash (Shutting system down while the player is open is a force close). Play times are periodically saved however.

### Extra Shortcuts

***Search***: Backslash \ or Ctrl + F  
***Toggle folder break for current playlist***: F1   
***Cycle Theme***: F2   
***Toggle Auto Theme***: F3   
***Show encoding output folder*** F9   
***Change Playlist***: Left and Right arrow keys  
***Seek***: + and -   
***Play next/previous track***: Shift + Left and Right arrow keys OR global mediakeys OR home/end keys  
***Volume Up/Down***: Shift + Up and Down arrow keys    
***Select TOP/END***: Home, End   
***Toggle gallery keyboard mode***: Tab   
***Delete current playlist***: Ctrl + W   
***Undo playlist delete***: Ctrl + Z   

### Inbound Streaming

Compatible with HTTP streams (Shoutcast, Icecast etc). To open a stream:

1) Go to MENU -> OPEN STREAM...
2) Type in address to stream or click paste if link is in clipboard (you can manually copy these URLs out of m3u files if available) (Must start with http:// or ftp://)
3) Click GO

To record a steam, once a stream has been opened, re enter the open stream box and click REC. Recordings are encoded using OGG codec at about 100kbs and are automatically split on metadata change. Press F9 to show output folder.

### Outbound Streaming / Broadcasting

From player top bar click MENU and select 'Start Broadcast'. You should then see a blue highlight that shows the currently streaming track. You can right click a track and select 'Broadcast This' to stream a track immediately.

The stream can be reached at http://localhost:8000. You can connect by opening the link in a media player or web browser (tends to be a little bit unreliable with some browsers, try refreshing the page if playback stalls).

Note: The codec used is OGG. Bit-rate can be set in 'config.txt'. Higher bit-rates may help reduce latency. Lower bit-rates will conserve bandwidth at cost of audio quality.

Note: Modifying the number of tracks in playlist that appear before the broadcast marker will impact the broadcast position.


### Transcoding albums

Intended to be an easy way to reduce file sizes for copying tracks to devices with limited storage. Results will be of degraded quality (lossy codec) and should not be used for archival.

1) Ensure FFMPEG is avaliable.
 - For Windows, download ffmpeg from https://ffmpeg.org/ and place 'ffmpeg.exe' in encoder directory. To find this folder press F9.
 - For Linux, install ffmpeg using your distro's package manager.
 - If you need MP3 output, repeat above steps for LAME (lame.exe). For Windows you may find lame.exe on the internet. For Linux consult your package manager.

2) Optionally configure settings in MENU -> SETTINGS...-> TRANSCODE
 - 64Kbps OPUS provides good sound quality with small file size, but not many players are compatible with it. (For andorid I might suggest Rocket Player or AIMP)
 - 96kbps OGG, or 128kbs MP3 provide comparable quality and are more widely compatible.
 - The FLAC option should only be used to convert other lossless audio files. Note that the generated picture will still be a lossy thumbnail.

3) Right click a track and select, TRACK MENU -> TRANSCODE FOLDER to transcode the the tracks in the folder to which the track resides. Wait for it to finish.
 - If the yellow text in the top panel does not change for an extended amount of time, the transcode may have stalled. In this case you will need to restart the application as there is currently no handling on errors.

4) See result folders in the encoder directory. To open this folder press F9.


### Japanese Mojibake

In case of mojibake (where displayed characters from Japanese language metadata is garbled), the ideal solution is to re-apply tags in a tag editor, preferably using a sane encoding (i.e UTF-8)

As a temporary solution a fix mojibake function is available under TRACK MENU -> META... -> FIX MOJIBAKE

Note: This function will apply changes to all tracks in the folder/album   

Note: Changes made by these functions only apply to internal database and are not written back to the tags on disk

Tip: To undo changes and revert to original, use TRACK MENU -> META... -> RELOAD METADATA

### Tag Editing

There is currently no built in support for tag editing.

An external tag editor can be used. This is configured for MusicBrainz Picard by default but can be changed in config.txt

To activate use: TRACK MENU -> META... -> Edit tags with XXXX

Note: While editing tracks externally, make sure not to change the file names. If you wish to change the file names after you have imported them, use the rename tracks function under TRACK MENU -> META... -> RENAME TRACKS.

Note: Picard has a bug that causes it to fail with Unicode paths on windows.


### Importing/Exporting Playlists

Playlists can be backed up, shared and imported using the XSPF playlist file format.

To import; drag and drop XSPF playlist file onto program window. (Any playlist files inside folders will be ignored)

To export; right click playlist tab and select Export.

Note: Its best to import any corresponding audio files before importing playlists.  

Important: It may be necessary to clean database beforehand. (MENU->Database->Find And Remove Dead Tracks)

Bug: Some tracks with strange characters in metadata may cause process to fail.  

Tip: Exporting then importing tracks also serves the function of reviving dead tracks when files have been moved.


### ReplayGain

Basic support for ReplayGain exists. When enabled, volume will be adjusted according to ReplayGain metadata in track tags.

Only applies to local playback. If no ReplayGain metadata exists, no adjustments will be made.

User data files
================

When program is installed to program files via installer, files are kept in a dedicated location. C:\Users\<user>\Music\TauonMusicBox on Windows and ~/.tauonmb-user on Linux.

**state.p** - Contains playlists, track database information and settings. Delete to reset player.

**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by a matching filename, artist and track title. Can be transferred between platforms.

### Upgrading / Moving

For moving installations or upgrading portable installations:

- Copy 'star.p' file from old directory to keep track play counts.
- Copy 'state.p' file to keep rest of player data such as playlists.

Tip: If you are moving platforms, resetting player or moved your music location and have custom playlists you wish to keep:

 1) Firstly, export the playlists using the export playlist function (TAB MENU -> MISC... -> EXPORT XSPF)
 2) Use the clean database function (MENU -> DATABASE... -> FIND AND REMOVE DEAD TRACKS). This may take a small while.
 3) Re-import your music from the new location to any playlist.
 4) Finally, drag and drop the old XSPF playlist back in to re-import.


Web components
=================================

Enable in MENU -> SETTINGS... -> SYSTEM tab

Warning: Enabling the 'allow external connections' option may pose a security risk.

Warning: Make sure there are no private files in the folders of your music, especially pictures that may inadvertently be sent as an album art thumbnail.

***localhost:7590/remote*** - Remote player control with album art and track info

***localhost:7590/radio*** - Album art and track info for broadcasting

-----------------------------

You made it to the end. Congratulations! I hope that all made sense and you enjoy using Tauon Music Box. Have fun listening!
