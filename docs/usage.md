Basic Usage
===========

##### Importing Music:

- Drag and drop files and folders from your file manager.

- Importing can take a while for large music collections. After importing, right click playlist tab and select 'Sort Tracks' to ensure tracks are ordered correctly.

##### Updating Library:

- Clear playlist and re-import


##### Upgrading / Moving:

- Copy 'star.p' file from old install to keep play counts.

Advanced Use
============

##### Track Navigation:

- 'Forward' and 'Back' buttons play the next and previous tracks as they appear in the playlist. However with random mode on, back functions as an absolute back, playing the
previous track played. (So if you intended to play the track that appears after the last track that was played, you could enter the sequence RANDOM ON > BACK > RANDOM OFF > FORWARD)

##### Panel Buttons:

![Screenshot - Panel](https://raw.githubusercontent.com/Taiko2k/tauonmb/master/docs/panel-guide.png)

##### Shortcuts:

- ***Search***: Backslash \ or Ctrl + F  
***Show playing***: Quote ' (the button next to the enter/return key on US keyboards)   
***Random Mode***: Period .   
***Repeat Mode***: Comma ,   
***Radio Random***: Slash /  
***Change Theme***: F2   
***Change Playlist***: Left and Right arrow keys  
***Seek***: + and -   
***Play next/previous track***: Shift + Left and Right arrow keys   
***Volume Up/Down***: Shift + Up and Down arrow keys   
***Toggle Gallery View***: Mouse button 4


##### Outbound Streaming:

- See config file to set up encoder. Install, configure (optional) and run icecast. From player right click top bar and
select 'Start Broadcast' from menu. You should now see an entry in the icecast web interface (default http://localhost:8000). From track context menu select 'Broadcast This'
to play a track immediately.

- The general idea here is that you can listen to music locally while streaming from and editing another playlist (Like a DJ might).


##### Transcoding albums (Experimental feature):


Current function: Folder of tracks -> folder + opus + cue + jpg  

Intended to be an easy way to reduce file sizes for copying to device
To playback a player that supports both opus codec and cue sheets will be required (I suggest AIMP for Android)

Requires ffmpeg and opusenc in encoder subdirectory
Will encode to opus with cue sheet and jpg album art (specify bitrate in config.txt)
Output folders will be placed in same encoder subdirectory
Enable the menu entry in config.txt


##### Tag Editing

There is currently no support for modifying files except for file names.
An external tag editor can be used. (I reccomend MusicBrainz Picard). 
After editing tracks externally, metadata can be updated by: Right Click Track -> Meta... -> Reload Metadata (Providing that the file names were not externally changed)


##### Importing/Exporting Playlists

Playlists can be backed up and shared using the XSPF playlist file format. 

To import; drag and drop playlist file onto program window. (Any playlist files in subfolders will be ignored)
To export; right click playlist tab and select Export.
Note: Its best to import any corresponding audio files before importing playlists
Note: Importing large playlists can take a very long time, cleaning database beforehand (MENU->Database->Remove Missing Tracks) may help speed this up

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

