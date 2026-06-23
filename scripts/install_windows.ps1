$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $repo "launchers\Biscuit-Windows.cmd"
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenu "Biscuit.lnk"

if (-not (Test-Path $launcher)) {
    throw "Missing launcher: $launcher"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $repo
$shortcut.WindowStyle = 7
$shortcut.Description = "Biscuit dictation toolbar"
$shortcut.Save()

Write-Host "Biscuit installed to Start Menu: $shortcutPath"
