
[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)

; Extra { here is indeed necessary!
AppId={{8793586B-AC0A-47EB-97D6-4060D8D63CB4}
AppName=Tauon
AppVersion={{ tauon_version }}

AppPublisher=Taiko2k
AppPublisherURL=https://github.com/Taiko2k/TauonMusicBox
AppSupportURL=https://github.com/Taiko2k/TauonMusicBox
AppUpdatesURL=https://github.com/Taiko2k/TauonMusicBox
DefaultDirName={commonpf}\Tauon Music Box
DisableProgramGroupPage=yes
OutputBaseFilename=tauonsetup-{{ tauon_version }}
Compression=lzma
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64os
ArchitecturesAllowed=x64os
SetupIconFile=D:\a\Tauon\Tauon\dist\TauonMusicBox\_internal\assets\icon.ico

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "D:\a\Tauon\Tauon\dist\TauonMusicBox\Tauon Music Box.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "D:\a\Tauon\Tauon\dist\TauonMusicBox\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTE: Don't use "Flags: ignoreversion" on any shared system files

[Icons]
Name: "{commonprograms}\Tauon"; Filename: "{app}\Tauon Music Box.exe"
Name: "{commondesktop}\Tauon"; Filename: "{app}\Tauon Music Box.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\Tauon Music Box.exe"; Description: "{cm:LaunchProgram,Tauon}"; Flags: nowait postinstall skipifsilent
