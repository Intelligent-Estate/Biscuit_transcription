# Biscuit Frontier-Grade Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Biscuit more dependable under real desktop dictation conditions while keeping it lightweight, local-first, and fast for repeated professional use.

**Architecture:** Add two small pure modules: `status.py` owns dictation result classification and user-facing status text, while `readiness.py` owns compact readiness probes for model/provider, invocation, insertion, and microphone backend availability. Wire those modules into `app.py` without adding persistent services, transcript history, large UI, or mandatory model downloads.

**Tech Stack:** Python 3.10 standard library, dataclasses, enums, Tkinter app coordinator, existing optional audio/transcription backends, `unittest`.

---

## File Structure

- Create `src/biscuit/status.py`: `DictationResult` enum, `DictationOutcome` dataclass, and centralized status text mapping.
- Create `src/biscuit/readiness.py`: pure readiness dataclasses and probe functions.
- Modify `src/biscuit/audio.py`: expose microphone backend availability without starting a recording.
- Modify `src/biscuit/app.py`: classify dictation completion through `DictationOutcome`, use readiness summary for settings status, and keep clipboard fallback explicit.
- Modify `src/biscuit/overlay.py`: update finished-status recognition to use centralized status text.
- Create `tests/test_status.py`: result classification and status string tests.
- Create `tests/test_readiness.py`: readiness probe tests without Tkinter, real microphone capture, or real transcription.
- Modify `tests/test_app_focus.py`: verify insertion failure becomes copied fallback outcome.
- Modify `tests/test_app_menu_flow.py`: update lifecycle status expectations from playful language to operational language.
- Modify `README.md` and `docs/biscuit-ontology.md`: keep public docs aligned with readiness/fallback behavior.

## Task 1: Central Dictation Status

**Files:**
- Create: `src/biscuit/status.py`
- Create: `tests/test_status.py`
- Modify: `src/biscuit/overlay.py`

- [ ] **Step 1: Write the failing status tests**

Create `tests/test_status.py`:

```python
import unittest

from biscuit.status import DictationOutcome, DictationResult, status_text


class DictationStatusTests(unittest.TestCase):
    def test_status_text_is_short_and_operational(self):
        expected = {
            DictationResult.INSERTED: "inserted",
            DictationResult.COPIED: "copied to clipboard",
            DictationResult.NO_SPEECH: "no speech found",
            DictationResult.MICROPHONE_ERROR: "microphone unavailable",
            DictationResult.MODEL_ERROR: "model unavailable",
            DictationResult.TRANSCRIPTION_ERROR: "transcription failed",
            DictationResult.TARGET_ERROR: "target unavailable",
        }
        for result, text in expected.items():
            with self.subTest(result=result):
                self.assertEqual(status_text(DictationOutcome(result)), text)

    def test_status_text_keeps_detail_when_it_helps_action(self):
        outcome = DictationOutcome(DictationResult.MODEL_ERROR, "GGUF/GGML models need a runner")
        self.assertEqual(status_text(outcome), "model unavailable: GGUF/GGML models need a runner")

    def test_status_text_truncates_long_detail(self):
        outcome = DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, "x" * 120)
        text = status_text(outcome)
        self.assertTrue(text.startswith("transcription failed: "))
        self.assertLessEqual(len(text), 96)
        self.assertTrue(text.endswith("..."))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run the new status tests to verify failure**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_status -v
```

Expected: `ModuleNotFoundError: No module named 'biscuit.status'`.

- [ ] **Step 3: Implement the status module**

Create `src/biscuit/status.py`:

```python
"""Operational dictation outcomes and user-facing status text."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DictationResult(str, Enum):
    INSERTED = "inserted"
    COPIED = "copied"
    NO_SPEECH = "no_speech"
    MICROPHONE_ERROR = "microphone_error"
    MODEL_ERROR = "model_error"
    TRANSCRIPTION_ERROR = "transcription_error"
    TARGET_ERROR = "target_error"


@dataclass(frozen=True, slots=True)
class DictationOutcome:
    result: DictationResult
    detail: str = ""


BASE_STATUS_TEXT = {
    DictationResult.INSERTED: "inserted",
    DictationResult.COPIED: "copied to clipboard",
    DictationResult.NO_SPEECH: "no speech found",
    DictationResult.MICROPHONE_ERROR: "microphone unavailable",
    DictationResult.MODEL_ERROR: "model unavailable",
    DictationResult.TRANSCRIPTION_ERROR: "transcription failed",
    DictationResult.TARGET_ERROR: "target unavailable",
}

MAX_STATUS_LENGTH = 96


def status_text(outcome: DictationOutcome) -> str:
    base = BASE_STATUS_TEXT[outcome.result]
    detail = outcome.detail.strip()
    if not detail:
        return base
    text = f"{base}: {detail}"
    if len(text) <= MAX_STATUS_LENGTH:
        return text
    return text[: MAX_STATUS_LENGTH - 3].rstrip() + "..."
```

