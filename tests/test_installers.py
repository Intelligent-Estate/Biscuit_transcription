import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class InstallerScriptTests(unittest.TestCase):
    def test_windows_installer_creates_start_menu_launcher(self):
        text = (ROOT / "scripts" / "install_windows.ps1").read_text(encoding="utf-8")
        self.assertIn('"Biscuit-Windows.cmd"', text)
        self.assertIn('"Run Biscuit.lnk"', text)
        self.assertIn('"assets\\Biscuit.ico"', text)
        self.assertNotIn("launchers\\Biscuit-Windows.cmd", text)
        self.assertIn("Start Menu", text)
        self.assertIn("Startup", text)
        self.assertIn("Could not save shortcut", text)

    def test_windows_installer_registers_context_menu_commands(self):
        text = (ROOT / "scripts" / "install_windows.ps1").read_text(encoding="utf-8")
        for context_root in (
            r"Software\Classes\*\shell\Biscuit",
            r"Software\Classes\AllFilesystemObjects\shell\Biscuit",
            r"Software\Classes\Directory\shell\Biscuit",
            r"Software\Classes\Directory\Background\shell\Biscuit",
            r"Software\Classes\Drive\shell\Biscuit",
        ):
            self.assertIn(context_root, text)
        self.assertIn("--dictate-once", text)
        self.assertIn("[AllowEmptyString()]", text)
        self.assertIn("CreateSubKey", text)
        self.assertIn('Set-HkcuRegistryString -Path $commandRoot -Name "" -Value $contextMenuCommand', text)
        self.assertNotIn('Name "(default)"', text)
        self.assertNotIn("Get-Item -LiteralPath $commandRoot", text)

    def test_windows_installer_launches_biscuit_unless_disabled(self):
        text = (ROOT / "scripts" / "install_windows.ps1").read_text(encoding="utf-8")
        self.assertIn("[switch]$NoLaunch", text)
        self.assertIn("Start-Process", text)
        self.assertIn("if (-not $NoLaunch)", text)

    def test_windows_click_installer_wraps_powershell_script(self):
        text = (ROOT / "Install-Biscuit-Windows.cmd").read_text(encoding="utf-8")
        self.assertIn("powershell.exe", text)
        self.assertIn("-ExecutionPolicy Bypass", text)
        self.assertIn("scripts\\install_windows.ps1", text)
        self.assertIn("%*", text)

    def test_windows_run_shortcut_artifacts_exist(self):
        self.assertTrue((ROOT / "Run Biscuit.lnk").exists())
        self.assertTrue((ROOT / "assets" / "Biscuit.ico").exists())

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
