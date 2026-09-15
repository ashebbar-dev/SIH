# Dhruva timestamp-aligned fixed-window ablation — implementation record

## Status and scope

Implemented the prespecified exploratory 60-second evaluation for S1, S2, S3a,
and S4. The runner evaluates all 12 fixed factorial combinations plus the
constant reference-initialized baseline on one common candidate set. It does
not evaluate alternative positioning systems, other outage durations, or new
models/features.

The evaluation is an offline diagnostic, not fresh confirmation. Reference
initial position/heading, reference initial speed where applicable, pre-outage
VBOX yaw labels, residual clock alignment, and both reference-oracle branches
are explicitly privileged. No novelty, deployment-readiness, target-pass, or
production-system claim is supported by these results.

## Created files

- `research/tools/audit_dhruva_aligned.py`
- `prototypes/dhruva/tests/test_aligned_ablation.py`
- `research/evidence/dhruva-aligned-ablation-implementation.md`
- `research/evidence/dhruva-aligned-2026-09-10-2/manifest.json`
- `research/evidence/dhruva-aligned-2026-09-10-2/windows.csv`
- `research/evidence/dhruva-aligned-2026-09-10-2/results.json`

The originally requested unnumbered output was never created: the first real
command failed at module import before entering `run()`. The corrected run used
the required clearly numbered fresh directory and did not overwrite anything.

## Implemented controls

- Actual `np.diff(times)` integration with L+1 timestamps, L velocities, and L
  left-endpoint headings.
- Exclusive gyro integration: outage sample zero uses exactly the privileged
  initial reference heading; only preceding yaw increments affect later samples.
- Raw-reference 600-row candidate grid, 1200-row pre-outage history, 200-row
  segment-local feature warmup, same-segment uniqueness, endpoint presence, and
  10 Hz cadence checks independent of speed/heading/error labels.
- Duplicate raw reference rows across aligned segments are rejected as
  `ambiguous_reference_rows`; gaps/restarts are never bridged.
- Unchanged legacy `causal_features`, computed independently within each aligned
  segment. Phone column 0 is proven absent from the learned inputs.
- S1 training rows require segment-local index at least 200, reference time
  strictly before the fixed 40% cutoff, both residual-shifted phone bracket times
  strictly before the cutoff, and an unambiguous raw reference row.
- One fixed `HistGradientBoostingRegressor` fit with the specified constants;
  learned predictions are clamped nonnegative. Exact changed aligned training
  rows are retained in the pre-fit manifest and are not presented as a
  single-variable comparison with the legacy 18.342% evidence.
- Frozen-S1 gyro calibration uses the manifested S1 training rows. Each
  journey-prefix calibration uses only its first aligned segment after row 200,
  stays inside both original raw clock prefixes, and has at least 50 finite rows.
- Manifest was exclusively created and fsynced before `model.fit`; its frozen
  SHA-256 is repeated in `results.json` and still matches the final file.
- All excluded and included candidates have all 13 method rows in `windows.csv`.
  Empty aggregate groups serialize as JSON `null`, never NaN.
- Reference-heading duplicate gyro-control branches are asserted equal to
  absolute tolerance `1e-12`; all methods are asserted to share identical valid
  window IDs.

## TDD record

### Expected red run

Command:

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_aligned_ablation.py' -v
```

Output (exit 1):

```text
/home/user_end4/.config/matplotlib is not a writable directory
Matplotlib created a temporary cache directory at /tmp/matplotlib-y2a6qrh5 because there was an issue with the path; it is highly recommended to set the MPLCONFIGDIR environment variable to a writable directory, in particular to speed up the import of Matplotlib and to better support multiprocessing.
test_aligned_ablation (unittest.loader._FailedTest.test_aligned_ablation) ... ERROR