- [ ] **Step 4: Teach the overlay which centralized statuses are finished**

Modify the import area of `src/biscuit/overlay.py`:

```python
from .config import BiscuitConfig
from .desktop import RightClickContext, raise_overlay_window
from .status import DictationOutcome, DictationResult, status_text
```

Replace `FINISHED_RECORDING_STATUSES` with:

```python
FINISHED_RECORDING_STATUSES = {
    status_text(DictationOutcome(DictationResult.COPIED)),
    status_text(DictationOutcome(DictationResult.INSERTED)),
    status_text(DictationOutcome(DictationResult.NO_SPEECH)),
}
```

Update the finished-state check inside `recording_control_state`:

```python
    if status in FINISHED_RECORDING_STATUSES or status.startswith("microphone unavailable") or status.startswith("model unavailable") or status.startswith("transcription failed") or status.startswith("target unavailable"):
```

- [ ] **Step 5: Run focused status and overlay tests**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_status tests.test_overlay -v
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit Task 1**

Run:

```powershell
git add src/biscuit/status.py src/biscuit/overlay.py tests/test_status.py
git commit -m "feat: centralize Biscuit dictation status"
```

## Task 2: Lightweight Readiness Probe

**Files:**
- Create: `src/biscuit/readiness.py`
- Create: `tests/test_readiness.py`
- Modify: `src/biscuit/audio.py`

- [ ] **Step 1: Write failing readiness tests**

Create `tests/test_readiness.py`:

```python
import unittest
from pathlib import Path
from unittest import mock

from biscuit.config import BiscuitConfig
from biscuit.desktop import RightClickContext
from biscuit.readiness import (
    ReadinessState,
    check_insertion_readiness,
    check_microphone_readiness,
    check_model_readiness,
    summarize_readiness,
)
from biscuit.transcription import ProviderChoice, TranscriptionError


class ReadinessTests(unittest.TestCase):
    def test_model_readiness_reports_ready_provider(self):
        with mock.patch("biscuit.readiness.detect_provider", return_value=ProviderChoice("faster_whisper")):
            state = check_model_readiness(BiscuitConfig(model_path="Systran/faster-whisper-tiny.en"))
        self.assertEqual(state.name, "model")
        self.assertTrue(state.ready)
        self.assertEqual(state.detail, "faster_whisper")

    def test_model_readiness_reports_missing_local_file(self):
        state = check_model_readiness(BiscuitConfig(model_path="C:/missing/model.gguf"))
        self.assertFalse(state.ready)
        self.assertEqual(state.detail, "selected model file is missing")

    def test_model_readiness_reports_provider_error(self):
        with mock.patch("biscuit.readiness.detect_provider", side_effect=TranscriptionError("bad provider")):
            state = check_model_readiness(BiscuitConfig(model_path="Systran/faster-whisper-tiny.en"))
        self.assertFalse(state.ready)
        self.assertEqual(state.detail, "bad provider")

    def test_insertion_readiness_reports_target_presence(self):
        context = RightClickContext(x=1, y=2, hwnd=3, title="Editor", captured_at=4.0)
        self.assertTrue(check_insertion_readiness(context).ready)
        self.assertFalse(check_insertion_readiness(None).ready)

    def test_microphone_readiness_uses_backend_probe(self):
        with mock.patch("biscuit.readiness.available_audio_backends", return_value=["sounddevice"]):
            state = check_microphone_readiness()
        self.assertEqual(state, ReadinessState("microphone", True, "sounddevice"))

    def test_microphone_readiness_reports_missing_backend(self):
        with mock.patch("biscuit.readiness.available_audio_backends", return_value=[]):
            state = check_microphone_readiness()
        self.assertFalse(state.ready)
        self.assertEqual(state.detail, "no microphone backend")

    def test_summarize_readiness_counts_ready_parts(self):
        states = [
            ReadinessState("model", True, "faster_whisper"),
            ReadinessState("microphone", False, "no microphone backend"),
            ReadinessState("target", True, "Editor"),
        ]
        self.assertEqual(summarize_readiness(states), "ready 2/3; microphone: no microphone backend")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run readiness tests to verify failure**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_readiness -v
```

