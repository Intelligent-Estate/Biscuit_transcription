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


def check_invocation_readiness(
    listener_running: bool,
    request_server_running: bool,
    tray_available: bool,
) -> ReadinessState:
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
