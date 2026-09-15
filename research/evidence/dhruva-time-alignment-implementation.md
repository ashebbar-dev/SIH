# Dhruva time-alignment implementation evidence

Date: 2026-09-10

## Scope and implementation

This task added only:

- `prototypes/dhruva/time_alignment.py`
- `prototypes/dhruva/tests/test_time_alignment.py`
- this evidence report

The existing benchmark, transfer audit, datasets, and result artifacts were not
changed. The implementation preserves both raw stream lengths, source paths,
corrected phone timestamps, VBOX timestamps, phone elapsed milliseconds, and raw
row provenance. It separates time gaps, nonmonotonic clocks, and phone logger
restarts before interpolation. Phone orientation is unwrapped inside each valid
span, interpolated along the shortest angular path, and wrapped to
`[-180 degrees, 180 degrees)`.

The residual clock convention is:

```text
aligned_phone_time = phone_time_s + residual_offset_s
```

Clock selection uses only each stream's initial contiguous raw acquisition span,
intersected with its fixed first 140 physical seconds. It does not admit later
samples by shifting a candidate clock or by falling through to a later logging
episode. Absolute gyro/yaw correlation is a reference-assisted offline benchmark
operation, not a phone-only deployment mechanism.

## Red/green evidence

The test file was created before the implementation. Exact initial command:

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_time_alignment.py' -v
```

Initial expected failure:

```text
ImportError: Failed to import test module: test_time_alignment
ModuleNotFoundError: No module named 'prototypes.dhruva.time_alignment'

FAILED (errors=1)
```

Exact final command:

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_time_alignment.py' -v
```

Exact final result:

```text
test_alignment_never_bridges_a_phone_gap_and_retains_raw_rows (test_time_alignment.TimeAlignmentTests.test_alignment_never_bridges_a_phone_gap_and_retains_raw_rows) ... ok
test_clock_calibration_recovers_offset_and_ignores_post_prefix_data (test_time_alignment.TimeAlignmentTests.test_clock_calibration_recovers_offset_and_ignores_post_prefix_data) ... ok
test_elapsed_restart_splits_smooth_wall_clock (test_time_alignment.TimeAlignmentTests.test_elapsed_restart_splits_smooth_wall_clock) ... ok
test_gap_and_restart_split (test_time_alignment.TimeAlignmentTests.test_gap_and_restart_split) ... ok
test_loader_preserves_unequal_lengths_and_explicit_timezone (test_time_alignment.TimeAlignmentTests.test_loader_preserves_unequal_lengths_and_explicit_timezone) ... ok
test_loader_rejects_invalid_or_nonfinite_input (test_time_alignment.TimeAlignmentTests.test_loader_rejects_invalid_or_nonfinite_input) ... ok
test_nonmonotonic_split (test_time_alignment.TimeAlignmentTests.test_nonmonotonic_split) ... ok
test_orientation_uses_shortest_angle_interpolation (test_time_alignment.TimeAlignmentTests.test_orientation_uses_shortest_angle_interpolation) ... ok
test_vbox_midnight_rollover_is_unwrapped (test_time_alignment.TimeAlignmentTests.test_vbox_midnight_rollover_is_unwrapped) ... ok
test_zero_motion_clock_calibration_fails_explicitly (test_time_alignment.TimeAlignmentTests.test_zero_motion_clock_calibration_fails_explicitly) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.108s

OK
```

An additional real-S4 invariant check returned:

```text
{'segments': 3, 'rows': 91447, 'brackets_confined': True}
```

Both implementation and test modules also passed `python -m py_compile` in the
existing virtual environment.

## Real-data CLI audits

Each audit used:

```sh
.venv/bin/python prototypes/dhruva/time_alignment.py --data-root /tmp/iovnbd --sequence SEQUENCE --phone-utc-offset-s 3600
```

### S1 exact output

