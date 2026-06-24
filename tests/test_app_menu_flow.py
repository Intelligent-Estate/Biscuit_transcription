import unittest
from types import SimpleNamespace

from biscuit.app import ACTION_MENU_DELAY_MS, BiscuitApp
from biscuit.desktop import RightClickContext


class AppMenuFlowTests(unittest.TestCase):
    def test_right_click_shows_action_after_host_menu_has_time_to_open(self):
        calls = []
        context = RightClickContext(x=200, y=120, hwnd=99, title="Target", captured_at=1.0)

        app = SimpleNamespace(
            last_context=None,
            root=SimpleNamespace(after=lambda delay, callback: calls.append((delay, callback))),
            overlay=SimpleNamespace(show_action=lambda ctx, callback: None),
            begin_recording=lambda ctx: None,
        )

        BiscuitApp.on_right_click(app, context)

        self.assertIs(app.last_context, context)
        self.assertEqual(calls[0][0], ACTION_MENU_DELAY_MS)
        self.assertGreaterEqual(calls[0][0], 100)

    def test_show_settings_does_not_deiconify_blank_root_window(self):
        calls = []

        app = SimpleNamespace(
            root=SimpleNamespace(deiconify=lambda: calls.append("deiconify root")),
            overlay=SimpleNamespace(show_settings=lambda: calls.append("show settings")),
        )

        BiscuitApp.show_settings(app)

        self.assertEqual(calls, ["show settings"])

    def test_quit_biscuit_status_says_stopped(self):
        calls = []

        app = SimpleNamespace(
            hook=SimpleNamespace(stop=lambda: calls.append("stop hook")),
            overlay=SimpleNamespace(
                close_action=lambda: calls.append("close action"),
                close_recording=lambda: calls.append("close recording"),
                set_settings_status=lambda status: calls.append(("status", status)),
            ),
        )

        BiscuitApp.kill_biscuit(app)

        self.assertEqual(calls[-1], ("status", "stopped"))


if __name__ == "__main__":
    unittest.main()
