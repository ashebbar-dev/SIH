# Dhruva Matched Speed-State Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure whether a matched interval-acceleration state model improves Dhruva's speed bottleneck, with a fixed known-defect training sensitivity and unchanged evaluation windows.

**Architecture:** A small pure numerical module fixes target support, speed propagation and metrics. A separate runner validates/reuses the frozen alignment manifest, fits four fixed models once, evaluates eight methods on every existing candidate and retains full predictions plus historical controls.

**Tech Stack:** Existing `.venv`, NumPy, scikit-learn, unittest and existing timestamp/ablation helpers; no installation or GPU.

**Spec:** `research/DHRUVA_SPEED_STATE_DESIGN_2026-09-11.md`.

## Global Constraints

- Preserve production code, previous runners, raw data, prior evidence and PDFs.
- No Git initialization/commits, downloads, installs, firmware or external writes.
- Use the existing `.venv` and fresh exclusive evidence paths.
- Use all400 existing candidate IDs and unchanged exclusions; evaluate all370 valid windows with all eight methods.
- Keep the existing355-window distance>=50m drift subset; retain absolute metrics for all370 valid windows.
- Fit only the original S1 training prefix; no S2/S3a/S4 fitting or new journey-prefix calibration.
- Keep unchanged247 features and five HGB constructor overrides; do not tune after seeing results.
- Compare both training targets on identical ALL and NZ2 row sets; NZ2 is not a clean-label certificate.
- Reference initial speed and outage-time heading are privileged diagnostics, not phone-only navigation.
- Keep all failed controls, warnings, model outputs and method outcomes; never exclude by prediction error.

---

### Task 1: Pure interval targets, speed state and metrics

**Files:**
- Create `research/tools/dhruva_speed_state.py`.
- Create `prototypes/dhruva/tests/test_speed_state.py`.
- Create `research/evidence/dhruva-speed-state-task-1-report.md`.

**Interfaces:**

```python
def backward_targets(times: np.ndarray, speed_mps: np.ndarray,
                     raw_rows: np.ndarray, satellite_field: np.ndarray
                     ) -> tuple[np.ndarray, np.ndarray, np.ndarray]: ...
# Returns n acceleration targets, n×2 raw supports, n NZ2 flags.
def integrate_speed(times: np.ndarray, acceleration_at_rows: np.ndarray,
                    initial_speed: float) -> tuple[np.ndarray, np.ndarray]: ...
# Both inputs have n=L+1 elements. Returns signed states and output-clipped states.
def absolute_speed(raw_prediction: np.ndarray, initial_speed: float | None = None
                   ) -> tuple[np.ndarray, np.ndarray]: ...
# Returns pre-final-clip candidate and nonnegative output, preserving old ordering.
def speed_metrics(*, times: np.ndarray, signed_speed: np.ndarray,
                  output_speed: np.ndarray, gps_speed: np.ndarray,
                  indicated_speed: np.ndarray, headings: np.ndarray,
                  truth_displacement: tuple[float, float],
                  acceleration: np.ndarray | None = None) -> dict: ...
```

All vectors must be one-dimensional with matching lengths and finite elements,
except backward_targets returns NaN at its first target. Times strictly
increase. Metrics require at least two timestamps. Raw rows are nonnegative
integers, consecutive, and within satellite_field bounds. Satellites must be
finite; arbitrary nonzero values are not decoded as quality flags. Initial
speed must be finite and nonnegative. Raise ValueError on invalid inputs;
do not silently shorten, mask or coerce them.

- [ ] **Step 1: Write focused tests and run RED.**

Include these numerical assertions, plus invalid-shape/nonfinite/duplicate-time,
nonconsecutive/out-of-bounds raw-row and negative-initial-speed rejection cases:

