import unittest

from biscuit.config import BiscuitConfig, choose_best_model, load_config, save_config


class ConfigTests(unittest.TestCase):
    def test_config_round_trips_json(self):
        with self.subTest("round trip"):
            import tempfile
            from pathlib import Path

            with tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "biscuit.json"
                config = BiscuitConfig(model_path="C:/model.bin", language="en", provider="auto")
                save_config(path, config)
                self.assertEqual(load_config(path).model_path, "C:/model.bin")

    def test_choose_best_model_prefers_small_quantized_file(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            big = root / "ggml-base.en.bin"
            small = root / "ggml-tiny.en-q5_1.bin"
            big.write_bytes(b"0" * 100)
            small.write_bytes(b"0" * 10)
            self.assertEqual(choose_best_model([big, small]), small)

    def test_choose_best_model_ignores_unsupported_onnx_assets(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            tts = root / "kitten_tts_nano_v0_1.onnx"
            whisper = root / "small.pt"
            tts.write_bytes(b"0" * 10)
            whisper.write_bytes(b"0" * 100)
            self.assertEqual(choose_best_model([tts, whisper]), whisper)

    def test_choose_best_model_ignores_non_speech_gguf_assets(self):
        import tempfile
        from pathlib import Path

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            qwen = root / "qwen-tiny-Q5_K_S.gguf"
            whisper = root / "whisper-tiny-q4_0.gguf"
            qwen.write_bytes(b"0" * 10)
            whisper.write_bytes(b"0" * 100)
            self.assertEqual(choose_best_model([qwen, whisper]), whisper)


if __name__ == "__main__":
    unittest.main()
