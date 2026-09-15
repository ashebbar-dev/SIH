"""Pure numerical contracts for the Dhruva speed-state experiment.

The acceleration labels estimate the interval ending at each row.  Integrated
speed remains signed internally; clipping is applied only to reported output.
"""

from __future__ import annotations

import math

import numpy as np

from research.tools.audit_dhruva_aligned import integrate_displacement


def _finite_vector(name: str, value: np.ndarray) -> np.ndarray:
    """Validate and return a finite, one-dimensional numeric array."""

    if not isinstance(value, np.ndarray) or value.ndim != 1:
        raise ValueError(f"{name} must be a one-dimensional numpy array")
    try:
        finite = np.all(np.isfinite(value))
    except TypeError as error:
        raise ValueError(f"{name} must contain finite numeric elements") from error
    if not finite:
        raise ValueError(f"{name} must contain finite elements")
    return value


def _strictly_increasing_times(times: np.ndarray, *, minimum: int = 1) -> np.ndarray:
    times = _finite_vector("times", times)
    if len(times) < minimum:
        raise ValueError(f"times must contain at least {minimum} elements")
    if np.any(np.diff(times) <= 0.0):
        raise ValueError("times must be strictly increasing")
    return times


def _finite_initial_speed(initial_speed: float) -> float:
    try:
        finite = math.isfinite(initial_speed)
    except TypeError as error:
        raise ValueError("initial_speed must be finite and nonnegative") from error
    if not finite or initial_speed < 0.0:
        raise ValueError("initial_speed must be finite and nonnegative")
    return float(initial_speed)


