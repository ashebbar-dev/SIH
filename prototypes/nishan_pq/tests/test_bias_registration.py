"""Focused checks only; the fixed 256-case experiment is a separate CLI."""
from dataclasses import replace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "research/tools"))
import nishan_bias_registration as reg
from nishan import tardos, watermark


class BiasRegistrationTests(unittest.TestCase):
    def setUp(self):
        cv2.setNumThreads(2)

    def test_keyed_biases_zero_rows_equal_existing_generator(self):
        config = replace(tardos.parameters(4, 4, .05), code_length=12)
        p = reg.keyed_biases(config, b"b" * 32, "tiny-test")
        expected, rows = tardos.generate_keyed(config, b"b" * 32, "tiny-test")
        np.testing.assert_array_equal(p, expected)
        self.assertEqual(rows.shape, (4, 12))
        self.assertTrue(np.all(np.isfinite(p) & (p > 0) & (p < 1)))

    def test_endpoint_response_and_erasure(self):
        b, w = reg.endpoint_expectation(np.array([[251., 255.]]),
                                       np.array([[255., 251.]]), np.array([[.25, .75]]))
        np.testing.assert_array_equal(b, [[253., 253.]])
        np.testing.assert_array_equal(w, [[-1., -1.]])
        _, w = reg.endpoint_expectation(np.full((2, 2), 255.),
                                       np.full((2, 2), 255.), np.full((2, 2), .9))
        np.testing.assert_array_equal(w, np.zeros((2, 2)))
        for q in (np.full((2, 2), np.nan), np.full((2, 2), 1.1)):
            with self.assertRaises(ValueError):
                reg.endpoint_expectation(np.ones((2, 2)), np.ones((2, 2)), q)
        with self.assertRaises(ValueError):
            reg.endpoint_expectation(np.ones((2, 2)), np.ones((2, 3)), np.ones((2, 2)))

    def fixture(self):
        source = np.full((240, 240), 245.)
        y, x = np.indices(source.shape)
        pilot = np.sin(x * 1.3) + np.cos(y * .8)
        return source, pilot, np.ones((40, 40), dtype=bool)

    def test_projection_linearity_and_plane_then_block_dc(self):
        source, pilot, active = self.fixture()
        p = reg.prepare_projection(source, pilot, np.ones(source.shape, bool), active)
        y, x = np.indices(source.shape)
        plane = 4 + .02 * x - .03 * y
        np.testing.assert_allclose(reg.project(plane, p), 0, atol=1e-12)
        a, b = np.sin(x), np.cos(y)
        np.testing.assert_allclose(reg.project(2 * a - 3 * b, p),
                                   2 * reg.project(a, p) - 3 * reg.project(b, p), atol=1e-12)
        blocks = reg.project(a, p).reshape(-1, 36)
        np.testing.assert_allclose(blocks.mean(axis=1), 0, atol=1e-14)
        with self.assertRaises(ValueError):
            reg.project(a[:-1], p)

    def test_edge_excludes_whole_block_and_neighborhood(self):
        source, pilot, active = self.fixture()
        source[:, 120] = 0
        p = reg.prepare_projection(source, pilot, np.ones(source.shape, bool), active)
        self.assertFalse(p["mask"][:, 114:132].any())
        self.assertTrue(p["mask"][60:66, 102:108].all())

    def test_no_active_and_zero_energy_abstain(self):
        source, pilot, active = self.fixture()
        for mask, w in ((active & False, pilot), (active, pilot * 0)):
            result = reg.search_translation(source, source, np.eye(3), source, w, mask)
            self.assertEqual(result["status"], "abstain")
            self.assertIsNone(result["raw_to_reference"])
            self.assertEqual(len(result["objectives"]), 289)
            self.assertTrue(all(not c["valid"] for c in result["objectives"]))

    def test_deterministic_exact_ties_and_roster_independence(self):
        source, pilot, active = self.fixture()
        unrelated = np.zeros((3, 12), dtype=np.uint8)
        with patch.object(reg, "render_capture", return_value=source + pilot):
            before = reg.search_translation(source, source, np.eye(3), source, pilot, active)
            unrelated = np.ones((7, 12), dtype=np.uint8)
            after = reg.search_translation(source, source, np.eye(3), source, pilot, active)
        self.assertEqual(unrelated.shape, (7, 12))
        self.assertEqual(before["status"], "accepted")
        self.assertEqual((before["dx"], before["dy"]), (0., 0.))
        self.assertEqual(before["exact_best_ties"], 289)
        self.assertEqual((before["runner_up"]["dx"], before["runner_up"]["dy"]), (-.25, 0.))
        for field in ("transform_sha256", "objectives_sha256", "mask_sha256", "projection_sha256"):
            self.assertEqual(before[field], after[field])

    def test_transform_composition_exact_rectangle(self):
        reference = np.full((64, 64), 255, dtype=np.uint8)
        reference[20:32, 20:34] = 80
        raw = cv2.warpPerspective(reference, reg.translation(7, -4), (64, 64), borderValue=255)
        combined = reg.translation(-2, 1) @ reg.translation(-5, 3)
        np.testing.assert_array_equal(combined, reg.translation(-7, 4))
        np.testing.assert_array_equal(reg.render_capture(raw, combined, reference.shape), reference)

    def test_rgb8_warp_before_luma_different_capture_shape(self):
        rgb = np.random.default_rng(7).integers(0, 256, (40, 50, 3), dtype=np.uint8)
        h = reg.translation(.25, -.5)
        expected = watermark._luma(cv2.warpPerspective(
            rgb, h, (48, 36), flags=cv2.INTER_LANCZOS4,
            borderMode=cv2.BORDER_CONSTANT, borderValue=(255, 255, 255))).astype(np.float64)
        np.testing.assert_array_equal(reg.render_capture(rgb, h, (36, 48)), expected)

    def test_common_support_margin(self):
        coverage = reg.common_coverage((240, 240), (250, 260), reg.translation(-5, 3))
        self.assertFalse(coverage[0].any())
        self.assertTrue(coverage[20:220, 20:220].all())

    def test_single_unsupported_pixel_excludes_entire_block(self):
        source, pilot, active = self.fixture()
        coverage = np.ones(source.shape, bool)
        coverage[61, 61] = False
        prepared = reg.prepare_projection(source, pilot, coverage, active)
        self.assertFalse(prepared["mask"][60:66, 60:66].any())
        self.assertTrue(prepared["mask"][60:66, 66:72].all())

    def test_nonpositive_and_zero_residual_are_not_accepted(self):
        source, pilot, active = self.fixture()
        for image, reason in ((source - pilot, "nonpositive_best_objective"),
                              (source, "all_candidates_invalid")):
            with patch.object(reg, "render_capture", return_value=image):
                result = reg.search_translation(source, source, np.eye(3), source, pilot, active)
            self.assertEqual(result["status"], "abstain")
            self.assertEqual(result["reason"], reason)

    def test_boundary_maximum_is_failure_with_diagnostic_transform(self):
        source, pilot, active = self.fixture()
        _, x = np.indices(source.shape)
        noise = np.cos(x * .3)
        def rendered(capture, transform, shape):
            return source + pilot + (2 - transform[0, 2]) * noise
        with patch.object(reg, "render_capture", side_effect=rendered):
            result = reg.search_translation(source, source, np.eye(3), source, pilot, active)
        self.assertEqual(result["status"], "boundary_failure")
        self.assertEqual((result["dx"], result["dy"]), (2., 0.))
        self.assertIsNone(result["raw_to_reference"])
        np.testing.assert_array_equal(result["diagnostic_raw_to_reference"], reg.translation(2, 0))

    def test_native_unused_pixels_have_no_overlay(self):
        source = np.full((12, 12), 128, np.uint8)
        rendered = reg.render_native(source, np.zeros(source.shape))
        np.testing.assert_allclose(rendered, source, atol=2e-5)


if __name__ == "__main__":
    unittest.main()
