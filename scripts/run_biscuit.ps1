$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $repo "src"

Set-Location $repo
$python = Get-Command pythonw.exe -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command python.exe -ErrorAction Stop
}

Start-Process -FilePath $python.Source -ArgumentList @("-m", "biscuit") -WorkingDirectory $repo -WindowStyle Hidden