```python
t = np.array([0., .1, .4, .6])
v = np.array([2., 2., 8., 5.])
sat = np.ones(20); sat[11] = 0
a, supports, keep = backward_targets(t, v, np.arange(10,14), sat)
assert np.isnan(a[0])
np.testing.assert_allclose(a[1:], [0.,20.,-15.], atol=1e-12)
np.testing.assert_array_equal(supports, [[-1,10],[10,11],[11,12],[12,13]])
np.testing.assert_array_equal(keep, [False,False,False,True])

v = np.array([0.,0.,1.,1.,0.,2.]); t = np.arange(6)*.1
a = np.r_[999., np.diff(v)/np.diff(t)]
signed, out = integrate_speed(t,a,v[0])
np.testing.assert_allclose(signed,v,atol=1e-12)
np.testing.assert_allclose(out,v,atol=1e-12)

signed, out = integrate_speed(np.array([0.,1.,2.]),np.array([999.,-2.,1.]),1.)
np.testing.assert_array_equal(signed,[1.,-1.,0.])
np.testing.assert_array_equal(out,[1.,0.,0.])  # No clipped-state feedback.
_, out = absolute_speed(np.array([-5.,2.,4.]),10.)
np.testing.assert_array_equal(out,[10.,12.,14.])

t = np.arange(601)*.1; gps = np.full(601,10.); a = np.full(601,.1)
signed,out = integrate_speed(t,a,10.)
r = speed_metrics(times=t,signed_speed=signed,output_speed=out,gps_speed=gps,
    indicated_speed=gps,headings=np.zeros(601),truth_displacement=(0.,600.),
    acceleration=a)
assert abs(r['endpoint_error_m']-179.7)<1e-8
assert abs(r['terminal_speed_error_mps']-6.)<1e-10
assert abs(r['mean_acceleration_error_mps2']-.1)<1e-12
```

Also test zero acceleration on times[0,.1,.3], v0=10, zero headings and truth
(0,3): exact constant speeds, MAE0, endpoint error0, distance3 and null drift.
Perturb a[0] without changing any integrated output. Test a nonconstant speed
onset/braking sequence (above), not only constant acceleration.

```sh
env MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_speed_state.py' -v
```

- [ ] **Step 2: Implement the exact arithmetic.**

After the declared checks, use these relationships:

```python
targets = np.r_[np.nan, np.diff(speed_mps)/np.diff(times)]
supports = np.column_stack((np.r_[-1,raw_rows[:-1]],raw_rows))
keep = np.r_[False, (satellite_field[raw_rows[:-1]] != 0) &
                    (satellite_field[raw_rows[1:]] != 0)]

signed = np.r_[initial_speed, initial_speed +
               np.cumsum(acceleration_at_rows[1:] * np.diff(times))]
output = np.maximum(0.,signed)

p = np.maximum(0.,raw_prediction)
candidate = raw_prediction.copy() if initial_speed is None else p+initial_speed-p[0]
output = np.maximum(0.,candidate)
```

For metrics reuse existing `audit_dhruva_aligned.integrate_displacement`;
do not copy its integration. All stored states/reference arrays include both
endpoints; position and time-weighted speed metrics use left samples[:-1].
Return exact keys `predicted_east_m`, `predicted_north_m`, `truth_east_m`,
`truth_north_m`, `distance_m`, `distance_eligible_for_drift_ratio`,
`endpoint_error_m`, `drift_ratio`, `speed_mae_gps_mps`,
`speed_mae_indicated_mps`, `mean_speed_error_mps`,
`mean_unclipped_speed_error_mps`, `clipped_fraction`,
`terminal_speed_error_mps`, `mean_acceleration_error_mps2`.

```python
dt = np.diff(times); duration = float(dt.sum())
gps_error = output_speed[:-1]-gps_speed[:-1]
speed_mae_gps_mps = float(np.sum(abs(gps_error)*dt)/duration)
mean_speed_error_mps = float(np.sum(gps_error*dt)/duration)
mean_unclipped_speed_error_mps = float(np.sum((signed_speed[:-1]-gps_speed[:-1])*dt)/duration)
clipped_fraction = float(np.mean(signed_speed[:-1] < 0))
terminal_speed_error_mps = float(output_speed[-1]-gps_speed[-1])
mean_acceleration_error_mps2 = None if acceleration is None else float(
    np.sum((acceleration[1:]-np.diff(gps_speed)/dt)*dt)/duration)
```

