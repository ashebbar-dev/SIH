"""Event-level accounting and schema regression tests; no classifier needed."""

from contextlib import redirect_stderr, redirect_stdout
from copy import deepcopy
import io
import json
import math
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate_stream import ManifestError, evaluate_manifest, main  # noqa: E402


def recording(**overrides):
    value = {
        "id": "r1",
        "duration_s": 60.0,
        "split": "test",
        "speaker_id": "s1",
        "environment": "quiet",
        "events": [{"start_s": 10.0, "end_s": 11.0}],
        "triggers_s": [10.8, 11.1, 25.0],
    }
    value.update(overrides)
    return value


def manifest(*recordings):
    return {"schema_version": 1, "recordings": list(recordings) or [recording()]}


class EventAccountingTests(unittest.TestCase):
    def test_duplicates_remain_in_unmatched_rate_and_negative_latency(self):
        report = evaluate_manifest(manifest())
        metrics = report["overall"]
        self.assertEqual(metrics["positive_event_count"], 1)
        self.assertEqual(metrics["matched_event_count"], 1)
        self.assertEqual(metrics["missed_event_count"], 0)
        self.assertEqual(metrics["duplicate_trigger_count"], 1)
        self.assertEqual(metrics["negative_false_trigger_count"], 1)
        self.assertEqual(metrics["unmatched_activation_count"], 2)
        self.assertEqual(metrics["trigger_count"], 3)
        self.assertEqual(metrics["negative_exposure_s"], 58.5)
        self.assertAlmostEqual(metrics["negative_false_activations_per_hour"], 3600 / 58.5)
        self.assertEqual(metrics["unmatched_activations_per_total_hour"], 120)
        self.assertIsNone(metrics["negative_false_activations_per_hour_poisson95_upper_zero_only"])
        event = report["per_recording"][0]["events"][0]
        self.assertAlmostEqual(event["latency_from_keyword_end_s"], -0.2)
        self.assertEqual(event["duplicate_triggers_s"], [11.1])

    def test_no_events_and_exact_zero_count_poisson_upper(self):
        report = evaluate_manifest(manifest(recording(duration_s=360000, events=[], triggers_s=[])))
        metrics = report["overall"]
        self.assertEqual(metrics["negative_exposure_hours"], 100)
        self.assertIsNone(metrics["event_recall"])
        self.assertIsNone(metrics["event_recall_wilson95_descriptive"])
        self.assertIsNone(metrics["latency_from_keyword_end_s"]["mean"])
        self.assertEqual(metrics["negative_false_activations_per_hour"], 0)
        self.assertAlmostEqual(metrics["negative_false_activations_per_hour_poisson95_upper_zero_only"], -math.log(0.05) / 100)

    def test_no_events_with_triggers_all_count_as_negative(self):
        metrics = evaluate_manifest(manifest(recording(events=[], triggers_s=[0, 60])))["overall"]
        self.assertEqual(metrics["negative_false_trigger_count"], 2)
        self.assertEqual(metrics["unmatched_activations_per_total_hour"], 120)

    def test_zero_negative_exposure_rates_are_undefined_but_duplicates_count(self):
        report = evaluate_manifest(manifest(recording(duration_s=1, events=[{"start_s": 0, "end_s": 1}], triggers_s=[0, 0, 1])))
        metrics = report["overall"]
        self.assertEqual(metrics["negative_exposure_s"], 0)
        self.assertIsNone(metrics["negative_false_activations_per_hour"])
        self.assertIsNone(metrics["negative_false_activations_per_hour_poisson95_upper_zero_only"])
        self.assertEqual(metrics["duplicate_trigger_count"], 2)
        self.assertEqual(metrics["unmatched_activations_per_total_hour"], 7200)
        self.assertEqual(metrics["latency_from_keyword_end_s"]["min"], -1)

    def test_tiny_negative_gaps_survive_nearly_full_acceptance_coverage(self):
        cases = (
            ([{"start_s": 1e-16, "end_s": 10}], [0], 0.5),
            ([{"start_s": 0, "end_s": 1e-16}, {"start_s": 2e-16, "end_s": 10}], [1.5e-16], 0),
        )
        for events, triggers, tolerance in cases:
            with self.subTest(events=events):
                report = evaluate_manifest(
                    manifest(recording(duration_s=10, events=events, triggers_s=triggers)),
                    end_tolerance_s=tolerance,
                )
                for metrics in (report["overall"], report["per_recording"][0]["metrics"]):
                    self.assertEqual(metrics["negative_false_trigger_count"], 1)
                    self.assertEqual(metrics["negative_exposure_s"], 1e-16)
                    self.assertEqual(metrics["negative_false_activations_per_hour"], 3.6e19)

    def test_acceptance_exposure_is_predeclared_even_when_events_missed(self):
        missed = evaluate_manifest(manifest(recording(triggers_s=[])))["overall"]
        detected = evaluate_manifest(manifest())["overall"]
        self.assertEqual(missed["negative_exposure_s"], detected["negative_exposure_s"])
        self.assertEqual(missed["missed_event_count"], 1)
        self.assertEqual(missed["event_recall"], 0)

    def test_end_tolerance_is_inclusive_and_configurable(self):
        data = manifest(recording(triggers_s=[9.999, 11.5, 11.500001]))
        default = evaluate_manifest(data)
        self.assertEqual([item["outcome"] for item in default["per_recording"][0]["activations"]], ["negative_false_trigger", "matched_event", "negative_false_trigger"])
        self.assertEqual(default["overall"]["negative_exposure_s"], 58.5)
        no_tolerance = evaluate_manifest(data, end_tolerance_s=0)
        self.assertEqual(no_tolerance["overall"]["matched_event_count"], 0)
        self.assertEqual(no_tolerance["overall"]["negative_false_trigger_count"], 3)
        self.assertEqual(no_tolerance["overall"]["negative_exposure_s"], 59)

    def test_overlapping_acceptance_windows_use_union_and_one_to_one_matches(self):
        data = manifest(recording(duration_s=10, events=[{"start_s": 1, "end_s": 2}, {"start_s": 2.2, "end_s": 3}], triggers_s=[2.3, 2.4, 2.45, 3.4]))
        report = evaluate_manifest(data)
        metrics = report["overall"]
        self.assertEqual(metrics["matched_event_count"], 2)
        self.assertEqual(metrics["duplicate_trigger_count"], 2)
        self.assertEqual(metrics["acceptance_exposure_s"], 2.5)
        self.assertEqual(metrics["negative_exposure_s"], 7.5)
        self.assertEqual([a["event_index"] for a in report["per_recording"][0]["activations"]], [0, 1, 0, 1])

    def test_single_trigger_cannot_match_two_eligible_events(self):
        data = manifest(recording(events=[{"start_s": 1, "end_s": 2}, {"start_s": 2, "end_s": 3}], triggers_s=[2]))
        report = evaluate_manifest(data)
        self.assertEqual(report["overall"]["matched_event_count"], 1)
        self.assertEqual(report["overall"]["missed_event_count"], 1)
        self.assertEqual(report["per_recording"][0]["activations"][0]["event_index"], 0)

    def test_expired_unmatched_event_does_not_steal_later_trigger(self):
        data = manifest(recording(events=[{"start_s": 1, "end_s": 2}, {"start_s": 3, "end_s": 4}], triggers_s=[3.5, 3.6]))
        report = evaluate_manifest(data)
        self.assertEqual(report["overall"]["missed_event_count"], 1)
        self.assertEqual([a["event_index"] for a in report["per_recording"][0]["activations"]], [1, 1])

    def test_windows_clip_at_recording_boundary_and_state_does_not_leak(self):
        data = manifest(
            recording(id="a", duration_s=1, events=[{"start_s": 0.8, "end_s": 1}], triggers_s=[1]),
            recording(id="b", duration_s=1, events=[], triggers_s=[0]),
        )
        report = evaluate_manifest(data)
        self.assertAlmostEqual(report["overall"]["negative_exposure_s"], 1.8)
        self.assertEqual(report["overall"]["matched_event_count"], 1)
        self.assertEqual(report["overall"]["negative_false_trigger_count"], 1)
        self.assertEqual(report["per_recording"][0]["events"][0]["acceptance_end_s"], 1)

    def test_grouping_uses_pooled_counts_and_exposure_not_mean_of_rates(self):
        data = manifest(
            recording(id="a", duration_s=3600, events=[], triggers_s=[100]),
            recording(id="b", duration_s=7200, events=[], triggers_s=[100], split="validation", speaker_id="s2"),
            recording(id="c", duration_s=3600, events=[], triggers_s=[], environment="fan"),
        )
        report = evaluate_manifest(data)
        self.assertAlmostEqual(report["per_environment"]["quiet"]["negative_false_activations_per_hour"], 2 / 3)
        self.assertEqual(report["overall"]["negative_false_activations_per_hour"], 0.5)
        self.assertEqual(report["per_split"]["validation"]["recording_count"], 1)
        self.assertEqual(report["per_speaker"]["s1"]["recording_count"], 2)
        self.assertEqual(report["per_recording"][0]["metrics"]["recording_count"], 1)

    def test_wilson_interval_is_event_level_and_labeled_descriptive(self):
        data = manifest(recording(events=[{"start_s": 1, "end_s": 2}, {"start_s": 4, "end_s": 5}], triggers_s=[1.5]))
        report = evaluate_manifest(data)
        interval = report["overall"]["event_recall_wilson95_descriptive"]
        self.assertAlmostEqual(interval["lower"], 0.09453120573423074)
        self.assertAlmostEqual(interval["upper"], 0.9054687942657693)
        self.assertTrue(any("correlated" in note for note in report["uncertainty_notes"]))


