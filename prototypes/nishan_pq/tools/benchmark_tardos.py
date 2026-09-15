#!/usr/bin/env python3
"""Generate one reproducible original-Tardos reference simulation.

The theorem metadata comes from the paper's conservative construction.  The
attack outcomes are one deterministic engineering fixture and are never
presented as statistical evidence or as proof that a PDF carrier realizes the
marking assumption.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from nishan import tardos


ATTACKS: tuple[tardos.Attack, ...] = (
    "interleaving",
    "majority",
    "minority",
    "coin_flip",
)


def run(
    roster_size: int,
    coalition_limit: int,
    familywise_epsilon: float,
    seed: int,
) -> dict[str, object]:
    config = tardos.parameters(roster_size, coalition_limit, familywise_epsilon)
    start = time.perf_counter()
    rng = np.random.default_rng(seed)
    biases, codebook = tardos.generate(config, rng)
    generation_seconds = time.perf_counter() - start
    coalition = np.arange(coalition_limit, dtype=np.int64)

    results: dict[str, object] = {}
    scoring_seconds = 0.0
    for offset, attack in enumerate(ATTACKS, start=1):
        attack_rng = np.random.default_rng(seed + offset)
        pirate = tardos.simulate_attack(codebook[coalition], attack, attack_rng)
        score_start = time.perf_counter()
        scores = tardos.accusation_scores(biases, codebook, pirate)
        scoring_seconds += time.perf_counter() - score_start
        accused = tardos.accuse(scores, config)
        colluder_hits = np.intersect1d(accused, coalition)
        innocent_hits = np.setdiff1d(accused, coalition)
        results[attack] = {
            "accused_user_indices": accused.tolist(),
            "colluders_recovered": colluder_hits.tolist(),
            "colluders_recovered_count": int(colluder_hits.size),
            "innocent_accusations": innocent_hits.tolist(),
            "innocent_accusations_count": int(innocent_hits.size),
            "colluder_score_min": float(scores[coalition].min()),
            "colluder_score_max": float(scores[coalition].max()),
            "innocent_score_max": float(scores[coalition_limit:].max()),
            "threshold": config.threshold,
            "marking_condition_checked": True,
        }

    return {
        "schema": "nishan.tardos.reference-simulation/v1",
        "claim_boundary": {
            "theorem": (
                "The error bounds apply to the original randomized Tardos construction "
                "for coalitions up to c that obey the marking condition."
            ),
            "simulation": (
                "Each named attack result is one reproducible codebook fixture, not a "
                "measured probability or a theorem."
            ),
            "carrier": (
                "No claim is made here that the current PDF watermark carrier realizes "
                "52,500 independent symbols or preserves the marking condition after distortion."
            ),
        },
        "source": {
            "paper": "Gabor Tardos, Optimal probabilistic fingerprint codes, JACM 2008",
            "doi": "10.1145/1346330.1346335",
            "construction": "original one-sided score and conservative constants",
        },
        "seed": seed,
        "manifest": tardos.manifest(config, biases, codebook),
        "coalition_user_indices": coalition.tolist(),
        "attacks": results,
        "runtime": {
            "generation_seconds": generation_seconds,
            "four_attack_scoring_seconds": scoring_seconds,
            "codebook_bytes": int(codebook.nbytes),
            "bias_vector_bytes": int(biases.nbytes),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--roster-size", type=int, default=1_000)
    parser.add_argument("--coalition-limit", type=int, default=5)
    parser.add_argument("--familywise-epsilon", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/nishan/tardos-reference-simulation.json"),
    )
    args = parser.parse_args()
    result = run(
        args.roster_size,
        args.coalition_limit,
        args.familywise_epsilon,
        args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
