Basic Usage
===========

##### Importing Music:

- Drag and drop files and folders from your file manager.

- Tracks will import to currently open playlist. Importing can take a while for large music collections. After importing, right click playlist tab and select 'Sort Tracks'
to ensure tracks are ordered correctly.

##### Updating Library:

- Clear playlist and re-import


##### Upgrading:

- Clean install recommended. Copy 'star.p' file from old install to keep play counts.

Advanced Use
============

##### Outbound Streaming:

- Find 'oggenc2.exe' or 'lame.exe' on the internet and place in 'encoder' subdirectory. Install, configure (optional) and run icecast. From player right click top bar and
select 'Start Broadcast' from menu. You should now see an entry in the icecast web interface (usually http://localhost:8000). From track context menu select 'Broadcast This'
to play a track immediately.

- The general idea here is that you can listen to music locally while streaming from and editing another playlist (Like a DJ might).

- If the web interface is enabled (in config.txt) listeners can see the album art of the playing track at :5000/radio

##### Track Navigation:

- 'Forward' and 'Back' play the next and previous tracks as they appear in the playlist. However with random mode on, back functions as an absolute back, playing the
previous track played. (So if you intended to play the track that appears after the last track that was played, you could enter the sequence RANDOM ON > BACK > RANDOM OFF > FORWARD)

##### Shortcuts:

- ***Search***: Backslash \ or Ctrl + F  
***Show playing***: Quote ' or Right click play button  
***Random Mode***: Slash / or Right click forward button  
***Repeat Mode***: Period . or Right click back button  
***Change Theme***: F2  
***Change Playlist***: Left and Right arrow keys  
***Play next/previous track***: Shift + Left and Right arrow keys  
***Toggle Gallery View***: Mouse button 4

#### Transcoding albums (Experimental feature):


Current function: Folder of tracks -> folder + opus + cue + jpg  

Intended to be an easy way to reduce file sizes for copying to device
To playback a player that supports both opus codec and cue sheets will be required (I suggest AIMP for Android)

Requires ffmpeg and opusenc in encoder subdirectory
Will encode to opus with cue sheet and jpg album art (specify bitrate in config.txt)
Output folders will be placed in same encoder subdirectory
Enable the menu entry in config.txt


User data files
================

**state.p** - Contains playlists and track database information, intended to be disposable, delete to reset player, cannot be transferred between platforms.  
**star.p**  - Contains track play count information independent of database, tracks are uniquely identified by filename and track title, can be transferred between platforms

Web components (enable in config)
=================================

localhost:5000/remote - Remote player control with album art and track info
localhost:5000/radio - Album art and track info for broadcasting

