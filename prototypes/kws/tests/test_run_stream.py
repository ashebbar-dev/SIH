from __future__ import annotations

import os
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import wave

import numpy as np


KWS_DIR = Path(__file__).resolve().parents[1]
if str(KWS_DIR) not in sys.path:
    sys.path.insert(0, str(KWS_DIR))

import run_stream as run_stream_module
from run_stream import StreamError, StreamingDetector, quantize_features, run_stream


def _write_wav(path: Path, samples: np.ndarray, *, channels: int = 1, sample_width: int = 2, rate: int = 16000):
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(sample_width)
        wav.setframerate(rate)
        wav.writeframes(samples.tobytes())


def _write_manifest(path: Path, model_name: str = "model.tflite", **micro_overrides):
    micro = {
        "probability_cutoff": 0.97,
        "feature_step_size": 10,
        "sliding_window_size": 5,
    }
    micro.update(micro_overrides)
    path.write_text(
        json.dumps({"version": 2, "model": model_name, "micro": micro}),
        encoding="utf-8",
    )


class _FakeFrontend:
    def __init__(self):
        self.calls = 0

    def process_samples(self, audio: bytes):
        self.calls += 1
        if len(audio) != 320:
            raise AssertionError(f"native call was {len(audio) // 2} samples, expected 160")
        features = [] if self.calls < 3 else [float((self.calls * 17 + index) % 500) / 25.6 for index in range(40)]
        return type("FrontendOutput", (), {"features": features, "samples_read": 160})()


class _FakeInterpreter:
    input_shape = [1, 3, 40]
    input_dtype = np.int8
    input_quantization = (26 / 255, -128)
    output_shape = [1, 1]
    output_dtype = np.uint8
    output_quantization = (1 / 256, 0)

    def __init__(self, model_path: str, num_threads: int):
        if num_threads != 1:
            raise AssertionError("runner must request exactly one interpreter thread")
        self.value = 0
        self.tensor = None

    def allocate_tensors(self):
        pass

    def get_input_details(self):
        return [{
            "index": 7,
            "shape": np.array(self.input_shape),
            "dtype": self.input_dtype,
            "quantization": self.input_quantization,
        }]

    def get_output_details(self):
        return [{
            "index": 8,
            "shape": np.array(self.output_shape),
            "dtype": self.output_dtype,
            "quantization": self.output_quantization,
        }]

    def set_tensor(self, index, value):
        self.tensor = value.copy()

    def invoke(self):
        self.value = (self.value + int(self.tensor.astype(np.int64).sum()) + 256) % 256

    def get_tensor(self, index):
        return np.array([[self.value]], dtype=np.uint8)


class FeatureConversionTests(unittest.TestCase):
    def test_feature_conversion(self):
        raw = np.array([0, 1, 333, 666, 1000], dtype=np.int64)
        expected = np.array([-128, -128, 0, 127, 127], dtype=np.int8)
        np.testing.assert_array_equal(quantize_features(raw / 25.6), expected)

    def test_rejects_nonfinite_or_negative_features(self):
        for value in (-0.01, np.nan, np.inf):
            with self.subTest(value=value), self.assertRaises(ValueError):
                quantize_features(np.array([value]))


class StreamingDetectorTests(unittest.TestCase):
    def test_strict_cutoff_and_reset(self):
        detector = StreamingDetector(cutoff=247, window=5)
        for _ in range(100):
            self.assertFalse(detector.advance(0))
        for _ in range(5):
            self.assertFalse(detector.advance(247))
        self.assertTrue(detector.advance(248))
        self.assertFalse(detector.advance(255))

    def test_high_output_and_none_do_not_advance_cooldown(self):
        detector = StreamingDetector(cutoff=100, window=2)
        self.assertFalse(detector.advance(101))
        for _ in range(200):
            self.assertFalse(detector.advance(None))
        self.assertFalse(detector.advance(0))
        for _ in range(99):
            self.assertFalse(detector.advance(None))
        self.assertFalse(detector.advance(101))
        self.assertTrue(detector.advance(101))

    def test_none_can_advance_suppression_but_cannot_trigger(self):
        detector = StreamingDetector(cutoff=100, window=2)
        for _ in range(99):
            self.assertFalse(detector.advance(None))
        self.assertFalse(detector.advance(None))
        self.assertFalse(detector.advance(101))
        self.assertFalse(detector.advance(None))
        self.assertTrue(detector.advance(101))

    def test_rejects_invalid_configuration_and_probability(self):
        for cutoff, window in [(-1, 5), (256, 5), (247, 0), (247, True)]:
            with self.subTest(cutoff=cutoff, window=window), self.assertRaises(ValueError):
                StreamingDetector(cutoff=cutoff, window=window)
        detector = StreamingDetector(cutoff=247, window=5)
        for probability in (-1, 256, 2.5, True):
            with self.subTest(probability=probability), self.assertRaises(ValueError):
                detector.advance(probability)


class RunStreamValidationTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.directory = Path(self.tempdir.name)
        self.model = self.directory / "model.tflite"
        self.model.write_bytes(b"fake tflite model")
        self.manifest = self.directory / "manifest.json"
        _write_manifest(self.manifest)
        self.audio = self.directory / "audio.wav"
        _write_wav(self.audio, np.zeros(1600, dtype=np.int16))

    def tearDown(self):
        self.tempdir.cleanup()

    def test_rejects_invalid_manifest_configuration(self):
        documents = [
            {"version": 1, "model": "model.tflite", "micro": {"feature_step_size": 10, "probability_cutoff": 0.97, "sliding_window_size": 5}},
            {"version": 2, "model": "model.tflite", "micro": {"feature_step_size": 20, "probability_cutoff": 0.97, "sliding_window_size": 5}},
            {"version": 2, "model": "model.tflite", "micro": {"feature_step_size": 10, "probability_cutoff": 1.1, "sliding_window_size": 5}},
            {"version": 2, "model": "model.tflite", "micro": {"feature_step_size": 10, "probability_cutoff": 0.97, "sliding_window_size": 0}},
        ]
        for document in documents:
            with self.subTest(document=document):
                self.manifest.write_text(json.dumps(document), encoding="utf-8")
                with self.assertRaises(StreamError):
                    run_stream(self.manifest, self.audio)

    def test_rejects_invalid_audio_formats_explicitly(self):
        bad_audio = self.directory / "stereo.wav"
        _write_wav(bad_audio, np.zeros(320, dtype=np.int16), channels=2)
        with self.assertRaisesRegex(StreamError, "mono"):
            run_stream(self.manifest, bad_audio)

    def test_rejects_invalid_chunk_size(self):
        with self.assertRaises(StreamError):
            run_stream(self.manifest, self.audio, chunk_samples=0)

    def test_rejects_incompatible_model_tensor(self):
        class WrongShapeInterpreter(_FakeInterpreter):
            input_shape = [1, 4, 40]

        with mock.patch.object(run_stream_module, "Interpreter", WrongShapeInterpreter):
            with self.assertRaisesRegex(StreamError, "input tensor"):
                run_stream(self.manifest, self.audio)

    def test_timestamps_counts_and_tail_are_transport_independent(self):
        samples = np.arange(1602, dtype=np.int16)
        _write_wav(self.audio, samples)
        results = []
        for chunk_samples in (73, 160, 997):
            with mock.patch.object(run_stream_module, "Interpreter", _FakeInterpreter), mock.patch.object(
                run_stream_module, "MicroFrontend", _FakeFrontend
            ):
                results.append(run_stream(self.manifest, self.audio, chunk_samples))
        comparable = lambda result: (
            [prediction["raw_uint8"] for prediction in result["predictions"]],
            [prediction["time_s"] for prediction in result["predictions"]],
            result["triggers_s"],
            result["feature_count"],
            result["invocation_count"],
            result["incomplete_final_stride_count"],
            result["read_samples"],
            result["consumed_samples"],
            result["unprocessed_tail_samples"],
        )
        self.assertEqual(comparable(results[0]), comparable(results[1]))
        self.assertEqual(comparable(results[0]), comparable(results[2]))
        self.assertEqual([0.05, 0.08], [entry["time_s"] for entry in results[0]["predictions"]])
        self.assertEqual((8, 2, 2), (
            results[0]["feature_count"],
            results[0]["invocation_count"],
            results[0]["incomplete_final_stride_count"],
        ))
        self.assertEqual((1602, 1600, 2), (
            results[0]["read_samples"],
            results[0]["consumed_samples"],
            results[0]["unprocessed_tail_samples"],
        ))
        self.assertEqual(0, results[0]["output_tensor"]["zero_point"])
        self.assertEqual("uint8", results[0]["output_tensor"]["dtype"])


@unittest.skipUnless(os.environ.get("KWS_TEST_MODEL_MANIFEST"), "KWS_TEST_MODEL_MANIFEST is not set")
class RealModelTests(unittest.TestCase):
    def test_chunk_independent_real_inference(self):
        sample_count = 6402
        indices = np.arange(sample_count, dtype=np.float64)
        signal = (
            9000.0 * np.sin(2.0 * np.pi * (180.0 + indices / 100.0) * indices / 16000.0)
            + 3000.0 * np.sin(2.0 * np.pi * 731.0 * indices / 16000.0)
        )
        samples = np.clip(np.rint(signal), -32768, 32767).astype(np.int16)
        with tempfile.TemporaryDirectory() as directory:
            audio = Path(directory) / "nonconstant.wav"
            _write_wav(audio, samples)
            results = [
                run_stream(Path(os.environ["KWS_TEST_MODEL_MANIFEST"]), audio, chunk_samples)
                for chunk_samples in (73, 160, 997)
            ]
        for result in results:
            self.assertEqual(2, result["unprocessed_tail_samples"])
            self.assertGreater(result["feature_count"], 3)
            self.assertEqual(0.05, result["predictions"][0]["time_s"])
            self.assertEqual(
                [0.05 + 0.03 * index for index in range(result["invocation_count"])],
                [prediction["time_s"] for prediction in result["predictions"]],
            )
        reference = (
            [prediction["raw_uint8"] for prediction in results[0]["predictions"]],
            results[0]["triggers_s"],
            results[0]["feature_count"],
        )
        for result in results[1:]:
            self.assertEqual(reference, (
                [prediction["raw_uint8"] for prediction in result["predictions"]],
                result["triggers_s"],
                result["feature_count"],
            ))


if __name__ == "__main__":
    unittest.main()