```json
{
  "aligned_row_count": 51743,
  "aligned_segments": [
    {
      "phone_bracket_row_bounds": [
        0,
        51743
      ],
      "phone_span": [
        0,
        51746
      ],
      "reference_row_bounds": [
        3,
        51745
      ],
      "reference_span": [
        0,
        51746
      ],
      "row_count": 51743,
      "time_bounds_s": [
        1567933669.3,
        1567938843.5
      ]
    }
  ],
  "clock_estimate": {
    "absolute_correlation": 0.973627262592731,
    "calibration_time_bounds_s": [
      1567933669.3,
      1567933809.0
    ],
    "low_confidence": false,
    "paired_sample_count": 1398,
    "phone_gyro_axis": 1,
    "phone_prefix_time_bounds_s": [
      1567933669.546,
      1567933809.545
    ],
    "reference_prefix_time_bounds_s": [
      1567933669.0,
      1567933809.0
    ],
    "residual_offset_s": -0.3
  },
  "phone_discontinuities": [],
  "phone_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/S-S1.csv",
  "phone_row_count": 51746,
  "phone_time_bounds_s": [
    1567933669.546,
    1567938844.045
  ],
  "reference_discontinuities": [],
  "reference_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/V-S1.csv",
  "reference_row_count": 51746,
  "reference_time_bounds_s": [
    1567933669.0,
    1567938843.5
  ]
}
```

### S2 exact output

```json
{
  "aligned_row_count": 93788,
  "aligned_segments": [
    {
      "phone_bracket_row_bounds": [
        0,
        1863
      ],
      "phone_span": [
        0,
        1864
      ],
      "reference_row_bounds": [
        76,
        1938
      ],
      "reference_span": [
        0,
        93876
      ],
      "row_count": 1863,
      "time_bounds_s": [
        1567940632.0,
        1567940818.2
      ]
    },
    {
      "phone_bracket_row_bounds": [
        1864,
        93789
      ],
      "phone_span": [
        1864,
        93876
      ],
      "reference_row_bounds": [
        1951,
        93875
      ],
      "reference_span": [
        0,
        93876
      ],
      "row_count": 91925,
      "time_bounds_s": [
        1567940819.5,
        1567950011.9
      ]
    }
  ],
  "clock_estimate": {
    "absolute_correlation": 0.9840840490091388,
    "calibration_time_bounds_s": [
      1567940632.0,
      1567940764.4
    ],
    "low_confidence": false,
    "paired_sample_count": 1325,
    "phone_gyro_axis": 1,
    "phone_prefix_time_bounds_s": [
      1567940631.741,
      1567940771.741
    ],
    "reference_prefix_time_bounds_s": [
      1567940624.4,
      1567940764.4
    ],
    "residual_offset_s": 0.2
  },
  "phone_discontinuities": [
    {
      "elapsed_delta_ms": -186301.0,
      "next_elapsed_ms": 10.0,
      "next_row": 1864,
      "next_time_s": 1567940819.249,
      "previous_elapsed_ms": 186311.0,
      "previous_row": 1863,
      "previous_time_s": 1567940818.041,
      "reasons": [
        "time_gap",
        "elapsed_restart"
      ],
      "time_delta_s": 1.2080001831054688
    }
  ],
  "phone_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S2/S-S2.csv",
  "phone_row_count": 93876,
  "phone_time_bounds_s": [
    1567940631.741,
    1567950020.349
  ],
  "reference_discontinuities": [],
  "reference_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S2/V-S2.csv",
  "reference_row_count": 93876,
  "reference_time_bounds_s": [
    1567940624.4,
    1567950011.9
  ]
}
```

### S3a exact output

```json
{
  "aligned_row_count": 24553,
  "aligned_segments": [
    {
      "phone_bracket_row_bounds": [
        67,
        24620
      ],
      "phone_span": [
        0,
        24621
      ],
      "reference_row_bounds": [
        0,
        24552
      ],
      "reference_span": [
        0,
        24621
      ],
      "row_count": 24553,
      "time_bounds_s": [
        1567621318.0,
        1567623773.2
      ]
    }
  ],
  "clock_estimate": {
    "absolute_correlation": 0.9712053258256621,
    "calibration_time_bounds_s": [
      1567621318.0,
      1567621451.1
    ],
    "low_confidence": false,
    "paired_sample_count": 1332,
    "phone_gyro_axis": 1,
    "phone_prefix_time_bounds_s": [
      1567621311.494,
      1567621451.393
    ],
    "reference_prefix_time_bounds_s": [
      1567621318.0,
      1567621458.0
    ],
    "residual_offset_s": -0.2
  },
  "phone_discontinuities": [],
  "phone_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S3a/S-S3a.csv",
  "phone_row_count": 24621,
  "phone_time_bounds_s": [
    1567621311.494,
    1567623773.494
  ],
  "reference_discontinuities": [],
  "reference_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S3a/V-S3a.csv",
  "reference_row_count": 24621,
  "reference_time_bounds_s": [
    1567621318.0,
    1567623780.0
  ]
}
```

