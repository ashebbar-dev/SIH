#!/usr/bin/env python3
r"""Evaluate recorded wake-word triggers without running or training a model.

Input is one JSON object with exactly this schema (seconds throughout)::

    {
      "schema_version": 1,
      "recordings": [
        {
          "id": "test-speaker-01-quiet-01",
          "duration_s": 60.0,
          "split": "test",
          "speaker_id": "speaker-01",
          "environment": "quiet",
          "events": [{"start_s": 10.0, "end_s": 11.0}],
          "triggers_s": [10.8, 11.1, 25.0]
        }
      ]
    }

All fields are required; unknown fields and duplicate JSON keys are errors.
Recording IDs must be unique. Metadata must be nonempty strings (use an explicit
speaker label such as "no-speaker" for noise-only recordings). Durations must be
positive and finite. Events must have 0 <= start < end <= duration, be sorted,
and not overlap; adjacent events are allowed. Trigger times must be finite,
sorted, and within [0, duration]. Equal trigger times are retained separately.
There must be at least one recording. Times are compared without rounding or
implicit epsilon. All recordings, including those with no events, are scored.
Inputs whose pooled durations or derived rates exceed finite floating-point
range are rejected explicitly.

Each event's predeclared acceptance window is the closed interval
[start_s, min(end_s + end_tolerance_s, duration_s)]. The default end tolerance is
0.5 seconds and must be fixed before evaluating test data. There is no pre-event
tolerance, refractory period, or trigger-dependent exclusion. At each trigger,
match the earliest-ending eligible unmatched event, if any. This chronological
greedy rule maximizes one-to-one matches for these ordered windows. Otherwise,
an in-window trigger is a duplicate, attributed to the earliest-ending eligible
event; a trigger outside every window is a negative false activation. A trigger
can never satisfy two events, including at adjacent or overlapping boundaries.

Negative exposure is duration minus the union of ALL acceptance windows,
including missed events. Windows are clipped to their own recording. Duplicate
triggers are reported separately and included in unmatched activations per total
hour. Latency is matched trigger time minus keyword END, so it can be negative.
No audio frames or overlapping classifier windows are treated as trials.
Exposure is computed by summing uncovered gaps directly to preserve small gaps
that subtraction of nearly equal duration and covered totals could erase.

Output contains configuration/uncertainty notes, per_recording detail, overall
metrics, and per_environment, per_split and per_speaker dictionaries. Overall
pools every supplied recording; consult per_split to keep validation/test results
separate. Per-recording events retain labels, acceptance bounds, matched trigger,
latency and duplicates; activations retain every timestamp and its assignment.
All summaries include event/activation counts, exposure, recall, rates, and
matched-event latency summaries. Rates and recall are null at zero denominator.
The descriptive 95% Wilson recall interval treats events as Bernoulli trials;
correlated events invalidate its use as recording/speaker-level uncertainty.
For zero negative false activations and positive exposure ONLY, report the exact
one-sided 95% Poisson upper rate -log(0.05)/negative_hours. For nonzero counts
that upper bound is null, not an approximation. Poisson assumes a homogeneous
independent event process; this report does not estimate environmental clustering
or uncertainty across independent speakers, recordings or repeated model seeds.

Usage (Python 3.12+, standard library only)::

    python3.12 prototypes/kws/evaluate_stream.py manifest.json
    python3.12 prototypes/kws/evaluate_stream.py manifest.json \
        --end-tolerance-s 0.5 --output report.json

The CLI exits 2 with an explicit error for invalid input. The Python entry point
``evaluate_manifest(data, end_tolerance_s=0.5)`` raises ``ManifestError``.
Matching takes O(events + triggers) time per recording; detail storage is linear
in the manifest. This is a timestamp evaluator, not an audio or hardware test.
"""

from __future__ import annotations

import argparse
from collections import deque
from dataclasses import dataclass
import json
import math
from pathlib import Path
import sys
from typing import Any


class ManifestError(ValueError):
    """A manifest or evaluation parameter does not satisfy the declared schema."""


@dataclass(frozen=True)
class _Event:
    start_s: float
    end_s: float


@dataclass(frozen=True)
class _Recording:
    id: str
    duration_s: float
    split: str
    speaker_id: str
    environment: str
    events: tuple[_Event, ...]
    triggers_s: tuple[float, ...]


