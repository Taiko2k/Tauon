Basic usage guide. Updated for v2.1.5
===========

Player is based around disposable playlists, and makes the assumption that folders are albums. Searching, sorting and filtering is applied to individual playlists and not derived from a central database. Before any sorting applied by the user, tracks are displayed in the order they are imported, typically representing the underlying file structure.

For best experience you will need an organized and structured music library, with each album in its own folder. 

I recommend the following file structure especially for large music libraries: LIBRARY/GENRE/ARTIST/ALBUM/TRACKS. Where GENRE can be any sort of broad categorization you feel is best. 

### Importing Music

- Drag and drop files and folders from your file manager.

Tip: After importing, right click playlist tab and select 'Sort Track Numbers' to ensure tracks are ordered correctly.

Tip: Try importing all your music to a single playlist to get started

Quirk: If a music file has an associated .cue file, they needed to be imported together within a folder and not individually otherwise the .cue file may not be detected.

### Updating Library

- Clear playlist and re-import. It should be faster the 2nd time.

### Track Navigation

- 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist.
- With random mode on, 'Back' plays songs from playback history.
- Right click the 'Play' button to jump playlist (Show playing) to the playing track. 

Trick: When using 'Show Playing', if an identical track appears in the currently open playlist it will be jumped to instead.

### Quick Search

1) Press the backslash key or Ctrl+F to open search box.
2) Type word fragments separated by spaces. Use UP and DOWN keys to navigate any matching results in current playlist. Press enter key to play selected track.
3) Press Shift+Enter to create a new playlist from matching results


### New Playlist from folder path fragment:

1) Press the backslash key '\' or Ctrl+F to open search entry.
2) Begin text with a forward slash '/', then type part of a folder path to search for. (Capitalization will be ignored but used for playlist title)
3) Press Enter to create the new playlist. Will fail if no matching results found.

Tip: End the search text with another forward slash to search just for folders with that name. For example, entering '/Pop' may bring up results for J-Pop and K-Pop, however '/Pop/' will only return folders with that exact name.

### Panel Buttons

![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)


### Playlist Scrolling

 - The playlist scroll bar is to the left of the playlist, hidden until moused over
 - Click above or below the scroll bar to scroll quickly in that direction
 - Right click anywhere in the scroll field to jump immediately to that location

### Moving Playlists and Tracks

 - Playlists can be rearranged by dragging them
 - A single track can be quickly copied to the end of another playlist by dragging it onto a playlist tab.
 - Single tracks can be moved within a playlist by holding shift and dragging
 - To move a block of tracks; highlight (use shift to highlight multiple), then click and drag

### Rename Folder Function (experimental)

***Rename*** - Renames the folder of the track to given template format. The default template can be changed in the config.txt file.  
***Compact*** - If the upper containing folder contains no other folders of files, this function will eleminate that folder.  

Warning: Although there are some checks in place it may still be possible to cause bad things to happen. Best not to use around files you cannot afford to lose.

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

Compatible with Shoutcast and Icecast streams. To open a stream:

1) Go to MENU -> OPEN STREAM...
2) Type in address to stream or click paste if link is in clipboard (you can manually copy these out of m3u files) (Must start with http:// or ftp://)
3) Click GO

To record a steam, once a stream has been opened, re enter the open stream box and click REC. If this fails, try make sure the encoder directory is valid and has write permissions. Recording are encoded to OGG at about 100kbs and are automatically split when on metadata change.

### Outbound Streaming

1) Install, configure (optional) and start Icecast. See config.txt for optional further setup.
2) From player click MENU from top bar and select 'Start Broadcast' from menu. You should now see an entry in the Icecast web interface (default http://localhost:8000). From track context menu select 'Broadcast This' to play a track immediately.

The point of this is that you can listen to music locally while streaming from and editing another playlist (Like a DJ might).  

Note: Broadcast will repeat from beginning of playlist once end is reached  
Warning: Modifying the number of tracks in playlist that appear before the broadcast marker will impact the broadcast position

Alternatively, by pressing F6 to enter 'sync' mode (experimental), the broadcast will receive commands from standard playback controls. The effect of this also allows for the listening and control of a stream remotely via the web interface.  

Note: The 'sync' function is experimental and unreliable. Pausing or stopping the player while in this mode will cause the stream to fail and/or generate other unexpected behavior  

Tip: Higher bitrates may help reduce latency. lower bitrates will conserve bandwidth at cost of audio quality.

### Transcoding albums

Intended to be an easy way to reduce file sizes for copying tracks to devices with limited storage. Results will be of degraded quality and should not be used for archival (Unless FLAC is chosen as codec, though note that generated picture will still be a lossy thumbnail).

Requires FFMPEG in encoder subdirectory. Additionally 'lame.exe' for mp3 encoding. (On Linux, programs only need be installed)

Will encode based on settings in MENU -> SETTINGS...-> TRANSCODE tab

Output folders will be placed in same encoder subdirectory

Tip: 64Kbps Opus, 96kbps OGG, or 128kbs MP3 should be good enough for most portable music listening.  

Tip: Not many players on Android support Opus. I suggest Rocket Player or AIMP for Android


### Japanese Mojibake

In case of mojibake (where displayed characters from Japanese track metadata is garbled), the ideal solution is to re-apply tags in a decent tag editor, preferably using a sane encoding (i.e UTF-8)

As a temporary solution Tauon Music Box offers a fix mojibake function under TRACK MENU -> META... -> FIX MOJIBAKE

 - 'Fix mojibake auto' should automatically correct the displayed characters in around 90% of cases.  
 - 'Fix mojibake manual' to apply manually based on presented suggestions, can be used for extreme cases where there are multiple encodings for different fields within the same tag

Note: These functions will apply changes to all tracks in folder/album   

Note: Changes made by these functions only apply to internal database and are not written back to tags on disk
Tip: To undo changes and revert to original, use TRACK MENU -> META... -> RELOAD METADATA

### Tag Editing

There is currently no built in support for tag editing.

An external tag editor can be used. See config.txt for linking to an external editor from the track menu (Track menu -> Meta... -> Edit tags with xxxx). Is configured for MusicBrainz Picard by default.

Tip: While editing tracks externally, make sure not to change the track file names. You should use the rename tracks function built into Tauon Music Box under TRACK MENU -> META... -> RENAME TRACKS   

Bug: Linking to Picard fails with Unicode paths on windows


### Importing/Exporting Playlists

Playlists can be backed up, shared and imported using the XSPF playlist file format.

To import; drag and drop XSPF playlist file onto program window. (Any playlist files inside folders will be ignored)

To export; right click playlist tab and select Export.

Note: Its best to import any corresponding audio files before importing playlists.  
Note: Importing large playlists can take a long time, cleaning database beforehand (MENU->Database->Find And Remove Dead Tracks) may help speed this up.  
Bug: Some tracks with strange characters in metadata may cause process to fail.  
Tip: Exporting then importing tracks also serves the function of reviving dead tracks when files have been moved.


User data files
================

**state.p** - Contains playlists, track database information and some settings. Delete to reset player.  
**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by filename and track title, can be transferred between platforms.

### Upgrading / Moving

When proram is installed to program files via installer, files are kept in a dedicated location. ~/.tauonmb-user on Linux and C:\Users\<user>\Music\TauonMusicBox on Windows.

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


You made it to the end, congrats! I hope that all made sense and you enjoy using Tauon Music Box. But whatever player you choose to use, have fun listening!