### S4 exact output

```json
{
  "aligned_row_count": 91447,
  "aligned_segments": [
    {
      "phone_bracket_row_bounds": [
        0,
        35185
      ],
      "phone_span": [
        0,
        35186
      ],
      "reference_row_bounds": [
        19,
        35203
      ],
      "reference_span": [
        0,
        94600
      ],
      "row_count": 35185,
      "time_bounds_s": [
        1567790175.3,
        1567793693.7
      ]
    },
    {
      "phone_bracket_row_bounds": [
        35186,
        90966
      ],
      "phone_span": [
        35186,
        90967
      ],
      "reference_row_bounds": [
        38325,
        94104
      ],
      "reference_span": [
        0,
        94600
      ],
      "row_count": 55780,
      "time_bounds_s": [
        1567794005.9,
        1567799583.8
      ]
    },
    {
      "phone_bracket_row_bounds": [
        90967,
        91449
      ],
      "phone_span": [
        90967,
        94600
      ],
      "reference_row_bounds": [
        94118,
        94599
      ],
      "reference_span": [
        0,
        94600
      ],
      "row_count": 482,
      "time_bounds_s": [
        1567799585.2,
        1567799633.3
      ]
    }
  ],
  "clock_estimate": {
    "absolute_correlation": 0.9686993298183117,
    "calibration_time_bounds_s": [
      1567790175.3,
      1567790313.4
    ],
    "low_confidence": false,
    "paired_sample_count": 1382,
    "phone_gyro_axis": 1,
    "phone_prefix_time_bounds_s": [
      1567790175.111,
      1567790315.11
    ],
    "reference_prefix_time_bounds_s": [
      1567790173.4,
      1567790313.4
    ],
    "residual_offset_s": 0.1
  },
  "phone_discontinuities": [
    {
      "elapsed_delta_ms": -3526919.0,
      "next_elapsed_ms": 10.0,
      "next_row": 35186,
      "next_time_s": 1567794005.753,
      "previous_elapsed_ms": 3526929.0,
      "previous_row": 35185,
      "previous_time_s": 1567793693.611,
      "reasons": [
        "time_gap",
        "elapsed_restart"
      ],
      "time_delta_s": 312.1419999599457
    },
    {
      "elapsed_delta_ms": -5578000.0,
      "next_elapsed_ms": 9.0,
      "next_row": 90967,
      "next_time_s": 1567799585.016,
      "previous_elapsed_ms": 5578009.0,
      "previous_row": 90966,
      "previous_time_s": 1567799583.752,
      "reasons": [
        "time_gap",
        "elapsed_restart"
      ],
      "time_delta_s": 1.2639999389648438
    }
  ],
  "phone_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4/S-S4.csv",
  "phone_row_count": 94600,
  "phone_time_bounds_s": [
    1567790175.111,
    1567799948.216
  ],
  "reference_discontinuities": [],
  "reference_path": "/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4/V-S4.csv",
  "reference_row_count": 94600,
  "reference_time_bounds_s": [
    1567790173.4,
    1567799633.3
  ]
}
```

The S4 audit exposes the verified raw `35185 -> 35186` phone gap as
`312.1419999599457` seconds and the elapsed logger restart from `3526929` to
`10` milliseconds. The aligned bracket bounds are confined to the half-open
phone spans `(0, 35186)`, `(35186, 90967)`, and `(90967, 94600)`; no bracket
crosses either restart.

## Assumptions and limitations

- The supplied 3600-second phone correction is an explicit inferred dataset
  setting. It is not independently certified acquisition metadata.
- Residual calibration uses VBOX yaw in a fixed healthy prefix. It is valid for
  this offline benchmark audit only and does not demonstrate phone-only clock
  recovery.
