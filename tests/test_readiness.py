import unittest
from unittest import mock

from biscuit.config import BiscuitConfig
from biscuit.desktop import RightClickContext
from biscuit.readiness import (
    ReadinessState,
    check_insertion_readiness,
    check_microphone_readiness,
    check_model_readiness,
    summarize_readiness,
)
from biscuit.transcription import ProviderChoice, TranscriptionError


class ReadinessTests(unittest.TestCase):
    def test_model_readiness_reports_ready_provider(self):
        with mock.patch("biscuit.readiness.detect_provider", return_value=ProviderChoice("faster_whisper")):
            state = check_model_readiness(BiscuitConfig(model_path="Systran/faster-whisper-tiny.en"))
        self.assertEqual(state.name, "model")
        self.assertTrue(state.ready)
        self.assertEqual(state.detail, "faster_whisper")

    def test_model_readiness_reports_missing_local_file(self):
        state = check_model_readiness(BiscuitConfig(model_path="C:/missing/model.gguf"))
        self.assertFalse(state.ready)
        self.assertEqual(state.detail, "selected model file is missing")

    def test_model_readiness_reports_provider_error(self):
        with mock.patch("biscuit.readiness.detect_provider", side_effect=TranscriptionError("bad provider")):
            state = check_model_readiness(BiscuitConfig(model_path="Systran/faster-whisper-tiny.en"))
        self.assertFalse(state.ready)
        self.assertEqual(state.detail, "bad provider")

    def test_insertion_readiness_reports_target_presence(self):
        context = RightClickContext(x=1, y=2, hwnd=3, title="Editor", captured_at=4.0)
        self.assertTrue(check_insertion_readiness(context).ready)
        self.assertFalse(check_insertion_readiness(None).ready)

    def test_microphone_readiness_uses_backend_probe(self):
        with mock.patch("biscuit.readiness.available_audio_backends", return_value=["sounddevice"]):
            state = check_microphone_readiness()
        self.assertEqual(state, ReadinessState("microphone", True, "sounddevice"))

    def test_microphone_readiness_reports_missing_backend(self):
        with mock.patch("biscuit.readiness.available_audio_backends", return_value=[]):
            state = check_microphone_readiness()
        self.assertFalse(state.ready)
        self.assertEqual(state.detail, "no microphone backend")

    def test_summarize_readiness_counts_ready_parts(self):
        states = [
            ReadinessState("model", True, "faster_whisper"),
            ReadinessState("microphone", False, "no microphone backend"),
            ReadinessState("target", True, "Editor"),
        ]
        self.assertEqual(summarize_readiness(states), "ready 2/3; microphone: no microphone backend")


if __name__ == "__main__":
    unittest.main()
