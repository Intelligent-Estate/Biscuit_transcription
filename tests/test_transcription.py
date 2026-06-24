import unittest
from pathlib import Path
import subprocess
import types
from unittest.mock import patch
from unittest.mock import Mock

from biscuit.transcription import (
    ProviderChoice,
    TranscriptionError,
    _MODEL_CACHE,
    _transcribe_external,
    _transcribe_whisper,
    build_external_command,
    detect_provider,
    warm_transcription_model,
)


class TranscriptionTests(unittest.TestCase):
    def test_external_command_keeps_model_and_audio_paths_as_arguments(self):
        choice = ProviderChoice(name="external", executable="C:/Tools/whisper.exe")
        command = build_external_command(
            choice,
            Path("C:/Models/tiny.bin"),
            Path("C:/Temp/sample.wav"),
            "en",
        )
        self.assertEqual(command[0], "C:/Tools/whisper.exe")
        self.assertIn("C:/Models/tiny.bin", command)
        self.assertIn("C:/Temp/sample.wav", command)
        self.assertIn("en", command)

    def test_external_transcription_hides_windows_console(self):
        choice = ProviderChoice(name="external", executable="C:/Tools/whisper-cli.exe")

        with patch("biscuit.transcription.subprocess.run") as run:
            run.return_value = types.SimpleNamespace(returncode=0, stdout=" hello", stderr="")
            text = _transcribe_external(choice, Path("C:/Models/tiny.bin"), Path("C:/Temp/sample.wav"), "en")

        self.assertEqual(text, "hello")
        options = run.call_args.kwargs
        self.assertTrue(options["creationflags"] & subprocess.CREATE_NO_WINDOW)
        self.assertTrue(options["startupinfo"].dwFlags & subprocess.STARTF_USESHOWWINDOW)
        self.assertEqual(options["startupinfo"].wShowWindow, subprocess.SW_HIDE)

    def test_gguf_model_requires_gguf_capable_runner(self):
        with patch("biscuit.transcription.shutil.which", return_value=None):
            with self.assertRaises(TranscriptionError):
                detect_provider("auto", Path("C:/Models/whisper-tiny-q4_0.gguf"))

    def test_pt_model_uses_whisper_backend_when_available(self):
        def fake_find_spec(name):
            if name in {"faster_whisper", "whisper"}:
                return object()
            return None

        with patch("biscuit.transcription.shutil.which", return_value=None):
            with patch("biscuit.transcription.importlib.util.find_spec", side_effect=fake_find_spec):
                choice = detect_provider("auto", Path("C:/Users/marsh/.cache/whisper/small.pt"))

        self.assertEqual(choice.name, "whisper")

    def test_whisper_model_is_cached_between_transcriptions(self):
        _MODEL_CACHE.clear()
        model = Mock()
        model.transcribe.return_value = {"text": " hello"}
        fake_whisper = types.SimpleNamespace(load_model=Mock(return_value=model))

        with patch.dict("sys.modules", {"whisper": fake_whisper}):
            first = _transcribe_whisper(Path("C:/Models/small.pt"), Path("C:/Temp/a.wav"), "en")
            second = _transcribe_whisper(Path("C:/Models/small.pt"), Path("C:/Temp/b.wav"), "en")

        self.assertEqual(first, "hello")
        self.assertEqual(second, "hello")
        fake_whisper.load_model.assert_called_once_with(str(Path("C:/Models/small.pt")))
        _MODEL_CACHE.clear()

    def test_warm_transcription_model_loads_whisper_model(self):
        _MODEL_CACHE.clear()
        model = Mock()
        fake_whisper = types.SimpleNamespace(load_model=Mock(return_value=model))

        with patch("biscuit.transcription.detect_provider", return_value=ProviderChoice("whisper")):
            with patch.dict("sys.modules", {"whisper": fake_whisper}):
                warm_transcription_model(Path("C:/Models/small.pt"), "auto")

        fake_whisper.load_model.assert_called_once_with(str(Path("C:/Models/small.pt")))
        self.assertIs(_MODEL_CACHE[("whisper", str(Path("C:/Models/small.pt")))], model)
        _MODEL_CACHE.clear()


if __name__ == "__main__":
    unittest.main()
