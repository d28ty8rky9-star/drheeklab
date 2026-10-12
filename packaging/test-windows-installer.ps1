param([Parameter(Mandatory=$true)][string]$SetupPath, [switch]$DisposableRunner)
$ErrorActionPreference = 'Stop'
# Instala/desinstala exclusivamente no runner Windows descartável, nunca no PC do negócio.
if (-not $DisposableRunner -or $env:CI -ne 'true' -or $env:RUNNER_OS -ne 'Windows') {
    throw 'Este teste exige runner CI Windows descartável e -DisposableRunner.'
}
$setup = (Resolve-Path $SetupPath).Path
$tempRoot = Join-Path $env:RUNNER_TEMP ('drheeklab-installer-' + [guid]::NewGuid())
New-Item -ItemType Directory -Path $tempRoot | Out-Null
$appPath = Join-Path $tempRoot 'Aplicativo de QA'
New-Item -ItemType Directory -Path 'C:\DrHeekLab' -Force | Out-Null
$sentinel = Join-Path 'C:\DrHeekLab' ('qa-preservation-' + [guid]::NewGuid() + '.txt')
$sentinelValue = [guid]::NewGuid().ToString()
Set-Content $sentinel $sentinelValue
$python = (Resolve-Path '.venv\Scripts\python.exe').Path
$seed = @'
from pathlib import Path
from drheeklab.storage import Storage
s=Storage(Path(r"C:\DrHeekLab"),'test')
s.save_draft('installer_qa','Preservado após reinstalação e desinstalação')
(s.home/'Marca'/'installer-qa.txt').write_text('mídia de QA preservada',encoding='utf-8')
s.close()
'@
$check = @'
from pathlib import Path
from drheeklab.storage import Storage
from drheeklab.backup import verify_backup
s=Storage(Path(r"C:\DrHeekLab"),'test')
assert s.load_draft('installer_qa')=='Preservado após reinstalação e desinstalação'
assert (s.home/'Marca'/'installer-qa.txt').read_text(encoding='utf-8')=='mídia de QA preservada'
assert any(verify_backup(p,'test') for p in (s.home/'Backups').glob('*.zip'))
s.close()
'@
function Invoke-Checked([string]$File, [string[]]$Arguments) {
    $process = Start-Process -FilePath $File -ArgumentList $Arguments -Wait -PassThru
    if ($process.ExitCode -ne 0) { throw "Processo falhou: $File, saída $($process.ExitCode)" }
}
try {
    foreach ($attempt in 1..2) {
        Invoke-Checked $setup @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART','/SP-',"/DIR=`"$appPath`"", "/LOG=`"$tempRoot\install-$attempt.log`"")
        if ((Get-Content $sentinel -Raw).Trim() -ne $sentinelValue) { throw 'Instalação alterou dados permanentes' }
        $report = Join-Path $tempRoot "installed-qa-$attempt.json"
        Invoke-Checked (Join-Path $appPath 'DrHeekLab.exe') @('--self-test','--self-test-report',"`"$report`"")
        $qa=Get-Content $report -Raw | ConvertFrom-Json
        if ($qa.status -ne 'passed' -or $qa.data -ne 'temporary only' -or $qa.checks -notcontains 'restart persistence') { throw 'QA do aplicativo instalado falhou' }
        if ($attempt -eq 1) {
            if (Test-Path 'C:\DrHeekLab\TESTES\Banco de Dados\drheeklab.sqlite3') { throw 'Runner contém dados anteriores; não sobrescrever' }
            & $python -c $seed
            if ($LASTEXITCODE -ne 0) { throw 'Falha na criação de dados fictícios para teste de atualização' }
        } else {
            & $python -c $check
            if ($LASTEXITCODE -ne 0) { throw 'Dados/backup pré-atualização não preservados' }
            Invoke-Checked (Join-Path $appPath 'DrHeekLab.exe') @('--scheduled-backup','--environment','test','--data-dir','C:\DrHeekLab')
            & $python -c 'from drheeklab.storage import Storage; from drheeklab.scheduler import install_task,remove_task; s=Storage(r"C:\DrHeekLab"); install_task(s); remove_task(s); s.close()'
            if ($LASTEXITCODE -ne 0) { throw 'Criação/remoção de tarefa Windows falhou' }
        }
    }
    Invoke-Checked (Join-Path $appPath 'unins000.exe') @('/VERYSILENT','/SUPPRESSMSGBOXES','/NORESTART',"/LOG=`"$tempRoot\uninstall.log`"")
    if ((Get-Content $sentinel -Raw).Trim() -ne $sentinelValue) { throw 'Desinstalação alterou dados permanentes' }
    if (Test-Path (Join-Path $appPath 'DrHeekLab.exe')) { throw 'Binário permaneceu após desinstalação' }
    & $python -c $check
    if ($LASTEXITCODE -ne 0) { throw 'Banco/arquivos foram alterados pela desinstalação' }
    New-Item -ItemType Directory -Path 'dist\installer-qa' -Force | Out-Null
    Copy-Item "$tempRoot\*" 'dist\installer-qa' -Exclude 'Aplicativo de QA' -Recurse
    @{status='passed';checks=@('install','reinstall','installed self-test','pre-update verified backup','database/media preserved','headless daily backup','task create/delete','uninstall');manual_homologation='pending'} | ConvertTo-Json | Set-Content 'dist\installer-qa\result.json'
} finally {
    Remove-Item $sentinel -ErrorAction SilentlyContinue
    Write-Host "Logs do teste: $tempRoot"
}
