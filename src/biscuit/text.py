"""Transcript cleanup utilities."""

from __future__ import annotations

import re


def normalize_transcript(text: str) -> str:
    """Return user-ready text without changing meaning."""
    return re.sub(r"\s+", " ", text or "").strip()
