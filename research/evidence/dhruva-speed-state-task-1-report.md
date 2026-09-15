# Dhruva Speed-State Task 1 Report

## Scope and status

Task 1 is complete. This change adds only the pure speed-state numerical module,
its focused synthetic tests, and this evidence report. It does not load real
data, fit a model, implement Task 2, modify the existing displacement helper,
write externally, download dependencies, or create a commit.

Changed files:

- `research/tools/dhruva_speed_state.py` (new)
- `prototypes/dhruva/tests/test_speed_state.py` (new)
- `research/evidence/dhruva-speed-state-task-1-report.md` (new)

## Arithmetic implemented

- Acceleration targets are backward-interval estimates: row `i` stores the
  speed difference over the interval ending at `i`; row zero is `NaN`.
- Each target records the required two-row raw support. NZ2 is true only when
  both exact supporting satellite-field values are nonzero; nonzero values are
  not otherwise decoded as quality categories.
- Integration treats `acceleration_at_rows[1:]` as interval values. The first
  acceleration element is deliberately unused.
- Integrated state remains signed. Nonnegativity is applied only to the output,
  so a clipped output is never fed back into the subsequent state.
- Absolute-speed initial offset preserves the specified legacy ordering:
  pre-clip raw predictions, anchor the pre-clipped first value to the finite
  nonnegative initial speed, then clip the resulting candidate for output.
- Displacement delegates to
  `research.tools.audit_dhruva_aligned.integrate_displacement`; its code was
  neither copied nor modified. State/reference arrays include both endpoints,
  while displacement and time-weighted metrics use only left samples.
- Distance uses left GPS-speed samples. Drift ratio is returned only at a
  distance of at least 50 m. Acceleration error excludes row zero and is `None`
  when acceleration is absent.

## Validation and focused coverage

The public functions reject invalid dimensionality, nonfinite vector elements,
mismatched lengths, non-increasing timestamps, invalid raw-row dtype/order/range,
and invalid initial speed with `ValueError`. Metrics additionally require at
least two timestamps, a finite two-value truth displacement, and a matching
optional acceleration vector.

The 12 focused tests cover the exact brief examples, including nonuniform
backward targets, NZ2 support, arbitrary nonzero satellite values, onset and
braking, negative signed state without clipped-state feedback, row-zero
acceleration perturbation, legacy absolute-speed ordering, 60-second constant
acceleration metrics, exact constant-speed results, left-sample weighting,
the exact metric-key set, and the required invalid inputs.

## TDD evidence

Exact command used for both RED and GREEN:

```sh
env MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_speed_state.py' -v
```

### RED — execution chunk `51021b`, exit code 1

```text
test_speed_state (unittest.loader._FailedTest.test_speed_state) ... ERROR

======================================================================
ERROR: test_speed_state (unittest.loader._FailedTest.test_speed_state)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_speed_state
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/user_end4/MySpace/SIH/prototypes/dhruva/tests/test_speed_state.py", line 5, in <module>
    from research.tools.dhruva_speed_state import (
    ...<4 lines>...
    )
ModuleNotFoundError: No module named 'research.tools.dhruva_speed_state'


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

### Initial GREEN — execution chunk `300903`, exit code 0

```text
test_absolute_speed_preserves_legacy_offset_ordering (test_speed_state.SpeedStateTests.test_absolute_speed_preserves_legacy_offset_ordering) ... ok
test_backward_targets_only_zero_satellites_fail_nz2 (test_speed_state.SpeedStateTests.test_backward_targets_only_zero_satellites_fail_nz2) ... ok
test_backward_targets_use_preceding_interval_and_nz2_support (test_speed_state.SpeedStateTests.test_backward_targets_use_preceding_interval_and_nz2_support) ... ok
test_integrate_speed_clips_output_without_state_feedback (test_speed_state.SpeedStateTests.test_integrate_speed_clips_output_without_state_feedback) ... ok
test_integrate_speed_ignores_first_acceleration_sample (test_speed_state.SpeedStateTests.test_integrate_speed_ignores_first_acceleration_sample) ... ok
test_integrate_speed_reproduces_onset_and_braking_sequence (test_speed_state.SpeedStateTests.test_integrate_speed_reproduces_onset_and_braking_sequence) ... ok
test_invalid_rows_and_initial_speed_are_rejected (test_speed_state.SpeedStateTests.test_invalid_rows_and_initial_speed_are_rejected) ... ok
test_invalid_shapes_nonfinite_values_and_duplicate_times_are_rejected (test_speed_state.SpeedStateTests.test_invalid_shapes_nonfinite_values_and_duplicate_times_are_rejected) ... ok
test_metrics_constant_acceleration_contract (test_speed_state.SpeedStateTests.test_metrics_constant_acceleration_contract) ... ok
test_metrics_reject_short_mismatched_and_invalid_optional_inputs (test_speed_state.SpeedStateTests.test_metrics_reject_short_mismatched_and_invalid_optional_inputs) ... ok
test_metrics_use_left_samples_and_report_signed_state (test_speed_state.SpeedStateTests.test_metrics_use_left_samples_and_report_signed_state) ... ok
test_metrics_zero_acceleration_has_exact_constant_speed_results (test_speed_state.SpeedStateTests.test_metrics_zero_acceleration_has_exact_constant_speed_results) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.005s

