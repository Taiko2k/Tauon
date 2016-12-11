Basic usage guide. Updated for v1.8.6
===========

Player is playlist oriented and makes the assumption that folders are albums.  Sorting and filtering is applied by creating new playlists from existing playlists.

For best experience it is recommended to have an organized and structured music library. I recommended the following file structure especially for large music libraries: LIBRARY/GENRE/ARTIST/ALBUM/TRACKS

### Importing Music

- Drag and drop files and folders from your file manager.

- Importing can take a while for large music collections. After importing, right click playlist tab and select 'Sort Track Numbers' to ensure tracks are ordered correctly.

Tip: Try importing all your music to a single playlist to get started
Quirk: If a music file has an associated .cue file, they needed to be imported together within a folder and not individually otherwise the .cue file may not be detected.

### Updating Library

- Clear playlist and re-import. It should be faster the 2nd time.

### Track Navigation

- 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist.
- With random mode on, 'Back' plays songs from playback history.
- Right click the play button to jump playlist to the playing track. If an identical track appears in the open playlist it will be jumped to instead.

### Quick Search

- Press the backslash key or Ctrl+F to open search box.
- Type word fragments separated by spaces. Use UP and DOWN keys to navigate any matching results in current playlist. Press enter key to play selected track.
- Press Shift+Enter to create a new playlist from results


### Filtering By Folder

- Press the backslash key '\' or Ctrl+F to open search entry.
- Begin search text with a forward slash '/', then type part of a folder path to search for. (Capitalization will be ignored but used for playlist title)
- Press Shift-Enter to create the new playlist. Will fail if no matching results found.
Tip: End the search text with another forward slash to search just for folders with that name. For example, entering '/Pop' may bring up results for J-Pop and K-Pop, however '/Pop/' will only return folders with that name.

### Panel Buttons

![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)


### Playlist Scrolling

 - The playlist scroll bar is to the left of the playlist, hidden until you mouse over it
 - Click above or below the scroll bar to scroll quickly in that direction
 - Right click anywhere in the scroll field to jump immediately to that location

### Moving Playlists and Tracks

 - Playlists can be rearranged by dragging them
 - A single track can be quickly copied to the end of another playlist by dragging it onto a playlist tab.
 - Single tracks can be moved within a playlist by holding shift and dragging
 - To move a block of tracks; click the first track, then while holding shift click the last track, then click and drag while holding shift

### Quirks

 - If you add or change album art, use MENU -> DATABASE -> RESET IMAGE CACHE to update this without needing to restart
 - Quirk: Although it is possible to open tracks via file association, this is not the recommended way of importing music. A different application would be better for this purpose.
 - Quirk: There is no playlist repeat function, player will stop once it reaches the end of a playlist (Broadcasting will repeat from the top however)
 - Quirk: Playlists and settings are only saved once the program is exited cleanly and not in the case of a force close or crash (Shutting system down while the player is open is a force close) Playtimes are periodically saved however.

### Extra Shortcuts

***Search***: Backslash \ or Ctrl + F  
***Cycle Theme***: F2   
***Change Playlist***: Left and Right arrow keys  
***Seek***: + and -   
***Play next/previous track***: Shift + Left and Right arrow keys (or global mediakeys)   
***Volume Up/Down***: Shift + Up and Down arrow keys   
***Toggle Gallery View***: Mouse button 4   
***Toggle folder break for current playlist***: F1   
***Toggle broadcast sync mode***: F6   
***Undo playlist delete***: Ctrl + Z

### Outbound Streaming

- Install, configure (optional) and start Icecast. See config.txt for optional further setup.
- From player right click top bar and select 'Start Broadcast' from menu. You should now see an entry in the Icecast web interface (default http://localhost:8000). From track context menu select 'Broadcast This' to play a track immediately.

The general idea here is that you can listen to music locally while streaming from and editing another playlist (Like a DJ might).  
Note: Broadcast will repeat from beginning of playlist once end is reached  
Warning: Modifying the number of tracks in playlist that appear before the broadcast marker will impact the broadcast position

Alternatively, by pressing F6 to enter 'sync' mode, the broadcast will receive commands from the player. The effect of this allows for the listening and control of a stream remotely via the web interface.  
Note: This function is experimental and unreliable. Pausing or stopping the player while in this mode will cause the stream to fail or generate other unexpected behavior  
Tip: Higher bitrates may help reduce latency

Linux Note: In my test I had difficulty getting this to work on Linux. Icecast appeared to be running and configured ok however BASS would report an unknown error and the stream would not appear. I have tested this to work previously on Linux and streaming works from Linux to a windows Icecast so I'm inclined to believe this is some sort of configuration issue rather than a bug in Tauon. Your luck may vary if you wish to try.

### Transcoding albums

Intended to be an easy way to reduce file sizes for copying to devices. Results will be of degraded quality and should not be used for archival.

Requires FFMPEG in encoder subdirectory. Additionally 'lame.exe' for mp3 encoding. (On Linux, programs only need be installed)

Will encode based on settings in MENU->Settings...->Transcode  
Output folders will be placed in same encoder subdirectory (can be changed in config.txt)

Tip: 64Kbps Opus should be good enough for most portable music listening.  
Tip: Not many players on Android support Opus. I suggest Rocket Player or AIMP


### Tag Editing

There is currently no built in support for tag editing.
An external tag editor can be used. See config.txt for linking to an external editor from the track menu (Track menu -> Meta... -> Edit tags with Editor). Is configured for MusicBrainz Picard by default.

Tip: While editing tracks externally, make sure not to change the track file names.  
Bug: Linking to Picard fails with Unicode paths on windows


To remove embedded album art from files (mp3 only): Right click track -> Track Info... -> SHIFT+2


### Importing/Exporting Playlists

Playlists can be backed up, shared and imported using the XSPF playlist file format.

To import; drag and drop XSPF playlist file onto program window. (Any playlist files inside folders will be ignored)

To export; right click playlist tab and select Export.

Note: Its best to import any corresponding audio files before importing playlists.  
Note: Importing large playlists can take a long time, cleaning database beforehand (MENU->Database->Remove Missing Tracks) may help speed this up.  
Note: Some tracks with strange characters in metadata may cause process to fail.  
Tip: Exporting then importing tracks also serves the function of reviving dead tracks when files have been moved.


User data files
================

**state.p** - Contains playlists, track database information and some settings. Delete to reset player.  
**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by filename and track title, can be transferred between platforms.

### Upgrading / Moving

- Copy 'star.p' file from old install to keep play counts.
- Copy 'state.p' file to keep rest of player data.
- If you are moving platforms, resetting player or moved your music location and have custom playlists you want to keep, export using the export playlist function then re-import.

Web components
=================================

Enable in MENU -> Settings -> System  
Warning: Enabling the 'allow external connections' option may pose a security risk  
Warning: Make sure there are no private files in the folders of your music, especially pictures that may inadvertently be sent as an album art thumbnail

***localhost:7590/remote*** - Remote player control with album art and track info  
***localhost:7590/radio*** - Album art and track info for broadcasting

Individual tracks can be made accessible from the UI (TRACK MENU-> Meta... -> Generate Websample)  
Note: Requires FFMPEG and web server enabled before menu entry will appear  
Note: Must be clicked for each track and will only be accessible for duration of session. Files are cleared on restart.
