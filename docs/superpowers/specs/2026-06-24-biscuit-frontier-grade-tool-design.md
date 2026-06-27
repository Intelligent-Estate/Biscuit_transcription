# Biscuit Frontier-Grade Tool Design

## Purpose

Biscuit is a lightweight local dictation instrument for trained professionals. Its job is narrow and important: turn the user's deliberate voice input into text inside the window they already chose.

The next frontier-grade step is not to make Biscuit larger. It is to make the core loop more dependable under real desktop conditions while preserving a tiny surface, local-first transcription, and fast startup behavior.

## Current Evidence

The current project already has:

- A Windows-first tray and context-menu dictation flow.
- A compact overlay and recording pill.
- Local/cached speech model support with external provider fallbacks.
- Model warmup and default hosted model source.
- Clipboard fallback when insertion fails.
- Installer, launcher, package, and dependency tests.
- A green unit suite covering app flow, focus, config, installers, overlay, transcription, launchers, and tray behavior.

## Design Principle

Biscuit should feel like a field tool, not a platform.

Every added capability must pass three gates:

1. **Does it make voice-to-window more reliable, faster, or clearer?**
2. **Does it avoid adding heavy runtime state or visual clutter?**
3. **Can it be verified with focused tests or direct runtime evidence?**

If the answer is no, it does not belong in this pass.

## Recommended Direction

Use a reliability-first core with speed improvements that naturally fall out of that work.

This beats a pure speed pass because fast failure is still failure. It also beats a broad power pass because extra modes, settings, and providers can make the tool heavier before the core loop is proven under pressure.

## Frontier References

Current edge speech work favors:

- Quantized and int8 local inference for lower memory and CPU load.
- Warmed model state to reduce first-use latency.
- Voice activity or silence filtering to avoid wasted decode work.
- Bounded audio processing rather than unbounded session state.
- Simple fallback paths when the target environment blocks direct insertion.

Biscuit should adopt these patterns only where they keep the tool small. The default remains a tiny local/cached transcription path, not a heavy command center.

## Target Behavior

### Ready Path

Biscuit should be able to tell whether the core parts are ready:

- Listener or invocation path is active.
- Microphone backend can start.
- Transcription provider can resolve the selected model.
- Target context exists when dictation starts.
- Text insertion has a fallback if direct typing is blocked.

This readiness state should remain compact. It can appear in the settings status line or be exposed through small pure functions for tests. It should not become a dashboard.

### Dictation Path

The main flow remains:

1. User invokes Biscuit from right-click, tray/menu-bar, launcher, or one-shot command.
2. Biscuit captures the active target context.
3. Biscuit starts recording and shows the small recording pill.
4. User stops recording.
5. Biscuit transcribes locally or through the configured local-compatible provider.
6. Biscuit restores the target and inserts text.
7. If insertion is blocked, Biscuit copies text to clipboard and reports the fallback.

### Failure Path

Biscuit should never fail silently during the core loop.

Expected failures should produce short, actionable statuses:

- Microphone unavailable.
- Model unavailable.
- Provider incompatible with model type.
- No speech found.
- Target missing.
- Direct insertion blocked, copied instead.

The status language should stay professional and compact.

## Lightweight Power

Biscuit's power should come from dependable composition:

- External model support, without storing model blobs in the repository.
- Provider detection that rejects incompatible combinations early.
- Cached model objects for repeated dictation.
- Optional backend silence filtering when available.
- Clipboard fallback as a deliberate recovery path.
- Source, launcher, installer, and package flows that stay aligned.

No new service, database, index, always-on transcript history, or large UI should be added in this pass.

## Proposed Components

### Readiness Probe

Add a small readiness layer that returns structured status for the main subsystems. It should be pure where possible and easy to test without starting Tkinter, microphone capture, or real transcription.

Suggested shape:

- Model/provider readiness from config and provider detection.
- Invocation readiness from hook/server/tray state.
- Insertion readiness based on target context presence.
- Microphone readiness through a light backend availability check, not actual long recording.

### Dictation Result

Represent the end of a dictation run with a small result object or enum-like value:

- `inserted`
- `copied`
- `no_speech`
- `microphone_error`
- `model_error`
- `transcription_error`
- `target_error`

This makes behavior clearer and tests stronger without changing the visible UI much.

### Status Mapping

Keep UI status strings centralized so tests can verify that each result maps to one short user-facing message.

This reduces scattered text and prevents vague or playful statuses from replacing operational feedback.

### Speed-Preserving Transcription

Keep current model warmup. Continue using int8 CPU settings for the faster local Python backend. Keep silence filtering enabled where the backend supports it. Do not add a larger default model.

Any additional tuning should be optional and should not add mandatory downloads beyond the current default model source.

## Data And Trust

Biscuit should continue to avoid retaining recordings by default. Temporary audio should be removed after transcription unless the user explicitly enables debug retention.

The trust surface remains:

- Microphone only while recording.
- Selected model/provider.
- Captured target window.
- Clipboard fallback only when needed.
- Local config file for settings.

No transcript archive is introduced in this design.

## Tests

Add focused tests for:

- Readiness probe with ready and not-ready model/provider states.
- Dictation result mapping to status strings.
- Clipboard fallback result when insertion fails.
- No target context path.
- Microphone/model/transcription error classification.
- Existing one-shot request behavior still routing to the running app.

Existing tests for launchers, installers, package metadata, overlay geometry, provider detection, and model prefetch remain part of the verification gate.

## Verification Gates

Before this pass is considered complete:

- Unit tests pass.
- Compile check passes.
- Import smoke test passes.
- No model/audio artifacts are tracked.
- README and ontology still describe the actual tool.
- Manual Windows launch path is either verified or explicitly recorded as not verified in the final report.

## Out Of Scope

This pass does not add:

- Transcript history.
- Multi-user profiles.
- Heavy command automation.
- Network speech services as a required path.
- Large bundled models.
- A full dashboard.
- Document indexing.

These can be reconsidered only if they directly serve the voice-to-window mission without making the tool heavy.

## Success Standard

Biscuit is frontier-grade for this pass when the user can trust that a deliberate dictation attempt will either place text in the selected window or clearly recover with copied text and an accurate status, while keeping the application small, local-first, and fast enough for repeated professional use.
