#define AppVersion "2.8.1"
[Setup]
AppId={{485013A4-F44F-47DF-9C89-9CECB56946A0}
AppName=Dr. Heek Lab 2.0
AppVersion={#AppVersion}
DefaultDirName={autopf}\DrHeekLab
DefaultGroupName=Dr. Heek Lab
OutputDir=..\dist\installer
OutputBaseFilename=DrHeekLab-2.8.1-Fase8-Setup
UninstallDisplayIcon={app}\DrHeekLab.exe
#ifdef OfficialIcon
SetupIconFile={#OfficialIcon}
#endif
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes

[Files]
Source: "..\dist\DrHeekLabUpdate.exe"; Flags: dontcopy
Source: "..\dist\DrHeekLab\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Dirs]
; Dados permanentes são separados dos binários e preservados na desinstalação.
Name: "C:\DrHeekLab"; Permissions: users-modify; Flags: uninsneveruninstall; Check: DataRootMissing

[Icons]
Name: "{group}\Dr. Heek Lab"; Filename: "{app}\DrHeekLab.exe"
Name: "{autodesktop}\Dr. Heek Lab"; Filename: "{app}\DrHeekLab.exe"

[Run]
Filename: "{app}\DrHeekLab.exe"; Description: "Abrir Dr. Heek Lab"; Flags: nowait postinstall skipifsilent

[Code]
function DataRootMissing: Boolean;
begin
  Result := not DirExists('C:\DrHeekLab');
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ExitCode: Integer;
  InstalledMS, InstalledLS: Cardinal;
  ReportPath: String;
begin
  Result := '';
  if GetVersionNumbers(ExpandConstant('{app}\DrHeekLab.exe'), InstalledMS, InstalledLS) then
    if (InstalledMS > 131080) or ((InstalledMS = 131080) and (InstalledLS > 65536)) then
    begin
      Result := 'Há uma versão mais recente instalada. Não é permitido rebaixar automaticamente.';
      Exit;
    end;
  ExtractTemporaryFile('DrHeekLabUpdate.exe');
  ReportPath := ExpandConstant('{tmp}\pre-update-report.json');
  if not Exec(ExpandConstant('{tmp}\DrHeekLabUpdate.exe'), '--data-dir "C:\DrHeekLab" --report "' + ReportPath + '"', '', SW_HIDE, ewWaitUntilTerminated, ExitCode) then
  begin
    Result := 'Não foi possível verificar os dados antes da instalação. Os arquivos anteriores foram preservados.';
    Exit;
  end;
  if (ExitCode <> 0) or not FileExists(ReportPath) then
    Result := 'Backup/verificação anterior falhou. Feche o aplicativo, confira espaço, permissões e integridade. A instalação foi bloqueada antes de substituir os binários. Relatório: ' + ReportPath;
end;