Expected: `ModuleNotFoundError: No module named 'biscuit.readiness'`.

- [ ] **Step 3: Add a no-capture audio backend probe**

Modify `src/biscuit/audio.py` after `RecordingResult`:

```python
def available_audio_backends() -> list[str]:
    backends: list[str] = []
    try:
        import sounddevice  # noqa: F401

        backends.append("sounddevice")
    except Exception:
        pass
    try:
        import pyaudio  # noqa: F401

        backends.append("pyaudio")
    except Exception:
        pass
    return backends
```

- [ ] **Step 4: Implement readiness module**

Create `src/biscuit/readiness.py`:

```python
"""Compact readiness probes for Biscuit's core dictation path."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .audio import available_audio_backends
from .config import BiscuitConfig
from .desktop import RightClickContext
from .transcription import TranscriptionError, detect_provider


@dataclass(frozen=True, slots=True)
class ReadinessState:
    name: str
    ready: bool
    detail: str


def is_hugging_face_model_id(source: str) -> bool:
    if "\\" in source or source.startswith(("/", ".")):
        return False
    if len(source) > 2 and source[1:3] == ":/":
        return False
    parts = source.split("/")
    return len(parts) == 2 and all(parts)


def check_model_readiness(config: BiscuitConfig) -> ReadinessState:
    source = config.model_path.strip()
    if not source:
        return ReadinessState("model", False, "no model selected")
    if not is_hugging_face_model_id(source):
        path = Path(source)
        if path.suffix and not path.exists():
            return ReadinessState("model", False, "selected model file is missing")
    try:
        provider = detect_provider(config.provider, None if is_hugging_face_model_id(source) else source)
    except TranscriptionError as exc:
        return ReadinessState("model", False, str(exc))
    return ReadinessState("model", True, provider.name)


def check_microphone_readiness() -> ReadinessState:
    backends = available_audio_backends()
    if not backends:
        return ReadinessState("microphone", False, "no microphone backend")
    return ReadinessState("microphone", True, backends[0])


def check_insertion_readiness(context: RightClickContext | None) -> ReadinessState:
    if context is None:
        return ReadinessState("target", False, "no target captured")
    title = context.title.strip() or "captured window"
    return ReadinessState("target", True, title)


def check_invocation_readiness(listener_running: bool, request_server_running: bool, tray_available: bool) -> ReadinessState:
    if listener_running:
        return ReadinessState("invocation", True, "listener")
    if request_server_running:
        return ReadinessState("invocation", True, "request server")
    if tray_available:
        return ReadinessState("invocation", True, "tray")
    return ReadinessState("invocation", False, "no invocation path active")


def summarize_readiness(states: Iterable[ReadinessState]) -> str:
    items = list(states)
    ready_count = sum(1 for state in items if state.ready)
    failures = [f"{state.name}: {state.detail}" for state in items if not state.ready]
    base = f"ready {ready_count}/{len(items)}"
    if not failures:
        return base
    return f"{base}; {'; '.join(failures)}"
```

- [ ] **Step 5: Run readiness and audio-adjacent tests**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_readiness tests.test_app_cli -v
```

Expected: all selected tests pass.

- [ ] **Step 6: Commit Task 2**

Run:

```powershell
git add src/biscuit/audio.py src/biscuit/readiness.py tests/test_readiness.py
git commit -m "feat: add Biscuit readiness probes"
```

## Task 3: Wire Outcomes Into The App Core

**Files:**
- Modify: `src/biscuit/app.py`
- Modify: `tests/test_app_focus.py`
- Modify: `tests/test_app_menu_flow.py`

- [ ] **Step 1: Write failing app outcome tests**

Append to `tests/test_app_focus.py`:

```python
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from biscuit.app import finish_dictation_result
from biscuit.desktop import RightClickContext
from biscuit.status import DictationResult
from biscuit.transcription import TranscriptionError


