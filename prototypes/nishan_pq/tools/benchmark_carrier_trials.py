#!/usr/bin/env python3
"""Measure carrier-to-carrier variation without pretending one UUID is a benchmark.

The full demo proves protocol integration.  This tool isolates the stochastic
watermark carrier on the same rendered synthetic page and repeats the three
current attacks over deterministic, independent session identifiers.  It is a
Monte Carlo engineering check, not a formal collusion-security proof.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

from nishan import watermark


def _summary(values: list[float]) -> dict[str, float]:
    data = np.asarray(values, dtype=float)
    return {
        "mean": round(float(data.mean()), 6),
        "sd_population": round(float(data.std()), 6),
        "minimum": round(float(data.min()), 6),
        "maximum": round(float(data.max()), 6),
    }


def _jpeg_q55_twice(image: np.ndarray) -> np.ndarray:
    """Match the current demo's JPEG fixture, including its second q55 save."""

    first = io.BytesIO()
    Image.fromarray(image).save(first, format="JPEG", quality=55, optimize=True)
    first.seek(0)
    second = io.BytesIO()
    Image.open(first).convert("RGB").save(second, format="JPEG", quality=55)
    second.seek(0)
    return np.asarray(Image.open(second).convert("RGB"), dtype=np.uint8)


def _score(original: np.ndarray, suspect: np.ndarray, carrier: np.ndarray) -> float:
    residual = watermark._luma(suspect) - watermark._luma(original)
    residual -= float(residual.mean())
    numerator = float(np.sum(residual * carrier))
    denominator = math.sqrt(
        float(np.sum(np.square(residual))) * float(np.sum(np.square(carrier)))
    )
    return 0.0 if denominator == 0.0 else numerator / denominator


def run(source: Path, output: Path, trials: int) -> dict[str, object]:
    if trials < 5:
        raise ValueError("trials must be at least 5")
    pages, _ = watermark.load_pages(source)
    if len(pages) != 1:
        raise ValueError("the current carrier-trial benchmark expects a one-page source")
    original = pages[0]
    secret = hashlib.sha3_256(b"NISHAN public carrier-trial fixture v1").digest()

    psnr_values: list[float] = []
    jpeg_guilty: list[float] = []
    jpeg_innocent_max: list[float] = []
    two_guilty: list[float] = []
    two_innocent: list[float] = []
    three_guilty: list[float] = []

    for trial in range(trials):
        session_ids = [
            str(uuid.uuid5(uuid.NAMESPACE_URL, f"nishan-carrier-trial-v1|{trial}|{name}"))
            for name in ("alice", "bob", "charlie")
        ]
        carriers = [
            watermark.pattern(secret, session_id, 0, original.shape[:2])
            for session_id in session_ids
        ]
        marked = [watermark.embed_array(original, carrier, 2.2) for carrier in carriers]
        for copy in marked:
            mse = float(np.mean(np.square(copy.astype(np.float32) - original.astype(np.float32))))
            psnr_values.append(20.0 * math.log10(255.0 / math.sqrt(mse)))

        jpeg = _jpeg_q55_twice(marked[1])
        jpeg_scores = [_score(original, jpeg, carrier) for carrier in carriers]
        jpeg_guilty.append(jpeg_scores[1])
        jpeg_innocent_max.append(max(jpeg_scores[0], jpeg_scores[2]))

        average_two = np.clip(
            np.mean(np.stack(marked[:2], axis=0, dtype=np.float32), axis=0),
            0,
            255,
        ).astype(np.uint8)
        two_scores = [_score(original, average_two, carrier) for carrier in carriers]
        two_guilty.extend(two_scores[:2])
        two_innocent.append(two_scores[2])

        average_three = np.clip(
            np.mean(np.stack(marked, axis=0, dtype=np.float32), axis=0),
            0,
            255,
        ).astype(np.uint8)
        three_scores = [_score(original, average_three, carrier) for carrier in carriers]
        three_guilty.extend(three_scores)

    result: dict[str, object] = {
        "version": "nishan-carrier-trials/v1",
        "method": (
            "deterministic Monte Carlo over independent UUID-derived carriers on the rendered "
            "one-page synthetic source; this measures run-to-run carrier variation, not a formal error bound"
        ),
        "trials": trials,
        "watermark_strength": 2.2,
        "psnr_db": _summary(psnr_values),
        "attacks": {
            "bob_jpeg_q55": {
                "guilty_score": _summary(jpeg_guilty),
                "maximum_innocent_score_per_trial": _summary(jpeg_innocent_max),
            },
            "alice_bob_pixel_average": {
                "guilty_scores": _summary(two_guilty),
                "innocent_score": _summary(two_innocent),
            },
            "alice_bob_charlie_pixel_average": {
                "guilty_scores": _summary(three_guilty),
            },
        },
        "limitations": [
            "The source page and attack parameters are fixed.",
            "The trial does not test print-scan, geometry, crop, OCR, interleaving, majority, or minority attacks.",
            "No rare-event false-accusation probability can be inferred from this trial count.",
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("artifacts/nishan/synthetic-source.pdf"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/nishan/carrier-trial-statistics.json"),
    )
    parser.add_argument("--trials", type=int, default=30)
    args = parser.parse_args()
    run(args.source.resolve(), args.output.resolve(), args.trials)


if __name__ == "__main__":
    main()
