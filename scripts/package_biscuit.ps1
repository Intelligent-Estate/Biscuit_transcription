$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $repo "src"
Set-Location $repo

$pyinstallerCommand = Get-Command pyinstaller -ErrorAction SilentlyContinue
$pyinstallerPath = if ($pyinstallerCommand) { $pyinstallerCommand.Source } else { "" }
if (-not $pyinstallerPath) {
    $fallback = "C:\Users\marsh\Downloads\roop-unleashed-main\roop-unleashed-main\installer\installer_files\env\Scripts\pyinstaller.exe"
    if (Test-Path $fallback) {
        $pyinstallerPath = $fallback
    }
}

if (-not $pyinstallerPath) {
    throw "PyInstaller was not found. Run from source with scripts\run_biscuit.ps1."
}

& $pyinstallerPath `
    --noconfirm `
    --clean `
    --windowed `
    --name Biscuit `
    --paths src `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module torchaudio `
    src\biscuit\__main__.py

Write-Host "Biscuit package written under dist\Biscuit"
