import unittest

import numpy as np

from research.tools.dhruva_speed_state import (
    absolute_speed,
    backward_targets,
    integrate_speed,
    speed_metrics,
)


class SpeedStateTests(unittest.TestCase):
    def test_backward_targets_use_preceding_interval_and_nz2_support(self):
        times = np.array([0.0, 0.1, 0.4, 0.6])
        speed = np.array([2.0, 2.0, 8.0, 5.0])
        satellites = np.ones(20)
        satellites[11] = 0.0

        targets, supports, keep = backward_targets(
            times, speed, np.arange(10, 14), satellites
        )

        self.assertTrue(np.isnan(targets[0]))
        np.testing.assert_allclose(targets[1:], [0.0, 20.0, -15.0], atol=1e-12)
        np.testing.assert_array_equal(
            supports, [[-1, 10], [10, 11], [11, 12], [12, 13]]
        )
        np.testing.assert_array_equal(keep, [False, False, False, True])

    def test_backward_targets_only_zero_satellites_fail_nz2(self):
        targets, _, keep = backward_targets(
            np.array([0.0, 1.0]),
            np.array([3.0, 4.0]),
            np.array([1, 2]),
            np.array([0.0, 2.0, -3.0]),
        )
        np.testing.assert_array_equal(targets[1:], [1.0])
        np.testing.assert_array_equal(keep, [False, True])

    def test_integrate_speed_reproduces_onset_and_braking_sequence(self):
        speed = np.array([0.0, 0.0, 1.0, 1.0, 0.0, 2.0])
        times = np.arange(6) * 0.1
        acceleration = np.r_[999.0, np.diff(speed) / np.diff(times)]

        signed, output = integrate_speed(times, acceleration, speed[0])

        np.testing.assert_allclose(signed, speed, atol=1e-12)
        np.testing.assert_allclose(output, speed, atol=1e-12)

    def test_integrate_speed_clips_output_without_state_feedback(self):
        signed, output = integrate_speed(
            np.array([0.0, 1.0, 2.0]), np.array([999.0, -2.0, 1.0]), 1.0
        )

        np.testing.assert_array_equal(signed, [1.0, -1.0, 0.0])
        np.testing.assert_array_equal(output, [1.0, 0.0, 0.0])

    def test_integrate_speed_ignores_first_acceleration_sample(self):
        times = np.array([0.0, 0.1, 0.3])
        baseline = integrate_speed(times, np.array([0.0, 0.0, 0.0]), 10.0)
        perturbed = integrate_speed(times, np.array([1e9, 0.0, 0.0]), 10.0)

        for actual in baseline + perturbed:
            np.testing.assert_array_equal(actual, [10.0, 10.0, 10.0])

    def test_absolute_speed_preserves_legacy_offset_ordering(self):
        candidate, output = absolute_speed(np.array([-5.0, 2.0, 4.0]), 10.0)

        np.testing.assert_array_equal(candidate, [10.0, 12.0, 14.0])
        np.testing.assert_array_equal(output, [10.0, 12.0, 14.0])

        candidate, output = absolute_speed(np.array([-5.0, 2.0, -4.0]))
        np.testing.assert_array_equal(candidate, [-5.0, 2.0, -4.0])
        np.testing.assert_array_equal(output, [0.0, 2.0, 0.0])

    def test_metrics_constant_acceleration_contract(self):
        times = np.arange(601) * 0.1
        gps = np.full(601, 10.0)
        acceleration = np.full(601, 0.1)
        signed, output = integrate_speed(times, acceleration, 10.0)

        result = speed_metrics(
            times=times,
            signed_speed=signed,
            output_speed=output,
            gps_speed=gps,
            indicated_speed=gps,
            headings=np.zeros(601),
            truth_displacement=(0.0, 600.0),
            acceleration=acceleration,
        )

        self.assertEqual(
            set(result),
            {
                "predicted_east_m",
                "predicted_north_m",
                "truth_east_m",
                "truth_north_m",
                "distance_m",
                "distance_eligible_for_drift_ratio",
                "endpoint_error_m",
                "drift_ratio",
                "speed_mae_gps_mps",
                "speed_mae_indicated_mps",
                "mean_speed_error_mps",
                "mean_unclipped_speed_error_mps",
                "clipped_fraction",
                "terminal_speed_error_mps",
                "mean_acceleration_error_mps2",
            },
        )
        self.assertAlmostEqual(result["endpoint_error_m"], 179.7, delta=1e-8)
        self.assertAlmostEqual(result["terminal_speed_error_mps"], 6.0, delta=1e-10)
        self.assertAlmostEqual(
            result["mean_acceleration_error_mps2"], 0.1, delta=1e-12
        )

    def test_metrics_zero_acceleration_has_exact_constant_speed_results(self):
        times = np.array([0.0, 0.1, 0.3])
        gps = np.full(3, 10.0)
        acceleration = np.zeros(3)
        signed, output = integrate_speed(times, acceleration, 10.0)

        result = speed_metrics(
            times=times,
            signed_speed=signed,
            output_speed=output,
            gps_speed=gps,
            indicated_speed=gps,
            headings=np.zeros(3),
            truth_displacement=(0.0, 3.0),
            acceleration=acceleration,
        )

        np.testing.assert_array_equal(signed, [10.0, 10.0, 10.0])
        np.testing.assert_array_equal(output, [10.0, 10.0, 10.0])
        self.assertEqual(result["speed_mae_gps_mps"], 0.0)
        self.assertEqual(result["speed_mae_indicated_mps"], 0.0)
        self.assertEqual(result["endpoint_error_m"], 0.0)
        self.assertEqual(result["distance_m"], 3.0)
        self.assertIsNone(result["drift_ratio"])
        self.assertFalse(result["distance_eligible_for_drift_ratio"])

    def test_metrics_use_left_samples_and_report_signed_state(self):
        result = speed_metrics(
            times=np.array([0.0, 1.0, 3.0]),
            signed_speed=np.array([2.0, -1.0, 99.0]),
            output_speed=np.array([2.0, 0.0, 99.0]),
            gps_speed=np.array([1.0, 1.0, 99.0]),
            indicated_speed=np.array([0.0, 2.0, 99.0]),
            headings=np.array([np.pi / 2.0, 0.0, 123.0]),
            truth_displacement=(2.0, 0.0),
        )

        self.assertAlmostEqual(result["predicted_east_m"], 2.0)
        self.assertAlmostEqual(result["predicted_north_m"], 0.0)
        self.assertAlmostEqual(result["distance_m"], 3.0)
        self.assertAlmostEqual(result["speed_mae_gps_mps"], 1.0)
        self.assertAlmostEqual(result["speed_mae_indicated_mps"], 2.0)
        self.assertAlmostEqual(result["mean_speed_error_mps"], -1.0 / 3.0)
        self.assertAlmostEqual(result["mean_unclipped_speed_error_mps"], -1.0)
        self.assertEqual(result["clipped_fraction"], 0.5)
        self.assertEqual(result["terminal_speed_error_mps"], 0.0)
        self.assertIsNone(result["mean_acceleration_error_mps2"])

    def test_invalid_shapes_nonfinite_values_and_duplicate_times_are_rejected(self):
        one_d = np.array([0.0, 1.0])
        with self.assertRaises(ValueError):
            backward_targets(one_d[:, None], one_d, np.array([0, 1]), one_d)
        with self.assertRaises(ValueError):
            backward_targets(one_d, np.array([0.0]), np.array([0, 1]), one_d)
        with self.assertRaises(ValueError):
            backward_targets(
                np.array([0.0, 0.0]), one_d, np.array([0, 1]), one_d
            )
        with self.assertRaises(ValueError):
            backward_targets(
                one_d, np.array([0.0, np.inf]), np.array([0, 1]), one_d
            )
        with self.assertRaises(ValueError):
            backward_targets(one_d, one_d, np.array([0, 1]), np.array([0.0, np.nan]))
        with self.assertRaises(ValueError):
            integrate_speed(one_d, one_d[:, None], 0.0)
        with self.assertRaises(ValueError):
            integrate_speed(np.array([0.0, 0.0]), one_d, 0.0)
        with self.assertRaises(ValueError):
            integrate_speed(one_d, np.array([0.0, np.nan]), 0.0)
        with self.assertRaises(ValueError):
            absolute_speed(np.array([[1.0]]))
        with self.assertRaises(ValueError):
            absolute_speed(np.array([np.inf]))

        valid_metrics = dict(
            times=one_d,
            signed_speed=one_d,
            output_speed=one_d,
            gps_speed=one_d,
            indicated_speed=one_d,
            headings=one_d,
            truth_displacement=(0.0, 0.0),
        )
        for name in (
            "signed_speed",
            "output_speed",
            "gps_speed",
            "indicated_speed",
            "headings",
        ):
            kwargs = valid_metrics.copy()
            kwargs[name] = one_d[:, None]
            with self.subTest(metrics_shape=name), self.assertRaises(ValueError):
                speed_metrics(**kwargs)
        kwargs = valid_metrics.copy()
        kwargs["gps_speed"] = np.array([0.0, np.nan])
        with self.assertRaises(ValueError):
            speed_metrics(**kwargs)
        kwargs = valid_metrics.copy()
        kwargs["times"] = np.array([0.0, 0.0])
        with self.assertRaises(ValueError):
            speed_metrics(**kwargs)

    def test_invalid_rows_and_initial_speed_are_rejected(self):
        times = np.arange(3, dtype=float)
        speed = np.arange(3, dtype=float)
        satellites = np.ones(4)
        for rows in (
            np.array([0.0, 1.0, 2.0]),
            np.array([0, -1, 0]),
            np.array([0, 2, 3]),
            np.array([2, 3, 4]),
        ):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                backward_targets(times, speed, rows, satellites)

        with self.assertRaises(ValueError):
            integrate_speed(times, speed, -1.0)
        with self.assertRaises(ValueError):
            integrate_speed(times, speed, np.inf)
        with self.assertRaises(ValueError):
            absolute_speed(speed, -1.0)

    def test_metrics_reject_short_mismatched_and_invalid_optional_inputs(self):
        valid = np.array([0.0, 1.0])
        kwargs = dict(
            times=valid,
            signed_speed=valid,
            output_speed=valid,
            gps_speed=valid,
            indicated_speed=valid,
            headings=valid,
            truth_displacement=(0.0, 0.0),
        )
        for name in (
            "signed_speed",
            "output_speed",
            "gps_speed",
            "indicated_speed",
            "headings",
        ):
            changed = kwargs.copy()
            changed[name] = np.array([0.0])
            with self.subTest(metrics_length=name), self.assertRaises(ValueError):
                speed_metrics(**changed)
        changed = kwargs.copy()
        changed["times"] = np.array([0.0])
        for name in (
            "signed_speed",
            "output_speed",
            "gps_speed",
            "indicated_speed",
            "headings",
        ):
            changed[name] = np.array([0.0])
        with self.assertRaises(ValueError):
            speed_metrics(**changed)
        with self.assertRaises(ValueError):
            speed_metrics(**kwargs, acceleration=np.array([0.0]))
        with self.assertRaises(ValueError):
            speed_metrics(**kwargs, acceleration=np.array([0.0, np.nan]))
        changed = kwargs.copy()
        changed["truth_displacement"] = (0.0, np.inf)
        with self.assertRaises(ValueError):
            speed_metrics(**changed)


if __name__ == "__main__":
    unittest.main()