======================================================================
ERROR: test_aligned_ablation (unittest.loader._FailedTest.test_aligned_ablation)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/usr/lib/python3.13/unittest/loader.py", line 396, in _find_test_path
    module = self._get_module_from_name(name)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/lib/python3.13/unittest/loader.py", line 339, in _get_module_from_name
    __import__(name)
  File "/home/user_end4/MySpace/SIH/prototypes/dhruva/tests/test_aligned_ablation.py", line 8, in <module>
    from research.tools.audit_dhruva_aligned import (
ModuleNotFoundError: No module named 'research.tools.audit_dhruva_aligned'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

### Intermediate test correction

The first implementation run executed 10 tests with 9 passing and one failing:

```text
FAIL: test_learned_raw_phone_gyro_does_not_use_outage_reference_labels
AssertionError: 180.06304787999548 == 180.06304787999548

----------------------------------------------------------------------
Ran 10 tests in 0.134s

FAILED (failures=1)
```

This was a test-assertion error: mutating only reference speed/heading/yaw does
not have to change coordinate-derived endpoint error. The requirement says
error/distance metrics may change. The assertion was corrected to require
unchanged predicted displacement and changed reference-derived distance.

### Final green run before diagnostic

Command:

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_aligned_ablation.py' -v
```

Output (exit 0):

```text
/home/user_end4/.config/matplotlib is not a writable directory
Matplotlib created a temporary cache directory at /tmp/matplotlib-9hbt5xcs because there was an issue with the path; it is highly recommended to set the MPLCONFIGDIR environment variable to a writable directory, in particular to speed up the import of Matplotlib and to better support multiprocessing.
test_actual_elapsed_integration_and_left_endpoint_heading (test_aligned_ablation.AlignedAblationTests.test_actual_elapsed_integration_and_left_endpoint_heading) ... ok
test_complete_window_and_full_history_are_accepted (test_aligned_ablation.AlignedAblationTests.test_complete_window_and_full_history_are_accepted) ... ok
test_final_out_of_range_candidate_is_not_silently_dropped (test_aligned_ablation.AlignedAblationTests.test_final_out_of_range_candidate_is_not_silently_dropped) ... ok
test_learned_raw_phone_gyro_does_not_use_outage_reference_labels (test_aligned_ablation.AlignedAblationTests.test_learned_raw_phone_gyro_does_not_use_outage_reference_labels) ... ok
test_missing_endpoint_row_is_not_integrated (test_aligned_ablation.AlignedAblationTests.test_missing_endpoint_row_is_not_integrated) ... ok
test_non_10hz_reference_cadence_is_rejected_and_logged (test_aligned_ablation.AlignedAblationTests.test_non_10hz_reference_cadence_is_rejected_and_logged) ... ok
test_overlapping_reference_rows_are_rejected_as_ambiguous (test_aligned_ablation.AlignedAblationTests.test_overlapping_reference_rows_are_rejected_as_ambiguous) ... ok
test_phone_gps_column_is_not_a_causal_feature (test_aligned_ablation.AlignedAblationTests.test_phone_gps_column_is_not_a_causal_feature) ... ok
test_split_inside_outage_or_calibration_rejects_same_candidate (test_aligned_ablation.AlignedAblationTests.test_split_inside_outage_or_calibration_rejects_same_candidate) ... ok
test_window_exclusion_does_not_use_reference_labels (test_aligned_ablation.AlignedAblationTests.test_window_exclusion_does_not_use_reference_labels) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.105s

OK
```

### Clean focused run retained for review

This evidence-only rerun used a writable matplotlib cache. No source or real
diagnostic was changed or rerun.

Command:

```sh
env MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_aligned_ablation.py' -v
```

Exact output (exit 0):

```text
test_actual_elapsed_integration_and_left_endpoint_heading (test_aligned_ablation.AlignedAblationTests.test_actual_elapsed_integration_and_left_endpoint_heading) ... ok
test_complete_window_and_full_history_are_accepted (test_aligned_ablation.AlignedAblationTests.test_complete_window_and_full_history_are_accepted) ... ok
test_final_out_of_range_candidate_is_not_silently_dropped (test_aligned_ablation.AlignedAblationTests.test_final_out_of_range_candidate_is_not_silently_dropped) ... ok
test_learned_raw_phone_gyro_does_not_use_outage_reference_labels (test_aligned_ablation.AlignedAblationTests.test_learned_raw_phone_gyro_does_not_use_outage_reference_labels) ... ok
test_missing_endpoint_row_is_not_integrated (test_aligned_ablation.AlignedAblationTests.test_missing_endpoint_row_is_not_integrated) ... ok
test_non_10hz_reference_cadence_is_rejected_and_logged (test_aligned_ablation.AlignedAblationTests.test_non_10hz_reference_cadence_is_rejected_and_logged) ... ok
test_overlapping_reference_rows_are_rejected_as_ambiguous (test_aligned_ablation.AlignedAblationTests.test_overlapping_reference_rows_are_rejected_as_ambiguous) ... ok
test_phone_gps_column_is_not_a_causal_feature (test_aligned_ablation.AlignedAblationTests.test_phone_gps_column_is_not_a_causal_feature) ... ok
test_split_inside_outage_or_calibration_rejects_same_candidate (test_aligned_ablation.AlignedAblationTests.test_split_inside_outage_or_calibration_rejects_same_candidate) ... ok
test_window_exclusion_does_not_use_reference_labels (test_aligned_ablation.AlignedAblationTests.test_window_exclusion_does_not_use_reference_labels) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.128s

OK
```

## Real execution record

### Attempt 1: entry-point bug before artifact creation

Command:

```sh
env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MPLCONFIGDIR=/tmp/sih-matplotlib \
  .venv/bin/python research/tools/audit_dhruva_aligned.py \
  --data-root /tmp/iovnbd \
  --output research/evidence/dhruva-aligned-2026-09-10
```

Output (exit 1):

```text
Traceback (most recent call last):
  File "/home/user_end4/MySpace/SIH/research/tools/audit_dhruva_aligned.py", line 26, in <module>
    from prototypes.dhruva import benchmark as legacy
ModuleNotFoundError: No module named 'prototypes'
```

The direct-script import path was corrected by inserting the resolved repository
root before repository imports. The failure happened before output-directory
creation, so there was no failed directory to preserve. After the correction,
the focused suite was run again with the same command. Complete output (exit 0):

```text
/home/user_end4/.config/matplotlib is not a writable directory
Matplotlib created a temporary cache directory at /tmp/matplotlib-sehiiq60 because there was an issue with the path; it is highly recommended to set the MPLCONFIGDIR environment variable to a writable directory, in particular to speed up the import of Matplotlib and to better support multiprocessing.
test_actual_elapsed_integration_and_left_endpoint_heading (test_aligned_ablation.AlignedAblationTests.test_actual_elapsed_integration_and_left_endpoint_heading) ... ok
test_complete_window_and_full_history_are_accepted (test_aligned_ablation.AlignedAblationTests.test_complete_window_and_full_history_are_accepted) ... ok
test_final_out_of_range_candidate_is_not_silently_dropped (test_aligned_ablation.AlignedAblationTests.test_final_out_of_range_candidate_is_not_silently_dropped) ... ok
test_learned_raw_phone_gyro_does_not_use_outage_reference_labels (test_aligned_ablation.AlignedAblationTests.test_learned_raw_phone_gyro_does_not_use_outage_reference_labels) ... ok
test_missing_endpoint_row_is_not_integrated (test_aligned_ablation.AlignedAblationTests.test_missing_endpoint_row_is_not_integrated) ... ok
test_non_10hz_reference_cadence_is_rejected_and_logged (test_aligned_ablation.AlignedAblationTests.test_non_10hz_reference_cadence_is_rejected_and_logged) ... ok
test_overlapping_reference_rows_are_rejected_as_ambiguous (test_aligned_ablation.AlignedAblationTests.test_overlapping_reference_rows_are_rejected_as_ambiguous) ... ok
test_phone_gps_column_is_not_a_causal_feature (test_aligned_ablation.AlignedAblationTests.test_phone_gps_column_is_not_a_causal_feature) ... ok
test_split_inside_outage_or_calibration_rejects_same_candidate (test_aligned_ablation.AlignedAblationTests.test_split_inside_outage_or_calibration_rejects_same_candidate) ... ok
test_window_exclusion_does_not_use_reference_labels (test_aligned_ablation.AlignedAblationTests.test_window_exclusion_does_not_use_reference_labels) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.101s

OK
```

### Attempt 2: successful numbered run

Command:

```sh
env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MPLCONFIGDIR=/tmp/sih-matplotlib \
  .venv/bin/python research/tools/audit_dhruva_aligned.py \
  --data-root /tmp/iovnbd \
  --output research/evidence/dhruva-aligned-2026-09-10-2
```

Output (exit 0):

```text
S1: candidates=52 valid=48 exclusions={'endpoint_out_of_range': 1, 'non_10hz_reference_cadence': 3}
S2: candidates=154 valid=144 exclusions={'endpoint_out_of_range': 1, 'missing_or_gap': 3, 'non_10hz_reference_cadence': 6}
S3a: candidates=39 valid=37 exclusions={'endpoint_out_of_range': 1, 'missing_or_gap': 1}
S4: candidates=155 valid=141 exclusions={'endpoint_out_of_range': 1, 'insufficient_feature_history': 1, 'missing_or_gap': 9, 'non_10hz_reference_cadence': 3}
```

Original successful-fit tool provenance retained from the execution context
(not reconstructed from generated artifacts):

```text
launch: session_id=78308 chunk_id=2c0971 wall_time_seconds=30.002220166 original_token_count=0 output=""
continuation request: session_id=78308
completion: chunk_id=f39423 wall_time_seconds=10.821833369 exit_code=0 original_token_count=118
```

Raw completion output retained by that tool session:

```text
S1: candidates=52 valid=48 exclusions={'endpoint_out_of_range': 1, 'non_10hz_reference_cadence': 3}
S2: candidates=154 valid=144 exclusions={'endpoint_out_of_range': 1, 'missing_or_gap': 3, 'non_10hz_reference_cadence': 6}
S3a: candidates=39 valid=37 exclusions={'endpoint_out_of_range': 1, 'missing_or_gap': 1}
S4: candidates=155 valid=141 exclusions={'endpoint_out_of_range': 1, 'insufficient_feature_history': 1, 'missing_or_gap': 9, 'non_10hz_reference_cadence': 3}
```

Fit facts: 20,495 manifested S1 training samples; fit elapsed
12.765429898863658 s. Journey-prefix gyro-fit row counts were S1 1,198,
S2 1,125, S3a 1,132, and S4 1,182. Clock absolute correlations were S1
0.9736273, S2 0.9840840, S3a 0.9712053, and S4 0.9686993; none was marked
low confidence.

Candidate totals and distance eligibility are common to every method:

| Sequence | Candidates | Valid | Drift eligible | Below 50 m | Exclusions |
|---|---:|---:|---:|---:|---|
| S1 | 52 | 48 | 46 | 2 | endpoint 1; cadence 3 |
| S2 | 154 | 144 | 139 | 5 | endpoint 1; gap 3; cadence 6 |
| S3a | 39 | 37 | 36 | 1 | endpoint 1; gap 1 |
| S4 | 155 | 141 | 134 | 7 | endpoint 1; history 1; gap 9; cadence 3 |

## Complete 13-method summaries

Values are direct from `results.json`. “Valid/eligible” is the common window
coverage; the share column is the fraction of distance-eligible windows with
drift strictly below 10%.

### S1

| Method | Valid/eligible | Median abs m | P95 abs m | Median drift % | P95 drift % | <10% share |
|---|---:|---:|---:|---:|---:|---:|
| `speed=learned_raw\|heading=phone_gyro\|gyro=frozen_s1` | 48/46 | 67.669 | 188.029 | 16.110 | 45.466 | 0.261 |
| `speed=learned_raw\|heading=phone_gyro\|gyro=journey_prefix` | 48/46 | 58.504 | 162.147 | 16.124 | 44.098 | 0.326 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=frozen_s1` | 48/46 | 43.131 | 118.156 | 11.695 | 35.740 | 0.457 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=journey_prefix` | 48/46 | 43.131 | 118.156 | 11.695 | 35.740 | 0.457 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=frozen_s1` | 48/46 | 69.495 | 302.768 | 17.971 | 59.431 | 0.196 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=journey_prefix` | 48/46 | 66.888 | 298.494 | 17.641 | 59.186 | 0.239 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=frozen_s1` | 48/46 | 51.993 | 277.914 | 14.803 | 57.527 | 0.413 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=journey_prefix` | 48/46 | 51.993 | 277.914 | 14.803 | 57.527 | 0.413 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=frozen_s1` | 48/46 | 23.678 | 111.987 | 6.739 | 22.608 | 0.630 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=journey_prefix` | 48/46 | 22.420 | 106.598 | 5.844 | 20.137 | 0.783 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=frozen_s1` | 48/46 | 1.897 | 4.341 | 0.426 | 1.072 | 1.000 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=journey_prefix` | 48/46 | 1.897 | 4.341 | 0.426 | 1.072 | 1.000 |
| `constant_reference_initialized` | 48/46 | 297.300 | 698.609 | 79.928 | 157.624 | 0.000 |

### S2

| Method | Valid/eligible | Median abs m | P95 abs m | Median drift % | P95 drift % | <10% share |
|---|---:|---:|---:|---:|---:|---:|
| `speed=learned_raw\|heading=phone_gyro\|gyro=frozen_s1` | 144/139 | 100.860 | 389.187 | 21.855 | 62.912 | 0.158 |
| `speed=learned_raw\|heading=phone_gyro\|gyro=journey_prefix` | 144/139 | 91.817 | 399.484 | 20.187 | 60.327 | 0.173 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=frozen_s1` | 144/139 | 71.596 | 360.894 | 17.947 | 45.172 | 0.223 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=journey_prefix` | 144/139 | 71.596 | 360.894 | 17.947 | 45.172 | 0.223 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=frozen_s1` | 144/139 | 110.520 | 379.358 | 23.473 | 83.179 | 0.129 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=journey_prefix` | 144/139 | 99.691 | 354.183 | 22.491 | 81.873 | 0.158 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=frozen_s1` | 144/139 | 79.779 | 293.127 | 19.618 | 60.215 | 0.245 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=journey_prefix` | 144/139 | 79.779 | 293.127 | 19.618 | 60.215 | 0.245 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=frozen_s1` | 144/139 | 34.971 | 163.415 | 7.923 | 23.862 | 0.612 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=journey_prefix` | 144/139 | 26.909 | 204.363 | 6.497 | 25.796 | 0.719 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=frozen_s1` | 144/139 | 1.688 | 4.347 | 0.353 | 1.305 | 1.000 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=journey_prefix` | 144/139 | 1.688 | 4.347 | 0.353 | 1.305 | 1.000 |
| `constant_reference_initialized` | 144/139 | 375.989 | 800.628 | 83.964 | 189.769 | 0.029 |

### S3a

| Method | Valid/eligible | Median abs m | P95 abs m | Median drift % | P95 drift % | <10% share |
|---|---:|---:|---:|---:|---:|---:|
| `speed=learned_raw\|heading=phone_gyro\|gyro=frozen_s1` | 37/36 | 255.379 | 836.214 | 45.412 | 73.985 | 0.028 |
| `speed=learned_raw\|heading=phone_gyro\|gyro=journey_prefix` | 37/36 | 258.125 | 835.424 | 44.878 | 73.936 | 0.028 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=frozen_s1` | 37/36 | 224.970 | 835.711 | 41.665 | 71.794 | 0.111 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=journey_prefix` | 37/36 | 224.970 | 835.711 | 41.665 | 71.794 | 0.111 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=frozen_s1` | 37/36 | 102.651 | 381.274 | 21.822 | 59.959 | 0.167 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=journey_prefix` | 37/36 | 107.827 | 361.806 | 22.766 | 60.124 | 0.250 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=frozen_s1` | 37/36 | 92.080 | 312.527 | 17.301 | 52.221 | 0.306 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=journey_prefix` | 37/36 | 92.080 | 312.527 | 17.301 | 52.221 | 0.306 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=frozen_s1` | 37/36 | 40.401 | 130.759 | 5.312 | 18.230 | 0.778 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=journey_prefix` | 37/36 | 25.762 | 105.496 | 4.736 | 23.974 | 0.806 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=frozen_s1` | 37/36 | 1.757 | 3.282 | 0.276 | 0.528 | 1.000 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=journey_prefix` | 37/36 | 1.757 | 3.282 | 0.276 | 0.528 | 1.000 |
| `constant_reference_initialized` | 37/36 | 280.631 | 578.259 | 50.886 | 128.132 | 0.056 |

### S4

| Method | Valid/eligible | Median abs m | P95 abs m | Median drift % | P95 drift % | <10% share |
|---|---:|---:|---:|---:|---:|---:|
| `speed=learned_raw\|heading=phone_gyro\|gyro=frozen_s1` | 141/134 | 93.645 | 738.462 | 20.347 | 54.215 | 0.112 |
| `speed=learned_raw\|heading=phone_gyro\|gyro=journey_prefix` | 141/134 | 108.836 | 738.778 | 23.729 | 56.910 | 0.104 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=frozen_s1` | 141/134 | 75.013 | 721.991 | 16.587 | 52.065 | 0.269 |
| `speed=learned_raw\|heading=reference_oracle\|gyro=journey_prefix` | 141/134 | 75.013 | 721.991 | 16.587 | 52.065 | 0.269 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=frozen_s1` | 141/134 | 113.447 | 433.214 | 20.331 | 76.730 | 0.149 |
| `speed=learned_initial_offset\|heading=phone_gyro\|gyro=journey_prefix` | 141/134 | 132.655 | 445.197 | 25.180 | 88.553 | 0.142 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=frozen_s1` | 141/134 | 88.979 | 363.628 | 17.061 | 61.522 | 0.291 |
| `speed=learned_initial_offset\|heading=reference_oracle\|gyro=journey_prefix` | 141/134 | 88.979 | 363.628 | 17.061 | 61.522 | 0.291 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=frozen_s1` | 141/134 | 35.085 | 167.760 | 6.623 | 21.305 | 0.634 |
| `speed=reference_oracle\|heading=phone_gyro\|gyro=journey_prefix` | 141/134 | 50.074 | 216.873 | 8.947 | 31.872 | 0.522 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=frozen_s1` | 141/134 | 2.102 | 6.894 | 0.361 | 1.355 | 1.000 |
| `speed=reference_oracle\|heading=reference_oracle\|gyro=journey_prefix` | 141/134 | 2.102 | 6.894 | 0.361 | 1.355 | 1.000 |
| `constant_reference_initialized` | 141/134 | 391.850 | 811.946 | 79.021 | 235.397 | 0.015 |

## Artifact verification

Commands:

```sh
wc -l research/evidence/dhruva-aligned-2026-09-10-2/windows.csv
sha256sum research/evidence/dhruva-aligned-2026-09-10-2/manifest.json \
  research/tools/audit_dhruva_aligned.py prototypes/dhruva/benchmark.py \
  prototypes/dhruva/time_alignment.py
jq -r '.pre_fit_manifest_sha256' \
  research/evidence/dhruva-aligned-2026-09-10-2/results.json
rg -n 'NaN|Infinity' research/evidence/dhruva-aligned-2026-09-10-2 || true
```

Output:

```text
5201 research/evidence/dhruva-aligned-2026-09-10-2/windows.csv
c8a82a54a587506a7546a1d635be4a6e1f397b6304f87517c8681803c5134c37  research/evidence/dhruva-aligned-2026-09-10-2/manifest.json
a5db4055e09a17cf669e9ad0544fa50c62d790186862ca7f97923bc4a3548440  research/tools/audit_dhruva_aligned.py
3aedc19ad7fc39e3ae10976f1504f428c129f0fcf8d9aa359594f7711833d2d9  prototypes/dhruva/benchmark.py
84d179c4f8d8ca75077acf42b3351f9c657937624beab62e3bd013620ceb273e  prototypes/dhruva/time_alignment.py
c8a82a54a587506a7546a1d635be4a6e1f397b6304f87517c8681803c5134c37
```

The 5,201 CSV lines are one header plus 400 candidates × 13 methods. Manifest
and recorded pre-fit hashes match. Current runner, legacy benchmark, and reviewed
alignment-module hashes match those stored in the manifest. All valid windows
have an actual duration of exactly 60.0 s. The NaN/Infinity scan returned no
matches.

## Concerns and interpretation limits

1. Attempt 1 exposed and documented the direct-entry import bug; it produced no
   artifact directory. Attempt 2 is therefore the only fitted/evaluated run.
2. The matplotlib cache warning in tests is environmental noise from importing
   the unchanged legacy benchmark. The prescribed real-run environment supplied
   `MPLCONFIGDIR`, so it did not recur there.
3. The refit uses 20,495 corrected timestamp/bracket-constrained S1 samples and
   shifted evaluation windows. It must not be described as a controlled
   old-18.342%-to-new causal improvement.
4. Learned-raw/phone-gyro median eligible drift remains 16.110%/16.124% on S1,
   21.855%/20.187% on S2, 45.412%/44.878% on S3a, and 20.347%/23.729% on S4
   for frozen-S1/journey-prefix calibration respectively. These exploratory
   values do not support a general accuracy or threshold claim.
5. Reference-speed and reference-heading branches are component/oracle sanity
   checks. The near-zero reference-speed/reference-heading integration residuals
   validate coordinate/velocity consistency but are not estimator performance.
6. Independent review is required before any accuracy number is reused.

## Round 1 table-format evidence fix

Only the 48 factorial-method labels in the four complete-summary tables were
changed: their two internal pipe characters are escaped for Markdown. Table
delimiters, baseline rows, numerical values, and all preceding evidence remain
unchanged.

Validation command:

```sh
.venv/bin/python - <<'PY'
from pathlib import Path
import re

report_path = Path("research/evidence/dhruva-aligned-ablation-implementation.md")
old_path = Path("research/evidence/dhruva-aligned-ablation-report-before-format-fix.md")
text = report_path.read_text()
marker = "## Round 1 table-format evidence fix\n"
prefix = text[: text.index(marker)]
tables = {}
sequence = None
for line in prefix.splitlines():
    if line in {"### S1", "### S2", "### S3a", "### S4"}:
        sequence = line[4:]
        tables[sequence] = []
    elif sequence is not None and line.startswith("|"):
        cells = re.split(r"(?<!\\)\|", line)[1:-1]
        tables[sequence].append(cells)
    elif sequence is not None and tables[sequence] and not line:
        sequence = None

factorial_total = 0
for sequence in ("S1", "S2", "S3a", "S4"):
    rows = tables[sequence]
    assert len(rows) == 15
    assert all(len(row) == 7 for row in rows)
    factorial = sum(row[0].strip().startswith("`speed=") for row in rows)
    baseline = sum("constant_reference_initialized" in row[0] for row in rows)
    assert factorial == 12 and baseline == 1
    factorial_total += factorial
    print(f"{sequence}: rows={len(rows)} cells_per_row=7 factorial={factorial} baseline={baseline}")
assert factorial_total == 48
print(f"factorial_rows={factorial_total}")
assert prefix.replace(r"\|", "|") == old_path.read_text()
print("unescaped_prefix_matches_retained_original=true")
PY
```

Exact output (exit 0):

```text
S1: rows=15 cells_per_row=7 factorial=12 baseline=1
S2: rows=15 cells_per_row=7 factorial=12 baseline=1
S3a: rows=15 cells_per_row=7 factorial=12 baseline=1
S4: rows=15 cells_per_row=7 factorial=12 baseline=1
factorial_rows=48
unescaped_prefix_matches_retained_original=true
```