class ValidationTests(unittest.TestCase):
    def test_required_recording_fields_and_nonempty_metadata(self):
        for key in recording():
            with self.subTest(missing=key):
                value = recording()
                del value[key]
                with self.assertRaisesRegex(ManifestError, f"missing field.*{key}"):
                    evaluate_manifest(manifest(value))
        for key in ("id", "split", "speaker_id", "environment"):
            for invalid in (None, "", "  ", 5):
                with self.subTest(key=key, invalid=invalid):
                    with self.assertRaisesRegex(ManifestError, f"{key}.*nonempty string"):
                        evaluate_manifest(manifest(recording(**{key: invalid})))

    def test_duplicate_ids_and_invalid_document_shapes(self):
        with self.assertRaisesRegex(ManifestError, "duplicate recording ID"):
            evaluate_manifest(manifest(recording(), recording()))
        for invalid in ({}, [], {"schema_version": 1, "recordings": []}, {"schema_version": True, "recordings": [recording()]}, {"schema_version": 2, "recordings": [recording()]}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ManifestError):
                    evaluate_manifest(invalid)
        with self.assertRaisesRegex(ManifestError, "unknown field.*eventz"):
            evaluate_manifest(manifest(recording(eventz=[])))

    def test_invalid_numbers_in_duration_events_triggers_and_tolerance(self):
        for number in (float("nan"), float("inf"), -float("inf"), True, "1", None, 10**400):
            for field in ("duration_s", "start_s", "end_s", "trigger", "tolerance"):
                with self.subTest(field=field, number=number):
                    data = manifest()
                    tolerance = 0.5
                    if field == "duration_s":
                        data["recordings"][0][field] = number
                    elif field in ("start_s", "end_s"):
                        data["recordings"][0]["events"][0][field] = number
                    elif field == "trigger":
                        data["recordings"][0]["triggers_s"] = [number]
                    else:
                        tolerance = number
                    with self.assertRaisesRegex(ManifestError, "finite number"):
                        evaluate_manifest(data, tolerance)

    def test_invalid_event_order_bounds_and_missing_times(self):
        cases = (
            [{"start_s": 2}],
            [{"end_s": 3}],
            [{"start_s": -1, "end_s": 3}],
            [{"start_s": 2, "end_s": 2}],
            [{"start_s": 3, "end_s": 2}],
            [{"start_s": 59, "end_s": 61}],
            [{"start_s": 4, "end_s": 5}, {"start_s": 1, "end_s": 2}],
            [{"start_s": 1, "end_s": 3}, {"start_s": 2, "end_s": 4}],
        )
        for events in cases:
            with self.subTest(events=events):
                with self.assertRaisesRegex(ManifestError, "events"):
                    evaluate_manifest(manifest(recording(events=events)))

    def test_invalid_trigger_bounds_order_duration_and_tolerance(self):
        for triggers in ([-0.1], [60.001], [3, 2], None):
            with self.subTest(triggers=triggers):
                with self.assertRaisesRegex(ManifestError, "triggers_s"):
                    evaluate_manifest(manifest(recording(triggers_s=triggers)))
        for duration in (0, -1):
            with self.assertRaisesRegex(ManifestError, "duration_s.*positive"):
                evaluate_manifest(manifest(recording(duration_s=duration)))
        with self.assertRaisesRegex(ManifestError, "tolerance.*nonnegative"):
            evaluate_manifest(manifest(), -0.5)

    def test_evaluation_does_not_mutate_input(self):
        data = manifest()
        original = deepcopy(data)
        evaluate_manifest(data)
        self.assertEqual(data, original)

    def test_unrepresentable_total_duration_and_rates_are_explicit_errors(self):
        with self.assertRaisesRegex(ManifestError, "total recording duration"):
            evaluate_manifest(manifest(recording(id="a", duration_s=1e308), recording(id="b", duration_s=1e308)))
        with self.assertRaisesRegex(ManifestError, "hourly rate exceeds finite numeric range"):
            evaluate_manifest(manifest(recording(duration_s=5e-324, events=[], triggers_s=[])))


