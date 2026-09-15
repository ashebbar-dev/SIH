#!/usr/bin/env python3
"""Measure the complete PDF-to-JPEG trace path over repeated release sessions.

The study holds the source, protected authority secret, and declared Tardos
profile fixed while issuing successive session rows. Each marked PDF is attacked
with JPEG quality 55 and traced against all 1,000 codebook rows. This measures
ordinary session/carrier variability; it is not an estimate of a rare
false-accusation probability and does not make the Tardos theorem apply to JPEG.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import statistics
import tempfile
import time
from pathlib import Path

from nishan import ledger, watermark
from nishan.core import decrypt_and_attribute, encrypt_once, trace_leak
from nishan.demo import _sample_pdf
from nishan.identity import create_identity
from nishan.util import write_private


def _wilson(successes: int, trials: int, z: float = 1.959963984540054) -> list[float]:
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


def run(trials: int) -> dict[str, object]:
    if not 1 <= trials <= 100:
        raise ValueError("trials must be between 1 and 100")
    rows: list[dict[str, object]] = []
    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="nishan-e2e-trials-") as directory:
        root = Path(directory)
        source = root / "source.pdf"
        _sample_pdf(source)
        identities = root / "identities"
        create_identity(identities, "bob", "Lieutenant Bob Singh")
        ledger_root = root / "ledger"
        ledger.initialize(
            ledger_root,
            validator_count=4,
            quorum=3,
            identities_root=identities,
        )
        authority_secret = root / "authority-secret.bin"
        write_private(
            authority_secret,
            hashlib.sha3_256(b"NISHAN repeated end-to-end study v1").digest(),
        )
        package = root / "broadcast.nishan.json"
        encrypt_once(source, identities, ["bob"], package)

        for trial in range(trials):
            trial_started = time.perf_counter()
            released = root / "released" / f"bob-{trial:03d}.pdf"
            release_started = time.perf_counter()
            event = decrypt_and_attribute(
                package,
                identities,
                "bob",
                authority_secret,
                ledger_root,
                released,
            )
            release_seconds = time.perf_counter() - release_started
            attacked = root / "attacks" / f"bob-{trial:03d}-q55.jpg"
            attacked.parent.mkdir(parents=True, exist_ok=True)
            attack_started = time.perf_counter()
            watermark.jpeg_attack(released, attacked, quality=55)
            attack_seconds = time.perf_counter() - attack_started
            trace_started = time.perf_counter()
            evidence = trace_leak(
                source,
                attacked,
                authority_secret,
                ledger_root,
            )
            trace_seconds = time.perf_counter() - trace_started
            expected_index = int(event["event"]["fingerprint"]["user_index"])
            selected_sessions = {
                item["session_id"] for item in evidence["attribution"]
            }
            expected_session = event["event"]["session_id"]
            expected_candidate = next(
                item
                for item in evidence["ranking"]
                if item["session_id"] == expected_session
            )
            other_issued_scores = [
                float(item["score"])
                for item in evidence["ranking"]
                if item["session_id"] != expected_session
            ]
            accused_rows = [int(index) for index in evidence["accused_codebook_rows"]]
            false_rows = [index for index in accused_rows if index != expected_index]
            rows.append(
                {
                    "trial": trial,
                    "session_id": expected_session,
                    "tardos_user_index": expected_index,
                    "expected_score": float(expected_candidate["score"]),
                    "threshold": float(evidence["detection_threshold"]),
                    "maximum_other_issued_score": (
                        max(other_issued_scores) if other_issued_scores else None
                    ),
                    "accused_codebook_rows": accused_rows,
                    "false_accused_codebook_rows": false_rows,
                    "exact_session_attribution": selected_sessions == {expected_session},
                    "recipient_signature_valid": bool(
                        expected_candidate["recipient_signature_valid"]
                    ),
                    "watermark_psnr_db": float(
                        event["event"]["watermark_metrics"]["psnr_db"]
                    ),
                    "source_bytes": source.stat().st_size,
                    "released_bytes": released.stat().st_size,
                    "jpeg_bytes": attacked.stat().st_size,
                    "release_seconds": release_seconds,
                    "jpeg_transform_seconds": attack_seconds,
                    "trace_seconds": trace_seconds,
                    "trial_seconds": time.perf_counter() - trial_started,
                }
            )
            print(f"completed end-to-end trial {trial + 1}/{trials}")

    exact = sum(bool(row["exact_session_attribution"]) for row in rows)
    signature_valid = sum(bool(row["recipient_signature_valid"]) for row in rows)
    false_rows_total = sum(len(row["false_accused_codebook_rows"]) for row in rows)
    expected_scores = [float(row["expected_score"]) for row in rows]
    psnr_values = [float(row["watermark_psnr_db"]) for row in rows]
    released_sizes = [int(row["released_bytes"]) for row in rows]
    release_times = [float(row["release_seconds"]) for row in rows]
    trace_times = [float(row["trace_seconds"]) for row in rows]
    trial_times = [float(row["trial_seconds"]) for row in rows]
    return {
        "schema": "nishan.repeated-end-to-end-jpeg-study/v1",
        "date": "2026-09-10",
        "parameters": {
            "trials": trials,
            "attack": "render first PDF page and encode JPEG at quality 55",
            "roster_rows_scored_per_trial": 1_000,
            "tardos_threshold": 2_100,
            "source_and_authority_secret_held_fixed": True,
            "fresh_session_and_successive_tardos_row_per_trial": True,
        },
        "summary": {
            "exact_session_attributions": exact,
            "exact_session_attribution_rate": exact / trials,
            "exact_session_attribution_wilson_95pct": _wilson(exact, trials),
            "valid_recipient_signatures": signature_valid,
            "false_accused_codebook_rows_total": false_rows_total,
            "expected_score_mean": statistics.fmean(expected_scores),
            "expected_score_population_sd": statistics.pstdev(expected_scores),
            "expected_score_min": min(expected_scores),
            "expected_score_max": max(expected_scores),
            "watermark_psnr_db_mean": statistics.fmean(psnr_values),
            "watermark_psnr_db_population_sd": statistics.pstdev(psnr_values),
            "released_pdf_bytes_mean": statistics.fmean(released_sizes),
            "source_pdf_bytes": int(rows[0]["source_bytes"]),
            "release_seconds_mean": statistics.fmean(release_times),
            "release_seconds_max": max(release_times),
            "trace_seconds_mean": statistics.fmean(trace_times),
            "trace_seconds_max": max(trace_times),
            "trial_seconds_mean": statistics.fmean(trial_times),
            "trial_seconds_max": max(trial_times),
        },
        "claim_boundary": {
            "measured": (
                "Repeated full cryptographic release, PDF marking, JPEG-Q55 transform, "
                "all-roster scoring, enrollment-bound signature lookup, and exact-session decision."
            ),
            "not_measured": (
                "Independent source documents, independent physical devices, a rare-event false-"
                "accusation probability, or Tardos theorem applicability to JPEG."
            ),
            "why_theorem_is_not_attached": (
                "The JPEG carrier can flip symbols at unanimous coalition positions; the separate "
                "attack matrix records that marking-condition failure."
            ),
        },
        "trials": rows,
        "runtime_seconds": time.perf_counter() - started,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=12)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/nishan/end-to-end-jpeg-trials.json"),
    )
    args = parser.parse_args()
    result = run(args.trials)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result["summary"], indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
