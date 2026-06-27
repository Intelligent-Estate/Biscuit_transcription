$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$buildVenv = Join-Path $repo ".biscuit-build-venv"
if (-not (Test-Path $buildVenv)) {
    python -m venv $buildVenv
}

$venvPython = Join-Path $buildVenv "Scripts\python.exe"
$venvPyinstaller = Join-Path $buildVenv "Scripts\pyinstaller.exe"
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install --upgrade -r (Join-Path $repo "requirements.txt") pyinstaller

if (-not (Test-Path $venvPyinstaller)) {
    throw "PyInstaller was not found in the clean build environment. Run from source with scripts\run_biscuit.ps1."
}

$env:PYTHONPATH = Join-Path $repo "src"
& $venvPyinstaller `
    --noconfirm `
    --clean `
    --console `
    --name Biscuit `
    --paths src `
    --hidden-import biscuit.release `
    --hidden-import faster_whisper `
    --hidden-import ctranslate2 `
    --hidden-import huggingface_hub `
    --hidden-import sounddevice `
    --hidden-import pyaudio `
    --hidden-import pystray `
    --hidden-import pystray._win32 `
    --hidden-import PIL.Image `
    --hidden-import PIL.ImageDraw `
    --exclude-module torch `
    --exclude-module torchvision `
    --exclude-module torchaudio `
    src\biscuit\__main__.py

Write-Host "Biscuit package written under dist\Biscuit"
