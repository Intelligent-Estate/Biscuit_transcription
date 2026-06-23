import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerScriptTests(unittest.TestCase):
    def test_windows_installer_creates_start_menu_launcher(self):
        text = (ROOT / "scripts" / "install_windows.ps1").read_text(encoding="utf-8")
        self.assertIn('"Biscuit-Windows.cmd"', text)
        self.assertNotIn("launchers\\Biscuit-Windows.cmd", text)
        self.assertIn("Start Menu", text)

    def test_linux_installer_creates_desktop_entry(self):
        text = (ROOT / "scripts" / "install_linux.sh").read_text(encoding="utf-8")
        self.assertIn("biscuit.desktop", text)
        self.assertIn('LAUNCHER="$APP_DIR/biscuit-linux.sh"', text)
        self.assertIn("Biscuit", text)

    def test_macos_installer_creates_app_bundle_launcher(self):
        text = (ROOT / "scripts" / "install_macos.sh").read_text(encoding="utf-8")
        self.assertIn("Biscuit.app", text)
        self.assertIn('LAUNCHER="$APP_DIR/Biscuit-macOS.command"', text)


if __name__ == "__main__":
    unittest.main()
