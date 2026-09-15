#!/usr/bin/env python3
"""Reproduce Dhruva, then audit fixed-model transfer and missing baselines.

This is a diagnostic, not a new navigation algorithm or a SOTA comparison.
No parameters are selected from the evaluation journeys. The original
benchmark's ideal reference initial state and pre-outage VBOX yaw calibration
are retained and explicitly disclosed, so this is not a deployment test.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys
import time

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "prototypes/dhruva"))
import benchmark as original  # noqa: E402


def load_sequence(data_root: Path, name: str):
    folder = (
        data_root / "Synchronised V abd S datasets"
        / "Categorised IOVNB Dataset" / "S (Driver A)" / name
    )
    phone_path, reference_path = folder / f"S-{name}.csv", folder / f"V-{name}.csv"
    phone = np.loadtxt(phone_path, delimiter=",", skiprows=1,
                       usecols=tuple([3] + list(range(9, 24))), encoding="latin1")
    reference = np.loadtxt(reference_path, delimiter=",", skiprows=1,
                           usecols=(2, 3, 4, 5, 14), encoding="latin1")
    length = min(len(phone), len(reference))
    return phone[:length], reference[:length], phone_path, reference_path


def evaluate(reference, speed, yaw, start_row):
    east, north = original.local_coordinates(reference)
    true_speed = reference[:, 2] / 3.6
    true_yaw = -np.deg2rad(reference[:, 4])
    rows = []
    for duration in (15, 30, 60, 120):
        length = round(duration / original.SAMPLE_PERIOD_S)
        for start in range(start_row, len(reference) - length, length):
            end = start + length
            # Match the original's privileged healthy-GNSS calibration proxy.
            calibration_start = max(original.FEATURE_WARMUP, start - 1200)
            yaw_bias = float(np.mean(yaw[calibration_start:start] - true_yaw[calibration_start:start]))
            heading = np.deg2rad(reference[start, 3]) + np.cumsum(
                yaw[start:end] - yaw_bias
            ) * original.SAMPLE_PERIOD_S
            velocities = {
                "original_learned_speed": speed[start:end],
                "constant_speed_with_gyro": np.full(length, true_speed[start]),
                "learned_speed_initial_offset": speed[start:end] + true_speed[start] - speed[start],
                "learned_speed_preoutage_mean_offset": speed[start:end] + np.mean(
                    true_speed[calibration_start:start] - speed[calibration_start:start]
                ),
            }
            distance = float(np.sum(true_speed[start:end]) * original.SAMPLE_PERIOD_S)
            for method, velocity in velocities.items():
                velocity = np.maximum(velocity, 0)
                x = east[start] + float(np.sum(velocity * np.sin(heading)) * original.SAMPLE_PERIOD_S)
                y = north[start] + float(np.sum(velocity * np.cos(heading)) * original.SAMPLE_PERIOD_S)
                error = float(np.hypot(x - east[end], y - north[end]))
                rows.append({
                    "duration_s": duration, "start_row": start, "end_row": end,
                    "method": method, "distance_m": distance, "endpoint_error_m": error,
                    "drift_percent": 100 * error / distance if distance >= 50 else None,
                })
    return rows


def summarize(rows):
    summaries = []
    for duration in (15, 30, 60, 120):
        for method in sorted({row["method"] for row in rows}):
            group = [row for row in rows if row["duration_s"] == duration and row["method"] == method]
            eligible = [row["drift_percent"] for row in group if row["drift_percent"] is not None]
            summaries.append({
                "duration_s": duration, "method": method,
                "windows": len(group), "distance_eligible_windows": len(eligible),
                "median_endpoint_error_m": float(np.median([row["endpoint_error_m"] for row in group])),
                "median_drift_percent": float(np.median(eligible)) if eligible else None,
                "p95_drift_percent": float(np.percentile(eligible, 95)) if eligible else None,
                "fraction_under_10_percent": float(np.mean(np.asarray(eligible) < 10)) if eligible else None,
            })
    return summaries


def run(data_root: Path, output: Path):
    output.mkdir(parents=True, exist_ok=True)
    plan_path = output / "experiment-manifest.json"
    if plan_path.exists():
        raise FileExistsError(f"Use a fresh output directory: {plan_path}")
    sequences = ("S1", "S2", "S3a", "S4")
    files = {}
    for name in sequences:
        _, _, phone_path, reference_path = load_sequence(data_root, name)
        files[name] = {"phone_sha256": original.sha256(phone_path),
                       "reference_sha256": original.sha256(reference_path)}
    manifest = {
        "purpose": "fixed-model reproduction and transfer diagnostic; no SOTA claim",
        "training": "first 40% of S1 only, rows after 200-sample feature warmup",
        "evaluation": "S1 remaining 60%; S2/S3a/S4 after 120-second calibration prefix",
        "lag": "estimate on S1 training prefix, apply unchanged to all sequences",
        "parameters": "identical to original benchmark; no tuning on transfer journeys",
        "methods": ["original_learned_speed", "constant_speed_with_gyro",
                    "learned_speed_initial_offset", "learned_speed_preoutage_mean_offset"],
        "limitations": [
            "Reference initial position, heading and speed are idealized healthy-GNSS proxies.",
            "Pre-outage yaw calibration uses VBOX yaw, not a demonstrated smartphone GNSS implementation.",
            "Same driver group only; no claimed device/driver/Indian-road generalization.",
            "Unchanged timing alignment can expose timing transfer errors as well as model transfer errors.",
            "Diagnostic comparisons are exploratory, not an untouched confirmatory test of a new method.",
            "No confidence interval treats outages from one journey as independent journeys.",
        ],
        "input_hashes": files,
        "script_sha256": original.sha256(Path(__file__)),
        "original_benchmark_sha256": original.sha256(Path(original.__file__)),
        "written_before_fit": True,
    }
    plan_path.write_text(json.dumps(manifest, indent=2) + "\n")
    phone, reference, _, _ = load_sequence(data_root, "S1")
    lag = original.estimate_training_lag(phone, reference, int(len(phone) * 0.4))
    phone, reference = original.apply_lag(phone, reference, lag["lag_rows"])
    features = original.causal_features(phone)
    train_end = int(len(phone) * 0.4)
    train = slice(original.FEATURE_WARMUP, train_end)
    model = HistGradientBoostingRegressor(max_iter=250, max_leaf_nodes=31,
        learning_rate=0.08, l2_regularization=1.0, random_state=42)
    before = time.monotonic()
    model.fit(features[train], reference[train, 2] / 3.6)
    fit_seconds = time.monotonic() - before
    yaw_design = np.column_stack([phone[:, 7:10], np.ones(len(phone))])
    yaw_coefficients = np.linalg.lstsq(yaw_design[train], -np.deg2rad(reference[train, 4]), rcond=None)[0]
    results = {}
    all_rows = []
    for name in sequences:
        phone, reference, _, _ = load_sequence(data_root, name)
        phone, reference = original.apply_lag(phone, reference, lag["lag_rows"])
        speed = np.maximum(model.predict(original.causal_features(phone)), 0)
        yaw = np.column_stack([phone[:, 7:10], np.ones(len(phone))]) @ yaw_coefficients
        start = train_end if name == "S1" else 1400
        rows = evaluate(reference, speed, yaw, start)
        for row in rows:
            row["sequence"] = name
        all_rows.extend(rows)
        results[name] = summarize(rows)
        if name == "S1":
            # Check the vectorized integrator against the existing implementation.
            existing = original.evaluate(reference, speed, yaw, -np.deg2rad(reference[:, 4]), start)
            current = [row for row in rows if row["method"] == "original_learned_speed"]
            np.testing.assert_allclose([row["endpoint_error_m"] for row in current],
                [row.phone_imu_error_m for row in existing], rtol=1e-8, atol=1e-7)
        print(json.dumps({"sequence": name, "sixty_second_results": [
            row for row in results[name] if row["duration_s"] == 60
        ]}), flush=True)
    with (output / "windows.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(all_rows[0]))
        writer.writeheader()
        writer.writerows(all_rows)
    (output / "results.json").write_text(json.dumps({
        "fit_seconds": fit_seconds, "lag": lag, "summaries": results,
        "s1_integrator_matches_existing": True, "limitations": manifest["limitations"],
    }, indent=2) + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    run(args.data_root, args.output)
