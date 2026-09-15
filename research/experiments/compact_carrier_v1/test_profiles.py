from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import numpy as np

import profiles as profiles_module
import run_study as run_study_module
from profiles import (
    PROFILES,
    collapse_correlations,
    load_replay_state,
    symmetric_scores,
)
from run_study import (
    build_declared_matrix,
    create_output_directory,
    marking_diagnostics_for_row,
)


EVIDENCE_TEMP_ROOT = (
    Path(__file__).resolve().parents[2]
    / "evidence/nishan-compact-carrier-2026-09-12"
)


class SymmetricScoreTests(unittest.TestCase):
    def test_symmetric_uses_both_output_symbols(self):
        p = np.array([0.2, 0.8])
        x = np.array([[1, 0], [0, 1]], dtype=np.uint8)
        np.testing.assert_allclose(
            symmetric_scores(x, p, np.array([1, 0])), [4.0, -1.0]
        )
        np.testing.assert_allclose(
            symmetric_scores(x, p, np.array([0, 1])), [-4.0, 1.0]
        )

    def test_repetition_sums_analog_correlations_before_threshold(self):
        # Majority hard decisions would give the wrong first bit.
        corr = np.array([9.0, -2.0, -1.0, 1.0, -1.0, 1.0, -1.0, -2.0])
        word, summed = collapse_correlations(corr, 2, 4)
        np.testing.assert_allclose(summed, [6.0, -2.0])
        np.testing.assert_array_equal(word, [1, 0])

    def test_zero_correlation_tie_is_zero(self):
        word, summed = collapse_correlations(np.array([1.0, -1.0]), 1, 2)
        self.assertEqual(int(word[0]), 0)
        self.assertEqual(float(summed[0]), 0.0)

    def test_symmetric_validates_shape_binary_and_finiteness(self):
        valid_x = np.array([[0, 1]], dtype=np.uint8)
        valid_p = np.array([0.2, 0.8])
        valid_y = np.array([0, 1], dtype=np.uint8)
        bad_calls = (
            lambda: symmetric_scores(valid_x.reshape(-1), valid_p, valid_y),
            lambda: symmetric_scores(valid_x, valid_p[:1], valid_y),
            lambda: symmetric_scores(valid_x, valid_p, valid_y[:1]),
            lambda: symmetric_scores(np.array([[0, 2]]), valid_p, valid_y),
            lambda: symmetric_scores(valid_x, valid_p, np.array([0, 2])),
            lambda: symmetric_scores(valid_x, np.array([0.0, 0.8]), valid_y),
            lambda: symmetric_scores(valid_x, np.array([np.nan, 0.8]), valid_y),
        )
        for call in bad_calls:
            with self.subTest(call=call), self.assertRaises(ValueError):
                call()

    def test_collapse_validates_shape_and_finiteness(self):
        for correlations, positions, repetitions in (
            (np.zeros((2, 2)), 2, 2),
            (np.array([1.0, np.inf]), 1, 2),
            (np.ones(3), 2, 2),
            (np.ones(2), 0, 2),
            (np.ones(2), 2, 0),
        ):
            with self.subTest(
                correlations=correlations,
                positions=positions,
                repetitions=repetitions,
            ), self.assertRaises(ValueError):
                collapse_correlations(correlations, positions, repetitions)


class FrozenProfileTests(unittest.TestCase):
    def test_profile_constants_and_matched_area(self):
        expected = {
            "original-6-r1": (52500, 6, 1, 52500, 1890000, 2100.0),
            "symmetric-6-r4": (
                12331,
                6,
                4,
                49324,
                1775664,
                837.2843088602898,
            ),
            "symmetric-12-r1": (
                12331,
                12,
                1,
                12331,
                1775664,
                837.2843088602898,
            ),
        }
        self.assertEqual(tuple(PROFILES), tuple(expected))
        for name, values in expected.items():
            profile = PROFILES[name]
            self.assertEqual(
                (
                    profile.logical_positions,
                    profile.block_size,
                    profile.repetitions,
                    profile.physical_placements,
                    profile.nominal_pixels,
                    profile.threshold,
                ),
                values,
            )
            self.assertEqual(
                profile.physical_placements * profile.block_size**2,
                profile.nominal_pixels,
            )

    def test_profiles_mapping_is_immutable(self):
        with self.assertRaises(TypeError):
            PROFILES["extra"] = PROFILES["original-6-r1"]  # type: ignore[index]

    def test_fixed_matrix_count_and_identity(self):
        matrix = build_declared_matrix()
        identities = {
            (item["kind"], item["profile"], item["row"], item["transform"])
            for item in matrix
        }
        profile_names = (
            "original-6-r1",
            "symmetric-6-r4",
            "symmetric-12-r1",
        )
        rows = (0, 7)
        transforms = ("clean", "jpeg55", "blur1", "blur2", "half-resize")
        expected = {
            ("positive", profile, row, transform)
            for profile in profile_names
            for row in rows
            for transform in transforms
        }
        expected.update(
            ("unmarked", profile, None, transform)
            for profile in profile_names
            for transform in transforms
        )
        expected.update(
            (kind, profile, row, "clean")
            for kind in ("wrong-key", "wrong-context")
            for profile in profile_names
            for row in rows
        )
        self.assertEqual(len(matrix), 57)
        self.assertEqual(identities, expected)

    def test_row_bearing_negative_has_marking_diagnostics(self):
        codebook = np.array([[0, 1, 1], [1, 0, 1]], dtype=np.uint8)
        word = np.array([0, 0, 1], dtype=np.uint8)
        diagnostics, reason = marking_diagnostics_for_row(word, codebook, 1)
        self.assertIsNone(reason)
        self.assertEqual(diagnostics["unanimous_positions"], 3)
        self.assertEqual(diagnostics["violations"], 1)
        missing, missing_reason = marking_diagnostics_for_row(word, codebook, None)
        self.assertIsNone(missing)
        self.assertEqual(
            missing_reason,
            "no participating source row; marking-condition BER is undefined",
        )


