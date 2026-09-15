#!/usr/bin/env python3
"""Score scans and photographs of the public dual-carrier test page.

The page is a public reproducibility fixture, so its deterministic carrier key is
intentionally embedded in this tool.  Results from it demonstrate the physical
channel implementation; they are not security evidence for a production secret.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from PIL import Image

from nishan import registration, tardos, tardos_carrier, watermark


FIXTURE_SECRET = hashlib.sha3_256(
    b"NISHAN Tardos carrier public fixture v1"
).digest()
CODEBOOK_CONTEXT = "public-benchmark-codebook/v1"
CARRIER_CONTEXT = "synthetic-source/full-tardos-profile-v1"
EXPECTED_USER_INDEX = 0


def _sha3(path: Path) -> str:
    return hashlib.sha3_256(path.read_bytes()).hexdigest()


def _alignment_preview(reference: Path, suspect: Path, output: Path) -> dict[str, object]:
    original = watermark.load_pages(reference, dpi=144)[0][0]
    captured = watermark.load_pages(suspect, dpi=144)[0][0]
    aligned, metrics = registration.align_page(original, captured)
    output.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(aligned).save(output)
    return metrics.to_dict()


def score_capture(
    reference: Path,
    suspect: Path,
    preview: Path,
    config: tardos.Parameters,
    biases: np.ndarray,
    codebook: np.ndarray,
) -> dict[str, object]:
    word, correlations, preprocessing = tardos_carrier.decode_word_with_diagnostics(
        reference,
        suspect,
        config.code_length,
        FIXTURE_SECRET,
        CARRIER_CONTEXT,
    )
    scores = tardos.accusation_scores(biases, codebook, word)
    accused = tardos.accuse(scores, config)
    marking = tardos_carrier.marking_condition_errors(
        word, codebook[[EXPECTED_USER_INDEX]]
    )
    innocent_indices = np.arange(1, config.roster_size)
    preview_metrics = _alignment_preview(reference, suspect, preview)
    return {
        "capture": str(suspect),
        "capture_sha3_256": _sha3(suspect),
        "aligned_preview": str(preview),
        "expected_user_index": EXPECTED_USER_INDEX,
        "expected_score": float(scores[EXPECTED_USER_INDEX]),
        "threshold": config.threshold,
        "expected_user_recovered": EXPECTED_USER_INDEX in set(accused.tolist()),
        "accused_user_indices": accused.tolist(),
        "innocent_accusations": np.setdiff1d(
            accused, np.array([EXPECTED_USER_INDEX])
        ).tolist(),
        "highest_innocent_score": float(scores[innocent_indices].max()),
        "marking_condition": marking,
        "median_absolute_block_correlation": float(
            np.median(np.abs(correlations))
        ),
        "decoder_preprocessing": preprocessing,
        "preview_registration": preview_metrics,
        "passed_fixture_rule": (
            accused.tolist() == [EXPECTED_USER_INDEX]
        ),
        "theorem_applied_to_capture": False,
        "theorem_note": (
            "A physical capture is reported empirically. The Tardos reference theorem is not "
            "invoked unless the coalition limit and decoded marking condition are established."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("captures", type=Path, nargs="+")
    parser.add_argument(
        "--reference",
        type=Path,
        default=Path("artifacts/nishan/synthetic-source.pdf"),
        help="unmarked source used by the non-blind decoder",
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=Path("artifacts/nishan/physical-capture-evidence.json"),
    )
    parser.add_argument(
        "--preview-directory",
        type=Path,
        default=Path("artifacts/nishan/physical-alignments"),
    )
    arguments = parser.parse_args()

    config = tardos.parameters(1_000, 5, 1e-6)
    biases, codebook = tardos.generate_keyed(
        config,
        FIXTURE_SECRET,
        CODEBOOK_CONTEXT,
    )
    results = []
    for index, capture in enumerate(arguments.captures):
        preview = arguments.preview_directory / f"{index:02d}-{capture.stem}-aligned.png"
        results.append(
            score_capture(
                arguments.reference,
                capture,
                preview,
                config,
                biases,
                codebook,
            )
        )
    payload = {
        "schema": "nishan.physical-capture-evidence/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "fixture_only": True,
        "reference": {
            "path": str(arguments.reference),
            "sha3_256": _sha3(arguments.reference),
        },
        "parameters": {
            "roster_size": config.roster_size,
            "coalition_limit": config.coalition_limit,
            "code_length": config.code_length,
            "threshold": config.threshold,
        },
        "captures": results,
        "passed": sum(bool(item["passed_fixture_rule"]) for item in results),
        "total": len(results),
    }
    arguments.evidence.parent.mkdir(parents=True, exist_ok=True)
    arguments.evidence.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
