#define AppVersion "2.9.10"
[Setup]
AppId={{485013A4-F44F-47DF-9C89-9CECB56946A0}
AppName=Dr. Heek Lab
AppVersion={#AppVersion}
AppVerName=Dr. Heek Lab {#AppVersion} Beta
DefaultDirName={autopf}\DrHeekLab
DefaultGroupName=Dr. Heek Lab
OutputDir=..\dist\installer
OutputBaseFilename=DrHeekLab-{#AppVersion}-Beta-Setup
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

function NextVersionComponent(var Version: String): Cardinal;
var
  Separator: Integer;
begin
  Separator := Pos('.', Version);
  if Separator = 0 then
  begin
    Result := StrToIntDef(Version, 0);
    Version := '';
  end
  else
  begin
    Result := StrToIntDef(Copy(Version, 1, Separator - 1), 0);
    Delete(Version, 1, Separator);
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  ExitCode: Integer;
  InstalledMS, InstalledLS, TargetMS, TargetLS: Cardinal;
  TargetVersion: String;
  ReportPath: String;
begin
  Result := '';
  TargetVersion := '{#AppVersion}';
  TargetMS := NextVersionComponent(TargetVersion) shl 16;
  TargetMS := TargetMS or NextVersionComponent(TargetVersion);
  TargetLS := NextVersionComponent(TargetVersion) shl 16;
  TargetLS := TargetLS or NextVersionComponent(TargetVersion);
  if GetVersionNumbers(ExpandConstant('{app}\DrHeekLab.exe'), InstalledMS, InstalledLS) then
    if (InstalledMS > TargetMS) or ((InstalledMS = TargetMS) and (InstalledLS > TargetLS)) then
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