def backward_targets(
    times: np.ndarray,
    speed_mps: np.ndarray,
    raw_rows: np.ndarray,
    satellite_field: np.ndarray,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return backward-interval acceleration, raw support, and NZ2 flags."""

    times = _strictly_increasing_times(times)
    speed_mps = _finite_vector("speed_mps", speed_mps)
    satellite_field = _finite_vector("satellite_field", satellite_field)
    if not isinstance(raw_rows, np.ndarray) or raw_rows.ndim != 1:
        raise ValueError("raw_rows must be a one-dimensional numpy array")
    if not np.issubdtype(raw_rows.dtype, np.integer):
        raise ValueError("raw_rows must contain integers")
    if not (len(times) == len(speed_mps) == len(raw_rows)):
        raise ValueError("times, speed_mps and raw_rows must have matching lengths")
    if np.any(raw_rows < 0):
        raise ValueError("raw_rows must be nonnegative")
    if len(raw_rows) > 1 and np.any(np.diff(raw_rows) != 1):
        raise ValueError("raw_rows must be consecutive")
    if np.any(raw_rows >= len(satellite_field)):
        raise ValueError("raw_rows must be within satellite_field bounds")

    targets = np.r_[np.nan, np.diff(speed_mps) / np.diff(times)]
    supports = np.column_stack((np.r_[-1, raw_rows[:-1]], raw_rows))
    keep = np.r_[
        False,
        (satellite_field[raw_rows[:-1]] != 0)
        & (satellite_field[raw_rows[1:]] != 0),
    ]
    return targets, supports, keep


def integrate_speed(
    times: np.ndarray, acceleration_at_rows: np.ndarray, initial_speed: float
) -> tuple[np.ndarray, np.ndarray]:
    """Integrate backward-interval acceleration into signed and clipped speed."""

    times = _strictly_increasing_times(times)
    acceleration_at_rows = _finite_vector(
        "acceleration_at_rows", acceleration_at_rows
    )
    if len(times) != len(acceleration_at_rows):
        raise ValueError("times and acceleration_at_rows must have matching lengths")
    initial_speed = _finite_initial_speed(initial_speed)

    signed = np.r_[
        initial_speed,
        initial_speed
        + np.cumsum(acceleration_at_rows[1:] * np.diff(times)),
    ]
    output = np.maximum(0.0, signed)
    return signed, output


def absolute_speed(
    raw_prediction: np.ndarray, initial_speed: float | None = None
) -> tuple[np.ndarray, np.ndarray]:
    """Apply the legacy initial-offset ordering, then output-only clipping."""

    raw_prediction = _finite_vector("raw_prediction", raw_prediction)
    if initial_speed is not None:
        initial_speed = _finite_initial_speed(initial_speed)
        if len(raw_prediction) == 0:
            raise ValueError("raw_prediction must not be empty with an initial_speed")

    p = np.maximum(0.0, raw_prediction)
    candidate = (
        raw_prediction.copy()
        if initial_speed is None
        else p + initial_speed - p[0]
    )
    output = np.maximum(0.0, candidate)
    return candidate, output


def speed_metrics(
    *,
    times: np.ndarray,
    signed_speed: np.ndarray,
    output_speed: np.ndarray,
    gps_speed: np.ndarray,
    indicated_speed: np.ndarray,
    headings: np.ndarray,
    truth_displacement: tuple[float, float],
    acceleration: np.ndarray | None = None,
) -> dict:
    """Compute left-sample displacement and time-weighted speed metrics."""

    times = _strictly_increasing_times(times, minimum=2)
    vectors = {
        "signed_speed": _finite_vector("signed_speed", signed_speed),
        "output_speed": _finite_vector("output_speed", output_speed),
        "gps_speed": _finite_vector("gps_speed", gps_speed),
        "indicated_speed": _finite_vector("indicated_speed", indicated_speed),
        "headings": _finite_vector("headings", headings),
    }
    if any(len(value) != len(times) for value in vectors.values()):
        raise ValueError("all state and reference vectors must match times")
    if acceleration is not None:
        acceleration = _finite_vector("acceleration", acceleration)
        if len(acceleration) != len(times):
            raise ValueError("acceleration must match times")
    try:
        truth = np.asarray(truth_displacement, dtype=float)
    except (TypeError, ValueError) as error:
        raise ValueError("truth_displacement must contain two finite values") from error
    if truth.shape != (2,) or not np.all(np.isfinite(truth)):
        raise ValueError("truth_displacement must contain two finite values")

    dt = np.diff(times)
    duration = float(dt.sum())
    gps_error = output_speed[:-1] - gps_speed[:-1]
    indicated_error = output_speed[:-1] - indicated_speed[:-1]
    predicted_east, predicted_north = integrate_displacement(
        times, output_speed[:-1], headings[:-1]
    )
    truth_east, truth_north = float(truth[0]), float(truth[1])
    distance = float(np.sum(gps_speed[:-1] * dt))
    endpoint_error = float(
        np.hypot(predicted_east - truth_east, predicted_north - truth_north)
    )
    distance_eligible = distance >= 50.0

    return {
        "predicted_east_m": predicted_east,
        "predicted_north_m": predicted_north,
        "truth_east_m": truth_east,
        "truth_north_m": truth_north,
        "distance_m": distance,
        "distance_eligible_for_drift_ratio": distance_eligible,
        "endpoint_error_m": endpoint_error,
        "drift_ratio": endpoint_error / distance if distance_eligible else None,
        "speed_mae_gps_mps": float(np.sum(np.abs(gps_error) * dt) / duration),
        "speed_mae_indicated_mps": float(
            np.sum(np.abs(indicated_error) * dt) / duration
        ),
        "mean_speed_error_mps": float(np.sum(gps_error * dt) / duration),
        "mean_unclipped_speed_error_mps": float(
            np.sum((signed_speed[:-1] - gps_speed[:-1]) * dt) / duration
        ),
        "clipped_fraction": float(np.mean(signed_speed[:-1] < 0.0)),
        "terminal_speed_error_mps": float(output_speed[-1] - gps_speed[-1]),
        "mean_acceleration_error_mps2": (
            None
            if acceleration is None
            else float(
                np.sum(
                    (acceleration[1:] - np.diff(gps_speed) / dt) * dt
                )
                / duration
            )
        ),
    }