class FinishDictationResultTests(unittest.TestCase):
    def test_finish_dictation_reports_no_speech(self):
        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=RightClickContext(1, 2, 3, "Editor", 4.0),
            transcribe=lambda _path: "",
            insert=lambda _context, _text: 4,
            copy=lambda _text: None,
        )
        self.assertEqual(outcome.result, DictationResult.NO_SPEECH)

    def test_finish_dictation_copies_when_target_missing(self):
        copied = []
        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=None,
            transcribe=lambda _path: "field note",
            insert=lambda _context, _text: 10,
            copy=copied.append,
        )
        self.assertEqual(outcome.result, DictationResult.COPIED)
        self.assertEqual(copied, ["field note"])

    def test_finish_dictation_copies_when_insert_fails(self):
        copied = []

        def fail_insert(_context, _text):
            raise OSError("blocked")

        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=RightClickContext(1, 2, 3, "Editor", 4.0),
            transcribe=lambda _path: "field note",
            insert=fail_insert,
            copy=copied.append,
        )
        self.assertEqual(outcome.result, DictationResult.COPIED)
        self.assertEqual(outcome.detail, "direct insertion blocked")
        self.assertEqual(copied, ["field note"])

    def test_finish_dictation_classifies_transcription_error(self):
        def fail_transcribe(_path):
            raise TranscriptionError("model missing")

        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=RightClickContext(1, 2, 3, "Editor", 4.0),
            transcribe=fail_transcribe,
            insert=lambda _context, _text: 4,
            copy=lambda _text: None,
        )
        self.assertEqual(outcome.result, DictationResult.TRANSCRIPTION_ERROR)
        self.assertEqual(outcome.detail, "model missing")
```

Replace the menu-flow kill status assertion in `tests/test_app_menu_flow.py` so it expects operational language:

```python
    def test_quit_biscuit_status_says_stopped(self):
        app = self.build_app()
        app.kill_biscuit()
        self.assertEqual(app.overlay.statuses[-1], "stopped")
```

- [ ] **Step 2: Run focused app tests to verify failure**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_app_focus tests.test_app_menu_flow -v
```

Expected: import failure for `finish_dictation_result` and one lifecycle status failure.

- [ ] **Step 3: Add app imports**

Modify imports in `src/biscuit/app.py`:

```python
from .readiness import (
    check_insertion_readiness,
    check_invocation_readiness,
    check_microphone_readiness,
    check_model_readiness,
    summarize_readiness,
)
from .status import DictationOutcome, DictationResult, status_text
```

- [ ] **Step 4: Add pure dictation finish helper**

Add below `insert_text_into_context` in `src/biscuit/app.py`:

```python
def finish_dictation_result(recording, context, transcribe, insert, copy) -> DictationOutcome:
    try:
        text = transcribe(recording.path)
    except TranscriptionError as exc:
        return DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, str(exc))
    if not text:
        return DictationOutcome(DictationResult.NO_SPEECH)
    if context is None:
        copy(text)
        return DictationOutcome(DictationResult.COPIED, "target unavailable")
    try:
        insert(context, text)
    except Exception:
        copy(text)
        return DictationOutcome(DictationResult.COPIED, "direct insertion blocked")
    return DictationOutcome(DictationResult.INSERTED)
```

- [ ] **Step 5: Use readiness summary for settings status**

Add this method to `BiscuitApp`:

```python
    def readiness_summary(self) -> str:
        states = [
            check_invocation_readiness(
                listener_running=self.hook.running,
                request_server_running=self._request_socket is not None,
                tray_available=self.tray.available,
            ),
            check_microphone_readiness(),
            check_model_readiness(self.config),
            check_insertion_readiness(self.last_context),
        ]
        return summarize_readiness(states)
```

Change `start_biscuit`:

```python
    def start_biscuit(self) -> None:
        self.hook.start()
        self.overlay.set_settings_status(self.readiness_summary())
```

Change `kill_biscuit`:

```python
    def kill_biscuit(self) -> None:
        self.hook.stop()
        self.overlay.close_action()
        self.overlay.close_recording()
        self.overlay.set_settings_status("stopped")
```

- [ ] **Step 6: Use outcome classification in `_finish_recording`**

Replace `_finish_recording` in `src/biscuit/app.py` with:

```python
    def _finish_recording(self) -> None:
        try:
            recording = self.recorder.stop()
            outcome = finish_dictation_result(
                recording=recording,
                context=self.last_context,
                transcribe=self._transcribe,
                insert=insert_text_into_context,
                copy=self._copy_to_clipboard,
            )
            self._ui_status(status_text(outcome))
        except RecordingError as exc:
            self._ui_status(status_text(DictationOutcome(DictationResult.MICROPHONE_ERROR, str(exc))))
            traceback.print_exc()
        except Exception as exc:
            self._ui_status(status_text(DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, str(exc))))
            traceback.print_exc()
        finally:
            self.root.after(900, self.overlay.close_recording)
            if self.exit_after_recording:
                self.root.after(1200, self.quit_app)
```

