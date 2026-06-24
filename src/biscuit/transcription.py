"""Local transcription provider selection and execution."""

from __future__ import annotations

from dataclasses import dataclass
import importlib.util
from pathlib import Path
import shutil
import subprocess
import tempfile

from .text import normalize_transcript


class TranscriptionError(RuntimeError):
    """Raised when local transcription cannot complete."""


@dataclass(frozen=True, slots=True)
class ProviderChoice:
    name: str
    executable: str = ""


_MODEL_CACHE: dict[tuple[str, str], object] = {}


def build_external_command(
    provider: ProviderChoice,
    model_path: Path,
    audio_path: Path,
    language: str,
) -> list[str]:
    executable = provider.executable
    lowered = Path(executable).name.lower()
    model = model_path.as_posix()
    audio = audio_path.as_posix()

    if "whisper-cli" in lowered or "main.exe" == lowered:
        return [executable, "-m", model, "-f", audio, "-l", language, "-otxt"]

    return [
        executable,
        audio,
        "--model",
        model,
        "--language",
        language,
        "--output_format",
        "txt",
    ]


def detect_provider(preferred: str = "auto", model_path: Path | None = None) -> ProviderChoice:
    suffix = model_path.suffix.lower() if model_path else ""
    needs_gguf_runner = suffix in {".gguf", ".bin"}
    needs_whisper_loader = suffix == ".pt"

    if preferred and preferred != "auto":
        executable = shutil.which(preferred)
        if executable:
            return ProviderChoice(name="external", executable=executable)
        preferred_path = Path(preferred)
        if preferred_path.exists() and preferred_path.suffix.lower() == ".exe":
            return ProviderChoice(name="external", executable=str(preferred_path))
        if importlib.util.find_spec(preferred):
            return ProviderChoice(name=preferred)

    for executable_name in ("whisper-cli", "whisper-cli.exe", "main.exe"):
        executable = shutil.which(executable_name)
        if executable:
            return ProviderChoice(name="external", executable=executable)

    if needs_whisper_loader and importlib.util.find_spec("whisper"):
        return ProviderChoice(name="whisper")
    if needs_whisper_loader:
        raise TranscriptionError("PT models need the local whisper Python package.")
    if needs_gguf_runner:
        raise TranscriptionError("GGUF/GGML models need a whisper.cpp runner such as whisper-cli.exe.")

    if importlib.util.find_spec("faster_whisper"):
        return ProviderChoice(name="faster_whisper")
    if importlib.util.find_spec("whisper"):
        return ProviderChoice(name="whisper")

    raise TranscriptionError("No local transcription backend found.")


def transcribe_audio(
    audio_path: Path,
    model_path: Path,
    language: str = "en",
    provider: str = "auto",
) -> str:
    choice = detect_provider(provider, model_path)
    if choice.name == "external":
        return _transcribe_external(choice, model_path, audio_path, language)
    if choice.name == "faster_whisper":
        return _transcribe_faster_whisper(model_path, audio_path, language)
    if choice.name == "whisper":
        return _transcribe_whisper(model_path, audio_path, language)
    raise TranscriptionError(f"Unsupported transcription provider: {choice.name}")


def warm_transcription_model(model_path: Path, provider: str = "auto") -> None:
    choice = detect_provider(provider, model_path)
    if choice.name == "faster_whisper":
        _get_faster_whisper_model(model_path)
        return
    if choice.name == "whisper":
        _get_whisper_model(model_path)


def _hidden_subprocess_options() -> dict[str, object]:
    options: dict[str, object] = {}
    if hasattr(subprocess, "CREATE_NO_WINDOW"):
        options["creationflags"] = subprocess.CREATE_NO_WINDOW
    if hasattr(subprocess, "STARTUPINFO"):
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        options["startupinfo"] = startupinfo
    return options


def _transcribe_external(
    choice: ProviderChoice,
    model_path: Path,
    audio_path: Path,
    language: str,
) -> str:
    command = build_external_command(choice, model_path, audio_path, language)
    with tempfile.TemporaryDirectory(prefix="biscuit-transcribe-") as output_dir:
        if "--output_format" in command:
            command.extend(["--output_dir", output_dir])
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            timeout=180,
            **_hidden_subprocess_options(),
        )
        if result.returncode != 0:
            message = result.stderr.strip() or result.stdout.strip() or "transcription failed"
            raise TranscriptionError(message)

        txt_files = sorted(Path(output_dir).glob("*.txt"))
        if txt_files:
            return normalize_transcript(txt_files[0].read_text(encoding="utf-8", errors="ignore"))

        sidecar = audio_path.with_suffix(".txt")
        if sidecar.exists():
            try:
                return normalize_transcript(sidecar.read_text(encoding="utf-8", errors="ignore"))
            finally:
                sidecar.unlink(missing_ok=True)

        return normalize_transcript(result.stdout)


def _transcribe_faster_whisper(model_path: Path, audio_path: Path, language: str) -> str:
    try:
        from faster_whisper import WhisperModel
    except Exception as exc:  # pragma: no cover - backend availability varies.
        raise TranscriptionError(str(exc)) from exc

    model = _get_faster_whisper_model(model_path)
    segments, _info = model.transcribe(str(audio_path), language=language, vad_filter=True)
    return normalize_transcript(" ".join(segment.text for segment in segments))


def _transcribe_whisper(model_path: Path, audio_path: Path, language: str) -> str:
    try:
        import whisper
    except Exception as exc:  # pragma: no cover - backend availability varies.
        raise TranscriptionError(str(exc)) from exc

    model = _get_whisper_model(model_path)
    result = model.transcribe(str(audio_path), language=language)
    return normalize_transcript(result.get("text", ""))


def _get_faster_whisper_model(model_path: Path) -> object:
    from faster_whisper import WhisperModel

    key = ("faster_whisper", str(model_path))
    model = _MODEL_CACHE.get(key)
    if model is None:
        model = WhisperModel(str(model_path), device="cpu", compute_type="int8")
        _MODEL_CACHE[key] = model
    return model


def _get_whisper_model(model_path: Path) -> object:
    import whisper

    key = ("whisper", str(model_path))
    model = _MODEL_CACHE.get(key)
    if model is None:
        model = whisper.load_model(str(model_path))
        _MODEL_CACHE[key] = model
    return model
