#!/usr/bin/env python3
"""Repeat the code-level Tardos experiment across independent codebooks.

This study answers a narrow empirical question: was the public one-codebook
fixture unusually favorable?  It does not replace the theorem, prove a physical
watermark, or estimate a rare false-accusation probability from a small sample.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
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


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
    """Return a two-sided 95% Wilson score interval for one binomial rate."""

    if trials < 1 or not 0 <= successes <= trials:
        raise ValueError("require 0 <= successes <= trials and trials >= 1")
    rate = successes / trials
    denominator = 1.0 + z * z / trials
    center = (rate + z * z / (2.0 * trials)) / denominator
    radius = (
        z
        * math.sqrt(rate * (1.0 - rate) / trials + z * z / (4.0 * trials * trials))
        / denominator
    )
    return [round(max(0.0, center - radius), 6), round(min(1.0, center + radius), 6)]


def _trial_secret(seed: int, trial: int) -> bytes:
    return hashlib.sha3_256(
        f"NISHAN-TARDOS-INDEPENDENT-TRIAL/v1|{seed}|{trial}".encode("ascii")
    ).digest()


def run(
    *,
    trials: int,
    roster_size: int,
    coalition_limit: int,
    familywise_epsilon: float,
    seed: int,
) -> dict[str, object]:
    if trials < 1:
        raise ValueError("trials must be positive")
    config = tardos.parameters(roster_size, coalition_limit, familywise_epsilon)
    results: dict[str, list[dict[str, object]]] = {attack: [] for attack in ATTACKS}
    start = time.perf_counter()

    for trial in range(trials):
        secret = _trial_secret(seed, trial)
        biases, codebook = tardos.generate_keyed(
            config,
            secret,
            f"independent-codebook-trial:{trial}",
        )
        coalition_rng = np.random.default_rng(seed + 100_000 + trial)
        coalition = np.sort(
            coalition_rng.choice(roster_size, size=coalition_limit, replace=False)
        )
        innocent = np.setdiff1d(np.arange(roster_size), coalition)

        for offset, attack in enumerate(ATTACKS, start=1):
            attack_rng = np.random.default_rng(
                seed + 1_000_000 * offset + trial
            )
            pirate = tardos.simulate_attack(codebook[coalition], attack, attack_rng)
            scores = tardos.accusation_scores(biases, codebook, pirate)
            accused = tardos.accuse(scores, config)
            colluder_hits = np.intersect1d(accused, coalition)
            innocent_hits = np.intersect1d(accused, innocent)
            results[attack].append(
                {
                    "trial": trial,
                    "coalition_user_indices": coalition.tolist(),
                    "colluders_recovered_count": int(colluder_hits.size),
                    "innocent_accusations_count": int(innocent_hits.size),
                    "colluder_score_min": round(float(scores[coalition].min()), 6),
                    "colluder_score_max": round(float(scores[coalition].max()), 6),
                    "innocent_score_max": round(float(scores[innocent].max()), 6),
                }
            )

        if (trial + 1) % 5 == 0 or trial + 1 == trials:
            print(f"completed {trial + 1}/{trials} independent codebooks", file=sys.stderr)

    summaries: dict[str, object] = {}
    for attack, rows in results.items():
        at_least_one = sum(row["colluders_recovered_count"] >= 1 for row in rows)
        all_colluders = sum(
            row["colluders_recovered_count"] == coalition_limit for row in rows
        )
        any_innocent = sum(row["innocent_accusations_count"] >= 1 for row in rows)
        summaries[attack] = {
            "trials": trials,
            "at_least_one_colluder_recovered": at_least_one,
            "at_least_one_rate": round(at_least_one / trials, 6),
            "at_least_one_rate_wilson_95pct": _wilson(at_least_one, trials),
            "all_colluders_recovered": all_colluders,
            "all_colluders_rate": round(all_colluders / trials, 6),
            "all_colluders_rate_wilson_95pct": _wilson(all_colluders, trials),
            "trials_with_any_innocent_accusation": any_innocent,
            "any_innocent_rate": round(any_innocent / trials, 6),
            "any_innocent_rate_wilson_95pct": _wilson(any_innocent, trials),
            "total_innocent_accusations": int(
                sum(row["innocent_accusations_count"] for row in rows)
            ),
            "colluder_score_min_across_trials": min(
                row["colluder_score_min"] for row in rows
            ),
            "innocent_score_max_across_trials": max(
                row["innocent_score_max"] for row in rows
            ),
        }

    return {
        "schema": "nishan.tardos.independent-codebook-study/v1",
        "date": "2026-09-10",
        "parameters": {
            "trials": trials,
            "seed": seed,
            "roster_size": config.roster_size,
            "coalition_limit": config.coalition_limit,
            "familywise_epsilon": config.familywise_epsilon,
            "code_length": config.code_length,
            "threshold": config.threshold,
        },
        "claim_boundary": {
            "measured": (
                "Code-level outcomes across deterministic, independently derived keyed codebooks, "
                "random coalition members, and four named marking-condition attacks."
            ),
            "not_measured": (
                "A real PDF-collusion workflow, a physical carrier success rate, a cryptographic "
                "proof of generator independence, or rare false-accusation probability."
            ),
            "statistics": (
                "Wilson intervals describe only this finite trial population. The Tardos theorem, "
                "not the empirical interval, supplies the conditional code-level error bound."
            ),
        },
        "theorem_bounds": tardos.theorem_bounds(config),
        "summary": summaries,
        "trials": results,
        "runtime_seconds": round(time.perf_counter() - start, 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=30)
    parser.add_argument("--roster-size", type=int, default=1_000)
    parser.add_argument("--coalition-limit", type=int, default=5)
    parser.add_argument("--familywise-epsilon", type=float, default=1e-6)
    parser.add_argument("--seed", type=int, default=20260910)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/nishan/tardos-independent-codebook-study.json"),
    )
    args = parser.parse_args()
    result = run(
        trials=args.trials,
        roster_size=args.roster_size,
        coalition_limit=args.coalition_limit,
        familywise_epsilon=args.familywise_epsilon,
        seed=args.seed,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
