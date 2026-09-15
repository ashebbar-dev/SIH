# Dhruva Aligned Ablation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Measure corrected Dhruva speed, heading and calibration errors on a single pre-fit manifest of identical timestamp-valid physical outages.

**Architecture:** A new research runner consumes the reviewed timestamp loader without modifying it or the legacy benchmark. It freezes candidate windows and exclusions before fitting one unchanged-hyperparameter S1 speed model, then evaluates a prespecified factorial set of speed/heading/calibration branches. All outputs are retained in a fresh directory, including excluded windows and reference-assisted limitations.

**Tech Stack:** Existing `.venv`, Python, NumPy, scikit-learn HistGradientBoostingRegressor, existing Dhruva causal features and timestamp dataclasses, unittest.

**Spec:** `research/DHRUVA_ALIGNMENT_FINDINGS_2026-09-10.md`, final section; `research/ORIGINAL_IDEAS_FIRST_2026-09-10.md` fixes project priority and clarifies the legacy starting-speed confound.

## Global Constraints

- No alternative problem-statement work; NISHAN and Dhruva are the active tracks.
- Keep all raw data, legacy benchmark/results and reviewed time_alignment.py unchanged.
- No Git initialization, commits, firmware, downloads, package installs or GPU provisioning.
- Freeze physical outage candidates, exclusion reasons, training indices and hyperparameters before speed-model fitting.
- Never bridge gaps/restarts, mix feature history across segments or use outage reference values in the learned model inputs.
- Reference speed/heading within outages are diagnostic oracles only; initial state and pre-outage VBOX calibration are explicitly idealized proxies.
- Report all prespecified branches and every candidate window, not just favorable medians.
- No novelty, field-deployment or less-than-10%-requirement claim follows automatically from this diagnostic.
- Use apply_patch for source edits. Retain fresh evidence instead of overwriting prior runs.

---

### Task 1: Fixed-window factorial evaluation

**Files:**
- Create `research/tools/audit_dhruva_aligned.py`.
- Create `prototypes/dhruva/tests/test_aligned_ablation.py`.
- Create report `research/evidence/dhruva-aligned-ablation-implementation.md`.
- Generate a fresh directory `research/evidence/dhruva-aligned-2026-09-10/` through the runner. It contains manifest.json, windows.csv and results.json. Do not use any existing directory with output artifacts.
- Own no other files; import existing causal_features/local_coordinates/sha256 and timestamp APIs.

**Interfaces and fixed values:**
- `make_windows(pair: TimestampedPair, segments: list[AlignedSegment], first_candidate_row: int, duration_rows: int=600, calibration_rows: int=1200) -> list[dict]`.
- `integrate_displacement(times: np.ndarray, velocities: np.ndarray, headings: np.ndarray) -> tuple[float,float]`: times has L+1 endpoints; velocity and heading arrays each have L samples. Use actual `np.diff(times)` and left-endpoint integration, headings clockwise radians from north.
- `phone_headings(initial_heading: float, yaw: np.ndarray, dt: np.ndarray, bias: float) -> np.ndarray`: yaw and dt each length L; output L left-endpoint headings. First heading is exactly initial_heading; later values use cumulative preceding yaw increments, not current-sample increments before first displacement.
- CLI: `.venv/bin/python research/tools/audit_dhruva_aligned.py --data-root /tmp/iovnbd --output research/evidence/dhruva-aligned-2026-09-10`.
- Only sequences S1, S2, S3a, S4; only 60-second outages for this first corrected comparison. All are exploratory development sequences, not fresh confirmation.
- Clock setting: explicit phone_utc_offset_s=3600, each sequence's existing estimate_clock_offset defaults. Reject low-confidence alignment rather than selecting another shift using trajectory accuracy.
- Training cutoff: S1 reference_time_s[0] + 0.4*(reference_time_s[-1]-reference_time_s[0]). Eligible training rows are in S1 aligned segments, at least 200 segment-local rows after their starts, reference time strictly below cutoff, and BOTH phone interpolation-bracket timestamps after residual shift strictly below cutoff. Record exact segment-local indices and raw reference rows.
- Train one HistGradientBoostingRegressor(max_iter=250,max_leaf_nodes=31,learning_rate=0.08,l2_regularization=1.0,random_state=42), with unchanged legacy causal_features. Do not tune or add a new model.
- Speed profiles: `learned_raw`, `learned_initial_offset`, `reference_oracle`.
- Heading profiles: `phone_gyro`, `reference_oracle`.
- Gyro calibration profiles: `frozen_s1`, `journey_prefix`.
- All 12 combinations must be reported. Duplicated reference-heading outcomes across gyro-calibration profiles are intentional factorial controls and should be numerically identical. Add one constant-speed/constant-heading reference-initialized baseline per window (13 methods total).

