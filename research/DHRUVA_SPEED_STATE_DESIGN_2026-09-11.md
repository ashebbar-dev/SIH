# Dhruva: matched speed-state and known-defect sensitivity experiment

Status: fixed design before fitting. The previous goal turn made progress:
NISHAN's physical experiment and independent reviews completed. No additional
capture was recovered; the broader novelty/performance goal remains unmet.

## Purpose and comparison boundary

Test whether the current speed bottleneck improves when the same estimator
learns interval velocity changes and propagates a known initial speed, instead
of regressing absolute speed from inertial features. Separately measure
sensitivity to a narrowly defined subset of suspect training references.
This is an established state-estimation baseline, not a proposed invention.
DVSE already learns velocity changes with noise/mounting compensation and a
timing-aware loss; see its [motion model and training formulation](https://arxiv.org/html/2505.18490v1).

The [vehicle comparator audit](DHRUVA_VEHICLE_COMPARATORS_2026-09-11.md)
recommends an adapted four-second attention-LSTM as a stronger speed baseline
and an AI-IMU adaptation for full navigation. This experiment establishes a
matched comparison protocol and tests a specific failure mechanism; it does
not substitute improvement over our gradient booster for improvement over the
field. A neural framework is not installed in either inspected local venv.
No dependency installation or neural training is part of this experiment.

## Binding constraints

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

## Frozen data and timing

Input manifest: `research/evidence/dhruva-aligned-2026-09-10-2/manifest.json`,
SHA256 `c8a82a54a587506a7546a1d635be4a6e1f397b6304f87517c8681803c5134c37`.
Its sibling windows.csv is the historical numeric control. Verify all eight
raw hashes and the recorded unchanged loader/benchmark/ablation-runner hashes.
Reuse stored clock offsets (S1−0.3,S2+0.2,S3a−0.2,S4+0.1 seconds) and explicit
phone UTC correction3600s; do not estimate new offsets. Regenerate aligned
segments and check their provenance against the manifest, then use its windows
and training index lists directly. S1 training cutoff is1567935738.8; the
original rows are raw203..20697, local200..20694 in segment0.

The current-sample/trailing feature vector has247 columns. Compute it separately
inside each aligned segment using unchanged `legacy.causal_features`. Its
largest history is200 samples. GPS and orientation columns are unused.
Interpolation is offline and may use a phone sample after the reference time.
Record the shifted right-bracket availability time for every saved segment;
do not claim strict raw-sensor causality or silently replace interpolation.

Read raw reference columns0 and15 as satellite field and indicated speed
(km/h). Match by raw reference row, without interpreting status bits or changing
reference values. Indicated speed is a corroborating channel, not position truth.

## Target/support correction

For each aligned row i>0, define the average acceleration over its immediately
preceding interval:

`a[i] = (GPS_speed_mps[i] - GPS_speed_mps[i-1]) / (time[i] - time[i-1])`.

The unchanged feature X[i] estimates a just-completed interval; this is not
future forecasting. It uses no label after the training cutoff. A trailing
one-second target would smooth/lag propagation; a forward target would need a
post-cutoff label for the final frozen training row. Neither is used here.

ALL retains the exact20495 original training records. NZ2 applies a common
mask to BOTH absolute-speed and acceleration targets: the raw satellite field
must be nonzero at both endpoints {raw_row−1,raw_row}. This removes80 records
and leaves20415. Preserve order and record every included/excluded raw row and
both target-support rows before fitting. The first aligned row has no target;
none of the frozen training rows is first in its segment. All support times
must be finite, increasing, contiguous and strictly below the frozen cutoff.

NZ2 does not remove adjacent nonzero-field GPS errors, certify satellite
semantics or establish truth. It is a known-defect sensitivity only. Do not
change any evaluation membership based on satellite metadata or channel errors.

## Exact methods and integration

Fit four models: absolute speed and backward-interval acceleration, each under
ALL and NZ2. Use `HistGradientBoostingRegressor(max_iter=250,
max_leaf_nodes=31,learning_rate=.08,l2_regularization=1.,random_state=42)`.
Record full `get_params()`, library versions and fitted `n_iter_`;250 is the
maximum, not a promised fitted iteration count. Keep raw model predictions.

Eight method IDs, all using the same reference-heading sequence:

| ID | Speed construction |
|---|---|
| CONST_V0 | Constant reference speed at outage start |
| ABS_ALL | max(0, raw absolute-model prediction), ALL |
| ABS_V0_ALL | max(0, p[i]+v0−p[start]), where p=max(0,raw prediction), ALL |
| DELTA_V0_ALL | Signed accumulated acceleration estimate, output-clipped only, ALL |
| ABS_NZ2 | Same absolute branch, NZ2 |
| ABS_V0_NZ2 | Same offset branch, NZ2 |
| DELTA_V0_NZ2 | Same acceleration branch, NZ2 |
| REF_SPEED | Recorded GPS speed oracle |

For an outage with L+1 timestamps and acceleration predictions a[0..L], let
u[0]=v0 and `u[i]=u[i-1]+a[i]*(t[i]-t[i-1])` for i=1..L. Ignore a[0]. Do not
clamp acceleration or feed clipped speed back into the signed state. Return
both signed u and output speed max(0,u). Per-step state projection is a
different untested algorithm. Save both states so clipping cannot hide bias.

Use existing `integrate_displacement(times,output_speed[:-1],reference_heading[:-1])`.
All headings are radians. Use the existing local-coordinate and GPS integrated
distance formulas, including the original per-segment coordinate origin.
The existing constant baseline freezes heading too and is NOT this experiment's
CONST_V0 control. Perfect interval targets must reconstruct arbitrary nonnegative
reference speeds; constant acceleration alone is an insufficient test.

## Metrics, artifacts and decision

For each valid window/method save all601 signed/output speeds (600 intervals),
times, reference GPS/indicated speeds and headings. Persist raw full-segment
model predictions and availability timestamps in NPZ. Retain all400×8 CSV rows,
with explicit unchanged exclusions and null metrics on excluded candidates.
Primary window metric is actual-dt-weighted speed MAE against recorded GPS over
the600 left endpoints. Also report indicated-speed MAE, mean signed speed error,
output-clipping fraction, terminal speed error, reference-heading endpoint
error and existing eligible drift ratio. For acceleration branches, report
dt-weighted mean acceleration error over the600 reconstructed intervals.

Summarize median/p95 of window speed MAE and endpoint errors by journey/method;
retain counts, drift subset and all individual rows. Satellite flags are
descriptive only. Save a pre-fit manifest, models' parameter/iteration records,
arrays and per-array hashes, CSV, results and final file hashes. Capture all
warnings and failure states. One full fit/evaluation invocation after unit
tests; an implementation failure preserves its evidence before a numbered
retry. A scientific failure does not trigger tuning or another fit.

Compare ABS_ALL, ABS_V0_ALL and REF_SPEED per-window east/north/error/distance/
drift to the corresponding historical reference-heading/frozen-S1 branches at
rtol0,atol1e-8 (null drift must match null). Save every discrepancy. Package
versions were not fully recorded historically, so equality must be observed,
not assumed. A mismatch does not erase the fresh paired results, but disables
the historical-reproduction gate and any claim of exactly reproducing it.

The advance criterion is fixed before fitting. In BOTH support arms, on
S2/S3a/S4 the DELTA branch must lower median GPS-speed MAE by>=10% versus BOTH
the corresponding ABS_V0 branch and CONST_V0 on at least two journeys; on the
remaining journey it may be at most5% worse than each comparator. Its p95
window MAE may be at most10% worse than each comparator on any transfer journey.
On every journey counted as improved, indicated-speed MAE and reference-heading
endpoint-error medians must also strictly improve against both comparators.
The set of improving journeys must match between ALL and NZ2. Zero comparator
metrics are treated with explicit inequalities, never division by zero.

If ALL/NZ2 reverses a DELTA-versus-ABS_V0 ordering or changes any method's transfer
median GPS-speed MAE by>=10%, report reference-quality sensitivity as material.
The overall advance gate also requires historical reproduction and no missing
metrics; otherwise report not-advanced with every reason. These engineering
criteria determine whether to continue this formulation, not statistical
significance, less-than10% PS compliance or state-of-the-art superiority.

Regardless of outcome, a stronger published-method baseline and independent
journeys/devices remain necessary for the original goal.
