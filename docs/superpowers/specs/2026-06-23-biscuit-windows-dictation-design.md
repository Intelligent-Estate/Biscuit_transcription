# Biscuit Windows Dictation Design

## Purpose

Biscuit is a small Windows tool that adds speech-to-text where the user is already working. When the user right-clicks in a window, Biscuit shows a compact topmost `biscuit` action at the cursor. Clicking it starts recording, shows a small recording control, transcribes locally with an existing Whisper-compatible model, and inserts the text into the target window.

The first build is Windows-first, lightweight, and model-external. It must not copy large model files into this repository. It should reference the model already present in the user's AI bio project when that path is known, and otherwise let the user select a model path in settings.

## User Experience

1. Biscuit starts as a background tray-style utility.
2. On right-click, Biscuit records the cursor position, active window handle, and foreground window title.
3. Biscuit shows a small topmost menu near the cursor with a microphone mark and the word `biscuit`.
4. Selecting `biscuit` closes normal context clutter, opens a recording pill, and begins microphone capture.
5. The recording pill shows status and a clear stop action.
6. When stopped, Biscuit transcribes audio locally and inserts the resulting text into the last clicked target.
7. A small control panel exposes:
   - Model path
   - Language
   - Update/refresh model state
   - Start Biscuit
   - Kill Biscuit

## Visual Direction

The interface follows the Cenedril/Gundam theme used in neighboring projects:

- Blue-black base: deep navy and gunmetal panels.
- Yellow top accent: a sharp yellow stripe along the top of the action menu and control panel.
- Compact, tool-like surfaces; no marketing page, no decorative clutter.
- `biscuit` text is visible on the overlay action, paired with a microphone glyph.
- Status colors are functional: yellow for ready/listening, red for recording, cyan for processing, green for inserted.

## Architecture

Biscuit is a Python 3.10 Windows desktop utility using standard library UI and Win32 calls through `ctypes` plus already-installed local speech packages when present.

Core modules:

- `src/biscuit/config.py`: load/save settings, discover likely external model paths, keep defaults small.
- `src/biscuit/win32_api.py`: low-level Windows helpers for foreground windows, cursor position, Unicode text injection, Escape key cleanup, and optional mouse hook.
- `src/biscuit/overlay.py`: tiny topmost right-click action and recording pill using Tkinter.
- `src/biscuit/audio.py`: microphone capture to temporary WAV with `sounddevice` first, `pyaudio` fallback.
- `src/biscuit/transcription.py`: local transcription provider with external executable, `faster_whisper`, and `whisper` fallbacks.
- `src/biscuit/app.py`: application coordinator and settings panel.
- `tests/`: focused tests for config, text cleanup, provider selection, and safe command construction.

The first implementation uses a global right-click listener and overlay menu, not invasive menu injection. Windows applications own their own context menus; injecting into every application's private menu is fragile. The overlay gives the user the same workflow with a reliable path: right-click, choose Biscuit, speak, insert.

## Model Strategy

Biscuit must not import large objects into this repository.

Model resolution order:

1. User-configured `model_path` in `config/biscuit.json`.
2. A discovered model under `C:\Users\marsh\Documents\ai bio`.
3. A small known local model name if a Python transcription package can resolve it from existing cache.
4. A clear settings warning asking for a model path.

Preferred target is a tiny quantized Whisper-compatible model under 50 MiB when available. The design also accepts larger existing local models because the user specifically wants to reuse the AI bio model.

## Dictation Flow

1. `RightClickContext` captures `x`, `y`, `hwnd`, `window_title`, and timestamp.
2. Overlay appears at `x`, `y`.
3. User clicks `biscuit`.
4. Biscuit sends Escape once to dismiss a host context menu if one opened.
5. Recorder starts and writes PCM WAV to a temp file.
6. User clicks Stop in the recording pill.
7. Transcriber runs locally and returns normalized text.
8. Biscuit restores focus to the captured window and inserts Unicode text via `SendInput`.
9. Temp audio is deleted unless debug retention is enabled.

## Error Handling

- No microphone backend: show settings/status message with the missing backend.
- No model found: open settings and highlight model path.
- Transcription failure: keep the recording pill open with the error and do not insert empty text.
- Target window gone: place text on clipboard and show `Copied` status.
- Text insertion blocked by Windows integrity rules: place text on clipboard and show a clear fallback message.

## Packaging

The repository should ship a runnable source build first:

- `scripts/run_biscuit.ps1` starts the tool with local Python.
- `requirements.txt` lists optional speech/UI packages already expected on this machine.
- `scripts/package_biscuit.ps1` uses PyInstaller when available to build `dist/Biscuit/Biscuit.exe`.

Large model files remain external and are never committed.

## Verification

Minimum verification for this build:

- Python compile check for all source files.
- Unit tests for config discovery and transcription command handling.
- Manual launch smoke test for settings UI import/startup.
- No model blobs or temp audio committed.

## Research Notes

- `whisper.cpp` supports small quantized models and CPU-only local transcription.
- The public model listing for `ggerganov/whisper.cpp` includes `tiny.en-q5_1` at 31 MiB and `tiny.en-q8_0` at 42 MiB.
- Windows `SendInput` supports Unicode packet input and is the correct fallback-friendly insertion path for focused desktop apps.
- Windows low-level mouse hooks can observe right-click events across the active desktop, but global hooks are shared resources and must be kept small and removable.
- UI Automation can discover and manipulate many text controls, but the first build keeps insertion simpler with focus restoration plus Unicode input.
