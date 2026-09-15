import unittest
from pathlib import Path

import numpy as np

from prototypes.dhruva.benchmark import causal_features
from prototypes.dhruva.time_alignment import AlignedSegment, TimestampedPair
from research.tools.audit_dhruva_aligned import (
    evaluate_window_method,
    integrate_displacement,
    make_windows,
    phone_headings,
)


class AlignedAblationTests(unittest.TestCase):
    @staticmethod
    def _fixture() -> tuple[TimestampedPair, AlignedSegment]:
        times = np.arange(4001, dtype=float) * 0.1
        phone = np.zeros((len(times), 16), dtype=float)
        reference = np.zeros((len(times), 5), dtype=float)
        reference[:, 0] = 52.0 + times * 10.0 / 6_371_000.0 * 180.0 / np.pi
        reference[:, 2] = 36.0
        rows = np.arange(len(times), dtype=int)
        pair = TimestampedPair(
            phone_time_s=times.copy(),
            phone_elapsed_ms=times * 1000.0,
            phone=phone.copy(),
            reference_time_s=times.copy(),
            reference=reference.copy(),
            phone_path=Path("phone.csv"),
            reference_path=Path("reference.csv"),
        )
        segment = AlignedSegment(
            phone=phone.copy(),
            reference=reference.copy(),
            time_s=times.copy(),
            reference_rows=rows,
            phone_span=(0, len(times)),
            reference_span=(0, len(times)),
            phone_left_rows=rows.copy(),
            phone_right_rows=rows.copy(),
        )
        return pair, segment

    @staticmethod
    def _slice_segment(segment: AlignedSegment, start: int, end: int) -> AlignedSegment:
        return AlignedSegment(
            phone=segment.phone[start:end].copy(),
            reference=segment.reference[start:end].copy(),
            time_s=segment.time_s[start:end].copy(),
            reference_rows=segment.reference_rows[start:end].copy(),
            phone_span=(start, end),
            reference_span=(start, end),
            phone_left_rows=segment.phone_left_rows[start:end].copy(),
            phone_right_rows=segment.phone_right_rows[start:end].copy(),
        )

    def test_actual_elapsed_integration_and_left_endpoint_heading(self):
        east, north = integrate_displacement(
            np.array([0.0, 0.1, 0.3]),
            np.array([10.0, 10.0]),
            np.zeros(2),
        )
        np.testing.assert_allclose([east, north], [0.0, 3.0], atol=1e-10)
        heading = phone_headings(
            0.0, np.array([np.pi / 2, np.pi / 2]), np.ones(2), 0.0
        )
        np.testing.assert_allclose(heading, [0.0, np.pi / 2])

    def test_complete_window_and_full_history_are_accepted(self):
        pair, segment = self._fixture()

        windows = make_windows(pair, [segment], first_candidate_row=1800)

        first = windows[0]
        self.assertTrue(first["included"])
        self.assertEqual(first["raw_start_row"], 1800)
        self.assertEqual(first["raw_end_row"], 2400)
        self.assertEqual(first["calibration_raw_bounds"], [600, 1800])
        self.assertEqual(first["local_bounds"], [1800, 2400])
        self.assertEqual(first["calibration_local_bounds"], [600, 1800])
        east, north = integrate_displacement(
            pair.reference_time_s[1800:2401],
            pair.reference[1800:2400, 2] / 3.6,
            np.deg2rad(pair.reference[1800:2400, 3]),
        )
        np.testing.assert_allclose([east, north], [0.0, 600.0], atol=1e-8)

    def test_split_inside_outage_or_calibration_rejects_same_candidate(self):
        pair, segment = self._fixture()
        for split in (2100, 1200):
            with self.subTest(split=split):
                segments = [
                    self._slice_segment(segment, 0, split),
                    self._slice_segment(segment, split, len(segment.time_s)),
                ]
                record = make_windows(pair, segments, first_candidate_row=1800)[0]
                self.assertEqual(record["raw_start_row"], 1800)
                self.assertFalse(record["included"])
                self.assertEqual(record["exclusion_reason"], "missing_or_gap")

    def test_overlapping_reference_rows_are_rejected_as_ambiguous(self):
        pair, segment = self._fixture()
        duplicate = self._slice_segment(segment, 1700, 2501)

        record = make_windows(pair, [segment, duplicate], first_candidate_row=1800)[0]

        self.assertFalse(record["included"])
        self.assertEqual(record["exclusion_reason"], "ambiguous_reference_rows")

    def test_final_out_of_range_candidate_is_not_silently_dropped(self):
        pair, segment = self._fixture()

        windows = make_windows(pair, [segment], first_candidate_row=1800)

        self.assertEqual([row["raw_start_row"] for row in windows], [1800, 2400, 3000, 3600])
        self.assertFalse(windows[-1]["included"])
        self.assertEqual(windows[-1]["exclusion_reason"], "endpoint_out_of_range")

    def test_missing_endpoint_row_is_not_integrated(self):
        pair, segment = self._fixture()
        shortened = self._slice_segment(segment, 0, 2400)

        record = make_windows(pair, [shortened], first_candidate_row=1800)[0]

        self.assertFalse(record["included"])
        self.assertEqual(record["exclusion_reason"], "missing_or_gap")

    def test_non_10hz_reference_cadence_is_rejected_and_logged(self):
        pair, segment = self._fixture()
        pair.reference_time_s[2000] += 0.002
        segment.time_s[2000] += 0.002

        record = make_windows(pair, [segment], first_candidate_row=1800)[0]

        self.assertFalse(record["included"])
        self.assertEqual(record["exclusion_reason"], "non_10hz_reference_cadence")

    def test_window_exclusion_does_not_use_reference_labels(self):
        pair, segment = self._fixture()
        before = make_windows(pair, [segment], first_candidate_row=1800)
        pair.reference[:, 2:] = np.linspace(-1e6, 1e6, len(pair.reference))[:, None]
        segment.reference[:, 2:] = pair.reference[:, 2:]
        after = make_windows(pair, [segment], first_candidate_row=1800)

        self.assertEqual(
            [(row["included"], row["exclusion_reason"]) for row in before],
            [(row["included"], row["exclusion_reason"]) for row in after],
        )

    def test_phone_gps_column_is_not_a_causal_feature(self):
        pair, _ = self._fixture()
        before = causal_features(pair.phone)
        pair.phone[:, 0] = np.linspace(-1e9, 1e9, len(pair.phone))
        after = causal_features(pair.phone)
        np.testing.assert_array_equal(before, after)

    def test_learned_raw_phone_gyro_does_not_use_outage_reference_labels(self):
        pair, segment = self._fixture()
        window = make_windows(pair, [segment], first_candidate_row=1800)[0]
        predicted_speed = np.linspace(8.0, 12.0, len(segment.time_s))
        predicted_yaw = np.linspace(-0.02, 0.03, len(segment.time_s))
        before = evaluate_window_method(
            window,
            segment,
            predicted_speed,
            predicted_yaw,
            speed_profile="learned_raw",
            heading_profile="phone_gyro",
            gyro_calibration_profile="frozen_s1",
        )
        # Preserve the privileged initial state and the complete pre-outage
        # calibration labels; mutate only labels strictly after outage start.
        segment.reference[1801:, 2] = 720.0
        segment.reference[1801:, 3] = 177.0
        segment.reference[1801:, 4] = -900.0
        after = evaluate_window_method(
            window,
            segment,
            predicted_speed,
            predicted_yaw,
            speed_profile="learned_raw",
            heading_profile="phone_gyro",
            gyro_calibration_profile="frozen_s1",
        )

        np.testing.assert_allclose(
            [before["predicted_east_m"], before["predicted_north_m"]],
            [after["predicted_east_m"], after["predicted_north_m"]],
            atol=1e-10,
        )
        self.assertNotEqual(before["distance_m"], after["distance_m"])


if __name__ == "__main__":
    unittest.main()
