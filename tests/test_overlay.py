import unittest

from biscuit.overlay import recording_pill_position


class RecordingPillPositionTests(unittest.TestCase):
    def test_recording_pill_appears_beneath_cursor(self):
        x, y = recording_pill_position(400, 300)
        self.assertEqual(x, 400)
        self.assertGreater(y, 300)

    def test_recording_pill_stays_on_screen_when_near_bottom(self):
        x, y = recording_pill_position(900, 700, screen_width=1024, screen_height=720)
        self.assertLessEqual(x + 230, 1024)
        self.assertLessEqual(y + 76, 720)


if __name__ == "__main__":
    unittest.main()