- [ ] **Step 1: Write focused failing tests.**

Test actual elapsed integration and left-endpoint heading convention:

```python
east, north = integrate_displacement(
    np.array([0.0, 0.1, 0.3]), np.array([10.0, 10.0]), np.zeros(2))
np.testing.assert_allclose([east, north], [0.0, 3.0], atol=1e-10)
heading = phone_headings(0.0, np.array([np.pi/2, np.pi/2]), np.ones(2), 0.0)
np.testing.assert_allclose(heading, [0.0, np.pi/2])
```

Build numerical TimestampedPair/AlignedSegment fixtures directly using the reviewed dataclasses (all required fields: phone,reference,time_s,reference_rows,phone_span,reference_span,phone_left_rows,phone_right_rows). Use 4001 timestamps at0.1s, phone Nx16, reference Nx5 with speed36km/h, northward coordinates `lat=52+t*10/6371000*180/pi`, longitude0, heading0,yaw0, raw brackets equal row index. At the fixed10m/s speed, each60s outage has an expected600m northward displacement.

Assert a complete window and its120s history are accepted; splitting a segment inside outage or calibration rejects that SAME raw-row candidate and records a reason; duplicated reference rows across overlapping segments reject as ambiguous; shortened/out-of-range windows are recorded if generated; missing endpoint row is not silently integrated. Reference cadence inconsistent with0.1s beyond1e-3 is rejected and logged. Exclusion must not change when only reference speed/heading labels are changed. Add a GPS-input isolation test: modifying phone column0 leaves imported causal_features identical. Add a no-outage-label-leak test for the learned_raw/phone_gyro evaluator: mutate reference speed/heading/yaw strictly after start, keeping initial state and pre-outage labels fixed; predicted displacement must stay unchanged (error/distance metrics may change).

- [ ] **Step 2: Run only the new test file and record expected import failure.**

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_aligned_ablation.py' -v
```

- [ ] **Step 3: Construct windows and training manifest before fitting.**

Load all four timestamped pairs and aligned segments with the reviewed APIs. Validate each returned segment preserves consecutive raw reference rows and has no nonpositive timestamps. Keep a raw-reference-row→list of(segment_index,local_index) lookup so backward-clock overlaps cannot silently duplicate samples.

Use a common raw-reference 600-row grid per sequence, anchored at raw row0. S1's first candidate is the first multiple of600 whose timestamp is at/after its training cutoff; other journeys start at raw row1800. Enumerate candidate starts up to the last existing raw row, even if the final proposed endpoint is out of range. Each window is [start,start+600], with600 intervals. Both outage and entire [start-1200,start) history must lie uniquely in the SAME aligned segment, with at least200 earlier segment-local feature-history rows before the calibration prefix. This conservative boundary means initial candidate exclusions remain visible. Require actual duration60s within1e-3 and all relevant reference sample intervals0.1s within1e-3. Do not decide inclusion using model error, speed, heading or distance.

Each record includes sequence, raw start/end rows, physical times, included flag, exclusion reason, segment/local bounds when valid, calibration local/raw bounds and source spans. Use reasons such as endpoint_out_of_range, missing_or_gap, ambiguous_reference_rows, insufficient_feature_history, non_10hz_reference_cadence. Do not silently drop a candidate because it is excluded.

The pre-fit manifest includes all records; data/code hashes (runner, original benchmark, alignment module); exact training indices; model constants; calibration fits' eligible index lists; clock estimates and explicit UTC assumption; segment provenance; all method names; and written_before_fit=true. Create output directory with exist_ok=False, then exclusive-create manifest.json before invoking model.fit. Existing outputs cause failure, never overwrite. Run timestamps and elapsed fit duration should be recorded.

- [ ] **Step 4: Fit once and evaluate the fixed branches.**

Compute causal features independently inside each segment, never concatenating history across restarts. S1 model uses ONLY manifested training rows and reference speed/3.6 labels. Clamp learned prediction to nonnegative as in the legacy model. Record training refit and the changed aligned training samples explicitly; retain old evidence rather than claiming an exact matched improvement over18.342%.

For frozen_s1 gyro calibration, fit least squares from three phone gyro axes plus intercept to -deg2rad(VBOX yaw) on the SAME manifested S1 training rows. For journey_prefix fit separately per sequence using only the initial aligned segment, after its200-row warmup, and within BOTH raw clock prefixes recorded by estimate_clock_offset. Check phone_right_rows and phone_left_rows remain inside the original initial contiguous prefix; candidate shifts must not import later raw phone samples. Require at least50 finite fit rows; report a failure rather than using evaluation data. Save coefficients and eligible row lists; no fit chosen using outage errors.

For each valid window, use exactly1200 pre-outage reference yaw samples to estimate mean yaw bias for each gyro profile. Initial heading=deg2rad(reference[start,3]); initial position uses reference[start,0:2]. These privileged quantities must be labeled. Phone headings use exclusive cumulative integration as defined above. Reference-oracle headings use reference[start:end,3] directly.

Velocity rules:

```python
if speed_profile == 'learned_raw':
    velocity = predicted_speed[start:end]
