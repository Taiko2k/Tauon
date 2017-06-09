Basic usage guide. Updated for v2.4.0
===========

Player is based around disposable playlists, and makes the assumption that folders are albums. Searching, sorting and filtering is applied to individual playlists and not derived from a central database. 

For best experience you will need an organized and structured music library, ideally with each album in its own folder. 

I recommend the following file structure: LIBRARY/GENRE/ARTIST/ALBUM/TRACKS. Where GENRE can be any sort of broad categorization you feel is best. 

### Importing Music

 - Drag and drop files and folders from your file manager.

Tip: Try importing all your music to a single playlist to get started

### Updating Library

 - Clear playlist and re-import. It should be faster the 2nd time.

### Track Navigation

 - 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist.
 - With random mode on, 'Back' plays songs from playback history.
 - Right click the 'Play' button to jump to / show the playing track. This function will search playlists for a matching track with the following priority:
   1) The currently viewed playlist
   2) The playlist that the playing track is playing from
   3) All other playlists starting from left to right


### Quick Search

1) Use LEFT and RIGHT keys to switch to the playlist containing the track you want to search for.
2) Press the backslash key or Ctrl+F to open the search box.
3) Type word fragments separated by spaces. 

 - Use UP and DOWN keys to navigate any matching results. Press enter key to play selected track. 
 - Press Shift+Enter to create a new playlist of all matching results

### Playlist Scrolling

 - The playlist scroll bar is to the left of the playlist, hidden until moused over
 - Click above or below the scroll bar to scroll quickly in that direction
 - Right click anywhere in the scroll field to jump immediately to that location

### New Playlist from folder path fragment:

This function filters tracks to a new playlist that only contains tracks that have a given folder name fragment in their file path.

1) Press the backslash key '\' or Ctrl+F to open search entry.
2) Begin text with a forward slash '/', then type part of a folder path to search for. (Capitalization will be ignored but used for playlist title)
3) Press Enter to create the new playlist.

Tip: End the search text with another forward slash to search just for folders with that name. For example, entering '/Pop' may bring up results for J-Pop and K-Pop, however '/Pop/' will only return folders with that exact name.

### Panel Buttons

![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)


### Moving Playlists and Tracks

 - Playlist tabs can be rearranged by dragging them onto one another.
 - A single track can be quickly copied to the end of another playlist by dragging it onto a playlist tab.
 - Single tracks can be moved within a playlist by holding shift, clicking on them and dragging while holding shift
 - To move a block of tracks; highlight (use shift to highlight multiple), then click and drag.
 
 Note: Not all of these dragging operations currently have an animation or indicator, but it should work if performed correctly.

### Modify Folder Function

Access by right clicking track; TRACK MENU -> META... -> MODIFY FOLDER...  OR  right click folder title; SELECTION MENU -> MODIFY FOLDER...

***Rename*** - Renames the folder of the track to given template format. The template that this defaults to can be changed in the config.txt file.  

***Delete*** - Deletes the folder and all containing files and folders (hold shift to enable)

***Compact*** - If the upper containing folder contains no other folders or files, this function will eliminate that folder by moving the lower folder up 2 levels and deleting the old containing folder.

***Clean*** - Deletes the following OS related items in the folder: 'desktop.ini', 'Thumbs.db', Windows Media Player generated thumbnail images, Mac OS related '.DS_Store' and '__MACOSX' files/folders.

Warning: Although there are some checks in place it may still be possible to cause bad things to happen. Best not to use this function around files or folders you cannot afford to lose.

### Quirks

 - If you add or change album art, use MENU -> DATABASE -> RESET IMAGE CACHE to update this without needing to restart
 - Quirk: There is no playlist repeat function, player will stop once it reaches the end of a playlist (Broadcasting will repeat from the top however)
 - Quirk: Playlists and settings are only saved once the program is exited cleanly and not in the case of a force close or crash (Shutting system down while the player is open is a force close) Playtimes are periodically saved however.

### Extra Shortcuts

***Search***: Backslash \ or Ctrl + F  
***Toggle folder break for current playlist***: F1   
***Cycle Theme***: F2   
***Toggle Auto Theme***: F3   
***Change Playlist***: Left and Right arrow keys  
***View Playlist List***: Tilde ~
***Seek***: + and -   
***Play next/previous track***: Shift + Left and Right arrow keys OR global mediakeys OR home/end keys  
***Volume Up/Down***: Shift + Up and Down arrow keys    
***Toggle broadcast sync mode***: F6   
***Select TOP/END***: Home, End   
***Undo playlist delete***: Ctrl + Z

### Inbound Streaming

Compatible with HTTP streams (Shoutcast, Icecast etc). To open a stream:

1) Go to MENU -> OPEN STREAM...
2) Type in address to stream or click paste if link is in clipboard (you can manually copy these links out of m3u files if available) (Must start with http:// or ftp://)
3) Click GO

To record a steam, once a stream has been opened, re enter the open stream box and click REC. If this fails, try make sure the encoder directory is valid and has write permissions. Recordings are encoded to OGG at about 100kbs and are automatically split when on metadata change.

### Outbound Streaming / Broadcasting

From player click MENU from top bar and select 'Start Broadcast' from menu. You should now be able to connect a player to the target port. 

From track context menu select 'Broadcast This' to play a track immediately.