- A correlation below 0.8 is returned as low confidence rather than certified
  alignment. Zero-motion or otherwise degenerate prefixes fail explicitly.
- The 0.1-second search grid limits resolution; this task does not model clock
  drift or piecewise clock changes after the prefix.
- Singleton spans are retained by segmentation but cannot provide interpolation
  intervals. No extrapolation, sorting, label interpolation, or gap bridging is
  performed.
- These loader and alignment checks make no navigation-accuracy claim and do not
  validate a later estimator comparison.

## Final review fix: initial-span-only calibration

The final cross-file review found that the original upper-bound-only prefix
selection could include a later raw span after a backward timestamp restart.
Because overlap selection then ranked spans by timestamp, a restarted span with
an earlier clock could replace the initial acquisition episode.

The fix determines each stream's initial contiguous raw span first and only then
clips that span at `first_timestamp + prefix_s`. Calibration considers this
single acquisition-ordered span from each stream. It never falls back to a later
span; fewer than 50 varying observations in the initial overlap fail explicitly.
`align_pair` is unchanged and continues to return every valid alignment span.

Three focused regressions cover:

- mutation of a later backward-reset phone span;
- mutation after an elapsed-clock reset despite a smooth wall clock;
- an inadequate initial overlap followed by a long correlating span, which must
  fail instead of falling back.

Exact red command:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_time_alignment.py' -v
```

Exact red result before the fix:

```text
test_alignment_never_bridges_a_phone_gap_and_retains_raw_rows (test_time_alignment.TimeAlignmentTests.test_alignment_never_bridges_a_phone_gap_and_retains_raw_rows) ... ok
test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap (test_time_alignment.TimeAlignmentTests.test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap) ... FAIL
test_clock_calibration_ignores_later_backward_restart (test_time_alignment.TimeAlignmentTests.test_clock_calibration_ignores_later_backward_restart) ... FAIL
test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset (test_time_alignment.TimeAlignmentTests.test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset) ... FAIL
test_clock_calibration_recovers_offset_and_ignores_post_prefix_data (test_time_alignment.TimeAlignmentTests.test_clock_calibration_recovers_offset_and_ignores_post_prefix_data) ... ok
test_elapsed_restart_splits_smooth_wall_clock (test_time_alignment.TimeAlignmentTests.test_elapsed_restart_splits_smooth_wall_clock) ... ok
test_gap_and_restart_split (test_time_alignment.TimeAlignmentTests.test_gap_and_restart_split) ... ok
test_loader_preserves_unequal_lengths_and_explicit_timezone (test_time_alignment.TimeAlignmentTests.test_loader_preserves_unequal_lengths_and_explicit_timezone) ... ok
test_loader_rejects_invalid_or_nonfinite_input (test_time_alignment.TimeAlignmentTests.test_loader_rejects_invalid_or_nonfinite_input) ... ok
test_nonmonotonic_split (test_time_alignment.TimeAlignmentTests.test_nonmonotonic_split) ... ok
test_orientation_uses_shortest_angle_interpolation (test_time_alignment.TimeAlignmentTests.test_orientation_uses_shortest_angle_interpolation) ... ok
test_vbox_midnight_rollover_is_unwrapped (test_time_alignment.TimeAlignmentTests.test_vbox_midnight_rollover_is_unwrapped) ... ok
test_zero_motion_clock_calibration_fails_explicitly (test_time_alignment.TimeAlignmentTests.test_zero_motion_clock_calibration_fails_explicitly) ... ok

