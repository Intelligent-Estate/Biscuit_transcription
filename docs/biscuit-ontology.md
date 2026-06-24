# Biscuit Ontology

Biscuit is a small local bridge between a professional's voice and the window they already chose.

![How Biscuit Runs](biscuit-ontology.svg)

## The Simple Model

- **User**: chooses when Biscuit acts through the right-click action, tray/menu-bar item, or launcher.
- **Context**: the target window and cursor location captured at the moment the user asks for dictation.
- **Overlay**: the tiny visible control that starts and stops the dictation run.
- **Recorder**: the microphone worker that writes one temporary WAV for the active recording.
- **Speech Model**: the selected local or cached speech backend that turns the WAV into text.
- **Inserter**: the desktop bridge that restores focus and types the finished text into the target window.
- **Fallback**: the clipboard path used when direct insertion is blocked by the desktop.
- **Settings**: the user-controlled place for model, language, and provider choices.

## Run Path

1. The user chooses Biscuit.
2. Biscuit captures the active target.
3. The user records speech.
4. The selected speech model produces text.
5. Biscuit inserts the text into the target window.
6. If insertion is blocked, Biscuit copies the text to the clipboard.

## Trust Surface

Biscuit is intentionally narrow. Its core loop touches the microphone while recording, the selected target window for insertion, the configured model path/provider, and the clipboard only as a fallback.

Biscuit reports readiness for the listener/invocation path, microphone backend, model/provider, and captured target. These checks do not add transcript storage or a background document index.

It does not ship large model files in the repository. It does not need a document index to work. It does not keep recording after the user stops the run.
