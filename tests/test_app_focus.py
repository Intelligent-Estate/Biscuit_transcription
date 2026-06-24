import unittest
from unittest.mock import Mock
from unittest.mock import patch

from biscuit.app import insert_text_into_context
from biscuit.desktop import RightClickContext


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


if __name__ == "__main__":
    unittest.main()
