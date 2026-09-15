#!/usr/bin/env python3
"""Fixed-window, timestamp-aligned Dhruva ablation diagnostic.

This is an exploratory offline diagnostic.  Clock alignment, the outage-start
position/heading/speed, pre-outage VBOX yaw calibration, reference-speed
branches, and reference-heading branches are explicitly privileged oracles.
They are not a deployable phone-only navigation path.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.ensemble import HistGradientBoostingRegressor

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from prototypes.dhruva import benchmark as legacy
from prototypes.dhruva.time_alignment import (
    AlignedSegment,
    TimestampedPair,
    align_pair,
    contiguous_spans,
    estimate_clock_offset,
    load_timestamped_pair,
)


SEQUENCES = ("S1", "S2", "S3a", "S4")
PHONE_UTC_OFFSET_S = 3600.0
DURATION_ROWS = 600
CALIBRATION_ROWS = 1200
FEATURE_WARMUP_ROWS = 200
MIN_DISTANCE_FOR_DRIFT_M = 50.0
REFERENCE_CADENCE_S = 0.1
CADENCE_TOLERANCE_S = 1e-3
CLOCK_PREFIX_S = 140.0
MODEL_CONSTANTS = {
    "max_iter": 250,
    "max_leaf_nodes": 31,
    "learning_rate": 0.08,
    "l2_regularization": 1.0,
    "random_state": 42,
}
SPEED_PROFILES = ("learned_raw", "learned_initial_offset", "reference_oracle")
HEADING_PROFILES = ("phone_gyro", "reference_oracle")
GYRO_CALIBRATION_PROFILES = ("frozen_s1", "journey_prefix")
BASELINE_METHOD = "constant_reference_initialized"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_value(value: Any) -> Any:
    """Convert numpy scalars/arrays and non-finite floats to strict JSON values."""

    if isinstance(value, np.ndarray):
        return [_json_value(item) for item in value.tolist()]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        value = float(value)
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _write_json(path: Path, value: Any, *, exclusive: bool = False) -> None:
    mode = "x" if exclusive else "w"
    with path.open(mode, encoding="utf-8") as handle:
        json.dump(_json_value(value), handle, indent=2, sort_keys=True, allow_nan=False)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())


def method_name(
    speed_profile: str, heading_profile: str, gyro_calibration_profile: str
) -> str:
    return (
        f"speed={speed_profile}|heading={heading_profile}|"
        f"gyro={gyro_calibration_profile}"
    )


METHODS = tuple(
    method_name(speed, heading, gyro)
    for speed in SPEED_PROFILES
    for heading in HEADING_PROFILES
    for gyro in GYRO_CALIBRATION_PROFILES
) + (BASELINE_METHOD,)


def integrate_displacement(
    times: np.ndarray, velocities: np.ndarray, headings: np.ndarray
) -> tuple[float, float]:
    """Integrate velocity samples at their left-endpoint headings."""

    times = np.asarray(times, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    headings = np.asarray(headings, dtype=float)
    if times.ndim != 1 or velocities.ndim != 1 or headings.ndim != 1:
        raise ValueError("times, velocities and headings must be one-dimensional")
    if len(times) != len(velocities) + 1 or len(velocities) != len(headings):
        raise ValueError("times must have L+1 endpoints for L velocity and heading samples")
    if not (
        np.all(np.isfinite(times))
        and np.all(np.isfinite(velocities))
        and np.all(np.isfinite(headings))
    ):
        raise ValueError("integration inputs must be finite")
    dt = np.diff(times)
    if np.any(dt <= 0.0):
        raise ValueError("integration timestamps must be strictly increasing")
    east = float(np.sum(velocities * np.sin(headings) * dt))
    north = float(np.sum(velocities * np.cos(headings) * dt))
    return east, north


def phone_headings(
    initial_heading: float, yaw: np.ndarray, dt: np.ndarray, bias: float
) -> np.ndarray:
    """Return left-endpoint headings using only preceding yaw increments."""

    yaw = np.asarray(yaw, dtype=float)
    dt = np.asarray(dt, dtype=float)
    if yaw.ndim != 1 or dt.ndim != 1 or len(yaw) != len(dt):
        raise ValueError("yaw and dt must be one-dimensional arrays of equal length")
    if not (
        math.isfinite(initial_heading)
        and math.isfinite(bias)
        and np.all(np.isfinite(yaw))
        and np.all(np.isfinite(dt))
    ):
        raise ValueError("heading inputs must be finite")
    if np.any(dt <= 0.0):
        raise ValueError("heading intervals must be positive")
    headings = np.empty(len(yaw), dtype=float)
    if len(headings) == 0:
        return headings
    headings[0] = initial_heading
    if len(headings) > 1:
        headings[1:] = initial_heading + np.cumsum((yaw[:-1] - bias) * dt[:-1])
    return headings


def _reference_lookup(
    segments: list[AlignedSegment],
) -> dict[int, list[tuple[int, int]]]:
    lookup: dict[int, list[tuple[int, int]]] = defaultdict(list)
    for segment_index, segment in enumerate(segments):
        for local_index, raw_row in enumerate(segment.reference_rows):
            lookup[int(raw_row)].append((segment_index, local_index))
    return dict(lookup)


def _base_window_record(
    pair: TimestampedPair, start: int, end: int, calibration_start: int
) -> dict[str, Any]:
    reference_count = len(pair.reference_time_s)
    return {
        "window_id": f"raw-{start}-{end}",
        "raw_start_row": start,
        "raw_end_row": end,
        "calibration_raw_bounds": [calibration_start, start],
        "start_time_s": (
            float(pair.reference_time_s[start]) if 0 <= start < reference_count else None
        ),
        "end_time_s": (
            float(pair.reference_time_s[end]) if 0 <= end < reference_count else None
        ),
        "actual_duration_s": (
            float(pair.reference_time_s[end] - pair.reference_time_s[start])
            if 0 <= start < reference_count and 0 <= end < reference_count
            else None
        ),
        "included": False,
        "exclusion_reason": None,
        "segment_index": None,
        "local_bounds": None,
        "calibration_local_bounds": None,
        "phone_span": None,
        "reference_span": None,
        "phone_bracket_row_bounds": None,
    }


def make_windows(
    pair: TimestampedPair,
    segments: list[AlignedSegment],
    first_candidate_row: int,
    duration_rows: int = DURATION_ROWS,
    calibration_rows: int = CALIBRATION_ROWS,
) -> list[dict]:
    """Enumerate a gap-safe fixed raw-reference grid without using labels."""

    if duration_rows <= 0 or calibration_rows <= 0:
        raise ValueError("duration_rows and calibration_rows must be positive")
    if first_candidate_row < 0 or first_candidate_row % duration_rows:
        raise ValueError("first_candidate_row must lie on the raw-row duration grid")
    reference_count = len(pair.reference_time_s)
    lookup = _reference_lookup(segments)
    records: list[dict] = []
    for start in range(first_candidate_row, reference_count, duration_rows):
        end = start + duration_rows
        calibration_start = start - calibration_rows
        record = _base_window_record(pair, start, end, calibration_start)
        if end >= reference_count:
            record["exclusion_reason"] = "endpoint_out_of_range"
            records.append(record)
            continue
        if calibration_start < 0:
            record["exclusion_reason"] = "insufficient_feature_history"
            records.append(record)
            continue

        required_rows = range(calibration_start, end + 1)
        matches = [lookup.get(raw_row, []) for raw_row in required_rows]
        if any(len(items) > 1 for items in matches):
            record["exclusion_reason"] = "ambiguous_reference_rows"
            records.append(record)
            continue
        if any(len(items) == 0 for items in matches):
            record["exclusion_reason"] = "missing_or_gap"
            records.append(record)
            continue
        segment_indices = {items[0][0] for items in matches}
        if len(segment_indices) != 1:
            record["exclusion_reason"] = "missing_or_gap"
            records.append(record)
            continue
        segment_index = segment_indices.pop()
        local_indices = np.asarray([items[0][1] for items in matches], dtype=int)
        if not np.array_equal(
            local_indices, np.arange(local_indices[0], local_indices[0] + len(local_indices))
        ):
            record["exclusion_reason"] = "missing_or_gap"
            records.append(record)
            continue
        calibration_local_start = int(local_indices[0])
        start_local = int(local_indices[calibration_rows])
        end_local = int(local_indices[-1])
        if calibration_local_start < FEATURE_WARMUP_ROWS:
            record["exclusion_reason"] = "insufficient_feature_history"
            records.append(record)
            continue

        relevant_times = np.asarray(
            pair.reference_time_s[calibration_start : end + 1], dtype=float
        )
        intervals = np.diff(relevant_times)
        actual_duration = float(pair.reference_time_s[end] - pair.reference_time_s[start])
        expected_duration = duration_rows * REFERENCE_CADENCE_S
        if (
            not np.all(np.isfinite(relevant_times))
            or np.any(np.abs(intervals - REFERENCE_CADENCE_S) > CADENCE_TOLERANCE_S)
            or abs(actual_duration - expected_duration) > CADENCE_TOLERANCE_S
        ):
            record["exclusion_reason"] = "non_10hz_reference_cadence"
            records.append(record)
            continue

        segment = segments[segment_index]
        bracket_left = segment.phone_left_rows[calibration_local_start : end_local + 1]
        bracket_right = segment.phone_right_rows[calibration_local_start : end_local + 1]
        record.update(
            {
                "included": True,
                "segment_index": segment_index,
                "local_bounds": [start_local, end_local],
                "calibration_local_bounds": [calibration_local_start, start_local],
                "phone_span": list(segment.phone_span),
                "reference_span": list(segment.reference_span),
                "phone_bracket_row_bounds": [
                    int(np.min(bracket_left)),
                    int(np.max(bracket_right)),
                ],
            }
        )
        records.append(record)
    return records


def evaluate_window_method(
    window: dict,
    segment: AlignedSegment,
    predicted_speed: np.ndarray,
    predicted_yaw: np.ndarray,
    *,
    speed_profile: str,
    heading_profile: str,
    gyro_calibration_profile: str,
) -> dict[str, Any]:
    """Evaluate one fixed branch; selection and fit happen outside this function."""

    if not window.get("included"):
        raise ValueError("cannot evaluate an excluded window")
    if speed_profile not in SPEED_PROFILES:
        raise ValueError(f"unknown speed profile: {speed_profile}")
    if heading_profile not in HEADING_PROFILES:
        raise ValueError(f"unknown heading profile: {heading_profile}")
    if gyro_calibration_profile not in GYRO_CALIBRATION_PROFILES:
        raise ValueError(f"unknown gyro calibration profile: {gyro_calibration_profile}")
    predicted_speed = np.asarray(predicted_speed, dtype=float)
    predicted_yaw = np.asarray(predicted_yaw, dtype=float)
    if len(predicted_speed) != len(segment.time_s) or len(predicted_yaw) != len(segment.time_s):
        raise ValueError("prediction arrays must match the aligned segment")

    start, end = (int(value) for value in window["local_bounds"])
    calibration_start, calibration_end = (
        int(value) for value in window["calibration_local_bounds"]
    )
    if calibration_end != start or calibration_end - calibration_start != CALIBRATION_ROWS:
        raise ValueError("window must contain exactly 1200 pre-outage calibration samples")
    times = segment.time_s[start : end + 1]
    dt = np.diff(times)
    reference = segment.reference

    if speed_profile == "learned_raw":
        velocity = np.maximum(0.0, predicted_speed[start:end])
    elif speed_profile == "learned_initial_offset":
        initial_offset = float(reference[start, 2] / 3.6 - predicted_speed[start])
        velocity = np.maximum(0.0, predicted_speed[start:end] + initial_offset)
    else:
        velocity = reference[start:end, 2] / 3.6

    initial_heading = math.radians(float(reference[start, 3]))
    if heading_profile == "phone_gyro":
        yaw_target_history = -np.deg2rad(reference[calibration_start:start, 4])
        yaw_bias = float(
            np.mean(predicted_yaw[calibration_start:start] - yaw_target_history)
        )
        headings = phone_headings(
            initial_heading, predicted_yaw[start:end], dt, yaw_bias
        )
    else:
        yaw_bias = None
        headings = np.deg2rad(reference[start:end, 3])

    predicted_east, predicted_north = integrate_displacement(times, velocity, headings)
    east, north = legacy.local_coordinates(reference)
    truth_east = float(east[end] - east[start])
    truth_north = float(north[end] - north[start])
    distance = float(np.sum((reference[start:end, 2] / 3.6) * dt))
    endpoint_error = math.hypot(
        predicted_east - truth_east, predicted_north - truth_north
    )
    eligible = distance >= MIN_DISTANCE_FOR_DRIFT_M
    return {
        "predicted_east_m": predicted_east,
        "predicted_north_m": predicted_north,
        "truth_east_m": truth_east,
        "truth_north_m": truth_north,
        "distance_m": distance,
        "distance_eligible_for_drift_ratio": eligible,
        "endpoint_error_m": endpoint_error,
        "drift_ratio": endpoint_error / distance if eligible else None,
        "yaw_bias_rad_s": yaw_bias,
        "privileged_initial_position": True,
        "privileged_initial_heading": True,
        "privileged_initial_speed": speed_profile == "learned_initial_offset",
        "reference_speed_oracle": speed_profile == "reference_oracle",
        "reference_heading_oracle": heading_profile == "reference_oracle",
        "pre_outage_vbox_yaw_calibration": heading_profile == "phone_gyro",
    }


def _evaluate_constant(window: dict, segment: AlignedSegment) -> dict[str, Any]:
    start, end = (int(value) for value in window["local_bounds"])
    times = segment.time_s[start : end + 1]
    dt = np.diff(times)
    reference = segment.reference
    velocity = np.full(end - start, float(reference[start, 2] / 3.6))
    headings = np.full(end - start, math.radians(float(reference[start, 3])))
    predicted_east, predicted_north = integrate_displacement(times, velocity, headings)
    east, north = legacy.local_coordinates(reference)
    truth_east = float(east[end] - east[start])
    truth_north = float(north[end] - north[start])
    distance = float(np.sum((reference[start:end, 2] / 3.6) * dt))
    endpoint_error = math.hypot(
        predicted_east - truth_east, predicted_north - truth_north
    )
    eligible = distance >= MIN_DISTANCE_FOR_DRIFT_M
    return {
        "predicted_east_m": predicted_east,
        "predicted_north_m": predicted_north,
        "truth_east_m": truth_east,
        "truth_north_m": truth_north,
        "distance_m": distance,
        "distance_eligible_for_drift_ratio": eligible,
        "endpoint_error_m": endpoint_error,
        "drift_ratio": endpoint_error / distance if eligible else None,
        "yaw_bias_rad_s": None,
        "privileged_initial_position": True,
        "privileged_initial_heading": True,
        "privileged_initial_speed": True,
        "reference_speed_oracle": False,
        "reference_heading_oracle": False,
        "pre_outage_vbox_yaw_calibration": False,
    }


def _validate_segments(segments: list[AlignedSegment], sequence: str) -> None:
    if not segments:
        raise ValueError(f"{sequence}: alignment returned no segments")
    for segment_index, segment in enumerate(segments):
        if len(segment.reference_rows) == 0:
            raise ValueError(f"{sequence}: aligned segment {segment_index} is empty")
        if not np.all(np.diff(segment.reference_rows) == 1):
            raise ValueError(
                f"{sequence}: aligned segment {segment_index} does not preserve consecutive raw rows"
            )
        if not np.all(np.isfinite(segment.time_s)) or np.any(np.diff(segment.time_s) <= 0.0):
            raise ValueError(
                f"{sequence}: aligned segment {segment_index} has nonpositive timestamp intervals"
            )


def _first_s1_candidate(pair: TimestampedPair, cutoff_s: float) -> int:
    for raw_row in range(0, len(pair.reference_time_s), DURATION_ROWS):
        if pair.reference_time_s[raw_row] >= cutoff_s:
            return raw_row
    raise ValueError("S1 contains no raw-row grid candidate at or after the training cutoff")


def _segment_provenance(segments: list[AlignedSegment]) -> list[dict[str, Any]]:
    records = []
    for index, segment in enumerate(segments):
        records.append(
            {
                "segment_index": index,
                "row_count": len(segment.time_s),
                "phone_span": list(segment.phone_span),
                "reference_span": list(segment.reference_span),
                "raw_reference_row_bounds": [
                    int(segment.reference_rows[0]),
                    int(segment.reference_rows[-1]),
                ],
                "time_bounds_s": [float(segment.time_s[0]), float(segment.time_s[-1])],
                "phone_bracket_row_bounds": [
                    int(np.min(segment.phone_left_rows)),
                    int(np.max(segment.phone_right_rows)),
                ],
            }
        )
    return records


def _training_indices(
    pair: TimestampedPair,
    segments: list[AlignedSegment],
    residual_offset_s: float,
    cutoff_s: float,
) -> list[dict[str, int]]:
    lookup = _reference_lookup(segments)
    records: list[dict[str, int]] = []
    shifted_phone_times = pair.phone_time_s + residual_offset_s
    for segment_index, segment in enumerate(segments):
        for local_index in range(FEATURE_WARMUP_ROWS, len(segment.time_s)):
            raw_row = int(segment.reference_rows[local_index])
            left = int(segment.phone_left_rows[local_index])
            right = int(segment.phone_right_rows[local_index])
            if len(lookup[raw_row]) != 1:
                continue
            if not (
                segment.time_s[local_index] < cutoff_s
                and shifted_phone_times[left] < cutoff_s
                and shifted_phone_times[right] < cutoff_s
            ):
                continue
            records.append(
                {
                    "segment_index": segment_index,
                    "local_index": local_index,
                    "raw_reference_row": raw_row,
                    "phone_left_row": left,
                    "phone_right_row": right,
                }
            )
    if not records:
        raise ValueError("S1 has no eligible aligned training rows")
    return records


def _prefix_fit_indices(
    pair: TimestampedPair,
    segments: list[AlignedSegment],
    estimate: dict,
) -> list[dict[str, int]]:
    segment = segments[0]
    phone_prefix_end = contiguous_spans(pair.phone_time_s, pair.phone_elapsed_ms)[0][1]
    phone_prefix_end = min(
        phone_prefix_end,
        int(
            np.searchsorted(
                pair.phone_time_s[:phone_prefix_end],
                pair.phone_time_s[0] + CLOCK_PREFIX_S,
                side="right",
            )
        ),
    )
    reference_prefix_end = contiguous_spans(pair.reference_time_s)[0][1]
    reference_prefix_end = min(
        reference_prefix_end,
        int(
            np.searchsorted(
                pair.reference_time_s[:reference_prefix_end],
                pair.reference_time_s[0] + CLOCK_PREFIX_S,
                side="right",
            )
        ),
    )
    phone_bounds = estimate["phone_prefix_time_bounds_s"]
    reference_bounds = estimate["reference_prefix_time_bounds_s"]
    records: list[dict[str, int]] = []
    for local_index in range(FEATURE_WARMUP_ROWS, len(segment.time_s)):
        raw_row = int(segment.reference_rows[local_index])
        left = int(segment.phone_left_rows[local_index])
        right = int(segment.phone_right_rows[local_index])
        if raw_row >= reference_prefix_end or left >= phone_prefix_end or right >= phone_prefix_end:
            continue
        if not (
            reference_bounds[0] <= segment.time_s[local_index] <= reference_bounds[1]
            and phone_bounds[0] <= pair.phone_time_s[left] <= phone_bounds[1]
            and phone_bounds[0] <= pair.phone_time_s[right] <= phone_bounds[1]
        ):
            continue
        records.append(
            {
                "segment_index": 0,
                "local_index": local_index,
                "raw_reference_row": raw_row,
                "phone_left_row": left,
                "phone_right_row": right,
            }
        )
    if len(records) < 50:
        raise ValueError(
            "journey-prefix gyro calibration requires at least 50 finite aligned rows "
            "after the 200-row warmup inside both original clock prefixes"
        )
    return records


def _features_by_segment(segments: list[AlignedSegment]) -> list[np.ndarray]:
    return [legacy.causal_features(segment.phone) for segment in segments]


def _fit_gyro(
    segments: list[AlignedSegment], indices: list[dict[str, int]]
) -> np.ndarray:
    design_rows = []
    targets = []
    for record in indices:
        segment = segments[record["segment_index"]]
        local_index = record["local_index"]
        design_rows.append([*segment.phone[local_index, 7:10], 1.0])
        targets.append(-math.radians(float(segment.reference[local_index, 4])))
    design = np.asarray(design_rows, dtype=float)
    target = np.asarray(targets, dtype=float)
    finite = np.all(np.isfinite(design), axis=1) & np.isfinite(target)
    if int(np.sum(finite)) < 50:
        raise ValueError("gyro calibration requires at least 50 finite fit rows")
    return np.linalg.lstsq(design[finite], target[finite], rcond=None)[0]


def _predict_yaw(segment: AlignedSegment, coefficients: np.ndarray) -> np.ndarray:
    design = np.column_stack([segment.phone[:, 7:10], np.ones(len(segment.phone))])
    return design @ coefficients


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    return float(np.percentile(np.asarray(values, dtype=float), percentile))


def _summaries(rows: list[dict[str, Any]], manifest_windows: list[dict]) -> dict:
    summary: dict[str, dict[str, dict[str, Any]]] = {}
    for sequence in SEQUENCES:
        sequence_windows = [row for row in manifest_windows if row["sequence"] == sequence]
        exclusion_counts = Counter(
            row["exclusion_reason"] for row in sequence_windows if not row["included"]
        )
        summary[sequence] = {}
        for method in METHODS:
            method_rows = [
                row for row in rows if row["sequence"] == sequence and row["method"] == method
            ]
            valid = [row for row in method_rows if row["included"]]
            eligible = [
                row for row in valid if row["distance_eligible_for_drift_ratio"]
            ]
            errors = [float(row["endpoint_error_m"]) for row in valid]
            ratios = [float(row["drift_ratio"]) for row in eligible]
            summary[sequence][method] = {
                "candidate_count": len(sequence_windows),
                "valid_window_count": len(valid),
                "eligible_drift_window_count": len(eligible),
                "below_50m_ratio_excluded_count": len(valid) - len(eligible),
                "coverage_fraction": (
                    len(valid) / len(sequence_windows) if sequence_windows else None
                ),
                "exclusion_counts": dict(sorted(exclusion_counts.items())),
                "median_absolute_error_m": _percentile(errors, 50),
                "p95_absolute_error_m": _percentile(errors, 95),
                "median_eligible_drift_percent": (
                    _percentile(ratios, 50) * 100 if ratios else None
                ),
                "p95_eligible_drift_percent": (
                    _percentile(ratios, 95) * 100 if ratios else None
                ),
                "fraction_eligible_windows_below_10_percent": (
                    float(np.mean(np.asarray(ratios) < 0.10)) if ratios else None
                ),
            }
    return summary


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        raise ValueError("refusing to write an empty window/method table")
    fields = list(rows[0])
    with path.open("x", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    key: (
                        json.dumps(_json_value(value), separators=(",", ":"))
                        if isinstance(value, (list, tuple, dict))
                        else _json_value(value)
                    )
                    for key, value in row.items()
                }
            )


def run(data_root: Path, output: Path) -> dict:
    run_started_utc = _utc_now()
    data_root = Path(data_root).resolve()
    output = Path(output).resolve()
    if output.exists():
        raise FileExistsError(f"output directory already exists: {output}")

    pairs: dict[str, TimestampedPair] = {}
    segments_by_sequence: dict[str, list[AlignedSegment]] = {}
    clock_estimates: dict[str, dict] = {}
    all_windows: list[dict[str, Any]] = []
    for sequence in SEQUENCES:
        pair = load_timestamped_pair(data_root, sequence, PHONE_UTC_OFFSET_S)
        estimate = estimate_clock_offset(pair)
        if estimate["low_confidence"]:
            raise ValueError(
                f"{sequence}: low-confidence clock alignment "
                f"({estimate['absolute_correlation']:.6f}); refusing trajectory-based shift selection"
            )
        segments = align_pair(pair, estimate["residual_offset_s"])
        _validate_segments(segments, sequence)
        pairs[sequence] = pair
        segments_by_sequence[sequence] = segments
        clock_estimates[sequence] = estimate

    s1_pair = pairs["S1"]
    training_cutoff_s = float(
        s1_pair.reference_time_s[0]
        + 0.4 * (s1_pair.reference_time_s[-1] - s1_pair.reference_time_s[0])
    )
    first_candidates = {
        "S1": _first_s1_candidate(s1_pair, training_cutoff_s),
        "S2": 1800,
        "S3a": 1800,
        "S4": 1800,
    }
    for sequence in SEQUENCES:
        sequence_windows = make_windows(
            pairs[sequence],
            segments_by_sequence[sequence],
            first_candidates[sequence],
        )
        for record in sequence_windows:
            record["sequence"] = sequence
            record["window_id"] = f"{sequence}:{record['window_id']}"
        all_windows.extend(sequence_windows)

    training_indices = _training_indices(
        s1_pair,
        segments_by_sequence["S1"],
        float(clock_estimates["S1"]["residual_offset_s"]),
        training_cutoff_s,
    )
    prefix_indices = {
        sequence: _prefix_fit_indices(
            pairs[sequence], segments_by_sequence[sequence], clock_estimates[sequence]
        )
        for sequence in SEQUENCES
    }

    output.mkdir(parents=True, exist_ok=False)
    runner_path = Path(__file__).resolve()
    manifest = {
        "status": "exploratory development diagnostic; not fresh confirmation",
        "run_started_utc": run_started_utc,
        "manifest_written_utc": _utc_now(),
        "written_before_fit": True,
        "phone_utc_offset_s": PHONE_UTC_OFFSET_S,
        "sequence_scope": list(SEQUENCES),
        "outage_duration_s": 60.0,
        "raw_grid": {
            "anchor_raw_reference_row": 0,
            "duration_rows": DURATION_ROWS,
            "calibration_rows": CALIBRATION_ROWS,
            "feature_warmup_rows": FEATURE_WARMUP_ROWS,
            "first_candidate_rows": first_candidates,
            "reference_cadence_s": REFERENCE_CADENCE_S,
            "cadence_tolerance_s": CADENCE_TOLERANCE_S,
        },
        "training": {
            "sequence": "S1",
            "cutoff_reference_time_s": training_cutoff_s,
            "cutoff_formula": "S1 reference first + 0.4 * (reference last - reference first)",
            "eligibility": (
                "segment-local index >= 200; reference timestamp and both residual-shifted "
                "phone bracket timestamps strictly below cutoff; raw reference row unique"
            ),
            "indices": training_indices,
        },
        "model": {
            "class": "sklearn.ensemble.HistGradientBoostingRegressor",
            "constants": MODEL_CONSTANTS,
            "features": "unchanged prototypes.dhruva.benchmark.causal_features, per segment",
            "prediction_clamp": "maximum(0, prediction)",
        },
        "gyro_calibration": {
            "target": "-deg2rad(VBOX yaw rate)",
            "design": "three aligned phone gyro axes plus intercept",
            "frozen_s1": {
                "sequence": "S1",
                "indices": training_indices,
            },
            "journey_prefix": {
                sequence: {
                    "clock_prefix_s": CLOCK_PREFIX_S,
                    "initial_aligned_segment_only": True,
                    "indices": prefix_indices[sequence],
                }
                for sequence in SEQUENCES
            },
        },
        "clock_alignment": {
            "method": "estimate_clock_offset defaults; low confidence rejected",
            "explicit_phone_utc_offset_s": PHONE_UTC_OFFSET_S,
            "estimates": clock_estimates,
        },
        "segments": {
            sequence: _segment_provenance(segments_by_sequence[sequence])
            for sequence in SEQUENCES
        },
        "windows": all_windows,
        "methods": list(METHODS),
        "privileged_offline_inputs": [
            "reference position at outage start",
            "reference heading at outage start",
            "reference speed at outage start for baseline and learned_initial_offset",
            "1200 pre-outage reference yaw-rate samples for phone-heading bias",
            "reference speed for reference_oracle branches",
            "reference heading for reference_oracle branches",
            "reference-assisted residual clock estimates",
        ],
        "hashes": {
            "runner_sha256": legacy.sha256(runner_path),
            "original_benchmark_sha256": legacy.sha256(Path(legacy.__file__).resolve()),
            "alignment_module_sha256": legacy.sha256(
                Path(__file__).resolve().parents[2] / "prototypes/dhruva/time_alignment.py"
            ),
            "data": {
                sequence: {
                    "phone_path": str(pairs[sequence].phone_path),
                    "phone_sha256": legacy.sha256(pairs[sequence].phone_path),
                    "reference_path": str(pairs[sequence].reference_path),
                    "reference_sha256": legacy.sha256(pairs[sequence].reference_path),
                }
                for sequence in SEQUENCES
            },
        },
    }
    manifest_path = output / "manifest.json"
    _write_json(manifest_path, manifest, exclusive=True)
    pre_fit_manifest_sha256 = legacy.sha256(manifest_path)

    features = {
        sequence: _features_by_segment(segments_by_sequence[sequence])
        for sequence in SEQUENCES
    }
    train_x = np.vstack(
        [
            features["S1"][record["segment_index"]][record["local_index"]]
            for record in training_indices
        ]
    )
    train_y = np.asarray(
        [
            segments_by_sequence["S1"][record["segment_index"]].reference[
                record["local_index"], 2
            ]
            / 3.6
            for record in training_indices
        ],
        dtype=float,
    )
    model = HistGradientBoostingRegressor(**MODEL_CONSTANTS)
    fit_started_utc = _utc_now()
    fit_started = time.perf_counter()
    model.fit(train_x, train_y)
    fit_elapsed_s = time.perf_counter() - fit_started
    fit_completed_utc = _utc_now()

    predicted_speed = {
        sequence: [np.maximum(0.0, model.predict(block)) for block in features[sequence]]
        for sequence in SEQUENCES
    }
    frozen_coefficients = _fit_gyro(segments_by_sequence["S1"], training_indices)
    journey_coefficients = {
        sequence: _fit_gyro(segments_by_sequence[sequence], prefix_indices[sequence])
        for sequence in SEQUENCES
    }
    predicted_yaw: dict[str, dict[str, list[np.ndarray]]] = {}
    for sequence in SEQUENCES:
        predicted_yaw[sequence] = {
            "frozen_s1": [
                _predict_yaw(segment, frozen_coefficients)
                for segment in segments_by_sequence[sequence]
            ],
            "journey_prefix": [
                _predict_yaw(segment, journey_coefficients[sequence])
                for segment in segments_by_sequence[sequence]
            ],
        }

    output_rows: list[dict[str, Any]] = []
    for sequence in SEQUENCES:
        sequence_windows = [row for row in all_windows if row["sequence"] == sequence]
        segments = segments_by_sequence[sequence]
        for window in sequence_windows:
            for method in METHODS:
                row: dict[str, Any] = {
                    "window_id": window["window_id"],
                    "sequence": sequence,
                    "raw_start_row": window["raw_start_row"],
                    "raw_end_row": window["raw_end_row"],
                    "start_time_s": window["start_time_s"],
                    "end_time_s": window["end_time_s"],
                    "actual_duration_s": window["actual_duration_s"],
                    "included": window["included"],
                    "exclusion_reason": window["exclusion_reason"],
                    "segment_index": window["segment_index"],
                    "local_bounds": window["local_bounds"],
                    "calibration_raw_bounds": window["calibration_raw_bounds"],
                    "calibration_local_bounds": window["calibration_local_bounds"],
                    "phone_span": window["phone_span"],
                    "reference_span": window["reference_span"],
                    "method": method,
                    "speed_profile": None,
                    "heading_profile": None,
                    "gyro_calibration_profile": None,
                    "predicted_east_m": None,
                    "predicted_north_m": None,
                    "truth_east_m": None,
                    "truth_north_m": None,
                    "distance_m": None,
                    "distance_eligible_for_drift_ratio": None,
                    "endpoint_error_m": None,
                    "drift_ratio": None,
                    "yaw_bias_rad_s": None,
                    "privileged_initial_position": None,
                    "privileged_initial_heading": None,
                    "privileged_initial_speed": None,
                    "reference_speed_oracle": None,
                    "reference_heading_oracle": None,
                    "pre_outage_vbox_yaw_calibration": None,
                }
                if window["included"]:
                    segment_index = int(window["segment_index"])
                    segment = segments[segment_index]
                    if method == BASELINE_METHOD:
                        metrics = _evaluate_constant(window, segment)
                    else:
                        parts = dict(item.split("=", 1) for item in method.split("|"))
                        row.update(
                            {
                                "speed_profile": parts["speed"],
                                "heading_profile": parts["heading"],
                                "gyro_calibration_profile": parts["gyro"],
                            }
                        )
                        metrics = evaluate_window_method(
                            window,
                            segment,
                            predicted_speed[sequence][segment_index],
                            predicted_yaw[sequence][parts["gyro"]][segment_index],
                            speed_profile=parts["speed"],
                            heading_profile=parts["heading"],
                            gyro_calibration_profile=parts["gyro"],
                        )
                    row.update(metrics)
                output_rows.append(row)
        sequence_exclusions = Counter(
            row["exclusion_reason"] for row in sequence_windows if not row["included"]
        )
        print(
            f"{sequence}: candidates={len(sequence_windows)} "
            f"valid={sum(row['included'] for row in sequence_windows)} "
            f"exclusions={dict(sorted(sequence_exclusions.items()))}",
            flush=True,
        )

    valid_ids_by_method = {
        method: {
            row["window_id"]
            for row in output_rows
            if row["method"] == method and row["included"]
        }
        for method in METHODS
    }
    if len({frozenset(ids) for ids in valid_ids_by_method.values()}) != 1:
        raise AssertionError("methods did not evaluate identical valid-window IDs")
    for speed in SPEED_PROFILES:
        first = method_name(speed, "reference_oracle", "frozen_s1")
        second = method_name(speed, "reference_oracle", "journey_prefix")
        first_rows = [row for row in output_rows if row["method"] == first and row["included"]]
        second_rows = [row for row in output_rows if row["method"] == second and row["included"]]
        for left, right in zip(first_rows, second_rows, strict=True):
            for field in (
                "predicted_east_m",
                "predicted_north_m",
                "endpoint_error_m",
                "drift_ratio",
            ):
                if left[field] is None and right[field] is None:
                    continue
                if not np.isclose(left[field], right[field], rtol=0.0, atol=1e-12):
                    raise AssertionError(
                        f"reference-heading factorial controls disagree for {speed}, "
                        f"{left['window_id']}, {field}"
                    )

    summaries = _summaries(output_rows, all_windows)
    _write_csv(output / "windows.csv", output_rows)
    result = {
        "status": "exploratory development diagnostic; not fresh confirmation",
        "run_started_utc": run_started_utc,
        "fit_started_utc": fit_started_utc,
        "fit_completed_utc": fit_completed_utc,
        "run_completed_utc": _utc_now(),
        "fit_elapsed_s": fit_elapsed_s,
        "pre_fit_manifest_sha256": pre_fit_manifest_sha256,
        "training_sample_count": len(training_indices),
        "changed_aligned_training_samples": (
            "timestamp/bracket-constrained S1 samples listed in manifest; this refit is not "
            "an exact matched comparison with the legacy 18.342% result"
        ),
        "gyro_calibration": {
            "frozen_s1": {
                "coefficients": frozen_coefficients.tolist(),
                "fit_row_count": len(training_indices),
            },
            "journey_prefix": {
                sequence: {
                    "coefficients": journey_coefficients[sequence].tolist(),
                    "fit_row_count": len(prefix_indices[sequence]),
                }
                for sequence in SEQUENCES
            },
        },
        "method_count": len(METHODS),
        "methods": list(METHODS),
        "summaries": summaries,
        "limitations": [
            "All four sequences are exploratory development sequences, not fresh confirmation.",
            "Reference initialization, clock alignment, calibration, and oracle branches are privileged offline diagnostics.",
            "Only 60-second outages were evaluated; no claim is made for other durations.",
            "No novelty, deployment readiness, production-system pass, or target-compliance claim is made.",
        ],
    }
    _write_json(output / "results.json", result, exclusive=True)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    run(arguments.data_root, arguments.output)


if __name__ == "__main__":
    main()
