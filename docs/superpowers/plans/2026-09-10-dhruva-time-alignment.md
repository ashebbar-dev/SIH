# Dhruva Time Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace unsafe row-index pairing with explicit timestamp-aligned, gap-preserving inputs for a corrected benchmark.

**Architecture:** A new data module retains raw row indices and both clocks, splits discontinuities, estimates a residual clock shift from a bounded calibration prefix, and interpolates phone measurements onto existing reference timestamps only inside valid contiguous segments. Existing benchmark artifacts and code remain reproducible and unchanged until this loader is independently reviewed.

**Tech Stack:** Existing `.venv`, Python, NumPy, standard-library CSV/datetime/unittest.

**Spec:** `research/DHRUVA_ALIGNMENT_FINDINGS_2026-09-10.md`, especially One bounded next experiment; the exact source columns are also in that report.

## Global Constraints

- No alternative problem-statement work; NISHAN and Dhruva are the active tracks.
- Keep raw inputs and existing benchmark/results unchanged.
- Never interpolate across phone/reference gaps, logger resets or nonmonotonic timestamps.
- Clock calibration may use only the fixed healthy prefix, not evaluation labels or performance.
- Reference-assisted calibration is an offline benchmark operation, not proof of phone-only deployment.
- No Git initialization, commits, firmware, downloads or package changes.
- Use `apply_patch` for code edits; use the existing `.venv` for numerical tests.

---

### Task 1: Timestamp loader, safe alignment and prefix clock estimate

**Files:**
- Create `prototypes/dhruva/time_alignment.py`.
- Create `prototypes/dhruva/tests/test_time_alignment.py`.
- Create report `research/evidence/dhruva-time-alignment-implementation.md`.
- Do not modify `benchmark.py`, `audit_dhruva_transfer.py`, datasets or other files.

**Interfaces:**
- `load_timestamped_pair(data_root: Path, name: str, phone_utc_offset_s: float) -> TimestampedPair`.
- `contiguous_spans(times_s: np.ndarray, elapsed_ms: np.ndarray | None = None, max_gap_s: float = 0.25) -> list[tuple[int, int]]`, returning half-open raw-row spans.
- `estimate_clock_offset(pair: TimestampedPair, prefix_s: float = 140.0, max_residual_s: float = 2.0, step_s: float = 0.1) -> dict`.
- `align_pair(pair: TimestampedPair, residual_offset_s: float, max_gap_s: float = 0.25) -> list[AlignedSegment]`.
- The module's CLI is `--data-root PATH --sequence S1 --phone-utc-offset-s 3600`; print JSON audit with row counts, original discontinuities/times, selected clock estimate and aligned segment bounds/counts. No output-file mutation is required.

`TimestampedPair` retains `phone_time_s`, `phone_elapsed_ms`, `phone` numeric array, `reference_time_s`, `reference` numeric array and both source paths. Phone numeric columns are raw `[3,9..23]`, matching the original16-column feature representation; reference numeric columns are `[2,3,4,5,14]`. Do not truncate the two streams to the same length.

`AlignedSegment` retains `phone` and `reference` arrays, common `time_s`, exact `reference_rows`, containing raw `phone_span` and original `reference_span`. Also retain lower and upper raw phone interpolation indices (`phone_left_rows`, `phone_right_rows`) so every interpolation can be audited. Output reference rows remain original rows, never interpolated labels. There is no requirement for a new estimator in this task.

- [ ] **Step 1: Write failing tests.**

```python
def test_gap_and_restart_split(self):
    times = np.array([0.0, 0.1, 312.242, 312.342])
    elapsed = np.array([100.0, 200.0, 10.0, 110.0])
    self.assertEqual(contiguous_spans(times, elapsed), [(0, 2), (2, 4)])

def test_nonmonotonic_split(self):
    self.assertEqual(contiguous_spans(np.array([0.0, 0.1, 0.1, 0.2])),
                     [(0, 2), (2, 4)])
```

