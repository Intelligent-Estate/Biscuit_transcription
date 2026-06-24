$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $repo "src"
Set-Location $repo

$pyinstallerCommand = Get-Command pyinstaller -ErrorAction SilentlyContinue
$pyinstallerPath = if ($pyinstallerCommand) { $pyinstallerCommand.Source } else { "" }
if (-not $pyinstallerPath) {
    python -m pip install pyinstaller
    $pyinstallerCommand = Get-Command pyinstaller -ErrorAction SilentlyContinue
    $pyinstallerPath = if ($pyinstallerCommand) { $pyinstallerCommand.Source } else { "" }
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
    --hidden-import pystray `
    --hidden-import pystray._win32 `
    --hidden-import PIL.Image `
    --hidden-import PIL.ImageDraw `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module torchaudio `
    src\biscuit\__main__.py

Write-Host "Biscuit package written under dist\Biscuit"
