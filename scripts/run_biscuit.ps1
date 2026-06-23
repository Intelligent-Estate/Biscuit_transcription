$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$env:PYTHONPATH = Join-Path $repo "src"

Set-Location $repo
python -m biscuit