Add actual synthetic CSV fixtures with the real24/29 column layouts. Test unequal input lengths, the colon-millisecond timestamp format, explicit3600s timezone subtraction, midnight rollover in VBOX time, invalid/nonfinite timestamp rejection, and logger resets even with apparently smooth wall clock. Test that a reference timestamp within a phone gap never appears in aligned output and interpolation bracketing never crosses a segment. Test a wrapped phone orientation interpolates via shortest angle, not through180deg when359deg→1deg. Test zero-motion clock calibration fails explicitly. For clock calibration use a deterministic irregular signal with a known0.3s residual offset; mutate all data after the prefix and assert the selected offset/score/sample count remain unchanged.

- [ ] **Step 2: Run `.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_time_alignment.py' -v` and record the expected missing-module failure.**

- [ ] **Step 3: Implement clock-preserving loading and segmentation.**

Parse phone DATE with `datetime.strptime(value.strip(), '%Y-%m-%d %H:%M:%S:%f')`; interpret that wall time with an explicit supplied UTC offset, never system-local timezone. Anchor VBOX seconds-of-day to the closest day to the first corrected phone timestamp; unwrap a decrease larger than43200s as midnight rollover. Preserve smaller timestamp reversals so they split spans rather than silently sorting measurements. Require finite numeric measurements/clocks. Detect every adjacent time delta<=0 or>max_gap_s, and every elapsed-ms delta<=0 as a boundary. Both streams need their own spans; a zero-length input is invalid, singleton spans may exist but cannot supply interpolation intervals. The3600s clock relation is an explicit inferred dataset setting, not automatically certified acquisition metadata.

- [ ] **Step 4: Implement prefix-only residual alignment and interpolation.**

The sign convention is `aligned_phone_time = phone_time_s + residual_offset_s`. Enumerate a deterministic inclusive offset grid from-max_residual_s to+max_residual_s with step_s. For each candidate compare each raw phone gyro axis (`phone[:,7:10]`) against reference yaw (`reference[:,4]`, sign irrelevant for absolute correlation) at reference timestamps inside the FIRST contiguous phone/reference overlap. Restrict BOTH raw phone samples used for interpolation and reference rows to their respective fixed physical-time140s calibration prefixes; never let candidate shifts pull later samples into fitting. Require at least50 paired varying observations; reject all-degenerate candidates with clear ValueError. Select greatest finite absolute Pearson correlation, breaking exact ties by smallest absolute offset, then numeric offset, then axis. Return offset, axis, absolute correlation, paired sample count and exact calibration time bounds; report correlation below0.8 as low-confidence, not a certified clock alignment.

For final alignment intersect every valid phone span (after residual shift) and reference span. Select only existing reference times in that intersection; interpolate phone numeric columns on those times within the containing phone span. Handle the final three phone orientation-degree fields by unwrap/interpolate/wrap; other numeric fields use ordinary linear interpolation. Reference angular values need no interpolation. Compute left/right raw phone bracket indices with `np.searchsorted`; exact matching times may use the same raw row for both brackets. Do not extrapolate, bridge gaps or sort the underlying observations.

```python
right = np.searchsorted(phone_times, target_times, side='left')
right = np.clip(right, 0, len(phone_times) - 1)
left = np.maximum(right - 1, 0)
left = np.where(phone_times[right] == target_times, right, left)
```

- [ ] **Step 5: Run tests and an actual S4 audit.**

```sh
.venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_time_alignment.py' -v
.venv/bin/python prototypes/dhruva/time_alignment.py --data-root /tmp/iovnbd --sequence S4 --phone-utc-offset-s 3600
```

Actual S4 output must expose the raw35185→35186 gap and3526929→10ms restart; no interpolated bracket may straddle those indices. Also run the CLI for S1/S2/S3a and retain exact output in the report. These commands do not demonstrate improved navigation or validate later clock drift.

- [ ] **Step 6: Self-review and independent handoff.**

The report contains implementation files, exact red/green evidence, real-data audit outputs, unresolved clock assumptions and limitations. The root agent then dispatches a fresh spec/quality reviewer. No accuracy claim is allowed from loader tests.

## Execution decisions

Ruling: use snapshots and retained reports instead of Git worktrees/commits — repository initialization is reserved; cost is lack of commit-diff recovery.

Preflight: the sole task's loader, alignment and tests share the named dataclasses and interfaces above. Its CLI consumes the same loader/calibrator/alignment APIs rather than a duplicate path. Original benchmark files are deliberately untouched; corrected estimator evaluation is a subsequent reviewed integration task.