Indicated MAE uses the identical weighted formula against indicated_speed.
Distance is sum(gps_speed[:-1]*dt). Endpoint error is hypot of estimated-minus-
truth east/north. Drift is error/distance only if distance>=50m, else None.

- [ ] **Step 3: Run GREEN, self-review and report.**

Run only the focused command above, retain exact RED/GREEN output, changed
files, arithmetic decisions, and limitations in the Task1 report. Do not load
real data, fit models, create Task2 code or modify old helpers. Root performs
independent review before the physical-data experiment.

### Task 2: Frozen matched four-model/eight-method experiment

**Files:**
- Create `research/tools/audit_dhruva_speed_state.py`.
- Create `prototypes/dhruva/tests/test_speed_state_experiment.py`.
- Create `research/evidence/dhruva-speed-state-task-2-report.md`.
- Generate fresh `research/evidence/dhruva-speed-state-2026-09-11/`.

**Interfaces:** consumes Task1's four exact public APIs above. Add:

```python
def validate_parent(path: Path) -> dict: ...
def profile_states(method: str, times: np.ndarray, reference_speed: np.ndarray,
                   absolute_prediction: np.ndarray | None,
                   acceleration_prediction: np.ndarray | None
                   ) -> tuple[np.ndarray,np.ndarray]: ...
def compare_historical(rows: list[dict], prior_rows: list[dict]) -> dict: ...
def advance_decision(summaries: dict, historical_passed: bool) -> dict: ...
def run(parent_manifest: Path, output: Path) -> dict: ...
```

The eight method IDs are `CONST_V0`, `ABS_ALL`, `ABS_V0_ALL`, `DELTA_V0_ALL`,
`ABS_NZ2`, `ABS_V0_NZ2`, `DELTA_V0_NZ2`, `REF_SPEED`. Fit only four models;
offset/raw branches share the same absolute predictions. All use reference
heading. `profile_states` must consult only reference_speed[0] for non-oracle
methods requiring v0; ABS methods without V0 do not consult reference values.
Call Task1 functions for learned states. Constant/reference branches return
equal signed/output states, with no new heading or gyro fit.

- [ ] **Step 1: Write boundary tests and run RED.**

Tests use tiny arrays/temp files, not real fitting. Verify:

```python
t=np.array([0.,.1,.2]); ref=np.array([10.,11.,12.])
abs_pred=np.array([-5.,2.,4.]); acc=np.array([999.,1.,-1.])
for method in ('CONST_V0','ABS_ALL','ABS_V0_ALL','DELTA_V0_ALL',
               'ABS_NZ2','ABS_V0_NZ2','DELTA_V0_NZ2'):
    before=profile_states(method,t,ref,abs_pred,acc)
    changed=ref.copy(); changed[1:]=[10000.,20000.]
    after=profile_states(method,t,changed,abs_pred,acc)
    for left,right in zip(before,after): np.testing.assert_array_equal(left,right)
```

Also test raw ABS ignores changed v0; REF_SPEED follows changed labels;
unknown method raises ValueError; an existing output directory/sentinel is
preserved before validation/fit; wrong parent-manifest hash fails before data
loading; historical comparison catches numeric mismatch, missing and duplicate
records and preserves null drift; advance_decision passes a constructed table
with DELTA median7, ABS_V0/CONST10 on two journeys and10 on the third, p95<=10,
improved corroborating metrics, identical arms and historical_passed=True.
It fails if one required tail becomes12 against10, historical_passed=False,
an arm loses a required improvement, or any required metric is missing. Test
zero baselines without division by zero. Test feature mutation after row250
leaves unchanged causal_features output through row250 (phone shape300×16,
finite deterministic values, future-only mutation). No test assertion may be
replaced by merely checking that a mocked function was invoked.

```sh
env MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_speed_state_experiment.py' -v
```