OK
```

After the initial GREEN run, self-review added an assertion for the exact
metric-key set. No production arithmetic changed.

### Final GREEN — execution chunk `534979`, exit code 0

```text
test_absolute_speed_preserves_legacy_offset_ordering (test_speed_state.SpeedStateTests.test_absolute_speed_preserves_legacy_offset_ordering) ... ok
test_backward_targets_only_zero_satellites_fail_nz2 (test_speed_state.SpeedStateTests.test_backward_targets_only_zero_satellites_fail_nz2) ... ok
test_backward_targets_use_preceding_interval_and_nz2_support (test_speed_state.SpeedStateTests.test_backward_targets_use_preceding_interval_and_nz2_support) ... ok
test_integrate_speed_clips_output_without_state_feedback (test_speed_state.SpeedStateTests.test_integrate_speed_clips_output_without_state_feedback) ... ok
test_integrate_speed_ignores_first_acceleration_sample (test_speed_state.SpeedStateTests.test_integrate_speed_ignores_first_acceleration_sample) ... ok
test_integrate_speed_reproduces_onset_and_braking_sequence (test_speed_state.SpeedStateTests.test_integrate_speed_reproduces_onset_and_braking_sequence) ... ok
test_invalid_rows_and_initial_speed_are_rejected (test_speed_state.SpeedStateTests.test_invalid_rows_and_initial_speed_are_rejected) ... ok
test_invalid_shapes_nonfinite_values_and_duplicate_times_are_rejected (test_speed_state.SpeedStateTests.test_invalid_shapes_nonfinite_values_and_duplicate_times_are_rejected) ... ok
test_metrics_constant_acceleration_contract (test_speed_state.SpeedStateTests.test_metrics_constant_acceleration_contract) ... ok
test_metrics_reject_short_mismatched_and_invalid_optional_inputs (test_speed_state.SpeedStateTests.test_metrics_reject_short_mismatched_and_invalid_optional_inputs) ... ok
test_metrics_use_left_samples_and_report_signed_state (test_speed_state.SpeedStateTests.test_metrics_use_left_samples_and_report_signed_state) ... ok
test_metrics_zero_acceleration_has_exact_constant_speed_results (test_speed_state.SpeedStateTests.test_metrics_zero_acceleration_has_exact_constant_speed_results) ... ok

----------------------------------------------------------------------
Ran 12 tests in 0.005s

OK
```

## Code hashes

SHA-256 values after final GREEN:

```text
32d88d33eca001adb8231dde559f4b2b67ca46fe5e709ce7614ecd47429d5cbd  research/tools/dhruva_speed_state.py
b474fed7e633d88af5b4920182d255eeaf868cc3d03f794fdb86e64d8096f1af  prototypes/dhruva/tests/test_speed_state.py
```

## Self-review and limitations

Self-review traced every specified formula and return key against the Task 1
brief and inspected the focused validation paths. The implementation is a pure
numerical contract for a backward-interval experiment. The tests use synthetic
arrays only. They do not establish physical validity, real-data performance,
forecasting ability, deployability, or novelty. Independent review and any
physical-data experiment remain outside this task.
