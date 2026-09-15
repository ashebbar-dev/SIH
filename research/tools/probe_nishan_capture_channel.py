#!/usr/bin/env python3
"""Fixed public-fixture channel diagnostic, not physical or SOTA evidence.

Compare the existing hard decoder residual against an oracle residual that has
the EXACT capture transformation applied to the unmarked source as well. The
oracle uses unavailable information and is not a proposed deployed decoder.
It distinguishes source/capture mismatch from complete signal erasure.
No parameters are fitted, no identities influence preprocessing, and no
production carrier or decision threshold is changed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

import cv2
import numpy as np
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "prototypes/nishan_pq"))
from nishan import tardos, tardos_carrier, watermark  # noqa: E402


def conditional_null_threshold(biases: np.ndarray, word: np.ndarray,
                               family_epsilon: float, hypotheses: int) -> dict:
    """Numerical Chernoff threshold under an explicitly idealized null model.

    Capture/decoder must be independent of the innocent row conditional on p;
    columns of that row must follow independent ideal uniform-word sampling.
    Neither property is certified for adversarial known-key fixtures or the
    deterministic deployed PRF. This is a known statistical tool, not novelty.
    """
    p = biases[np.asarray(word, dtype=bool)]
    if not len(p):
        return {"threshold": None, "reason": "empty active symbol set"}
    q = np.floor(p * 2**32) / 2**32
    positive = np.sqrt((1 - p) / p)
    negative = -np.sqrt(p / (1 - p))
    log_budget = float(np.log(hypotheses / family_epsilon))

    def cumulant(theta: float) -> float:
        return float(np.logaddexp(np.log(q) + theta * positive,
                                 np.log1p(-q) + theta * negative).sum())

    def boundary(log_theta: float) -> float:
        theta = float(np.exp(log_theta))
        return (cumulant(theta) + log_budget) / theta

    optimum = minimize_scalar(boundary, bounds=(-20.0, 4.0), method="bounded")
    if not optimum.success or not np.isfinite(optimum.fun):
        raise RuntimeError("Chernoff threshold optimization failed")
    theta = float(np.exp(optimum.x))
    k = cumulant(theta)
    threshold = (k + log_budget) / theta + 1e-9
    return {"threshold": threshold, "theta": theta, "cumulant": k,
            "active_symbols": int(len(p)), "hypotheses": hypotheses,
            "family_epsilon": family_epsilon,
            "modeled_per_hypothesis_upper": float(np.exp(k - theta * threshold)),
            "sample_probability": "floor(p * 2^32) / 2^32"}


def run() -> dict:
    source = ROOT / "artifacts/nishan/synthetic-source.pdf"
    marked = ROOT / "artifacts/nishan/tardos-user-0000-live-text.pdf"
    original_rgb = watermark.load_pages(source, dpi=144)[0][0]
    marked_rgb = watermark.load_pages(marked, dpi=144)[0][0]
    secret = hashlib.sha3_256(b"NISHAN Tardos carrier public fixture v1").digest()
    config = tardos.parameters(1000, 5, 1e-6)
    biases, codebook = tardos.generate_keyed(config, secret, "public-benchmark-codebook/v1")
    block = 6
    height, width = original_rgb.shape[:2]
    rows, cols = height // block, width // block
    order, orientations, polarities = tardos_carrier._plan(
        secret, "synthetic-source/full-tardos-profile-v1", rows * cols,
        config.code_length,
    )
    signed_templates = tardos_carrier._templates(block)[orientations] * polarities[:, None, None]

    def decode(residual: np.ndarray) -> dict:
        blocks = (residual[:rows * block, :cols * block]
                  .reshape(rows, block, cols, block).transpose(0, 2, 1, 3)
                  .reshape(rows * cols, block, block))
        correlations = np.sum(blocks[order] * signed_templates, axis=(1, 2))
        word = (correlations > 0).astype(np.uint8)
        scores = tardos.accusation_scores(biases, codebook, word)
        accused = tardos.accuse(scores, config).tolist()
        # Fixed before this branch is scored: 8 capture conditions, 2 source
        # profiles, all1000 recipients; no best-decoder/recipient selection.
        null = conditional_null_threshold(biases, word, 1e-6, 1000 * 8 * 2)
        conditional_accused = ([] if null["threshold"] is None else
                               np.flatnonzero(scores > null["threshold"]).tolist())
        return {
            "bit_error_fraction": float(np.mean(word != codebook[0])),
            "median_abs_correlation": float(np.median(np.abs(correlations))),
            "zero_correlation_fraction": float(np.mean(correlations == 0)),
            "expected_score": float(scores[0]),
            "highest_other_score": float(scores[1:].max()),
            "accused_rows": accused,
            "expected_only_recovered": accused == [0],
            "conditional_null": null,
            "conditional_accused_rows": conditional_accused,
            "conditional_expected_only_recovered": conditional_accused == [0],
        }

    def quantize(values: np.ndarray) -> np.ndarray:
        return np.clip(np.rint(values), 0, 255).astype(np.uint8)

    conditions = [
        ("identity", lambda x: x.copy()),
        ("affine_0.85_plus15", lambda x: quantize(x.astype(float) * .85 + 15)),
        ("gamma_1.5", lambda x: quantize(255 * (x.astype(float) / 255) ** 1.5)),
        ("white_clip_250", lambda x: np.where(x >= 250, 255, x).astype(np.uint8)),
        ("binary_threshold_200", lambda x: np.where(x >= 200, 255, 0).astype(np.uint8)),
        ("gaussian_sigma0.75", lambda x: cv2.GaussianBlur(x, (0, 0), .75)),
        ("gaussian_sigma1.5", lambda x: cv2.GaussianBlur(x, (0, 0), 1.5)),
        ("gaussian_sigma2.5", lambda x: cv2.GaussianBlur(x, (0, 0), 2.5)),
    ]
    original = watermark._luma(original_rgb)
    results = []
    for name, transform in conditions:
        captured = watermark._luma(transform(marked_rgb))
        transformed_source = watermark._luma(transform(original_rgb))
        result = {
            "condition": name,
            "existing_source_residual": decode(captured - original),
            "oracle_matched_source_residual": decode(captured - transformed_source),
            "remaining_mark_rms": float(np.sqrt(np.mean((captured - transformed_source) ** 2))),
        }
        results.append(result)
        print(json.dumps(result), flush=True)
    return {
        "schema": "nishan.capture-channel-diagnostic/v1",
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "marked_sha256": hashlib.sha256(marked.read_bytes()).hexdigest(),
        "code_length": config.code_length,
        "threshold": config.threshold,
        "roster_size": config.roster_size,
        "conditions_fixed_before_run": [name for name, _ in conditions],
        "limitations": [
            "One synthetic public document/codebook; not independent-document or physical capture evidence.",
            "Known deterministic distortions, no calibrated real print/camera model.",
            "Oracle source transformation is unavailable to a real investigator and is not a candidate algorithm.",
            "Fixed historical threshold is a diagnostic operating point, not a certified physical false-accusation rate.",
            "All1000 rows scored, but one codebook cannot establish a rare-event error probability.",
            "Raster arrays share exact geometry; no registration-improvement claim.",
            "Conditional thresholds model independent innocent bits conditional on biases and identity-independent capture; not certified for this public deterministic codebook.",
            "Chernoff calibration is an established statistical method, not a newly invented watermark or security theorem.",
            "The modeled1e-6 error budget is shared over8 transformations x2 source profiles x1000 rows, not an empirical measured error rate.",
        ],
        "results": results,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(f"Preserve prior run; choose a new output: {args.output}")
    payload = run()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as handle:
        json.dump(payload, handle, indent=2, allow_nan=False)
        handle.write("\n")