======================================================================
FAIL: test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap (test_time_alignment.TimeAlignmentTests.test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/user_end4/MySpace/SIH/prototypes/dhruva/tests/test_time_alignment.py", line 266, in test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap
    with self.assertRaisesRegex(ValueError, "initial contiguous"):
         ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: ValueError not raised

======================================================================
FAIL: test_clock_calibration_ignores_later_backward_restart (test_time_alignment.TimeAlignmentTests.test_clock_calibration_ignores_later_backward_restart)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/user_end4/MySpace/SIH/prototypes/dhruva/tests/test_time_alignment.py", line 235, in test_clock_calibration_ignores_later_backward_restart
    self.assertEqual(before, after)
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^
AssertionError: {'res[65 chars]': 0.9999999999999999, 'paired_sample_count': [169 chars]alse} != {'res[65 chars]': 0.4789856000556507, 'paired_sample_count': [168 chars]True}
- {'absolute_correlation': 0.9999999999999999,
+ {'absolute_correlation': 0.4789856000556507,
   'calibration_time_bounds_s': [0.0, 9.9],
-  'low_confidence': False,
?                    ^^^^

+  'low_confidence': True,
?                    ^^^

   'paired_sample_count': 100,
   'phone_gyro_axis': 0,
   'phone_prefix_time_bounds_s': [10.0, 9.9],
   'reference_prefix_time_bounds_s': [0.0, 19.900000000000002],
   'residual_offset_s': 0.0}

======================================================================
FAIL: test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset (test_time_alignment.TimeAlignmentTests.test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/user_end4/MySpace/SIH/prototypes/dhruva/tests/test_time_alignment.py", line 255, in test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset
    self.assertEqual(before["phone_prefix_time_bounds_s"], [0.0, time[99]])
    ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
AssertionError: Lists differ: [0.0, 19.900000000000002] != [0.0, np.float64(9.9)]

First differing element 1:
19.900000000000002
np.float64(9.9)

- [0.0, 19.900000000000002]
+ [0.0, np.float64(9.9)]

----------------------------------------------------------------------
Ran 13 tests in 0.103s

FAILED (failures=3)
```

Exact green command:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_time_alignment.py' -v
```

Exact green output:

```text
test_alignment_never_bridges_a_phone_gap_and_retains_raw_rows (test_time_alignment.TimeAlignmentTests.test_alignment_never_bridges_a_phone_gap_and_retains_raw_rows) ... ok
test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap (test_time_alignment.TimeAlignmentTests.test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap) ... ok
test_clock_calibration_ignores_later_backward_restart (test_time_alignment.TimeAlignmentTests.test_clock_calibration_ignores_later_backward_restart) ... ok
test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset (test_time_alignment.TimeAlignmentTests.test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset) ... ok
test_clock_calibration_recovers_offset_and_ignores_post_prefix_data (test_time_alignment.TimeAlignmentTests.test_clock_calibration_recovers_offset_and_ignores_post_prefix_data) ... ok
test_elapsed_restart_splits_smooth_wall_clock (test_time_alignment.TimeAlignmentTests.test_elapsed_restart_splits_smooth_wall_clock) ... ok
test_gap_and_restart_split (test_time_alignment.TimeAlignmentTests.test_gap_and_restart_split) ... ok
test_loader_preserves_unequal_lengths_and_explicit_timezone (test_time_alignment.TimeAlignmentTests.test_loader_preserves_unequal_lengths_and_explicit_timezone) ... ok
test_loader_rejects_invalid_or_nonfinite_input (test_time_alignment.TimeAlignmentTests.test_loader_rejects_invalid_or_nonfinite_input) ... ok
test_nonmonotonic_split (test_time_alignment.TimeAlignmentTests.test_nonmonotonic_split) ... ok
test_orientation_uses_shortest_angle_interpolation (test_time_alignment.TimeAlignmentTests.test_orientation_uses_shortest_angle_interpolation) ... ok
test_vbox_midnight_rollover_is_unwrapped (test_time_alignment.TimeAlignmentTests.test_vbox_midnight_rollover_is_unwrapped) ... ok
test_zero_motion_clock_calibration_fails_explicitly (test_time_alignment.TimeAlignmentTests.test_zero_motion_clock_calibration_fails_explicitly) ... ok

----------------------------------------------------------------------
Ran 13 tests in 0.057s

OK
```

The four real-sequence audits were not repeated because their calibration
prefixes are unchanged by this correction: S1 and S3a have no discontinuity,
S2's first restart is after about 186 seconds, and S4's first restart is after
about 3,526 seconds. All are later than the fixed 140-second calibration prefix.
The exact retained S1/S2/S3a/S4 audit output above therefore remains applicable.
Independently, the implementation now guarantees that any gap, nonmonotonic
timestamp, or elapsed-clock reset before 140 seconds ends the eligible initial
span, so clocks or measurements after that boundary cannot affect calibration.
