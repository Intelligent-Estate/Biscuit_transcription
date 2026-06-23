import unittest
from pathlib import Path
from unittest.mock import patch

from biscuit.transcription import ProviderChoice, TranscriptionError, build_external_command, detect_provider


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

    def test_gguf_model_requires_gguf_capable_runner(self):
        with patch("biscuit.transcription.shutil.which", return_value=None):
            with self.assertRaises(TranscriptionError):
                detect_provider("auto", Path("C:/Models/whisper-tiny-q4_0.gguf"))


if __name__ == "__main__":
    unittest.main()
