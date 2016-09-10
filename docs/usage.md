Basic Usage. Updated for v1.6.3
===========

Player is playlist based (rather than library based) and makes the assumption that folders are albums.  Sorting and filtering is applied by creating new playlists from existing playlists. 

For best experience it is recommended to have an organised and structured music library. I  recommended the following file structure especially for large music libraries: MUSIC_LIBRARY/GENRE/ARTIST/ALBUM/tracks

##### Importing Music:

- Drag and drop files and folders from your file manager.

- Importing can take a while for large music collections. After importing, right click playlist tab and select 'Sort Tracks' to ensure tracks are ordered correctly.


##### Updating Library:

- Clear playlist and re-import.


##### Upgrading / Moving:

- Copy 'star.p' file from old install to keep play counts.
- Copy 'state.p' file to keep rest of player data. 
- If you are moving platforms or reseting player and have custom playlists you want to keep, export them using the export playlist function.


Advanced Use
============

##### Track Navigation:

- 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist. However with random mode on, 'Back' functions as an absolute back, playing the previous track played. (So if you intended to play the track that appears after the last track that was played, you could enter the sequence RANDOM ON > BACK > RANDOM OFF > FORWARD) (Does that make sense? no? I thought not.)


##### Quick Search:

- Press the backslash key or Ctrl+F to open search entry.
- Type word fragments separated by spaces. Use UP and DOWN keys to navigate matching results in current playlst. Press enter key to play selected track.
- Press Shift+Enter to create a new playlist from results


##### Folder Filtering

- Press the backslash key '\' or Ctrl+F to open search entry.
- Begin search text with a forwardslash '/', then type a part of a folder to search for. (Capitalization will be ignored but used for playlist title)
- Press Shift-Enter to create the new playlist. Will fail if no matching results found.
- Tip: End the search text with another forwardslash '/' to search just for folders with that name. For example entering '/Pop' may bring up results for J-Pop and K-Pop, however '/Pop/' will avoid those.


##### Panel Buttons:

![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)

##### Shortcuts:

- ***Search***: Backslash \ or Ctrl + F  
***Show playing***: Quote ' (the button next to the enter/return key)   
***Random Mode***: Period .   
***Repeat Mode***: Comma ,   
***Radio Random***: Slash /  
***Change Theme***: F2   
***Change Playlist***: Left and Right arrow keys  
***Seek***: + and -   
***Play next/previous track***: Shift + Left and Right arrow keys   
***Volume Up/Down***: Shift + Up and Down arrow keys   
***Toggle Gallery View***: Mouse button 4   
***Delete Current Playlist***: Ctrl + w   
***Toggle folder break for playlist***: F1


##### Outbound Streaming:

- See config file to set up encoder. Install, configure (optional) and run icecast. From player right click top bar and
select 'Start Broadcast' from menu. You should now see an entry in the icecast web interface (default http://localhost:8000). From track context menu select 'Broadcast This'
to play a track immediately.

- The general idea here is that you can listen to music locally while streaming from and editing another playlist (Like a DJ might).


##### Transcoding albums (Experimental feature):

Intended to be an easy way to reduce file sizes for copying to devices. Results will be of degraded quality and should not be used for archival.

Requires ffmpeg and opusenc/lame in encoder subdirectory. (For Linux, programs simply need be installed)

Will encode based on settings in MENU->Settings...->Transcode
Output folders will be placed in same encoder subdirectory


##### Tag Editing

There is currently no support for modifying audio file tags.
An external tag editor can be used. (I reccomend MusicBrainz Picard). 
After editing tracks externally, metadata can be updated by: Right clicking track -> Meta... -> Reload Metadata (Providing that the file names were not externally changed)


##### Importing/Exporting Playlists (Experimental feature)

Playlists can be backed up and shared using the XSPF playlist file format. 

To import; drag and drop playlist file onto program window. (Any playlist files in subfolders will be ignored)
To export; right click playlist tab and select Export.

Note: Its best to import any corresponding audio files before importing playlists.
Note: Importing large playlists can take a very long time, cleaning database beforehand (MENU->Database->Remove Missing Tracks) may help speed this up.
Note: Some tracks with strange characters in metadata may cause process to fail.
Tip: Exporting then importing tracks also serves the function of reviving dead tracks where files have been moved.


User data files
================

**state.p** - Contains playlists and track database information, intended to be disposable, delete to reset player, cannot be transferred between platforms.  
**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by filename and track title, can be transferred between platforms

Web components 
=================================

Enable in MENU -> Settings -> System 
Warning: Enabling the 'allow external connections' option may pose a security risk

***localhost:7590/remote*** - Remote player control with album art and track info  
***localhost:7590/radio*** - Album art and track info for broadcasting

