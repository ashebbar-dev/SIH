from __future__ import annotations

import unittest

import cv2
import numpy as np

from nishan import registration


class RegistrationTests(unittest.TestCase):
    def test_perspective_page_is_recovered_with_diagnostics(self) -> None:
        reference = np.full((760, 540, 3), 246, dtype=np.uint8)
        cv2.rectangle(reference, (22, 22), (518, 738), (25, 45, 80), 3)
        for row in range(14):
            y = 80 + row * 42
            cv2.putText(
                reference,
                f"OPERATIONAL LINE {row:02d}  ALPHA BRAVO",
                (48, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (35, 35, 35),
                1,
                cv2.LINE_AA,
            )
        source_corners = np.float32([[0, 0], [539, 0], [539, 759], [0, 759]])
        destination_corners = np.float32(
            [[170, 55], [705, 120], [650, 875], [80, 790]]
        )
        transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
        suspect = cv2.warpPerspective(
            reference,
            transform,
            (820, 930),
            borderValue=(45, 48, 52),
        )

        aligned, metrics = registration.align_page(reference, suspect)

        self.assertEqual(aligned.shape, reference.shape)
        self.assertTrue(metrics.applied)
        self.assertGreater(metrics.ransac_inliers, 100)
        self.assertGreater(metrics.registered_similarity, 0.5)
        self.assertGreater(
            metrics.registered_similarity,
            metrics.baseline_similarity + 0.45,
        )


if __name__ == "__main__":
    unittest.main()