elif speed_profile == 'learned_initial_offset':
    velocity = np.maximum(0, predicted_speed[start:end]
                          + reference[start,2]/3.6 - predicted_speed[start])
elif speed_profile == 'reference_oracle':
    velocity = reference[start:end,2]/3.6
```

The starting-speed offset is identical across heading profiles; no hidden extra correction. Constant baseline uses reference[start] speed and heading throughout. Use integrate_displacement with actual reference times, and compare with reference endpoint displacement from local_coordinates. Reference-oracle integration is a coordinate/velocity sanity check, not an estimator.

Compute path distance=sum(reference_speed[start:end]*dt). Report absolute endpoint error for every valid window, even distance<50m. Drift percent is null if distance<50m; include the excluded ratio count. Results per sequence/method: valid/eligible counts, median and p95 absolute error, median and p95 eligible drift, fraction eligible windows below10%, and coverage/exclusion counts. Write all window/method rows with identical window IDs to windows.csv. Assert factorial reference-heading duplicates agree and every method evaluates exactly the same valid-window IDs.

- [ ] **Step 5: Verify tests and run the real diagnostic once.**

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_aligned_ablation.py' -v
env OMP_NUM_THREADS=2 OPENBLAS_NUM_THREADS=2 MPLCONFIGDIR=/tmp/sih-matplotlib \
  .venv/bin/python research/tools/audit_dhruva_aligned.py \
  --data-root /tmp/iovnbd --output research/evidence/dhruva-aligned-2026-09-10
```

Print compact per-sequence summaries as each completes. Save every result; do not adjust constants or rerun for a better number. Empty eligible groups serialize null rather than NaN. Any code bug found during execution must be reported; preserve the failed directory and use a clearly numbered new output directory after correction.

- [ ] **Step 6: Self-review and independent handoff.**

The report names all created files/output directory, exact red/green test output, run command and result summaries, exclusion counts, and any implementation concerns. The root reviews before using accuracy numbers. No change to production or old benchmark code is part of this task.

## Preflight decisions

| Task/interface pair | Producer and consumer | Finding |
|---|---|---|
| Task 1 loader→window manifest | Reviewed segments retain source rows and actual timestamps | Need explicit rejection of duplicate reference rows after backwards clocks; included above |
| Task 1 windows→all13methods | One common ID set and same initialization rules | Two reference-heading duplicate groups are intentional numerical controls; no selective window exclusion |
| Task 1 tests→integrator | L+1 timestamps, L headings/velocities | Left-endpoint convention is explicit and differs from legacy advance-before-step convention |
| Task 1 training→evaluation | Corrected S1 first40% time, bracket-constrained train rows | Refit and window shift are explicit; cannot present old18.342→new as single-variable causal gain |

Ruling: retain snapshots and reports instead of Git worktrees/commits — initialization remains reserved — cost: no commit-based recovery.

Ruling: use60s outages and the prespecified12 factorial branches plus constant baseline for this diagnostic — isolate the existing60s failure before expanding durations — cost: no15/30/120s performance claim from this run.

Ruling: reference initialization/calibration remain privileged offline diagnostics, with left-endpoint integration and matched corrections — isolate errors without claiming a deployed GNSS path — cost: numerical gains require a later deployment-valid evaluation.
