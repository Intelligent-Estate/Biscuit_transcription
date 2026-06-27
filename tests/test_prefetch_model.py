import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from biscuit.config import DEFAULT_MODEL_SOURCE

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import prefetch_model  # noqa: E402


class PrefetchModelTests(unittest.TestCase):
    def test_prefetch_downloads_default_model_source(self):
        fake_hub = types.SimpleNamespace(snapshot_download=lambda repo_id: f"C:/cache/{repo_id}")

        with patch.dict(sys.modules, {"huggingface_hub": fake_hub}):
            with patch("prefetch_model.warm_transcription_model"):
                path = prefetch_model.prefetch_default_model()

        self.assertEqual(path, f"C:/cache/{DEFAULT_MODEL_SOURCE}")

    def test_prefetch_warms_runtime_loader_after_download(self):
        calls = []
        fake_hub = types.SimpleNamespace(
            snapshot_download=lambda repo_id: calls.append(("download", repo_id)) or f"C:/cache/{repo_id}"
        )

        with patch.dict(sys.modules, {"huggingface_hub": fake_hub}):
            with patch("prefetch_model.warm_transcription_model", side_effect=lambda source: calls.append(("warm", source))):
                prefetch_model.prefetch_default_model()

        self.assertEqual(calls, [("download", DEFAULT_MODEL_SOURCE), ("warm", DEFAULT_MODEL_SOURCE)])


if __name__ == "__main__":
    unittest.main()
