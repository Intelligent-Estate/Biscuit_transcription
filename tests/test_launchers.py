import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class LauncherTests(unittest.TestCase):
    def test_windows_launcher_starts_biscuit_from_repo_root(self):
        text = (ROOT / "Biscuit-Windows.cmd").read_text(encoding="utf-8")
        self.assertIn("set \"PYTHONPATH=%SCRIPT_DIR%src\"", text)
        self.assertIn("pythonw.exe", text)
        self.assertIn('start ""', text)
        self.assertIn("%*", text)
        self.assertNotIn("\npython -m biscuit", text)

    def test_linux_launcher_starts_biscuit_from_repo_root(self):
        text = (ROOT / "biscuit-linux.sh").read_text(encoding="utf-8")
        self.assertIn('export PYTHONPATH="$APP_DIR/src"', text)
        self.assertIn('python3 -m biscuit', text)

    def test_macos_launcher_starts_biscuit_from_repo_root(self):
        text = (ROOT / "Biscuit-macOS.command").read_text(encoding="utf-8")
        self.assertIn('export PYTHONPATH="$APP_DIR/src"', text)
        self.assertIn('python3 -m biscuit', text)


if __name__ == "__main__":
    unittest.main()
