# Biscuit Windows Dictation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Windows-first Biscuit dictation utility that shows a right-click overlay action, records speech, transcribes with an external local model, and inserts text into the clicked window.

**Architecture:** Python 3.10 package with small Win32 helpers, Tkinter overlays, pluggable local transcription providers, and source/package scripts. Large model files remain external and are referenced by path.

**Tech Stack:** Python standard library, Tkinter, `ctypes`, optional installed `sounddevice`, optional installed `pyaudio`, optional installed `faster_whisper`, optional installed `whisper`, optional PyInstaller.

---

## File Structure

- Create `src/biscuit/__init__.py`: package metadata.
- Create `src/biscuit/config.py`: settings, model discovery, JSON persistence.
- Create `src/biscuit/text.py`: transcript normalization.
- Create `src/biscuit/win32_api.py`: Windows right-click context, focus, Escape, Unicode insertion, mouse hook.
- Create `src/biscuit/audio.py`: recording worker and WAV output.
- Create `src/biscuit/transcription.py`: provider selection and transcription adapters.
- Create `src/biscuit/overlay.py`: topmost Biscuit menu, recorder pill, settings window.
- Create `src/biscuit/app.py`: coordinator.
- Create `src/biscuit/__main__.py`: module entrypoint.
- Create `tests/test_config.py`, `tests/test_text.py`, `tests/test_transcription.py`.
- Create `scripts/run_biscuit.ps1`, `scripts/package_biscuit.ps1`.
- Create `requirements.txt`, `.gitignore`, `README.md`.

### Task 1: Pure Config And Text Tests

**Files:**
- Create: `tests/test_config.py`
- Create: `tests/test_text.py`
- Create: `src/biscuit/__init__.py`
- Create: `src/biscuit/config.py`
- Create: `src/biscuit/text.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_text.py
from biscuit.text import normalize_transcript

def test_normalize_transcript_trims_and_collapses_space():
    assert normalize_transcript("  hello   biscuit \n") == "hello biscuit"

def test_normalize_transcript_keeps_empty_empty():
    assert normalize_transcript("   ") == ""
```

```python
# tests/test_config.py
from pathlib import Path
from biscuit.config import BiscuitConfig, choose_best_model, load_config, save_config

def test_config_round_trips_json(tmp_path):
    path = tmp_path / "biscuit.json"
    config = BiscuitConfig(model_path="C:/model.bin", language="en", provider="auto")
    save_config(path, config)
    assert load_config(path).model_path == "C:/model.bin"

def test_choose_best_model_prefers_small_quantized_file(tmp_path):
    big = tmp_path / "ggml-base.en.bin"
    small = tmp_path / "ggml-tiny.en-q5_1.bin"
    big.write_bytes(b"0" * 100)
    small.write_bytes(b"0" * 10)
    assert choose_best_model([big, small]) == small
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest discover -s tests -v`

Expected: FAIL or ERROR because `biscuit` modules do not exist yet.

- [ ] **Step 3: Implement config and text modules**

Create `BiscuitConfig`, JSON load/save, candidate model discovery under AI bio, and transcript normalization.

- [ ] **Step 4: Run tests to verify they pass**

Run: `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`

Expected: text/config tests pass.

### Task 2: Transcription Provider Tests

**Files:**
- Create: `tests/test_transcription.py`
- Create: `src/biscuit/transcription.py`

- [ ] **Step 1: Write failing tests**

```python
# tests/test_transcription.py
from pathlib import Path
from biscuit.transcription import build_external_command, ProviderChoice

def test_external_command_quotes_model_and_audio_paths():
    choice = ProviderChoice(name="external", executable="C:/Tools/whisper.exe")
    command = build_external_command(choice, Path("C:/Models/tiny.bin"), Path("C:/Temp/sample.wav"), "en")
    assert command[0] == "C:/Tools/whisper.exe"
    assert "C:/Models/tiny.bin" in command
    assert "C:/Temp/sample.wav" in command
    assert "en" in command
```

- [ ] **Step 2: Run tests to verify failure**

Run: `$env:PYTHONPATH='src'; python -m unittest tests.test_transcription -v`

Expected: FAIL or ERROR because `biscuit.transcription` does not exist.

- [ ] **Step 3: Implement provider module**

Implement provider detection for external executable, `faster_whisper`, and `whisper`. Return clear `TranscriptionError` messages when no backend is available.

- [ ] **Step 4: Run tests to verify pass**

Run: `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`

Expected: all unit tests pass.

### Task 3: Windows Shell And UI

**Files:**
- Create: `src/biscuit/win32_api.py`
- Create: `src/biscuit/audio.py`
- Create: `src/biscuit/overlay.py`
- Create: `src/biscuit/app.py`
- Create: `src/biscuit/__main__.py`

- [ ] **Step 1: Implement Win32 helpers**

Add `RightClickContext`, `get_foreground_context`, `set_foreground_window`, `send_escape`, `send_unicode_text`, and `MouseHook`.

- [ ] **Step 2: Implement recorder**

Add a `Recorder` class that starts a background capture and writes a WAV temp file on stop. Prefer `sounddevice`; fall back to `pyaudio`; raise a plain error if neither works.

- [ ] **Step 3: Implement overlays**

Add topmost Tkinter overlay action with blue-black/yellow styling, recording pill, and settings panel.

- [ ] **Step 4: Implement app coordinator**

Wire right-click context to overlay, overlay to recorder, recorder to transcriber, and transcribed text to `send_unicode_text`.

- [ ] **Step 5: Compile check**

Run: `python -m py_compile src/biscuit/*.py`

Expected: exit 0.

### Task 4: Scripts, Docs, Package Guardrails

**Files:**
- Create: `scripts/run_biscuit.ps1`
- Create: `scripts/package_biscuit.ps1`
- Create: `requirements.txt`
- Create: `.gitignore`
- Create: `README.md`

- [ ] **Step 1: Add run script**

Run script sets `PYTHONPATH=src` and launches `python -m biscuit`.

- [ ] **Step 2: Add package script**

Package script uses `pyinstaller` if present, excludes model/audio artifacts, and writes to `dist/Biscuit`.

- [ ] **Step 3: Add docs and ignore rules**

Ignore `dist/`, `build/`, `*.wav`, `*.mp3`, `*.bin`, `*.gguf`, `*.onnx`, `*.pt`, `*.tflite`, and local config.

- [ ] **Step 4: Verify no large model files are staged**

Run: `git status --short`

Expected: no model/audio artifacts listed.

### Task 5: Final Verification And Commit

**Files:**
- Modify: all implementation files above.

- [ ] **Step 1: Run unit tests**

Run: `$env:PYTHONPATH='src'; python -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 2: Run compile check**

Run: `python -m py_compile src/biscuit/*.py`

Expected: exit 0.

- [ ] **Step 3: Run import smoke test**

Run: `$env:PYTHONPATH='src'; python -c "from biscuit.app import BiscuitApp; print('ok')"`

Expected: prints `ok`.

- [ ] **Step 4: Commit implementation**

```bash
git add .gitignore README.md requirements.txt scripts src tests docs/superpowers/plans/2026-06-23-biscuit-windows-dictation.md
git commit -m "feat: build Biscuit Windows dictation shell"
```
