import unittest

from biscuit.tray import build_tray_icon_image


class TrayIconTests(unittest.TestCase):
    def test_tray_icon_uses_biscuit_theme_colors(self):
        image = build_tray_icon_image(64)
        self.assertEqual(image.size, (64, 64))
        self.assertEqual(image.getpixel((8, 4))[:3], (255, 210, 63))
        self.assertEqual(image.getpixel((2, 32))[:3], (7, 17, 31))


if __name__ == "__main__":
    unittest.main()
