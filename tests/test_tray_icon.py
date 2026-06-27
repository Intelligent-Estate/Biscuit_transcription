import unittest
import sys
from types import SimpleNamespace
from unittest.mock import patch

from biscuit.tray import TrayCallbacks, TrayController, build_tray_icon_image


class TrayIconTests(unittest.TestCase):
    def test_tray_icon_uses_biscuit_theme_colors(self):
        image = build_tray_icon_image(64)
        self.assertEqual(image.size, (64, 64))
        self.assertEqual(image.getpixel((8, 4))[:3], (255, 210, 63))
        self.assertEqual(image.getpixel((2, 32))[:3], (7, 17, 31))

    def test_tray_icon_click_defaults_to_settings_panel(self):
        menu_items = []

        class FakeMenu:
            def __init__(self, *items):
                self.items = items

        class FakeMenuItem:
            def __init__(self, text, action, **kwargs):
                self.text = text
                self.action = action
                self.kwargs = kwargs
                menu_items.append(self)

        class FakeIcon:
            def __init__(self, name, image, title, menu):
                self.name = name
                self.image = image
                self.title = title
                self.menu = menu

            def run(self):
                return None

            def stop(self):
                return None

        fake_pystray = SimpleNamespace(Menu=FakeMenu, MenuItem=FakeMenuItem, Icon=FakeIcon)
        opened = {"count": 0}
        callbacks = TrayCallbacks(
            show_settings=lambda: opened.__setitem__("count", opened["count"] + 1),
            dictate_at_cursor=lambda: None,
            start_biscuit=lambda: None,
            stop_biscuit=lambda: None,
            quit_app=lambda: None,
        )

        with patch.dict(sys.modules, {"pystray": fake_pystray}):
            self.assertTrue(TrayController(callbacks).start())

        self.assertEqual(menu_items[0].text, "Biscuit Settings")
        self.assertTrue(menu_items[0].kwargs.get("default"))
        menu_items[0].action(None, None)
        self.assertEqual(opened["count"], 1)

    def test_tray_menu_uses_full_biscuit_lifecycle_labels(self):
        menu_items = []

        class FakeMenu:
            def __init__(self, *items):
                self.items = items

        class FakeMenuItem:
            def __init__(self, text, action, **kwargs):
                self.text = text
                self.action = action
                self.kwargs = kwargs
                menu_items.append(self)

        class FakeIcon:
            def __init__(self, name, image, title, menu):
                self.name = name
                self.image = image
                self.title = title
                self.menu = menu

            def run(self):
                return None

        fake_pystray = SimpleNamespace(Menu=FakeMenu, MenuItem=FakeMenuItem, Icon=FakeIcon)
        callbacks = TrayCallbacks(
            show_settings=lambda: None,
            dictate_at_cursor=lambda: None,
            start_biscuit=lambda: None,
            stop_biscuit=lambda: None,
            quit_app=lambda: None,
        )

        with patch.dict(sys.modules, {"pystray": fake_pystray}):
            self.assertTrue(TrayController(callbacks).start())

        labels = [item.text for item in menu_items]
        self.assertIn("Start Biscuit", labels)
        self.assertIn("Stop Biscuit", labels)
        self.assertIn("Quit Biscuit", labels)
        self.assertNotIn("Kill Biscuit", labels)
        self.assertNotIn("Kill Biscuit (Quit)", labels)
        self.assertNotIn("Quit", labels)


if __name__ == "__main__":
    unittest.main()