class ReplayAndGuardTests(unittest.TestCase):
    def _complete_preload_manifest(self, run: Path) -> dict[str, object]:
        replay = run / "private/replay-state.npz"
        replay.parent.mkdir(parents=True)
        replay.write_bytes(b"valid-hash-placeholder")
        source = run / "source/synthetic-source.pdf"
        source.parent.mkdir(parents=True)
        source.write_bytes(b"source-placeholder")
        return {
            "private_replay": {
                "path": "private/replay-state.npz",
                "sha3_256": hashlib.sha3_256(replay.read_bytes()).hexdigest(),
            },
            "source": {
                "input_path": "artifacts/nishan/synthetic-source.pdf",
                "run_path": "source/synthetic-source.pdf",
                "sha3_256": hashlib.sha3_256(source.read_bytes()).hexdigest(),
            },
            "families": {
                "original": {
                    "biases_sha3_256": "1" * 64,
                    "codebook_sha3_256": "2" * 64,
                    "codebook_shape": [1000, 52500],
                },
                "symmetric": {
                    "biases_sha3_256": "3" * 64,
                    "codebook_sha3_256": "4" * 64,
                    "codebook_shape": [1000, 12331],
                },
            },
        }

    def test_replay_state_hash_rejection_happens_before_npz_load(self):
        with tempfile.TemporaryDirectory(dir=EVIDENCE_TEMP_ROOT) as temporary:
            run = Path(temporary)
            private = run / "private"
            private.mkdir()
            replay = private / "replay-state.npz"
            replay.write_bytes(b"not-an-npz")
            digest = hashlib.sha3_256(b"different").hexdigest()
            manifest = {
                "private_replay": {
                    "path": "private/replay-state.npz",
                    "sha3_256": digest,
                }
            }
            with self.assertRaisesRegex(ValueError, "replay-state hash mismatch"):
                load_replay_state(run, manifest)

    def test_missing_source_fails_before_private_npz_load(self):
        with tempfile.TemporaryDirectory(dir=EVIDENCE_TEMP_ROOT) as temporary:
            run = Path(temporary)
            manifest = self._complete_preload_manifest(run)
            del manifest["source"]
            with mock.patch.object(
                profiles_module.np,
                "load",
                side_effect=AssertionError("NPZ_LOAD_REACHED"),
            ) as loader:
                with self.assertRaisesRegex(ValueError, "source metadata"):
                    load_replay_state(run, manifest)
            loader.assert_not_called()

    def test_missing_families_fail_before_private_npz_load(self):
        with tempfile.TemporaryDirectory(dir=EVIDENCE_TEMP_ROOT) as temporary:
            run = Path(temporary)
            manifest = self._complete_preload_manifest(run)
            del manifest["families"]
            with mock.patch.object(
                profiles_module.np,
                "load",
                side_effect=AssertionError("NPZ_LOAD_REACHED"),
            ) as loader:
                with self.assertRaisesRegex(ValueError, "family commitments"):
                    load_replay_state(run, manifest)
            loader.assert_not_called()

    def test_no_overwrite_output_guard(self):
        with tempfile.TemporaryDirectory(dir=EVIDENCE_TEMP_ROOT) as temporary:
            existing = Path(temporary) / "existing"
            existing.mkdir()
            sentinel = existing / "sentinel.txt"
            sentinel.write_text("preserve", encoding="utf-8")
            with self.assertRaises(FileExistsError):
                create_output_directory(existing)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "preserve")

    def test_early_preparation_failure_retains_manifest_and_traceback(self):
        with tempfile.TemporaryDirectory(dir=EVIDENCE_TEMP_ROOT) as temporary:
            output = Path(temporary) / "failed-run"
            with mock.patch.object(
                run_study_module.shutil,
                "copy2",
                side_effect=RuntimeError("simulated early preparation failure"),
            ):
                with self.assertRaisesRegex(
                    RuntimeError, "simulated early preparation failure"
                ):
                    run_study_module.run(output)
            manifest = json.loads((output / "manifest.json").read_text())
            failure = json.loads((output / "failure.json").read_text())
            self.assertEqual(manifest["status"], "failure")
            self.assertEqual(manifest["declared_observation_count"], 57)
            self.assertEqual(
                manifest["source"]["input_path"],
                "artifacts/nishan/synthetic-source.pdf",
            )
            self.assertIsNotNone(manifest["source"]["sha3_256"])
            self.assertIsNone(manifest["source"]["run_copy_sha3_256"])
            self.assertIsNotNone(
                manifest["source"]["run_copy_sha3_256_unavailable_reason"]
            )
            self.assertIsNone(
                manifest["families"]["original"]["codebook_sha3_256"]
            )
            self.assertIsNotNone(
                manifest["families"]["original"][
                    "codebook_sha3_256_unavailable_reason"
                ]
            )
            self.assertIn("simulated early preparation failure", failure["traceback"])


if __name__ == "__main__":
    unittest.main()
