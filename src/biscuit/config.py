"""Configuration and external model discovery for Biscuit."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import json
import os
from pathlib import Path
from typing import Iterable


APP_NAME = "Biscuit"
MODEL_EXTENSIONS = {".bin", ".gguf", ".pt"}
SPEECH_MODEL_MARKERS = ("whisper", "ggml")
DEFAULT_MODEL_SOURCE = "Systran/faster-whisper-tiny.en"
DEFAULT_WHISPER_CACHE_ROOT = Path.home() / ".cache" / "whisper"
DEFAULT_MODEL_ROOTS = (DEFAULT_WHISPER_CACHE_ROOT,)
SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    "node_modules",
    "site-packages",
    "venv",
    ".venv",
    "Lib",
    "go",
}


@dataclass(slots=True)
class BiscuitConfig:
    model_path: str = ""
    language: str = "en"
    provider: str = "auto"
    sample_rate: int = 16000
    keep_debug_audio: bool = False


def default_config_path() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / APP_NAME / "biscuit.json"
    return Path.cwd() / "config" / "biscuit.json"


def load_config(path: Path | None = None) -> BiscuitConfig:
    config_path = path or default_config_path()
    if not config_path.exists():
        return BiscuitConfig(model_path=DEFAULT_MODEL_SOURCE)

    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    defaults = asdict(BiscuitConfig())
    defaults.update({key: value for key, value in payload.items() if key in defaults})
    return BiscuitConfig(**defaults)


def save_config(path: Path | None, config: BiscuitConfig) -> None:
    config_path = path or default_config_path()
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with config_path.open("w", encoding="utf-8") as handle:
        json.dump(asdict(config), handle, indent=2)
        handle.write("\n")


def discover_model_candidates(root: Path | None = None, max_depth: int = 6) -> list[Path]:
    if root is None:
        candidates: list[Path] = []
        for model_root in DEFAULT_MODEL_ROOTS:
            candidates.extend(discover_model_candidates(model_root, max_depth=max_depth))
        return candidates

    if not root.exists():
        return []

    candidates: list[Path] = []
    root = root.resolve()
    for current, dirs, files in os.walk(root):
        current_path = Path(current)
        try:
            relative_depth = len(current_path.relative_to(root).parts)
        except ValueError:
            relative_depth = 0

        dirs[:] = [
            directory
            for directory in dirs
            if directory not in SKIP_DIRS and relative_depth < max_depth
        ]

        for filename in files:
            path = current_path / filename
            if is_supported_model_path(path):
                candidates.append(path)

    return candidates


def choose_best_model(paths: Iterable[Path]) -> Path | None:
    existing = [path for path in paths if path.exists() and is_supported_model_path(path)]
    if not existing:
        return None

    def score(path: Path) -> tuple[int, int, int, str]:
        name = path.name.lower()
        size = path.stat().st_size
        tiny_bonus = 0 if "tiny" in name else 1
        quant_bonus = 0 if any(token in name for token in ("q4", "q5", "q8", "int8")) else 1
        return (tiny_bonus, quant_bonus, size, name)

    return sorted(existing, key=score)[0]


def is_supported_model_path(path: Path) -> bool:
    suffix = path.suffix.lower()
    if suffix not in MODEL_EXTENSIONS:
        return False
    if suffix == ".pt":
        return True
    lowered = path.as_posix().lower()
    return any(marker in lowered for marker in SPEECH_MODEL_MARKERS)
