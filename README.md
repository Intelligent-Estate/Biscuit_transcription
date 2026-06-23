# Biscuit

Biscuit is a Windows-first dictation overlay. Right-click anywhere, choose the small `biscuit` action, speak, stop recording, and Biscuit inserts the transcribed text back into the clicked window.

The first build is intentionally lean:

- Python/Win32 source tool.
- Tiny topmost right-click overlay instead of fragile per-app menu injection.
- Tiny Biscuit tray/menu-bar icon for settings and cursor dictation, with a floating `biscuit` fallback button if tray support is missing.
- Local model path configuration.
- No model blobs copied into this repository.

## Run

```powershell
.\scripts\run_biscuit.ps1
```

## Launchers

Double-click or run the launcher for the current desktop:

- Windows: `launchers\Biscuit-Windows.cmd`
- Linux: `launchers/biscuit-linux.sh`
- macOS: `launchers/Biscuit-macOS.command`

Linux and macOS users may need to mark the launcher executable after checkout:

```bash
chmod +x launchers/biscuit-linux.sh launchers/Biscuit-macOS.command
```

## Install-Style Setup

Use the installer script for the current desktop to make Biscuit feel like a normal app launcher:

```powershell
.\scripts\install_windows.ps1
```

```bash
./scripts/install_linux.sh
./scripts/install_macos.sh
```

Windows creates a Start Menu shortcut. Linux creates a `biscuit.desktop` application entry. macOS creates `~/Applications/Biscuit.app`. At runtime Biscuit tries to show a tiny blue-black/yellow Biscuit icon in the system tray or menu bar; if tray support is not available, it shows the small themed floating Biscuit button.

The settings panel has:

- Model
- Language
- Provider
- Update
- Start Biscuit
- Kill Biscuit

`Update` tries to find a local model under `C:\Users\marsh\Documents\ai bio`. If none is found, use Browse and choose the existing model file manually.

The AI bio model currently discovered by Biscuit is:

```text
C:\Users\marsh\Documents\ai bio\data\stt_probe\whisper-tiny-q4_0.gguf
```

For GGUF/GGML models, set Provider to a GGUF-capable runner such as `whisper-cli.exe` when it is available on the machine. Leave Provider as `auto` for Python-backed local model directories or model names.

## Package

```powershell
.\scripts\package_biscuit.ps1
```

The package script uses PyInstaller when available and writes output to `dist\Biscuit`. Large model files and recordings are ignored by git.

## Notes

Windows apps own their private context menus. Biscuit uses a topmost overlay action at the cursor so the workflow stays universal: right-click, click Biscuit, speak, insert.
