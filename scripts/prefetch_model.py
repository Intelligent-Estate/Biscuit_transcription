"""Fetch Biscuit's default speech model into the local Hugging Face cache."""

from __future__ import annotations

from biscuit.config import DEFAULT_MODEL_SOURCE
from biscuit.transcription import warm_transcription_model


def prefetch_default_model() -> str:
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise SystemExit(f"huggingface-hub is required to fetch {DEFAULT_MODEL_SOURCE}: {exc}") from exc

    path = snapshot_download(repo_id=DEFAULT_MODEL_SOURCE)
    warm_transcription_model(DEFAULT_MODEL_SOURCE)
    return str(path)


def main() -> None:
    path = prefetch_default_model()
    print(f"Biscuit model ready: {DEFAULT_MODEL_SOURCE}")
    print(path)


if __name__ == "__main__":
    main()
