import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURRENT_REQUIREMENTS = [
    "faster-whisper>=1.2.1",
    "huggingface-hub>=1.20.1",
    "numpy>=2.2.6",
    "pillow>=12.2.0",
    "pyaudio>=0.2.14",
    "pystray>=0.19.5",
    "sounddevice>=0.5.5",
]


class DependencyManifestTests(unittest.TestCase):
    def test_requirements_use_current_minimum_versions(self):
        requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines()

        self.assertEqual(requirements, CURRENT_REQUIREMENTS)

    def test_pyproject_dependencies_match_requirements(self):
        pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")

        for requirement in CURRENT_REQUIREMENTS:
            self.assertIn(f'"{requirement}"', pyproject)

    def test_package_script_forces_dynamic_runtime_imports(self):
        package_script = (ROOT / "scripts" / "package_biscuit.ps1").read_text(encoding="utf-8")

        self.assertIn(".biscuit-build-venv", package_script)
        self.assertIn("python -m venv $buildVenv", package_script)
        self.assertIn("-r (Join-Path $repo \"requirements.txt\") pyinstaller", package_script)
        self.assertIn("--console", package_script)
        self.assertNotIn("--windowed", package_script)
        self.assertNotIn("--collect-submodules", package_script)

        for module in (
            "biscuit.release",
            "faster_whisper",
            "ctranslate2",
            "huggingface_hub",
            "sounddevice",
            "pyaudio",
            "pystray",
        ):
            self.assertIn(f"--hidden-import {module}", package_script)


if __name__ == "__main__":
    unittest.main()