- [ ] **Step 2: Validate frozen inputs and write the pre-fit manifest.**

Default parent path `research/evidence/dhruva-aligned-2026-09-10-2/manifest.json`;
require SHA256 `c8a82a54a587506a7546a1d635be4a6e1f397b6304f87517c8681803c5134c37`.
Check recorded raw phone/reference paths/hashes for S1,S2,S3a,S4 and the original
benchmark/alignment/ablation-runner hashes. Use the existing load_timestamped_pair
and align_pair, stored residual offsets and phone correction3600. Compare
`_segment_provenance` to parent segments; do not reestimate clocks or windows.
All parent training records must match regenerated local/raw/phone bracket
indices and strict cutoff1567935738.8 for feature brackets AND target support.
Derive data_root from the recorded S1 phone path's parents[4], then assert
every path returned by the existing loader equals its recorded resolved path.
Record availability as pair.phone_time_s[segment.phone_right_rows]+offset.

Read raw reference satellite/indicated columns(0,15) with np.loadtxt; gather by
segment.reference_rows. For every parent training record call/use Task1 targets
and NZ2 support, verify actual dt within the original0.1±0.001s tolerance,
retain common ALL20495/NZ220415 lists in original order, and list the80 removed
records before fitting. No fitted quantity can affect those lists.

Preserve parent400 windows exactly. Require370 included with counts
S1:48,S2:144,S3a:37,S4:141. Write exclusive `manifest.json` before fitting,
including parent/hash, all source/data/prior-CSV hashes, settings/methods,
training/target support lists, windows, offsets, full library versions and
HGB get_params(), and explicit privileged/offline limitations.

- [ ] **Step 3: Fit once and retain all predictions and outcomes.**

```python
features = {name: [legacy.causal_features(seg.phone) for seg in segments[name]]
            for name in ('S1','S2','S3a','S4')}
train_x = np.vstack([features['S1'][r['segment_index']][r['local_index']]
                     for r in selected_records])
absolute_y = np.asarray([segments['S1'][r['segment_index']].reference[r['local_index'],2]/3.6
                         for r in selected_records])
acceleration_y = np.asarray([targets_by_segment[r['segment_index']][r['local_index']]
                             for r in selected_records])
# train_y is absolute_y or acceleration_y for the declared target, with the
# same selected_records in each support arm.
model = HistGradientBoostingRegressor(max_iter=250,max_leaf_nodes=31,
    learning_rate=.08,l2_regularization=1.,random_state=42)
model.fit(train_x,train_y)
raw_predictions = [model.predict(block) for block in features[name]]
```

Perform this for exactly (absolute,acceleration)×(ALL,NZ2). Retain full raw
predictions, fitted parameters/n_iter_, fit times, input/target array hashes
and warnings. Never clip acceleration predictions. For each included window
slice predictions/reference/times start:end+1, build its eight states, and call
Task1 speed_metrics with reference headings and existing local-coordinate
displacement. Save per-segment raw predictions, availability timestamps,
references, and each window/method's signed/output601-element states in
`predictions.npz` with per-array shape/dtype/hash inventory.

Write `windows.csv` with3200 rows, retaining all30×8 excluded records with
explicit original reasons/null metrics. Include raw/local IDs and reference
quality flags descriptively; no new exclusion. Write `results.json` with
all summaries, actual counts, models, comparisons, advance decision and every
limitation. Retain median/p95 speed MAE and endpoint error plus355-window drift
summaries. Write final `artifact-hashes.json` for manifest/NPZ/CSV/results.

- [ ] **Step 4: Compare historical controls and apply fixed decision.**

Map ABS_ALL to legacy learned_raw/reference_oracle/frozen_s1, ABS_V0_ALL to
learned_initial_offset/reference_oracle/frozen_s1, REF_SPEED to
reference_oracle/reference_oracle/frozen_s1. Compare all400 mapped candidate
records each: included flags/reasons and valid east/north/error/distance/drift,
rtol0/atol1e-8, with nulls exact. Keep each comparison and mismatch. Do not
retune or refit to force reproduction. Historical mismatch disables the
advance gate but preserves the fresh paired results.

