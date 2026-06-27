import unittest

from biscuit.status import DictationOutcome, DictationResult, status_text


class DictationStatusTests(unittest.TestCase):
    def test_status_text_is_short_and_operational(self):
        expected = {
            DictationResult.INSERTED: "inserted",
            DictationResult.COPIED: "copied to clipboard",
            DictationResult.NO_SPEECH: "no speech found",
            DictationResult.MICROPHONE_ERROR: "microphone unavailable",
            DictationResult.MODEL_ERROR: "model unavailable",
            DictationResult.TRANSCRIPTION_ERROR: "transcription failed",
            DictationResult.TARGET_ERROR: "target unavailable",
        }
        for result, text in expected.items():
            with self.subTest(result=result):
                self.assertEqual(status_text(DictationOutcome(result)), text)

    def test_status_text_keeps_detail_when_it_helps_action(self):
        outcome = DictationOutcome(DictationResult.MODEL_ERROR, "GGUF/GGML models need a runner")
        self.assertEqual(status_text(outcome), "model unavailable: GGUF/GGML models need a runner")

    def test_status_text_truncates_long_detail(self):
        outcome = DictationOutcome(DictationResult.TRANSCRIPTION_ERROR, "x" * 120)
        text = status_text(outcome)
        self.assertTrue(text.startswith("transcription failed: "))
        self.assertLessEqual(len(text), 96)
        self.assertTrue(text.endswith("..."))


if __name__ == "__main__":
    unittest.main()