Note: The codec used is OGG. Bitrate can be set in 'config.txt'. Higher bitrates may help reduce latency. Lower bitrates will conserve bandwidth at cost of audio quality.

Warning: Modifying the number of tracks in playlist that appear before the broadcast marker will impact the broadcast position


### Transcoding albums

Intended to be an easy way to reduce file sizes for copying tracks to devices with limited storage. Results will be of degraded quality and should not be used for archival.

1) Ensure FFMPEG is avaliable. 
 - For windows, Download ffmpeg from https://ffmpeg.org/ and place 'ffmpeg.exe' in encoder directory. To find this folder, go to MENU -> SETTINGS... -> TRANSCODE -> OPEN OUTPUT FOLDER
 - For linux, install ffmpeg using your distro's package manager.
 - If you need MP3 output, repeat above steps for LAME (lame.exe). For windows you may find lame.exe on the internet. For linux consult your package manager.

2) Optionally configure settings in MENU -> SETTINGS...-> TRANSCODE
 - 64Kbps Opus provides good sound quality with small file size, but not may players are compatible with it. As of 2017 I suggest Rocket Player or AIMP for Android.
 96kbps OGG, or 128kbs MP3 should be good enough for most portable music listening. 
 - 96kbps OGG, or 128kbs MP3 provide comparable quality and are more widely compatible.
 - The FLAC option should only be used to convert other lossless audio files. Note that the generated picture will still be a lossy thumbnail.
 
3) Right click a track and select, TRACK MENU -> TRANSCODE FOLDER to transcode the track in the folder to which the track resides. Wait for it to finish.
 - If the yellow text in the top panel does not change for an extended duration, the transcode may have stalled. 

4) See result folders in the encoder directroy. Again, to find this folder, go to MENU -> SETTINGS... -> TRANSCODE -> OPEN OUTPUT FOLDER 



### Japanese Mojibake

In case of mojibake (where displayed characters from Japanese language metadata is garbled), the ideal solution is to re-apply tags in a decent tag editor, preferably using a sane encoding (i.e UTF-8)

As a temporary solution Tauon Music Box offers a fix mojibake function under TRACK MENU -> META... -> FIX MOJIBAKE

Note: These functions will apply changes to all tracks in the folder/album   

Note: Changes made by these functions only apply to internal database and are not written back to tags on disk

Tip: To undo changes and revert to original, use TRACK MENU -> META... -> RELOAD METADATA

### Tag Editing

There is currently no built in support for tag editing.

An external tag editor can be used. See config.txt for linking to an external editor from the track menu (TRACK MENU -> META... -> Edit tags with xxxx). Is configured for MusicBrainz Picard by default.

Note: While editing tracks externally, make sure not to change the track file names. You should use the rename tracks function built into Tauon Music Box under TRACK MENU -> META... -> RENAME TRACKS   

Bug: Linking to Picard fails with Unicode paths on windows


### Importing/Exporting Playlists

Playlists can be backed up, shared and imported using the XSPF playlist file format.

To import; drag and drop XSPF playlist file onto program window. (Any playlist files inside folders will be ignored)

To export; right click playlist tab and select Export.

Note: Its best to import any corresponding audio files before importing playlists.  
 
Note: Importing large playlists can take a long time, cleaning database beforehand (MENU->Database->Find And Remove Dead Tracks) may help speed this up.  
  
Bug: Some tracks with strange characters in metadata may cause process to fail.  

Tip: Exporting then importing tracks also serves the function of reviving dead tracks when files have been moved.


### ReplayGain

Basic support for ReplayGain exists. When enabled, volume will be adjusted according to ReplayGain metadata in track tags.

Only applies to local playback. If no ReplayGain metadata exists, no adjustments will be made.

User data files
================

**state.p** - Contains playlists, track database information and some settings. Delete to reset player. 

**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by a matching filename, artist and track title. Can be transferred between platforms.

### Upgrading / Moving

When program is installed to program files via installer, files are kept in a dedicated location. ~/.tauonmb-user on Linux and C:\Users\<user>\Music\TauonMusicBox on Windows.

For moving installations or upgrading portable installations:

- Copy 'star.p' file from old directory to keep track play counts.
- Copy 'state.p' file to keep rest of player data such as playlists.

Tip: If you are moving platforms, resetting player or moved your music location and have custom playlists you wish to keep:

 1) Firstly, export the playlists using the export playlist function (TAB MENU -> ... -> EXPORT XSPF)
 2) Use the clean database function (MENU -> DATABASE... -> FIND AND REMOVE DEAD TRACKS). This may take a small while.
 3) Re-import your music from the new location to any playlist
 4) Finally, drag and drop the old XSPF playlist back in to re-import.



Web components
=================================

Enable in MENU -> SETTINGS... -> SYSTEM tab
Warning: Enabling the 'allow external connections' option may pose a security risk

Warning: Make sure there are no private files in the folders of your music, especially pictures that may inadvertently be sent as an album art thumbnail

***localhost:7590/remote*** - Remote player control with album art and track info

***localhost:7590/radio*** - Album art and track info for broadcasting

Individual tracks can be made accessible from the UI (TRACK MENU-> META... -> Generate Websample)
  
Note: Requires FFMPEG and web server enabled before menu entry will appear
  
Note: Must be clicked for each track and will only be accessible for duration of session as files and links are cleared on restart.

-----------------------------

You made it to the end! congrats. I hope that all made sense and you enjoy using Tauon Music Box. Have fun listening!
