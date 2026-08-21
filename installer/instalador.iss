; Instalador de multiCAD-MCP (Inno Setup 6)
; Compilar desde la raiz del repo, tras generar dist\multiCAD-MCP con PyInstaller:
;   "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" installer\instalador.iss
; O directamente:  powershell -File installer\build.ps1

#define NombreApp "multiCAD-MCP"
#define Version "0.2.0"
#define Ejecutable "multiCAD-MCP.exe"

[Setup]
AppId={{2C7F1E64-9B48-4D7A-A5E3-6F0B27C914DA}
AppName={#NombreApp}
AppVersion={#Version}
AppPublisher=APOGEA Consulting
AppPublisherURL=https://github.com/JardiMargalefAgusti/multiCAD-mcp
DefaultDirName={autopf}\multiCAD-MCP
DefaultGroupName={#NombreApp}
; per-user y sin UAC: el registro del MCP corre como el usuario final,
; que es justo el perfil cuyos config de Claude hay que tocar.
PrivilegesRequired=lowest
SourceDir=..
OutputDir=installer\salida
OutputBaseFilename=Instalar_multiCAD-MCP
SetupIconFile=installer\icono.ico
UninstallDisplayIcon={app}\{#Ejecutable}
Compression=lzma2/fast
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
InfoAfterFile=installer\post_instalacion.txt

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "desktopicon"; Description: "Crear un acceso directo en el escritorio"; GroupDescription: "Accesos directos:"

[Files]
Source: "dist\multiCAD-MCP\*"; DestDir: "{app}"; Flags: recursesubdirs ignoreversion

[Icons]
Name: "{autoprograms}\{#NombreApp}"; Filename: "{app}\{#Ejecutable}"
Name: "{autodesktop}\{#NombreApp}"; Filename: "{app}\{#Ejecutable}"; Tasks: desktopicon

[Run]
; registro automatico del servidor MCP en los config de Claude del usuario
Filename: "{app}\{#Ejecutable}"; Parameters: "--registrar-mcp"; Flags: runhidden
Filename: "{app}\{#Ejecutable}"; Description: "Abrir el panel de multiCAD-MCP"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{app}\{#Ejecutable}"; Parameters: "--desregistrar-mcp"; Flags: runhidden; RunOnceId: "DesregistrarMCP"
