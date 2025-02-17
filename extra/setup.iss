
[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{8793586B-AC0A-47EB-97D6-4060D8D63CB4}
AppName=Tauon
AppVersion=7.9.0

AppPublisher=Taiko2k
AppPublisherURL=https://github.com/Taiko2k/TauonMusicBox
AppSupportURL=https://github.com/Taiko2k/TauonMusicBox
AppUpdatesURL=https://github.com/Taiko2k/TauonMusicBox
DefaultDirName={pf}\Tauon Music Box
DisableProgramGroupPage=yes
OutputBaseFilename=setup
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64
ArchitecturesAllowed=x64
SetupIconFile=C:\<???>\TauonMusicBox\_internal\assets\icon.ico



[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\<???>\TauonMusicBox\tauon.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\<???>\TauonMusicBox\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{commonprograms}\Tauon"; Filename: "{app}\Tauon.exe"
Name: "{commondesktop}\Tauon"; Filename: "{app}\Tauon.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Tauon.exe"; Description: "{cm:LaunchProgram,Tauon}"; Flags: nowait postinstall skipifsilent

