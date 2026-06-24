import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock
from unittest.mock import patch

from biscuit.app import finish_dictation_result, insert_text_into_context
from biscuit.desktop import RightClickContext
from biscuit.status import DictationResult
from biscuit.transcription import TranscriptionError


class AppFocusTests(unittest.TestCase):
    def test_insert_restores_target_focus_before_typing(self):
        context = RightClickContext(x=320, y=240, hwnd=1234, title="Target", captured_at=1.0)
        calls = []

        def restore(target):
            calls.append(("restore", target))

        def send(hwnd, text):
            calls.append(("send", hwnd, text))
            return len(text)

        with patch("biscuit.app.restore_input_focus", side_effect=restore):
            with patch("biscuit.app.send_unicode_text", side_effect=send):
                inserted = insert_text_into_context(context, "hello")

        self.assertEqual(inserted, 5)
        self.assertEqual(calls, [("restore", context), ("send", 1234, "hello")])

    def test_insert_skips_empty_text(self):
        context = RightClickContext(x=320, y=240, hwnd=1234, title="Target", captured_at=1.0)
        with patch("biscuit.app.restore_input_focus") as restore:
            with patch("biscuit.app.send_unicode_text", Mock(return_value=0)) as send:
                inserted = insert_text_into_context(context, "")

        self.assertEqual(inserted, 0)
        restore.assert_not_called()
        send.assert_not_called()


class FinishDictationResultTests(unittest.TestCase):
    def test_finish_dictation_reports_no_speech(self):
        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=RightClickContext(1, 2, 3, "Editor", 4.0),
            transcribe=lambda _path: "",
            insert=lambda _context, _text: 4,
            copy=lambda _text: None,
        )
        self.assertEqual(outcome.result, DictationResult.NO_SPEECH)

    def test_finish_dictation_copies_when_target_missing(self):
        copied = []
        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=None,
            transcribe=lambda _path: "field note",
            insert=lambda _context, _text: 10,
            copy=copied.append,
        )
        self.assertEqual(outcome.result, DictationResult.COPIED)
        self.assertEqual(copied, ["field note"])

    def test_finish_dictation_copies_when_insert_fails(self):
        copied = []

        def fail_insert(_context, _text):
            raise OSError("blocked")

        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=RightClickContext(1, 2, 3, "Editor", 4.0),
            transcribe=lambda _path: "field note",
            insert=fail_insert,
            copy=copied.append,
        )
        self.assertEqual(outcome.result, DictationResult.COPIED)
        self.assertEqual(outcome.detail, "direct insertion blocked")
        self.assertEqual(copied, ["field note"])

    def test_finish_dictation_classifies_transcription_error(self):
        def fail_transcribe(_path):
            raise TranscriptionError("model missing")

        outcome = finish_dictation_result(
            recording=SimpleNamespace(path=Path("sample.wav")),
            context=RightClickContext(1, 2, 3, "Editor", 4.0),
            transcribe=fail_transcribe,
            insert=lambda _context, _text: 4,
            copy=lambda _text: None,
        )
        self.assertEqual(outcome.result, DictationResult.TRANSCRIPTION_ERROR)
        self.assertEqual(outcome.detail, "model missing")


if __name__ == "__main__":
    unittest.main()
