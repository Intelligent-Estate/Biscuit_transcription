import tempfile
import unittest
from pathlib import Path

from biscuit.config import (
    DEFAULT_MODEL_SOURCE,
    BiscuitConfig,
    choose_best_model,
    load_config,
    save_config,
)


class ConfigTests(unittest.TestCase):
    def test_config_round_trips_json(self):
        with self.subTest("round trip"):
            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "biscuit.json"
                config = BiscuitConfig(
                    model_path="C:/model.bin",
                    language="en",
                    provider="auto",
                    run_at_login=True,
                )
                save_config(path, config)
                loaded = load_config(path)
                self.assertEqual(loaded.model_path, "C:/model.bin")
                self.assertTrue(loaded.run_at_login)

    def test_missing_config_defaults_to_public_hugging_face_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "biscuit.json"

            config = load_config(path)

        self.assertEqual(config.model_path, DEFAULT_MODEL_SOURCE)
        self.assertEqual(config.provider, "auto")
        self.assertFalse(config.run_at_login)

    def test_choose_best_model_prefers_small_quantized_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            big = root / "ggml-base.en.bin"
            small = root / "ggml-tiny.en-q5_1.bin"
            big.write_bytes(b"0" * 100)
            small.write_bytes(b"0" * 10)
            self.assertEqual(choose_best_model([big, small]), small)

    def test_choose_best_model_ignores_unsupported_onnx_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tts = root / "kitten_tts_nano_v0_1.onnx"
            whisper = root / "small.pt"
            tts.write_bytes(b"0" * 10)
            whisper.write_bytes(b"0" * 100)
            self.assertEqual(choose_best_model([tts, whisper]), whisper)

    def test_choose_best_model_ignores_non_speech_gguf_assets(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qwen = root / "qwen-tiny-Q5_K_S.gguf"
            whisper = root / "whisper-tiny-q4_0.gguf"
            qwen.write_bytes(b"0" * 10)
            whisper.write_bytes(b"0" * 100)
            self.assertEqual(choose_best_model([qwen, whisper]), whisper)


if __name__ == "__main__":
    unittest.main()