def _object(value: Any, keys: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ManifestError(f"{context}: expected an object")
    missing = keys - value.keys()
    extra = value.keys() - keys
    if missing:
        raise ManifestError(f"{context}: missing field(s): {', '.join(sorted(missing))}")
    if extra:
        raise ManifestError(f"{context}: unknown field(s): {', '.join(map(str, extra))}")
    return value


def _number(value: Any, context: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ManifestError(f"{context}: expected a finite number")
    try:
        number = float(value)
    except OverflowError as exc:
        raise ManifestError(f"{context}: expected a finite number") from exc
    if not math.isfinite(number):
        raise ManifestError(f"{context}: expected a finite number")
    return number


def _label(value: Any, context: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ManifestError(f"{context}: expected a nonempty string")
    return value


def _validate_manifest(data: Any) -> list[_Recording]:
    document = _object(data, {"schema_version", "recordings"}, "manifest")
    if type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise ManifestError("manifest.schema_version: expected integer 1")
    if not isinstance(document["recordings"], list) or not document["recordings"]:
        raise ManifestError("manifest.recordings: expected a nonempty array")
    recordings = []
    ids: set[str] = set()
    for index, value in enumerate(document["recordings"]):
        context = f"recordings[{index}]"
        entry = _object(
            value,
            {"id", "duration_s", "split", "speaker_id", "environment", "events", "triggers_s"},
            context,
        )
        labels = {
            key: _label(entry[key], f"{context}.{key}")
            for key in ("id", "split", "speaker_id", "environment")
        }
        if labels["id"] in ids:
            raise ManifestError(f"{context}.id: duplicate recording ID {labels['id']!r}")
        ids.add(labels["id"])
        duration = _number(entry["duration_s"], f"{context}.duration_s")
        if duration <= 0:
            raise ManifestError(f"{context}.duration_s: must be positive")
        if not isinstance(entry["events"], list):
            raise ManifestError(f"{context}.events: expected an array")
        events = []
        for event_index, event_value in enumerate(entry["events"]):
            event_context = f"{context}.events[{event_index}]"
            event = _object(event_value, {"start_s", "end_s"}, event_context)
            start = _number(event["start_s"], f"{event_context}.start_s")
            end = _number(event["end_s"], f"{event_context}.end_s")
            if not 0 <= start < end <= duration:
                raise ManifestError(f"{event_context}: require 0 <= start_s < end_s <= duration_s")
            if events and start < events[-1].end_s:
                raise ManifestError(f"{event_context}: events must be sorted and nonoverlapping")
            events.append(_Event(start, end))
        if not isinstance(entry["triggers_s"], list):
            raise ManifestError(f"{context}.triggers_s: expected an array")
        triggers = []
        for trigger_index, trigger_value in enumerate(entry["triggers_s"]):
            trigger_context = f"{context}.triggers_s[{trigger_index}]"
            trigger = _number(trigger_value, trigger_context)
            if not 0 <= trigger <= duration:
                raise ManifestError(f"{trigger_context}: must be within [0, duration_s]")
            if triggers and trigger < triggers[-1]:
                raise ManifestError(f"{trigger_context}: trigger times must be sorted")
            triggers.append(trigger)
        recordings.append(_Recording(**labels, duration_s=duration, events=tuple(events), triggers_s=tuple(triggers)))
    try:
        total = math.fsum(recording.duration_s for recording in recordings)
    except OverflowError as exc:
        raise ManifestError("manifest: total recording duration exceeds finite numeric range") from exc
    if not math.isfinite(total):
        raise ManifestError("manifest: total recording duration exceeds finite numeric range")
    return recordings


def _union_exposure(windows: list[tuple[float, float]]) -> float:
    if not windows:
        return 0.0
    lengths = []
    start, end = windows[0]
    for next_start, next_end in windows[1:]:
        if next_start <= end:
            end = max(end, next_end)
        else:
            lengths.append(end - start)
            start, end = next_start, next_end
    lengths.append(end - start)
    return math.fsum(lengths)


def _negative_exposure(windows: list[tuple[float, float]], duration_s: float) -> float:
    """Sum gaps outside sorted, recording-clipped windows without cancellation."""
    gaps = []
    covered_until = 0.0
    for start, end in windows:
        if start > covered_until:
            gaps.append(start - covered_until)
        covered_until = max(covered_until, end)
    gaps.append(duration_s - covered_until)
    return math.fsum(gaps)


def _score_recording(recording: _Recording, tolerance: float) -> dict[str, Any]:
    windows = [(event.start_s, min(event.end_s + tolerance, recording.duration_s)) for event in recording.events]
    event_details = [
        {
            "event_index": index,
            "start_s": event.start_s,
            "end_s": event.end_s,
            "acceptance_start_s": windows[index][0],
            "acceptance_end_s": windows[index][1],
            "matched_trigger_s": None,
            "latency_from_keyword_end_s": None,
            "duplicate_triggers_s": [],
        }
        for index, event in enumerate(recording.events)
    ]
    active: deque[int] = deque()
    unmatched: deque[int] = deque()
    next_event = 0
    activations = []
    for trigger in recording.triggers_s:
        while next_event < len(windows) and windows[next_event][0] <= trigger:
            active.append(next_event)
            unmatched.append(next_event)
            next_event += 1
        while active and windows[active[0]][1] < trigger:
            active.popleft()
        while unmatched and windows[unmatched[0]][1] < trigger:
            unmatched.popleft()
        event_index = None
        if unmatched:
            event_index = unmatched.popleft()
            event_details[event_index]["matched_trigger_s"] = trigger
            event_details[event_index]["latency_from_keyword_end_s"] = trigger - recording.events[event_index].end_s
            outcome = "matched_event"
        elif active:
            event_index = active[0]
            event_details[event_index]["duplicate_triggers_s"].append(trigger)
            outcome = "duplicate_trigger"
        else:
            outcome = "negative_false_trigger"
        activations.append({"time_s": trigger, "outcome": outcome, "event_index": event_index})
    acceptance = min(recording.duration_s, _union_exposure(windows))
    return {
        "id": recording.id,
        "duration_s": recording.duration_s,
        "split": recording.split,
        "speaker_id": recording.speaker_id,
        "environment": recording.environment,
        "acceptance_exposure_s": acceptance,
        "negative_exposure_s": _negative_exposure(windows, recording.duration_s),
        "events": event_details,
        "activations": activations,
    }


def _wilson_interval(matched: int, total: int) -> dict[str, float] | None:
    if total == 0:
        return None
    z = 1.959963984540054
    p = matched / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    radius = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / denominator
    return {"lower": max(0.0, center - radius), "upper": min(1.0, center + radius)}


def _hourly_rate(count: int | float, exposure_s: float) -> float | None:
    if exposure_s == 0:
        return None
    rate = count / exposure_s * 3600
    if not math.isfinite(rate):
        raise ManifestError("derived hourly rate exceeds finite numeric range; check exposure duration")
    return rate


def _latency_summary(latencies: list[float]) -> dict[str, int | float | None]:
    count = len(latencies)
    if not count:
        return {"count": 0, "mean": None, "min": None, "median": None, "max": None}
    ordered = sorted(latencies)
    middle = count // 2
    median = ordered[middle] if count % 2 else ordered[middle - 1] / 2 + ordered[middle] / 2
    return {
        "count": count,
        # Normalize before summing to avoid overflow for large finite latencies.
        "mean": math.fsum(latency / count for latency in latencies),
        "min": ordered[0],
        "median": median,
        "max": ordered[-1],
    }


def _summarize(recordings: list[dict[str, Any]]) -> dict[str, Any]:
    duration = math.fsum(recording["duration_s"] for recording in recordings)
    negative = math.fsum(recording["negative_exposure_s"] for recording in recordings)
    acceptance = math.fsum(recording["acceptance_exposure_s"] for recording in recordings)
    event_count = sum(len(recording["events"]) for recording in recordings)
    latencies = [
        event["latency_from_keyword_end_s"]
        for recording in recordings
        for event in recording["events"]
        if event["matched_trigger_s"] is not None
    ]
    matched = len(latencies)
    duplicate_count = sum(
        activation["outcome"] == "duplicate_trigger"
        for recording in recordings for activation in recording["activations"]
    )
    false_count = sum(
        activation["outcome"] == "negative_false_trigger"
        for recording in recordings for activation in recording["activations"]
    )
    unmatched_count = duplicate_count + false_count
    return {
        "recording_count": len(recordings),
        "duration_s": duration,
        "positive_event_count": event_count,
        "matched_event_count": matched,
        "missed_event_count": event_count - matched,
        "trigger_count": matched + unmatched_count,
        "duplicate_trigger_count": duplicate_count,
        "negative_false_trigger_count": false_count,
        "unmatched_activation_count": unmatched_count,
        "acceptance_exposure_s": acceptance,
        "negative_exposure_s": negative,
        "negative_exposure_hours": negative / 3600,
        "event_recall": matched / event_count if event_count else None,
        "event_recall_wilson95_descriptive": _wilson_interval(matched, event_count),
        "negative_false_activations_per_hour": _hourly_rate(false_count, negative),
        "negative_false_activations_per_hour_poisson95_upper_zero_only": (
            _hourly_rate(-math.log(0.05), negative) if false_count == 0 else None
        ),
        "unmatched_activations_per_total_hour": _hourly_rate(unmatched_count, duration),
        "latency_from_keyword_end_s": _latency_summary(latencies),
    }


def evaluate_manifest(data: Any, end_tolerance_s: float = 0.5) -> dict[str, Any]:
    """Validate and score a manifest; return only JSON-serializable report data."""
    tolerance = _number(end_tolerance_s, "end_tolerance_s")
    if tolerance < 0:
        raise ManifestError("end_tolerance_s: must be nonnegative")
    recordings = _validate_manifest(data)
    details = [_score_recording(recording, tolerance) for recording in recordings]
    report: dict[str, Any] = {
        "schema_version": 1,
        "config": {
            "end_tolerance_s": tolerance,
            "acceptance_window": "[event.start_s, min(event.end_s + end_tolerance_s, recording.duration_s)] (inclusive)",
            "matching": "chronological trigger, earliest-ending eligible unmatched event first",
            "duplicate_assignment": "earliest-ending eligible matched event if no eligible unmatched event remains",
            "negative_exposure": "recording duration minus union of all predeclared acceptance windows",
            "refractory_censoring": False,
        },
        "uncertainty_notes": [
            "Wilson recall intervals are descriptive event-level intervals; events within recordings/speakers may be correlated.",
            "Poisson one-sided 95% upper rate is provided only for zero negative false triggers and positive negative exposure; nonzero-count bounds are not computed.",
            "The Poisson bound assumes a homogeneous independent event process and does not account for environmental clustering.",
            "No independent-recording, speaker or seed uncertainty is estimated; no overlapping frames are counted as independent trials.",
            "Overall metrics pool all supplied splits. Use per_split and lock test data before model/threshold selection.",
        ],
        "overall": _summarize(details),
    }
    for metadata, output_key in (("environment", "per_environment"), ("split", "per_split"), ("speaker_id", "per_speaker")):
        groups: dict[str, list[dict[str, Any]]] = {}
        for recording in details:
            groups.setdefault(recording[metadata], []).append(recording)
        report[output_key] = {label: _summarize(group) for label, group in sorted(groups.items())}
    for recording in details:
        recording["metrics"] = _summarize([recording])
    report["per_recording"] = details
    return report


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ManifestError(f"JSON object: duplicate key {key!r}")
        result[key] = value
    return result


def _reject_constant(value: str) -> Any:
    raise ManifestError(f"JSON: nonfinite numeric constant {value!r} is not allowed")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("manifest", type=Path, help="recording/event/trigger JSON manifest")
    parser.add_argument("--end-tolerance-s", type=float, default=0.5, help="predeclared post-keyword tolerance in seconds (default: 0.5)")
    parser.add_argument("--output", type=Path, help="write report JSON here instead of standard output")
    args = parser.parse_args(argv)
    try:
        if args.output and args.output.resolve() == args.manifest.resolve():
            raise ManifestError("output must not overwrite the input manifest")
        with args.manifest.open(encoding="utf-8") as handle:
            manifest = json.load(handle, object_pairs_hook=_unique_object, parse_constant=_reject_constant)
        report = evaluate_manifest(manifest, args.end_tolerance_s)
        output = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(output, encoding="utf-8")
        else:
            sys.stdout.write(output)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
