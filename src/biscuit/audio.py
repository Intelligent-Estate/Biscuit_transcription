"""Microphone recording worker."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import queue
import tempfile
import threading
import wave


class RecordingError(RuntimeError):
    """Raised when recording cannot start or stop cleanly."""


@dataclass(slots=True)
class RecordingResult:
    path: Path
    sample_rate: int
    seconds: float


class Recorder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        self.sample_rate = sample_rate
        self.channels = channels
        self._frames: queue.Queue[bytes] = queue.Queue()
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._backend = ""

    @property
    def recording(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def backend(self) -> str:
        return self._backend

    def start(self) -> None:
        if self.recording:
            return
        self._stop.clear()
        self._drain()
        self._thread = threading.Thread(target=self._capture, name="BiscuitRecorder", daemon=True)
        self._thread.start()

    def stop(self) -> RecordingResult:
        if not self._thread:
            raise RecordingError("Recording has not started.")
        self._stop.set()
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            raise RecordingError("Recorder did not stop cleanly.")

        frames: list[bytes] = []
        while not self._frames.empty():
            frames.append(self._frames.get())
        if not frames:
            raise RecordingError("No microphone audio was captured.")

        handle = tempfile.NamedTemporaryFile(prefix="biscuit-", suffix=".wav", delete=False)
        path = Path(handle.name)
        handle.close()

        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(self.channels)
            wav.setsampwidth(2)
            wav.setframerate(self.sample_rate)
            wav.writeframes(b"".join(frames))

        sample_count = sum(len(frame) for frame in frames) / 2 / self.channels
        return RecordingResult(path=path, sample_rate=self.sample_rate, seconds=sample_count / self.sample_rate)

    def _capture(self) -> None:
        try:
            self._capture_sounddevice()
            return
        except Exception:
            self._capture_pyaudio()

    def _capture_sounddevice(self) -> None:
        import sounddevice as sd

        self._backend = "sounddevice"

        def callback(indata, frames, time_info, status):
            del frames, time_info, status
            self._frames.put(indata.copy().tobytes())

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype="int16",
            callback=callback,
        ):
            self._stop.wait()

    def _capture_pyaudio(self) -> None:
        import pyaudio

        self._backend = "pyaudio"
        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=self.channels,
            rate=self.sample_rate,
            input=True,
            frames_per_buffer=1024,
        )
        try:
            while not self._stop.is_set():
                self._frames.put(stream.read(1024, exception_on_overflow=False))
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()

    def _drain(self) -> None:
        while not self._frames.empty():
            self._frames.get()
