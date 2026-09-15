"""Content-based registration for photographed or shifted document pages.

The watermark decoder is non-blind: the authority retains the source document.
That makes the visible document content a synchronization reference.  This module
uses ORB correspondences and a RANSAC homography to map a suspect rendering back
onto the source page.  It accepts the transform only when a gradient-domain
similarity score improves, and records enough diagnostics to reject weak matches.

This is preprocessing evidence, not part of the Tardos theorem.  A successful
homography says that two page renderings were aligned; it does not establish that
the decoded fingerprint obeys the marking condition.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class RegistrationMetrics:
    method: str
    applied: bool
    reference_width: int
    reference_height: int
    suspect_width: int
    suspect_height: int
    reference_keypoints: int
    suspect_keypoints: int
    ratio_test_matches: int
    ransac_inliers: int
    ransac_inlier_ratio: float
    baseline_similarity: float
    registered_similarity: float
    rejection_reason: str | None
    homography_suspect_to_reference: list[list[float]] | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _gray(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3 or image.shape[2] != 3:
        raise ValueError("registration expects an RGB image")
    return cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)


def _gradient_signature(gray: np.ndarray) -> np.ndarray:
    scaled = gray
    height, width = gray.shape
    longest = max(height, width)
    if longest > 900:
        factor = 900.0 / longest
        scaled = cv2.resize(
            gray,
            (max(1, round(width * factor)), max(1, round(height * factor))),
            interpolation=cv2.INTER_AREA,
        )
    x = cv2.Sobel(scaled, cv2.CV_32F, 1, 0, ksize=3)
    y = cv2.Sobel(scaled, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(x, y)
    magnitude -= float(magnitude.mean())
    return magnitude


def _similarity(reference_gray: np.ndarray, candidate_gray: np.ndarray) -> float:
    if candidate_gray.shape != reference_gray.shape:
        candidate_gray = cv2.resize(
            candidate_gray,
            (reference_gray.shape[1], reference_gray.shape[0]),
            interpolation=cv2.INTER_AREA,
        )
    reference_signature = _gradient_signature(reference_gray)
    candidate_signature = _gradient_signature(candidate_gray)
    if candidate_signature.shape != reference_signature.shape:
        candidate_signature = cv2.resize(
            candidate_signature,
            (reference_signature.shape[1], reference_signature.shape[0]),
            interpolation=cv2.INTER_AREA,
        )
    denominator = float(
        np.linalg.norm(reference_signature) * np.linalg.norm(candidate_signature)
    )
    if denominator == 0:
        return 0.0
    return float(np.sum(reference_signature * candidate_signature) / denominator)


def align_page(
    reference: np.ndarray,
    suspect: np.ndarray,
    *,
    min_matches: int = 12,
    min_inliers: int = 10,
    min_inlier_ratio: float = 0.15,
    improvement_margin: float = 0.01,
) -> tuple[np.ndarray, RegistrationMetrics]:
    """Align one suspect page to a reference page and report the decision."""

    reference_gray = _gray(reference)
    suspect_gray = _gray(suspect)
    reference_height, reference_width = reference_gray.shape
    suspect_height, suspect_width = suspect_gray.shape
    baseline = cv2.resize(
        suspect,
        (reference_width, reference_height),
        interpolation=cv2.INTER_LANCZOS4,
    )
    baseline_similarity = _similarity(reference_gray, _gray(baseline))

    if (
        (suspect_height, suspect_width) == (reference_height, reference_width)
        and baseline_similarity >= 0.92
    ):
        return baseline, RegistrationMetrics(
            method="identity/content-similarity guard",
            applied=False,
            reference_width=reference_width,
            reference_height=reference_height,
            suspect_width=suspect_width,
            suspect_height=suspect_height,
            reference_keypoints=0,
            suspect_keypoints=0,
            ratio_test_matches=0,
            ransac_inliers=0,
            ransac_inlier_ratio=0.0,
            baseline_similarity=round(baseline_similarity, 6),
            registered_similarity=round(baseline_similarity, 6),
            rejection_reason=None,
            homography_suspect_to_reference=None,
        )

    orb = cv2.ORB_create(
        nfeatures=8_000,
        scaleFactor=1.2,
        nlevels=8,
        edgeThreshold=15,
        fastThreshold=7,
    )
    reference_keypoints, reference_descriptors = orb.detectAndCompute(
        reference_gray, None
    )
    suspect_keypoints, suspect_descriptors = orb.detectAndCompute(suspect_gray, None)
    reference_count = len(reference_keypoints or [])
    suspect_count = len(suspect_keypoints or [])

    def rejected(reason: str, matches: int = 0) -> tuple[np.ndarray, RegistrationMetrics]:
        return baseline, RegistrationMetrics(
            method="resize-only",
            applied=False,
            reference_width=reference_width,
            reference_height=reference_height,
            suspect_width=suspect_width,
            suspect_height=suspect_height,
            reference_keypoints=reference_count,
            suspect_keypoints=suspect_count,
            ratio_test_matches=matches,
            ransac_inliers=0,
            ransac_inlier_ratio=0.0,
            baseline_similarity=round(baseline_similarity, 6),
            registered_similarity=round(baseline_similarity, 6),
            rejection_reason=reason,
            homography_suspect_to_reference=None,
        )

    if reference_descriptors is None or suspect_descriptors is None:
        return rejected("ORB descriptors unavailable")

    matcher = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)
    pairs = matcher.knnMatch(suspect_descriptors, reference_descriptors, k=2)
    good = [
        first
        for pair in pairs
        if len(pair) == 2
        for first, second in [pair]
        if first.distance < 0.75 * second.distance
    ]
    if len(good) < min_matches:
        return rejected(f"only {len(good)} ratio-test matches", len(good))

    suspect_points = np.float32(
        [suspect_keypoints[match.queryIdx].pt for match in good]
    ).reshape(-1, 1, 2)
    reference_points = np.float32(
        [reference_keypoints[match.trainIdx].pt for match in good]
    ).reshape(-1, 1, 2)
    homography, inlier_mask = cv2.findHomography(
        suspect_points,
        reference_points,
        cv2.RANSAC,
        4.0,
    )
    if homography is None or inlier_mask is None:
        return rejected("RANSAC did not produce a homography", len(good))
    inliers = int(np.count_nonzero(inlier_mask))
    ratio = inliers / len(good)
    if inliers < min_inliers or ratio < min_inlier_ratio:
        return rejected(
            f"weak homography: {inliers} inliers ({ratio:.3f})",
            len(good),
        )

    registered = cv2.warpPerspective(
        suspect,
        homography,
        (reference_width, reference_height),
        flags=cv2.INTER_LANCZOS4,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(255, 255, 255),
    )
    registered_similarity = _similarity(reference_gray, _gray(registered))
    shape_changed = (suspect_height, suspect_width) != (
        reference_height,
        reference_width,
    )
    required_similarity = baseline_similarity + improvement_margin
    if not shape_changed and registered_similarity < required_similarity:
        return baseline, RegistrationMetrics(
            method="resize-only",
            applied=False,
            reference_width=reference_width,
            reference_height=reference_height,
            suspect_width=suspect_width,
            suspect_height=suspect_height,
            reference_keypoints=reference_count,
            suspect_keypoints=suspect_count,
            ratio_test_matches=len(good),
            ransac_inliers=inliers,
            ransac_inlier_ratio=round(ratio, 6),
            baseline_similarity=round(baseline_similarity, 6),
            registered_similarity=round(registered_similarity, 6),
            rejection_reason="homography did not improve same-size alignment",
            homography_suspect_to_reference=homography.tolist(),
        )
    if shape_changed and registered_similarity < max(0.08, baseline_similarity):
        return baseline, RegistrationMetrics(
            method="resize-only",
            applied=False,
            reference_width=reference_width,
            reference_height=reference_height,
            suspect_width=suspect_width,
            suspect_height=suspect_height,
            reference_keypoints=reference_count,
            suspect_keypoints=suspect_count,
            ratio_test_matches=len(good),
            ransac_inliers=inliers,
            ransac_inlier_ratio=round(ratio, 6),
            baseline_similarity=round(baseline_similarity, 6),
            registered_similarity=round(registered_similarity, 6),
            rejection_reason="homography failed the content-similarity guard",
            homography_suspect_to_reference=homography.tolist(),
        )

    return registered, RegistrationMetrics(
        method="ORB + RANSAC homography",
        applied=True,
        reference_width=reference_width,
        reference_height=reference_height,
        suspect_width=suspect_width,
        suspect_height=suspect_height,
        reference_keypoints=reference_count,
        suspect_keypoints=suspect_count,
        ratio_test_matches=len(good),
        ransac_inliers=inliers,
        ransac_inlier_ratio=round(ratio, 6),
        baseline_similarity=round(baseline_similarity, 6),
        registered_similarity=round(registered_similarity, 6),
        rejection_reason=None,
        homography_suspect_to_reference=homography.tolist(),
    )
