import unittest
from pathlib import Path
from unittest.mock import patch

from biscuit.app import choose_transcribable_model, is_hugging_face_model_id, main, save_config_if_possible
from biscuit.config import BiscuitConfig
from biscuit.transcription import TranscriptionError


class AppCliTests(unittest.TestCase):
    def test_main_starts_normal_run_by_default(self):
        with patch("biscuit.app.BiscuitApp") as app_class:
            app = app_class.return_value
            main([])
            app.run.assert_called_once_with()
            app.run_dictation_once.assert_not_called()

    def test_main_starts_one_shot_dictation_mode(self):
        with patch("biscuit.app.send_dictation_request", return_value=False):
            with patch("biscuit.app.BiscuitApp") as app_class:
                app = app_class.return_value
                main(["--dictate-once"])
                app.run_dictation_once.assert_called_once_with()
                app.run.assert_not_called()

    def test_main_sends_dictation_request_to_running_app(self):
        with patch("biscuit.app.send_dictation_request", return_value=True) as send_request:
            with patch("biscuit.app.BiscuitApp") as app_class:
                main(["--dictate-once"])

        send_request.assert_called_once_with()
        app_class.assert_not_called()

    def test_main_falls_back_to_one_shot_when_request_fails(self):
        with patch("biscuit.app.send_dictation_request", return_value=False):
            with patch("biscuit.app.BiscuitApp") as app_class:
                app = app_class.return_value
                main(["--dictate-once"])

        app.run_dictation_once.assert_called_once_with()
        app.run.assert_not_called()

    def test_choose_transcribable_model_skips_incompatible_candidate(self):
        gguf = Path("C:/Models/whisper-tiny-q4_0.gguf")
        pt = Path("C:/Models/whisper/small.pt")

        def fake_detect_provider(provider, model_path):
            del provider
            if model_path == gguf:
                raise TranscriptionError("needs runner")
            return object()

        with patch("biscuit.app.detect_provider", side_effect=fake_detect_provider):
            self.assertEqual(choose_transcribable_model([gguf, pt], "auto"), pt)

    def test_hugging_face_model_id_detection_rejects_local_paths(self):
        self.assertTrue(is_hugging_face_model_id("Systran/faster-whisper-tiny.en"))
        self.assertFalse(is_hugging_face_model_id("C:/Models/whisper/small.pt"))
        self.assertFalse(is_hugging_face_model_id("./models/small.pt"))

    def test_save_config_if_possible_reports_denied_write(self):
        with patch("biscuit.app.save_config", side_effect=PermissionError("denied")):
            self.assertFalse(save_config_if_possible(Path("C:/Locked/biscuit.json"), BiscuitConfig()))


if __name__ == "__main__":
    unittest.main()
