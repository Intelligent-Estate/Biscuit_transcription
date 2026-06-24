"""Fetch Biscuit's default speech model into the local Hugging Face cache."""

from __future__ import annotations

from biscuit.config import DEFAULT_MODEL_SOURCE


def main() -> None:
    try:
        from huggingface_hub import snapshot_download
    except Exception as exc:
        raise SystemExit(f"huggingface-hub is required to fetch {DEFAULT_MODEL_SOURCE}: {exc}") from exc

    path = snapshot_download(repo_id=DEFAULT_MODEL_SOURCE)
    print(f"Biscuit model ready: {DEFAULT_MODEL_SOURCE}")
    print(path)


if __name__ == "__main__":
    main()
