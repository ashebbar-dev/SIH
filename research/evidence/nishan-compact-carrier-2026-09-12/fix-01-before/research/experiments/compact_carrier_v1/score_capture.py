#!/usr/bin/env python3
"""Read-only empirical replay scorer for a supplied capture."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

from nishan import tardos, tardos_carrier

from profiles import (
    DPI,
    PROFILES,
    collapse_correlations,
    context_for_profile,
    decode_context_uuid,
    load_replay_state,
    read_manifest,
    symmetric_scores,
)


def score_capture(run: Path, profile_name: str, suspect: Path) -> dict[str, object]:
    run = Path(run)
    suspect = Path(suspect)
    if profile_name not in PROFILES:
        raise ValueError(f"unknown frozen profile: {profile_name}")
    if not suspect.is_file():
        raise ValueError(f"suspect capture does not exist: {suspect}")
    manifest = read_manifest(run)
    state = load_replay_state(run, manifest)
    profile = PROFILES[profile_name]
    context_uuid = decode_context_uuid(state)
    if profile.family == "original":
        biases = state["original_biases"]
        codebook = state["original_codebook"]
    else:
        biases = state["symmetric_biases"]
        codebook = state["symmetric_codebook"]
    source_metadata = manifest["source"]
    if not isinstance(source_metadata, dict):
        raise ValueError("manifest source metadata is invalid")
    source = run / str(source_metadata["run_path"])
    _, correlations, diagnostics = tardos_carrier.decode_word_with_diagnostics(
        source,
        suspect,
        profile.physical_placements,
        state["carrier_key"].tobytes(),
        context_for_profile(context_uuid, profile_name),
        dpi=DPI,
        block_size=profile.block_size,
        registration_mode="always",
    )
    word, summed = collapse_correlations(
        correlations, profile.logical_positions, profile.repetitions
    )
    if profile.scorer == "original-one-sided":
        scores = tardos.accusation_scores(biases, codebook, word)
    else:
        scores = symmetric_scores(codebook, biases, word)
    selected = np.flatnonzero(scores > profile.threshold)
    ordering = np.argsort(-scores, kind="stable")[:10]
    return {
        "schema_version": "nishan-compact-carrier-capture/v1",
        "empirical_extraction": True,
        "profile": profile_name,
        "suspect": str(suspect),
        "registration_mode": "always",
        "registration": diagnostics,
        "threshold": profile.threshold,
        "selected_rows": [int(row) for row in selected],
        "selected_count": int(selected.size),
        "highest_score_row": int(np.argmax(scores)),
        "highest_score": float(scores.max()),
        "highest_score_threshold_ratio": float(scores.max() / profile.threshold),
        "top_ten_rows": [
            {
                "row": int(row),
                "score": float(scores[row]),
                "score_threshold_ratio": float(scores[row] / profile.threshold),
            }
            for row in ordering
        ],
        "logical_one_count": int(word.sum()),
        "physical_correlation_minimum": float(correlations.min()),
        "physical_correlation_maximum": float(correlations.max()),
        "logical_correlation_minimum": float(summed.min()),
        "logical_correlation_maximum": float(summed.max()),
        "identity_verdict": None,
        "identity_verdict_reason": (
            "Diagnostic scores are not an identity verdict or production attribution."
        ),
        "limitations": [
            "Empirical extraction only; no theorem probability certification.",
            "A generated clean raster is replay smoke, not physical evidence.",
            "Registration is always enabled here and differs from the controlled synthetic study.",
            "The local manifest is not independently signed provenance.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path)
    parser.add_argument("--profile", required=True, choices=tuple(PROFILES))
    parser.add_argument("--suspect", required=True, type=Path)
    args = parser.parse_args()
    report = score_capture(args.run, args.profile, args.suspect)
    print(json.dumps(report, indent=2, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()
