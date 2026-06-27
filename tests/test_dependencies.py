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


if __name__ == "__main__":
    unittest.main()