- [ ] **Step 7: Run focused app tests**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest tests.test_app_focus tests.test_app_menu_flow tests.test_status tests.test_readiness -v
```

Expected: all selected tests pass.

- [ ] **Step 8: Commit Task 3**

Run:

```powershell
git add src/biscuit/app.py tests/test_app_focus.py tests/test_app_menu_flow.py
git commit -m "feat: classify Biscuit dictation outcomes"
```

## Task 4: Documentation Alignment

**Files:**
- Modify: `README.md`
- Modify: `docs/biscuit-ontology.md`
- Test: existing documentation-adjacent tests through the full unit suite

- [ ] **Step 1: Update README runtime notes**

In `README.md`, update the notes that describe runtime behavior so they include:

```markdown
Biscuit now keeps a compact readiness view for the core path: invocation, microphone backend, selected model/provider, and captured target. The readiness view is intentionally small and appears as operational status rather than a dashboard.
```

Also update fallback wording so it says:

```markdown
When direct insertion is blocked or the target is gone, Biscuit copies the finished text to the clipboard and reports that fallback in the recording status.
```

- [ ] **Step 2: Update ontology trust surface**

In `docs/biscuit-ontology.md`, update the trust surface section so it includes:

```markdown
Biscuit reports readiness for the listener/invocation path, microphone backend, model/provider, and captured target. These checks do not add transcript storage or a background document index.
```

- [ ] **Step 3: Run full unit suite**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit Task 4**

Run:

```powershell
git add README.md docs/biscuit-ontology.md
git commit -m "docs: describe Biscuit readiness and fallback"
```

## Task 5: Final Verification

**Files:**
- Verify: source, tests, docs, repository status

- [ ] **Step 1: Run full unit tests**

Run:

```powershell
$env:PYTHONPATH='src'; python -m unittest discover -s tests -v
```

Expected: all tests pass.

- [ ] **Step 2: Run compile check**

Run:

```powershell
python -m compileall -q src\biscuit
```

Expected: exit code `0`.

- [ ] **Step 3: Run import smoke test**

Run:

```powershell
$env:PYTHONPATH='src'; python -c "from biscuit.app import BiscuitApp, finish_dictation_result; from biscuit.readiness import check_model_readiness; from biscuit.status import DictationResult; print('ok')"
```

Expected:

```text
ok
```

- [ ] **Step 4: Verify no model or audio artifacts are tracked**

Run:

```powershell
git status --short
```

Expected: no tracked or untracked paths ending in `.wav`, `.mp3`, `.bin`, `.gguf`, `.onnx`, `.pt`, or `.tflite` unless they are intentionally ignored outside the status output.

- [ ] **Step 5: Record manual launch status**

If Windows desktop launch is verified, record the successful launch path in the final report. If it is not verified during this run, state exactly that manual Windows launch was not verified.

- [ ] **Step 6: Final commit if any verification-only documentation changed**

Run only if a verification note file or README line changed during Task 5:

```powershell
git add README.md docs/biscuit-ontology.md
git commit -m "docs: record Biscuit verification status"
```

If no file changed during Task 5, do not create an empty commit.

## Self-Review

Spec coverage:

- Reliability-first core: Tasks 1, 2, and 3.
- Readiness path: Task 2 and Task 3.
- Dictation result object: Task 1 and Task 3.
- Centralized status mapping: Task 1.
- Clipboard fallback as explicit recovery: Task 3.
- Speed-preserving transcription: no code change needed because current `faster_whisper` path already uses CPU int8, VAD filtering, and model caching; Task 5 verifies the existing implementation still compiles and imports.
- Data and trust: Task 4 documents no transcript archive and no background index.
- Verification gates: Task 5.

Red-flag scan:

- The plan contains no deferred implementation language or unspecified edge handling.

Type consistency:

- `DictationOutcome`, `DictationResult`, and `status_text` are defined in Task 1 and used with the same names in Task 3.
- `ReadinessState`, `check_model_readiness`, `check_microphone_readiness`, `check_insertion_readiness`, `check_invocation_readiness`, and `summarize_readiness` are defined in Task 2 and used with the same names in Task 3.
