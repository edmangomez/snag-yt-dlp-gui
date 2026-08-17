; Script Inno Setup para "Snag"
; Requisitos: Inno Setup 6 (https://jrsoftware.org/isinfo.php)
; Generar: abrir este archivo y compilar, o ejecutar:
;   ISCC.exe snag.iss

#define MyAppName "Snag"
#define MyAppVersion "1.0.0"
#define MyAppExeName "Snag.exe"

[Setup]
AppId={{B8E1A2D4-5C7F-4A9B-9E3D-2F6A8C1B4E5D}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher=Snag
AppPublisherURL=https://github.com/edmangomez/snag-yt-dlp-gui
DefaultDirName={autopf}\Snag
DefaultGroupName={#MyAppName}
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
OutputDir={#SourcePath}installer
OutputBaseFilename=Snag-Setup
SourceDir=dist
SetupIconFile={#SourcePath}snag.ico

[Files]
Source: "Snag.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "snag.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Crear acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Ejecutar {#MyAppName}"; Flags: nowait postinstall skipifsilent