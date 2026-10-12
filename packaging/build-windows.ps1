param([string]$IconPath = "")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
if (-not (Test-Path '.venv\Scripts\python.exe')) { py -3.12 -m venv .venv; if ($LASTEXITCODE -ne 0) { throw 'Falha no ambiente Python' } }
$python = '.venv\Scripts\python.exe'
& $python -m pip install -r requirements-dev.lock
if ($LASTEXITCODE -ne 0) { throw 'Falha nas dependências' }
& $python -m pip install --no-build-isolation --no-deps -e .
if ($LASTEXITCODE -ne 0) { throw 'Falha na instalação' }
& $python -m pip check
if ($LASTEXITCODE -ne 0) { throw 'Dependências incompatíveis; empacotamento bloqueado' }
$env:QT_QPA_PLATFORM = 'offscreen'
New-Item -ItemType Directory -Path 'dist' -Force | Out-Null
$tests = Start-Process -FilePath (Resolve-Path $python).Path -ArgumentList @('-m','pytest','-vv','--maxfail=1','--durations=20','-o','faulthandler_timeout=20','--junitxml=dist/test-results.xml') -NoNewWindow -PassThru -RedirectStandardOutput 'dist\windows-pytest.log' -RedirectStandardError 'dist\windows-pytest-errors.log'
if (-not $tests.WaitForExit(600000)) {
    Stop-Process -Id $tests.Id -Force -ErrorAction SilentlyContinue
    Get-Content 'dist\windows-pytest.log' -Tail 80
    Get-Content 'dist\windows-pytest-errors.log' -Tail 80
    throw 'Testes excederam 10 minutos; logs preservados, empacotamento bloqueado'
}
$tests.WaitForExit()
Get-Content 'dist\windows-pytest.log'
Get-Content 'dist\windows-pytest-errors.log'
if ($tests.ExitCode -ne 0) { throw 'Testes falharam: empacotamento bloqueado' }
Remove-Item Env:QT_QPA_PLATFORM
$argsList = @('-m','PyInstaller','--noconfirm','--clean','--windowed','--onedir','--name','DrHeekLab','--paths','src','--collect-all','drheeklab','--version-file','packaging/version_info.txt')
if ($IconPath) {
    if (-not (Test-Path $IconPath)) { throw 'Ícone oficial não encontrado' }
    $argsList += @('--icon', (Resolve-Path $IconPath).Path)
}
$argsList += 'packaging/launcher.py'
& $python @argsList
if ($LASTEXITCODE -ne 0) { throw 'Falha no empacotamento' }
& $python -m PyInstaller --noconfirm --clean --onefile --console --name DrHeekLabUpdate --paths src packaging/update_preflight.py
if ($LASTEXITCODE -ne 0) { throw 'Falha no verificador pré-atualização; instalador bloqueado' }
$report = Join-Path (Resolve-Path 'dist').Path 'windows-package-qa.json'
if (Test-Path $report) { Remove-Item $report }
$smoke = Start-Process -FilePath (Resolve-Path 'dist\DrHeekLab\DrHeekLab.exe').Path -ArgumentList @('--self-test','--self-test-report',"`"$report`"") -Wait -PassThru
if ($smoke.ExitCode -ne 0) { throw 'Verificação funcional do pacote falhou; instalador bloqueado' }
if (-not (Test-Path $report)) { throw 'Resultado verificável ausente; instalador bloqueado' }
$qa = Get-Content $report -Raw | ConvertFrom-Json
$expected = & $python -c 'import drheeklab; print(drheeklab.__version__)'
if ($LASTEXITCODE -ne 0 -or $qa.status -ne 'passed' -or $qa.version -ne $expected -or $qa.data -ne 'temporary only' -or $qa.checks -notcontains 'restart persistence' -or $qa.checks -notcontains 'encrypted backup/restore') { throw 'Resultado de QA incompatível; instalador bloqueado' }
$iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
if (-not $iscc) {
    $standard = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
    if (Test-Path $standard) { $compiler = $standard } else { throw 'Instale Inno Setup 6 para gerar o instalador; aplicativo disponível em dist\DrHeekLab' }
} else { $compiler = $iscc.Source }
if ($IconPath) { & $compiler "/DOfficialIcon=$((Resolve-Path $IconPath).Path)" packaging/installer.iss }
else { & $compiler packaging/installer.iss }
if ($LASTEXITCODE -ne 0) { throw 'Falha na criação do instalador' }
$setup = Get-ChildItem 'dist\installer\*.exe' | Where-Object { $_.Name -eq "DrHeekLab-$expected-Fase8-Setup.exe" }
if (-not $setup) { throw 'Instalador esperado ausente' }
Get-FileHash $setup.FullName -Algorithm SHA256 | Format-List | Out-File 'dist\installer\SHA256.txt'
Get-FileHash 'dist\DrHeekLab\DrHeekLab.exe','dist\DrHeekLabUpdate.exe' -Algorithm SHA256 | Format-List | Out-File 'dist\windows-SHA256.txt'
Write-Host 'Pacote gerado. Execute o checklist Windows antes de liberar. Sem ícone oficial fornecido, a identidade final está pendente.'
