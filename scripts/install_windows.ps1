param(
    [switch]$NoLaunch
)

$ErrorActionPreference = "Stop"

$repo = Split-Path -Parent $PSScriptRoot
$launcher = Join-Path $repo "Biscuit-Windows.cmd"
$iconPath = Join-Path $repo "assets\Biscuit.ico"
$runShortcutPath = Join-Path $repo "Run Biscuit.lnk"
$startMenu = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs"
$shortcutPath = Join-Path $startMenu "Biscuit.lnk"
$startup = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$startupShortcutPath = Join-Path $startup "Biscuit.lnk"

function Set-HkcuRegistryString {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,
        [Parameter(Mandatory = $true)]
        [AllowEmptyString()]
        [string]$Name,
        [Parameter(Mandatory = $true)]
        [string]$Value
    )

    $prefix = "HKCU:\"
    if (-not $Path.StartsWith($prefix)) {
        throw "Expected HKCU registry path: $Path"
    }

    $subKey = $Path.Substring($prefix.Length)
    $key = [Microsoft.Win32.Registry]::CurrentUser.CreateSubKey($subKey)
    if (-not $key) {
        throw "Could not create registry key: $Path"
    }

    try {
        $key.SetValue($Name, $Value, [Microsoft.Win32.RegistryValueKind]::String)
    }
    finally {
        $key.Close()
    }
}

function New-BiscuitShortcut {
    param(
        [Parameter(Mandatory = $true)]
        [object]$Shell,
        [Parameter(Mandatory = $true)]
        [string]$ShortcutPath,
        [Parameter(Mandatory = $true)]
        [string]$LauncherPath,
        [Parameter(Mandatory = $true)]
        [string]$WorkingDirectory,
        [string]$IconPath = ""
    )

    try {
        $shortcut = $Shell.CreateShortcut($ShortcutPath)
        $shortcut.TargetPath = $LauncherPath
        $shortcut.WorkingDirectory = $WorkingDirectory
        $shortcut.WindowStyle = 7
        $shortcut.Description = "Biscuit dictation toolbar"
        if ($IconPath -and (Test-Path $IconPath)) {
            $shortcut.IconLocation = $IconPath
        }
        $shortcut.Save()
        Write-Host "Biscuit shortcut installed: $ShortcutPath"
    }
    catch {
        Write-Warning "Could not save shortcut: $ShortcutPath. $($_.Exception.Message)"
    }
}

if (-not (Test-Path $launcher)) {
    throw "Missing launcher: $launcher"
}

$shell = New-Object -ComObject WScript.Shell
New-BiscuitShortcut -Shell $shell -ShortcutPath $runShortcutPath -LauncherPath $launcher -WorkingDirectory $repo -IconPath $iconPath
New-BiscuitShortcut -Shell $shell -ShortcutPath $shortcutPath -LauncherPath $launcher -WorkingDirectory $repo -IconPath $iconPath
New-BiscuitShortcut -Shell $shell -ShortcutPath $startupShortcutPath -LauncherPath $launcher -WorkingDirectory $repo -IconPath $iconPath

$contextMenuCommand = "`"$launcher`" --dictate-once"
$contextMenuRoots = @(
    "HKCU:\Software\Classes\*\shell\Biscuit",
    "HKCU:\Software\Classes\AllFilesystemObjects\shell\Biscuit",
    "HKCU:\Software\Classes\Directory\shell\Biscuit",
    "HKCU:\Software\Classes\Directory\Background\shell\Biscuit",
    "HKCU:\Software\Classes\Drive\shell\Biscuit"
)

foreach ($menuRoot in $contextMenuRoots) {
    Set-HkcuRegistryString -Path $menuRoot -Name "MUIVerb" -Value "Biscuit"
    if (Test-Path $iconPath) {
        Set-HkcuRegistryString -Path $menuRoot -Name "Icon" -Value $iconPath
    }
    else {
        Set-HkcuRegistryString -Path $menuRoot -Name "Icon" -Value $launcher
    }

    $commandRoot = Join-Path $menuRoot "command"
    Set-HkcuRegistryString -Path $commandRoot -Name "" -Value $contextMenuCommand
}

Write-Host "Biscuit launcher shortcut: $runShortcutPath"
Write-Host "Biscuit installed to Start Menu: $shortcutPath"
Write-Host "Biscuit installed to Startup: $startupShortcutPath"
Write-Host "Biscuit context menu command registered for files, folders, folder backgrounds, and drives."

if (-not $NoLaunch) {
    Start-Process -FilePath $launcher -WorkingDirectory $repo -WindowStyle Hidden
    Write-Host "Biscuit launched."
}
