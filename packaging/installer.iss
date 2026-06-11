[Setup]
AppName=KartOverlay
AppVersion=1.0.0
DefaultDirName={localappdata}\Programs\KartOverlay
DefaultGroupName=KartOverlay
DisableProgramGroupPage=yes
OutputBaseFilename=KartOverlay-Setup
Compression=lzma
SolidCompression=yes
PrivilegesRequired=lowest

[Files]
Source: "..\dist\KartOverlay\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{group}\KartOverlay"; Filename: "{app}\KartOverlay.exe"
Name: "{autodesktop}\KartOverlay"; Filename: "{app}\KartOverlay.exe"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: unchecked
