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
