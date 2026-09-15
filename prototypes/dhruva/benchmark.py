#!/usr/bin/env python3
"""Reproducible preliminary benchmark for SIH26168 (Dhruva).

This is deliberately an honest component-stage benchmark.  It trains a causal
IMU-to-speed model on the first 40% of IO-VNBD sequence S1 and evaluates on the
last 60%, with synthetic GNSS outages that never cross the split.  It reports:

* constant-speed/constant-heading dead reckoning;
* a speed-component diagnostic using reference heading (not an end-to-end result);
* a phone-IMU position estimate using a learned speed and phone gyro yaw rate.

Outage windows are non-overlapping within each duration bucket.  Absolute endpoint
error is reported for every window; percentage drift is reported only when the
vehicle travels at least 50 m, because a percentage of near-zero distance is not a
meaningful navigation metric.

The script makes no map constraint and does not claim ISRO's <10% target.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

import matplotlib
import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


SAMPLE_PERIOD_S = 0.1
TRAIN_FRACTION = 0.40
FEATURE_WARMUP = 200
MIN_DISTANCE_FOR_DRIFT_M = 50.0
NAVY = "#0B1F33"
TEAL = "#15B8A6"
AMBER = "#F4B942"
RED = "#D95555"
GREY = "#75879A"


@dataclass
class OutageResult:
    duration_s: int
    start_row: int
    end_row: int
    distance_m: float
    distance_eligible_for_drift_ratio: bool
    baseline_error_m: float
    baseline_drift_ratio: float | None
    speed_diagnostic_error_m: float
    speed_diagnostic_drift_ratio: float | None
    phone_imu_error_m: float
    phone_imu_drift_ratio: float | None


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_pair(data_root: Path) -> tuple[np.ndarray, np.ndarray, Path, Path]:
    sequence = (
        data_root
        / "Synchronised V abd S datasets"
        / "Categorised IOVNB Dataset"
        / "S (Driver A)"
        / "S1"
    )
    phone_path = sequence / "S-S1.csv"
    reference_path = sequence / "V-S1.csv"
    if not phone_path.exists() or not reference_path.exists():
        raise FileNotFoundError(
            "expected IO-VNBD S1 under "
            f"{sequence}; pass the directory created by extracting the synchronized dataset"
        )

    # Phone columns: speed label for an integrity check, then accelerometer,
    # gravity, gyro, magnetic field and Android orientation.  GPS never enters X.
    phone_columns = tuple([3] + list(range(9, 24)))
    phone = np.loadtxt(
        phone_path,
        delimiter=",",
        skiprows=1,
        usecols=phone_columns,
        encoding="latin1",
    )
    # Reference columns: latitude, longitude, speed (km/h), heading, yaw rate.
    reference = np.loadtxt(
        reference_path,
        delimiter=",",
        skiprows=1,
        usecols=(2, 3, 4, 5, 14),
        encoding="latin1",
    )
    length = min(len(phone), len(reference))
    return phone[:length], reference[:length], phone_path, reference_path


def estimate_training_lag(phone: np.ndarray, reference: np.ndarray, train_end: int) -> dict:
    """Find the sub-second IMU/VBOX lag from gyro/turn-rate correlation.

    Only the training prefix participates, preventing test-timing leakage.
    Positive lag means phone row i corresponds to VBOX row i + lag.
    """
    best: tuple[float, int, int] | None = None
    for lag in range(-20, 21):
        for axis in range(3):
            if lag >= 0:
                phone_signal = phone[: train_end - lag, 7 + axis]
                reference_signal = reference[lag:train_end, 4]
            else:
                phone_signal = phone[-lag:train_end, 7 + axis]
                reference_signal = reference[: train_end + lag, 4]
            correlation = abs(float(np.corrcoef(phone_signal, reference_signal)[0, 1]))
            candidate = (correlation, lag, axis)
            if best is None or candidate[0] > best[0]:
                best = candidate
    assert best is not None
    return {"correlation": best[0], "lag_rows": best[1], "phone_gyro_axis": best[2]}


def apply_lag(phone: np.ndarray, reference: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag >= 0:
        phone = phone[:-lag] if lag else phone
        reference = reference[lag:]
    else:
        phone = phone[-lag:]
        reference = reference[:lag]
    length = min(len(phone), len(reference))
    return phone[:length], reference[:length]


def rolling_moments(array: np.ndarray, window: int) -> tuple[np.ndarray, np.ndarray]:
    cumulative = np.vstack([np.zeros((1, array.shape[1])), np.cumsum(array, axis=0)])
    cumulative_sq = np.vstack([np.zeros((1, array.shape[1])), np.cumsum(array * array, axis=0)])
    end = np.arange(len(array)) + 1
    start = np.maximum(0, end - window)
    count = (end - start)[:, None]
    total = cumulative[end] - cumulative[start]
    total_sq = cumulative_sq[end] - cumulative_sq[start]
    mean = total / count
    std = np.sqrt(np.maximum(0.0, total_sq / count - mean * mean))
    return mean, std


def causal_features(phone: np.ndarray) -> np.ndarray:
    accelerometer = phone[:, 1:4]
    gravity = phone[:, 4:7]
    linear_acceleration = accelerometer - gravity
    gyro = phone[:, 7:10]
    magnetic = phone[:, 10:13]
    base = np.column_stack(
        [
            accelerometer,
            gravity,
            linear_acceleration,
            gyro,
            magnetic,
            np.linalg.norm(accelerometer, axis=1),
            np.linalg.norm(linear_acceleration, axis=1),
            np.linalg.norm(gyro, axis=1),
            np.linalg.norm(magnetic, axis=1),
        ]
    )
    blocks = [base]
    for window in (5, 10, 20, 50, 100, 200):
        mean, std = rolling_moments(base, window)
        blocks.extend([mean, std])
    return np.column_stack(blocks)


def local_coordinates(reference: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    earth_radius = 6_371_000.0
    latitude = np.deg2rad(reference[:, 0])
    longitude = np.deg2rad(reference[:, 1])
    latitude_origin = float(np.nanmedian(latitude))
    east = (longitude - longitude[0]) * earth_radius * math.cos(latitude_origin)
    north = (latitude - latitude[0]) * earth_radius
    return east, north


def endpoint(
    east: np.ndarray,
    north: np.ndarray,
    speed: np.ndarray,
    yaw_rate: np.ndarray,
    reference: np.ndarray,
    start: int,
    end: int,
    mode: str,
    yaw_bias: float = 0.0,
) -> tuple[float, float, list[float], list[float]]:
    heading = math.radians(float(reference[start, 3]))
    x = float(east[start])
    y = float(north[start])
    xs = [x]
    ys = [y]
    initial_speed_bias = float(reference[start, 2] / 3.6 - speed[start])
    for row in range(start, end):
        if mode == "constant":
            velocity = float(reference[start, 2] / 3.6)
        elif mode == "speed_diagnostic":
            # Reference heading deliberately isolates the learned speed component.
            heading = math.radians(float(reference[row, 3]))
            velocity = max(0.0, float(speed[row] + initial_speed_bias))
        elif mode == "phone_imu":
            heading += float(yaw_rate[row] - yaw_bias) * SAMPLE_PERIOD_S
            velocity = max(0.0, float(speed[row]))
        else:
            raise ValueError(mode)
        x += velocity * math.sin(heading) * SAMPLE_PERIOD_S
        y += velocity * math.cos(heading) * SAMPLE_PERIOD_S
        xs.append(x)
        ys.append(y)
    return x, y, xs, ys


def evaluate(
    reference: np.ndarray,
    predicted_speed: np.ndarray,
    predicted_yaw: np.ndarray,
    yaw_target: np.ndarray,
    test_start: int,
) -> list[OutageResult]:
    east, north = local_coordinates(reference)
    true_speed = reference[:, 2] / 3.6
    results: list[OutageResult] = []
    for duration_s in (15, 30, 60, 120):
        length = round(duration_s / SAMPLE_PERIOD_S)
        # Duration-specific stride prevents the large overlap that otherwise
        # makes the reported window count look much larger than its information.
        for start in range(test_start, len(reference) - length, length):
            end = start + length
            calibration_start = max(FEATURE_WARMUP, start - 1200)
            # In a deployed system this bias is learned while GNSS is healthy.
            yaw_bias = float(np.mean(predicted_yaw[calibration_start:start] - yaw_target[calibration_start:start]))
            baseline_x, baseline_y, _, _ = endpoint(
                east, north, predicted_speed, predicted_yaw, reference, start, end, "constant"
            )
            diagnostic_x, diagnostic_y, _, _ = endpoint(
                east,
                north,
                predicted_speed,
                predicted_yaw,
                reference,
                start,
                end,
                "speed_diagnostic",
            )
            phone_x, phone_y, _, _ = endpoint(
                east,
                north,
                predicted_speed,
                predicted_yaw,
                reference,
                start,
                end,
                "phone_imu",
                yaw_bias=yaw_bias,
            )
            distance = float(np.sum(true_speed[start:end]) * SAMPLE_PERIOD_S)
            eligible = distance >= MIN_DISTANCE_FOR_DRIFT_M
            truth_x = float(east[end])
            truth_y = float(north[end])
            baseline_error = math.hypot(baseline_x - truth_x, baseline_y - truth_y)
            diagnostic_error = math.hypot(diagnostic_x - truth_x, diagnostic_y - truth_y)
            phone_error = math.hypot(phone_x - truth_x, phone_y - truth_y)
            results.append(
                OutageResult(
                    duration_s=duration_s,
                    start_row=start,
                    end_row=end,
                    distance_m=distance,
                    distance_eligible_for_drift_ratio=eligible,
                    baseline_error_m=baseline_error,
                    baseline_drift_ratio=baseline_error / distance if eligible else None,
                    speed_diagnostic_error_m=diagnostic_error,
                    speed_diagnostic_drift_ratio=(
                        diagnostic_error / distance if eligible else None
                    ),
                    phone_imu_error_m=phone_error,
                    phone_imu_drift_ratio=phone_error / distance if eligible else None,
                )
            )
    return results


def aggregate(results: list[OutageResult]) -> dict[str, dict[str, float | int]]:
    summary: dict[str, dict[str, float | int]] = {}
    for duration in (15, 30, 60, 120):
        rows = [item for item in results if item.duration_s == duration]
        eligible_rows = [item for item in rows if item.distance_eligible_for_drift_ratio]
        entry: dict[str, float | int] = {
            "non_overlapping_windows_total": len(rows),
            "windows_distance_ge_50m": len(eligible_rows),
            "windows_below_50m_excluded_from_ratio": len(rows) - len(eligible_rows),
            "median_distance_m_all": round(
                float(np.median([item.distance_m for item in rows])), 3
            ),
            "minimum_distance_m_all": round(
                float(np.min([item.distance_m for item in rows])), 3
            ),
        }
        for label, ratio_field, error_field in [
            ("constant", "baseline_drift_ratio", "baseline_error_m"),
            (
                "speed_component_reference_heading",
                "speed_diagnostic_drift_ratio",
                "speed_diagnostic_error_m",
            ),
            ("phone_imu", "phone_imu_drift_ratio", "phone_imu_error_m"),
        ]:
            absolute_errors = np.asarray([getattr(row, error_field) for row in rows])
            ratios = np.asarray(
                [getattr(row, ratio_field) for row in eligible_rows], dtype=float
            )
            entry[f"{label}_median_absolute_error_m_all"] = round(
                float(np.median(absolute_errors)), 3
            )
            entry[f"{label}_p95_absolute_error_m_all"] = round(
                float(np.percentile(absolute_errors, 95)), 3
            )
            entry[f"{label}_median_drift_percent_distance_ge_50m"] = round(
                float(np.median(ratios) * 100), 3
            )
            entry[f"{label}_p95_drift_percent_distance_ge_50m"] = round(
                float(np.percentile(ratios, 95) * 100), 3
            )
            entry[f"{label}_under_10_percent_share_distance_ge_50m"] = round(
                float(np.mean(ratios <= 0.10)), 4
            )
        summary[str(duration)] = entry
    return summary


def write_rows(results: list[OutageResult], output: Path) -> None:
    with output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(results[0]).keys()))
        writer.writeheader()
        writer.writerows(asdict(row) for row in results)


def drift_chart(summary: dict[str, dict[str, float | int]], output: Path) -> None:
    durations = [15, 30, 60, 120]
    labels = ["Constant speed + heading", "Speed model\n(reference heading diagnostic)", "Phone IMU\nspeed + gyro"]
    keys = [
        "constant_median_drift_percent_distance_ge_50m",
        "speed_component_reference_heading_median_drift_percent_distance_ge_50m",
        "phone_imu_median_drift_percent_distance_ge_50m",
    ]
    colors = [GREY, AMBER, TEAL]
    x = np.arange(len(durations))
    width = 0.24
    figure, axis = plt.subplots(figsize=(11.4, 4.2))
    for index, (label, key, color) in enumerate(zip(labels, keys, colors, strict=True)):
        values = [float(summary[str(duration)][key]) for duration in durations]
        bars = axis.bar(x + (index - 1) * width, values, width, label=label, color=color)
        for bar, value in zip(bars, values, strict=True):
            axis.text(bar.get_x() + bar.get_width() / 2, value + 1.2, f"{value:.1f}%", ha="center", fontsize=8, color=NAVY)
    axis.axhline(10, color=RED, linestyle="--", linewidth=1.6, label="ISRO target: 10%")
    axis.set_xticks(
        x,
        [
            f"{duration} s\nn={summary[str(duration)]['windows_distance_ge_50m']}"
            for duration in durations
        ],
    )
    axis.set_ylabel("median endpoint error / distance travelled (%)")
    axis.set_title(
        "Preliminary IO-VNBD S1 holdout — non-overlapping windows, distance ≥ 50 m",
        color=NAVY,
        weight="bold",
    )
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.grid(axis="y", alpha=0.17)
    axis.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False, fontsize=8.5)
    figure.tight_layout()
    figure.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def representative_track(
    results: list[OutageResult],
    reference: np.ndarray,
    predicted_speed: np.ndarray,
    predicted_yaw: np.ndarray,
    yaw_target: np.ndarray,
    output: Path,
) -> None:
    candidates = [
        item
        for item in results
        if item.duration_s == 60 and item.distance_eligible_for_drift_ratio
    ]
    median = float(np.median([item.phone_imu_drift_ratio for item in candidates]))
    chosen = min(candidates, key=lambda item: abs(item.phone_imu_drift_ratio - median))
    east, north = local_coordinates(reference)
    calibration_start = max(FEATURE_WARMUP, chosen.start_row - 1200)
    yaw_bias = float(
        np.mean(
            predicted_yaw[calibration_start : chosen.start_row]
            - yaw_target[calibration_start : chosen.start_row]
        )
    )
    paths = {}
    for mode in ("constant", "speed_diagnostic", "phone_imu"):
        _, _, xs, ys = endpoint(
            east,
            north,
            predicted_speed,
            predicted_yaw,
            reference,
            chosen.start_row,
            chosen.end_row,
            mode,
            yaw_bias=yaw_bias,
        )
        paths[mode] = (np.asarray(xs), np.asarray(ys))
    truth_x = east[chosen.start_row : chosen.end_row + 1]
    truth_y = north[chosen.start_row : chosen.end_row + 1]
    origin_x, origin_y = float(truth_x[0]), float(truth_y[0])
    figure, axis = plt.subplots(figsize=(8.0, 5.1))
    axis.plot(truth_x - origin_x, truth_y - origin_y, color=NAVY, linewidth=3, label="GNSS/VBOX truth")
    axis.plot(paths["constant"][0] - origin_x, paths["constant"][1] - origin_y, color=GREY, linestyle="--", linewidth=2, label="constant baseline")
    axis.plot(paths["speed_diagnostic"][0] - origin_x, paths["speed_diagnostic"][1] - origin_y, color=AMBER, linewidth=2, label="speed diagnostic (reference heading)")
    axis.plot(paths["phone_imu"][0] - origin_x, paths["phone_imu"][1] - origin_y, color=TEAL, linewidth=2.5, label="phone IMU estimate")
    axis.scatter([0], [0], color=NAVY, s=42, zorder=4)
    axis.set_aspect("equal", adjustable="datalim")
    axis.set_xlabel("east from outage start (m)")
    axis.set_ylabel("north from outage start (m)")
    axis.set_title(
        f"Representative 60 s outage · phone-IMU drift {chosen.phone_imu_drift_ratio * 100:.1f}%",
        color=NAVY,
        weight="bold",
    )
    axis.grid(alpha=0.16)
    axis.spines[["top", "right"]].set_visible(False)
    axis.legend(frameon=False, fontsize=8.5)
    figure.tight_layout()
    figure.savefig(output, dpi=220, bbox_inches="tight", facecolor="white")
    plt.close(figure)


def run(data_root: Path, output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    phone, reference, phone_path, reference_path = load_pair(data_root)
    raw_train_end = int(len(phone) * TRAIN_FRACTION)
    lag = estimate_training_lag(phone, reference, raw_train_end)
    phone, reference = apply_lag(phone, reference, int(lag["lag_rows"]))
    train_end = int(len(phone) * TRAIN_FRACTION)
    test_start = max(train_end, FEATURE_WARMUP)

    features = causal_features(phone)
    true_speed = reference[:, 2] / 3.6
    train_rows = np.arange(FEATURE_WARMUP, train_end)
    test_rows = np.arange(test_start, len(phone))
    model = HistGradientBoostingRegressor(
        max_iter=250,
        max_leaf_nodes=31,
        learning_rate=0.08,
        l2_regularization=1.0,
        random_state=42,
    )
    model.fit(features[train_rows], true_speed[train_rows])
    predicted_speed = np.maximum(0.0, model.predict(features))

    gyro = phone[:, 7:10]
    yaw_target = -np.deg2rad(reference[:, 4])
    design = np.column_stack([gyro, np.ones(len(gyro))])
    yaw_coefficients = np.linalg.lstsq(
        design[train_rows], yaw_target[train_rows], rcond=None
    )[0]
    predicted_yaw = design @ yaw_coefficients

    results = evaluate(
        reference,
        predicted_speed,
        predicted_yaw,
        yaw_target,
        test_start,
    )
    summary = aggregate(results)
    # IO-VNBD's phone header says km/h. Paired VBOX values show the phone numbers
    # are numerically m/s; this check records the evidence instead of silently
    # choosing a unit.
    phone_speed_numeric = phone[:train_end, 0]
    reference_speed_ms = true_speed[:train_end]
    unit_check = {
        "correlation_phone_numeric_vs_vbox_m_s": round(
            float(np.corrcoef(phone_speed_numeric, reference_speed_ms)[0, 1]), 5
        ),
        "median_phone_numeric_over_vbox_m_s": round(
            float(
                np.median(
                    phone_speed_numeric[reference_speed_ms > 1.0]
                    / reference_speed_ms[reference_speed_ms > 1.0]
                )
            ),
            5,
        ),
        "interpretation": "phone GPS speed header says km/h, but paired values are numerically consistent with m/s",
    }
    metrics = {
        "status": "preliminary; not target-compliant",
        "dataset": "IO-VNBD synchronized S1 subset",
        "split": {
            "method": "contiguous temporal holdout within S1",
            "train_rows": [FEATURE_WARMUP, train_end - 1],
            "test_rows": [test_start, len(phone) - 1],
            "final_required_upgrade": "hold out complete journeys/sequences and Indian field recordings",
        },
        "evaluation_policy": {
            "window_sampling": "non-overlapping within each duration bucket",
            "absolute_endpoint_error": "reported for every sampled outage",
            "percentage_drift": (
                f"reported only when distance travelled is at least {MIN_DISTANCE_FOR_DRIFT_M:.0f} m"
            ),
            "reason": "percentage error is unstable and misleading for stopped or near-stationary windows",
        },
        "alignment_estimated_on_training_only": lag,
        "speed_model": {
            "type": "HistGradientBoostingRegressor over causal raw/rolling IMU features",
            "feature_count": int(features.shape[1]),
            "test_mae_m_s": round(
                float(mean_absolute_error(true_speed[test_rows], predicted_speed[test_rows])), 4
            ),
            "test_correlation": round(
                float(np.corrcoef(true_speed[test_rows], predicted_speed[test_rows])[0, 1]), 4
            ),
        },
        "yaw_model": {
            "type": "training-fit linear phone-gyro mount map with pre-outage bias calibration",
            "coefficients": [round(float(value), 8) for value in yaw_coefficients],
            "test_median_absolute_error_deg_s": round(
                float(np.median(np.abs(predicted_yaw[test_rows] - yaw_target[test_rows])) * 180 / math.pi),
                4,
            ),
            "test_correlation": round(
                float(np.corrcoef(predicted_yaw[test_rows], yaw_target[test_rows])[0, 1]), 4
            ),
        },
        "phone_speed_unit_integrity_check": unit_check,
        "outages": summary,
        "limitations": [
            "No road-map constraint or factor-graph smoother is included.",
            "The speed-component reference-heading curve is an ablation, not an end-to-end navigation result.",
            "The holdout is a contiguous part of one sequence, not a held-out journey/device/Indian-road benchmark.",
            "The current phone-IMU result remains above the SIH26168 10% median drift target.",
            "Long-duration buckets contain only the non-overlapping windows available in one S1 holdout; no 200-window claim is made.",
        ],
    }
    (output / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")
    manifest = {
        "source": "https://github.com/onyekpeu/IO-VNBD",
        "phone_file": str(phone_path),
        "phone_sha256": sha256(phone_path),
        "reference_file": str(reference_path),
        "reference_sha256": sha256(reference_path),
        "rows_after_alignment": len(phone),
        "split_indices_determined_before_model_fit": True,
        "manifest_written_after_run": True,
        "immutable_pre_fit_commit_exists": False,
        "train_end_exclusive": train_end,
        "test_start_inclusive": test_start,
        "random_state": 42,
    }
    (output / "split-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    write_rows(results, output / "outage-results.csv")
    drift_chart(summary, output / "drift-by-duration.png")
    representative_track(
        results,
        reference,
        predicted_speed,
        predicted_yaw,
        yaw_target,
        output / "representative-60s-track.png",
    )
    print(json.dumps(metrics, indent=2))
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        required=True,
        help="directory into which the synchronized IO-VNBD archive was extracted",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/dhruva"),
    )
    args = parser.parse_args()
    run(args.data_root.resolve(), args.output.resolve())


if __name__ == "__main__":
    main()
