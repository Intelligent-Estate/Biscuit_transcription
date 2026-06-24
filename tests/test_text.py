import unittest

from biscuit.text import normalize_transcript


class NormalizeTranscriptTests(unittest.TestCase):
    def test_normalize_transcript_trims_and_collapses_space(self):
        self.assertEqual(normalize_transcript("  hello   biscuit \n"), "hello biscuit")

    def test_normalize_transcript_keeps_empty_empty(self):
        self.assertEqual(normalize_transcript("   "), "")


if __name__ == "__main__":
    unittest.main()
