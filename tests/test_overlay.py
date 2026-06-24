import unittest
from pathlib import Path
from types import SimpleNamespace

from biscuit.overlay import (
    ACTION_MENU_HEIGHT,
    ACTION_MENU_WIDTH,
    ACCENT_TEXT,
    BLUE_BLACK,
    CORNER_RADIUS_ACTION,
    CORNER_RADIUS_PANEL,
    CYAN,
    EDGE_WHITE,
    GREEN,
    MENU_BG,
    MENU_HOVER,
    PANEL,
    RED,
    SETTINGS_ACTION_LABELS,
    SETTINGS_WINDOW_GEOMETRY,
    SETTINGS_WINDOW_MINSIZE,
    SURFACE_WHITE,
    TEXT,
    UI_FONT,
    UI_FONT_BOLD,
    UI_FONT_FAMILY,
    apply_biscuit_icon,
    action_menu_position,
    biscuit_icon_path,
    recording_control_state,
    recording_pill_position,
    rounded_rect_points,
    text_color_for_background,
)


class RecordingPillPositionTests(unittest.TestCase):
    def test_action_menu_row_appears_above_context_menu_origin(self):
        x, y = action_menu_position(400, 300)
        self.assertEqual(x, 400)
        self.assertEqual(y + ACTION_MENU_HEIGHT, 300)

    def test_action_menu_row_clamps_to_top_edge_when_cursor_near_top(self):
        x, y = action_menu_position(400, 12)
        self.assertEqual((x, y), (400, 0))

    def test_action_menu_row_stays_on_screen_when_near_edge(self):
        x, y = action_menu_position(1000, 700, screen_width=1024, screen_height=720)
        self.assertLessEqual(x + ACTION_MENU_WIDTH, 1024)
        self.assertLessEqual(y + ACTION_MENU_HEIGHT, 720)

    def test_recording_pill_appears_beneath_cursor(self):
        x, y = recording_pill_position(400, 300)
        self.assertEqual(x, 400)
        self.assertGreater(y, 300)

    def test_recording_pill_stays_on_screen_when_near_bottom(self):
        x, y = recording_pill_position(900, 700, screen_width=1024, screen_height=720)
        self.assertLessEqual(x + 230, 1024)
        self.assertLessEqual(y + 76, 720)

    def test_processing_state_replaces_stop_button_with_running_biscuit(self):
        state = recording_control_state("processing", tick=1)

        self.assertIn("run biscuit, run", state.text)
        self.assertIn("\n", state.text)
        self.assertNotEqual(state.text, "Stop")
        self.assertEqual(state.tk_state, "disabled")
        self.assertIn(state.spinner, {"\\(o.o)/", "/(o.o)\\"})

    def test_finished_state_flashes_good_biscuit(self):
        state = recording_control_state("inserted", tick=0)

        self.assertIn("good biscuit", state.text)
        self.assertIn("\n", state.text)
        self.assertNotEqual(state.text, "Stop")
        self.assertEqual(state.tk_state, "disabled")

    def test_visible_text_uses_courier_and_blue_white_tint(self):
        self.assertEqual(UI_FONT_FAMILY, "Courier New")
        self.assertEqual(UI_FONT[0], UI_FONT_FAMILY)
        self.assertEqual(UI_FONT_BOLD[0], UI_FONT_FAMILY)
        self.assertEqual(TEXT, "#f4fbff")

    def test_action_menu_keeps_blue_white_text_on_dark_surfaces(self):
        self.assertEqual(MENU_BG, BLUE_BLACK)
        self.assertEqual(MENU_HOVER, PANEL)

    def test_text_color_uses_blue_white_only_on_dark_backgrounds(self):
        self.assertEqual(text_color_for_background(BLUE_BLACK), TEXT)
        self.assertEqual(text_color_for_background(PANEL), TEXT)
        self.assertEqual(text_color_for_background(GREEN), ACCENT_TEXT)
        self.assertEqual(text_color_for_background(CYAN), ACCENT_TEXT)
        self.assertEqual(text_color_for_background(RED), ACCENT_TEXT)

    def test_recording_control_text_color_matches_background_brightness(self):
        processing = recording_control_state("processing")
        finished = recording_control_state("inserted")
        ready = recording_control_state("recording")

        self.assertEqual(processing.fg, TEXT)
        self.assertEqual(finished.fg, ACCENT_TEXT)
        self.assertEqual(ready.fg, ACCENT_TEXT)

    def test_biscuit_icon_path_points_to_packaged_icon(self):
        path = biscuit_icon_path()

        self.assertEqual(path.name, "Biscuit.ico")
        self.assertTrue(path.exists())

    def test_apply_biscuit_icon_sets_window_icon_when_available(self):
        calls = []

        class FakeWindow:
            def iconbitmap(self, path):
                calls.append(Path(path).name)

        apply_biscuit_icon(FakeWindow())

        self.assertEqual(calls, ["Biscuit.ico"])

    def test_settings_window_uses_forward_looking_layout_metrics(self):
        self.assertEqual(SETTINGS_WINDOW_GEOMETRY, "680x540+120+120")
        self.assertEqual(SETTINGS_WINDOW_MINSIZE, (640, 500))

    def test_cenedril_interface_uses_rounded_white_accent_surfaces(self):
        self.assertEqual(SURFACE_WHITE, "#ffffff")
        self.assertEqual(EDGE_WHITE, "#dff7ff")
        self.assertGreaterEqual(CORNER_RADIUS_ACTION, 10)
        self.assertGreaterEqual(CORNER_RADIUS_PANEL, 16)

    def test_rounded_rect_points_keep_edges_inside_bounds(self):
        points = rounded_rect_points(0, 0, 100, 40, 12)

        self.assertEqual(points[0], (12, 0))
        self.assertEqual(points[-1], (0, 12))
        self.assertTrue(all(0 <= x <= 100 and 0 <= y <= 40 for x, y in points))

    def test_settings_actions_use_full_biscuit_lifecycle_labels(self):
        self.assertEqual(SETTINGS_ACTION_LABELS["update"], "Find Model")
        self.assertEqual(SETTINGS_ACTION_LABELS["test"], "Test Biscuit")
        self.assertEqual(SETTINGS_ACTION_LABELS["stop"], "Stop Biscuit")

    def test_closing_settings_hides_fallback_launcher(self):
        calls = []

        class FakeSettingsWindow:
            def destroy(self):
                calls.append("destroy settings")

        overlay = SimpleNamespace(
            root=SimpleNamespace(withdraw=lambda: calls.append("withdraw root")),
            settings_window=FakeSettingsWindow(),
            show_fallback_toolbar=True,
        )

        from biscuit.overlay import BiscuitOverlay

        BiscuitOverlay.close_settings(overlay)

        self.assertEqual(calls, ["destroy settings", "withdraw root"])
        self.assertIsNone(overlay.settings_window)


if __name__ == "__main__":
    unittest.main()