For each arm and transfer journey, define improved as DELTA median GPS MAE
<=.9×ABS_V0 AND <=.9×CONST, with STRICT improvement versus both when a baseline
is0 (impossible with nonnegative MAE). Require at least two improved journeys
in each arm, identical improved sets, remaining median<=1.05×both baselines,
and p95<=1.10×both on every transfer journey. On improved journeys require
strictly smaller indicated-MAE and endpoint-error medians versus both.
Require historical_passed and all necessary metrics finite/present. Save all
boolean subchecks and reasons, not just a single pass flag. Also flag material
ALL/NZ2 sensitivity when DELTA-vs-ABS_V0 ordering reverses, or a matched method's
transfer median changes>=10% relative to ALL (zero ALL handled explicitly).

- [ ] **Step 5: GREEN tests, one real command and independent handoff.**

After focused GREEN, invoke once:

```sh
env MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python research/tools/audit_dhruva_speed_state.py --parent-manifest research/evidence/dhruva-aligned-2026-09-10-2/manifest.json --output research/evidence/dhruva-speed-state-2026-09-11
```

Report exact RED/GREEN output, real command/session/output, full method tables,
counts, all gate failures, library/model defaults/iterations, artifact hashes
and self-review in the Task2 report. Source bugs preserve attempted evidence
before a numbered retry; scientific failure is a completed negative result,
not permission to tune. Root performs task and final whole-plan reviews.

## Preflight and self-review

| Pair/task | Agreement check | Resolution |
|---|---|---|
| Task1 targets→Task2 fit | Backward support, common NZ2 mask | Both models use identical20495/20415 rows; no forward post-cutoff label |
| Task1 integration→Task2 states | n=L+1, acceleration[0] ignored, signed state retained | Metrics integrate output[:-1]; no clipping feedback |
| Task1 absolute→Task2 historical control | Clip raw before initial offset | Preserve existing branch arithmetic |
| Task1 metrics→Task2 report | Left endpoints, actual dt, common denominator | All370 absolute metrics;355 eligible ratios |
| Task1 tests→implementation | Arbitrary changes, not constant acceleration only | Onset/braking, ignored initial acceleration and clipping cases explicit |
| Task2 frozen input→fit | Hashes, strict cutoff, array support | Manifest precedes all fits; no new offset/window selection |
| Task2 results→decision | Same arms/windows/metrics and explicit failures | Failure retains outcomes; no tuning/repeated fits |

Ruling: retain snapshots/reports instead of Git commits/worktrees — initialization remains reserved — cost: no commit-based recovery.

Ruling: use backward single-interval targets instead of trailing one-second or forward targets — match the propagated interval and preserve all frozen training rows before cutoff — cost: target noise is not reduced by one-second averaging; this is current-interval estimation, not forecasting.

Ruling: apply the two-endpoint NZ2 mask to both targets — isolate target formulation from row membership — cost:80 rather than71 records are removed from the absolute-speed sensitivity arm; remaining labels are not certified clean.

Ruling: retain a signed accumulated speed state and clip only output — expose bias without introducing another state-projection algorithm — cost: negative internal state can delay output recovery after stopping; report it explicitly.

Ruling: keep reference-heading and reference-initial-speed privileges for this speed diagnostic — isolate the measured bottleneck before full navigation comparisons — cost: improved results would still require deployable initialization, heading and independent-journey validation.

Ruling: use fixed advance criteria and historical-control replay without post-result adjustment — make this branch falsifiable — cost: a real but differently shaped gain may fail this gate and would need a separately specified follow-up.

Self-review: spec target/support, all eight methods, model controls, timing
availability, metrics/artifacts and gate rules each map to the two tasks above.
All public signatures and state lengths agree. No new library/framework or
published-method replication is claimed. Stronger comparators remain future
work, not an omitted requirement of this explicitly scoped experiment.
