"""Release/package checks that avoid starting the desktop UI."""

from __future__ import annotations

import importlib.util


def release_self_check() -> tuple[bool, list[str]]:
    lines: list[str] = []
    required_modules = ("faster_whisper", "huggingface_hub", "PIL", "pystray")
    for module in required_modules:
        if importlib.util.find_spec(module):
            lines.append(f"found {module}")
        else:
            lines.append(f"missing {module}")

    audio_modules = ("sounddevice", "pyaudio")
    if any(importlib.util.find_spec(module) for module in audio_modules):
        lines.append("found sounddevice or pyaudio")
    else:
        lines.append("missing sounddevice or pyaudio")

    ok = not any(line.startswith("missing ") for line in lines)
    return ok, lines