class CLITests(unittest.TestCase):
    def test_cli_stdout_and_file_output(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "manifest.json"
            target = Path(directory) / "report.json"
            source.write_text(json.dumps(manifest()), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                self.assertEqual(main([str(source), "--end-tolerance-s", "0"]), 0)
            self.assertEqual(json.loads(stdout.getvalue())["config"]["end_tolerance_s"], 0)
            self.assertEqual(main([str(source), "--output", str(target)]), 0)
            self.assertEqual(json.loads(target.read_text())["overall"]["duplicate_trigger_count"], 1)

    def test_cli_rejects_invalid_json_duplicate_keys_nonfinite_and_overwrite(self):
        with TemporaryDirectory() as directory:
            source = Path(directory) / "manifest.json"
            cases = (
                ("{", [], "Expecting"),
                ('{"schema_version":1,"schema_version":1,"recordings":[]}', [], "duplicate key"),
                ('{"schema_version":1,"recordings":NaN}', [], "nonfinite numeric constant"),
                (json.dumps(manifest()), ["--output", str(source)], "must not overwrite"),
            )
            for contents, extra, message in cases:
                with self.subTest(message=message):
                    source.write_text(contents, encoding="utf-8")
                    stderr = io.StringIO()
                    with redirect_stderr(stderr), self.assertRaises(SystemExit) as exc:
                        main([str(source), *extra])
                    self.assertEqual(exc.exception.code, 2)
                    self.assertIn(message, stderr.getvalue())
                    self.assertEqual(source.read_text(), contents)


if __name__ == "__main__":
    unittest.main()
