import tempfile
import unittest
from pathlib import Path

from biscuit.startup import (
    startup_script_path,
    startup_shortcut_path,
    sync_run_at_login,
)


class StartupTests(unittest.TestCase):
    def test_startup_paths_use_user_startup_folder(self):
        path = startup_shortcut_path("C:/Users/Ada/AppData/Roaming")
        script = startup_script_path("C:/Users/Ada/AppData/Roaming")

        self.assertEqual(path.name, "Biscuit.lnk")
        self.assertEqual(script.name, "Biscuit.vbs")
        self.assertIn("Startup", path.parts)
        self.assertIn("Startup", script.parts)

    def test_sync_run_at_login_creates_silent_startup_script(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "Biscuit-Windows.vbs").write_text("", encoding="utf-8")
            appdata = repo / "AppData"

            changed = sync_run_at_login(True, repo, appdata=appdata)
            script = startup_script_path(appdata)
            text = script.read_text(encoding="utf-8")

            self.assertTrue(changed)
            self.assertIn("WScript.Shell", text)
            self.assertIn("Biscuit-Windows.vbs", text)
            self.assertIn(", 0, False", text)
            self.assertIn(str(repo), text)

    def test_sync_run_at_login_removes_script_and_legacy_shortcut_when_disabled(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            appdata = repo / "AppData"
            script = startup_script_path(appdata)
            shortcut = startup_shortcut_path(appdata)
            script.parent.mkdir(parents=True)
            script.write_text("old", encoding="utf-8")
            shortcut.write_text("old", encoding="utf-8")

            changed = sync_run_at_login(False, repo, appdata=appdata)

            self.assertTrue(changed)
            self.assertFalse(script.exists())
            self.assertFalse(shortcut.exists())


if __name__ == "__main__":
    unittest.main()
