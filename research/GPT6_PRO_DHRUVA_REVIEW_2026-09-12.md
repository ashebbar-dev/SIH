# GPT-6 Pro DHRUVA proposal: bounded feasibility review

12 September 2026. Scope: D1 lateral-acceleration speed-residual proposal and D2 reserve adaptation. This review inspected source, retained evidence and primary references; it performed no fitting, numerical experiment, tests, installation or data download. This document is the only file changed.

**Verdict:** D1 is a useful, falsifiable observability hypothesis, but its stated uncertainty gate is not yet justified and the current repository does not supply the required causal adapter or confirmation dataset manifest. Advance only to a small feasibility diagnostic. Neither D1 nor D2 currently supports superiority, novelty, or the PS's drift requirement. The existing speed-state pilot remains with its original Sol Ultra owner.

## Necessary mathematical corrections

The following derivation assumes vehicle axes x forward, y left, z up; a rigid mount; gravity-corrected acceleration; negligible lateral velocity at a specified vehicle reference point O; and a speed residual constant within one block. Define the lever arm from O to the phone, expressed in vehicle axes. Then planar rigid-body kinematics gives

\[
a_y^P = r v_x^O + \dot r\ell_x-r^2\ell_y
\]

under the zero-lateral-velocity assumption. With the proposed nuisance terms, set

\[
e=a_y-rv_{\rm base},\qquad
N=[\mathbf1,a_x,\dot r,-r^2],\qquad
\eta=[b_y,\delta\psi,\ell_x,\ell_y]^T.
\]

The sign of the small yaw-error term depends on the declared rotation-error convention. Define it and check it against a known rotation; it cannot be inferred from the symbol alone.

1. **Include learned prior means.** For the objective
   \[
   (e-rd-N\eta)^TW(e-rd-N\eta)
   +(\eta-\mu_\eta)^T\Lambda_\eta(\eta-\mu_\eta)
   +\lambda_v(d-\mu_v)^2,
   \]
   the proposed P is the correct Schur complement, but the solution is
   \[
   \hat d=\frac{r^TP(e-N\mu_\eta)+\lambda_v\mu_v}
                   {r^TPr+\lambda_v}.
   \]
   The supplied expression is valid only after centering nuisance parameters, with zero speed-residual prior mean. Prefix estimates of bias/alignment/lever arm will generally not all be zero. Joint prior cross-covariances also require the joint precision formulation, not independent penalties by assumption.

2. **Separate measurement identifiability from prior support.** With unconstrained nuisances, use the data-only quantity
   \[
   I_0=r^T\{W-WN(N^TWN)^+N^TW\}r.
   \]
   Exact constant r lies in the intercept column, so I0=0; straight motion r=0 also supplies no speed information. Varying r is necessary but insufficient: r can remain nearly in the span of acceleration, yaw acceleration and squared yaw rate. Use a scaled rank/conditioning check, not simply a minimum turn rate. Finite nuisance priors can make Iv positive when nonzero r lies in the nuisance span; lambda_v can tighten the posterior even when r=0. Report I0 and Iv separately and reject the stipulated constant-turn degeneracy; do not describe confidence inherited from a bias prior as newly observed speed. Measured-yaw noise must not masquerade as physical excitation. Use rank-aware solves rather than hiding degeneracy with arbitrary numerical jitter.

3. **Specify what the standard deviation means.** The variance `(Iv+lambda_v)^-1` is a conditional Gaussian posterior variance only with known absolute residual covariance W=R^-1, fixed exact regressors, the stated independent priors and a correct linear model. Robust weights alone are not an acceleration-noise precision. At nominal 10 Hz, a four-second block contains approximately 40 samples, not 40 independent measurements. Five fitted coefficients would leave 35 residual degrees of freedom only in the full-rank, unregularized IID case. Correlation, robust fitting, shrinkage and deficient rank change this calculation. Account for gyro/derivative noise, reference-calibration uncertainty and model discrepancy, and check uncertainty coverage on later past data. A small within-block residual can coexist with a biased speed estimate. The 2 m/s gate is about the fitted residual; it does not certify total future speed uncertainty or endpoint drift.

4. **Respect units and the reference point.** Use acceleration in m/s², r in rad/s, its derivative in rad/s², speed in m/s, lever arm in metres and yaw error in radians. Lambda_eta needs physically scaled precision entries; a common ridge number across bias, angle and distance is not a meaningful prior. With W in inverse acceleration-variance units, Iv and lambda_v have units `(m/s)^-2`. A GPS antenna reports motion at its own point; its scalar ground speed is not automatically `v_x^O`. The phone also has lever-arm lateral velocity. State where the nonholonomic constraint holds and transform navigation/reference outputs consistently. The equation uses signed longitudinal velocity: reverse motion needs a declared treatment, since nonnegative GPS speed and course are not signed speed and body heading.

5. **Bound the omitted physics.** In general `a_y^O = dot(v_y^O)+r*v_x^O`. Sideslip, bank/roll gravity leakage, bumps, mount motion and changing speed-model error can violate the four-second approximation. Gyro bias produces a term approximately `-b_r*v_base` when measured r is used, absent from the listed nuisance basis; uncertainty in r also affects r² and its derivative. Propagate these effects or restrict/report the model's operating conditions. Estimating additional nuisance directions can reduce the identifiable speed subspace. A short prefix with insufficient excitation cannot justify tight priors on all four nuisances.

## Dependence and causal update contract

The existing [speed features](../prototypes/dhruva/benchmark.py) use the same accelerometer and gyro channels, with trailing histories up to 200 samples. Thus `v_base`, ay, ax, r and the residual errors are statistically dependent. Nonoverlapping four-second measurement blocks do not remove that dependence or the shared 20-second feature history. This is not automatically label leakage, and a conditional predictor can still improve. It does invalidate treating learned speed and the proposed inertial correction as independent sensors. For the first diagnostic, hold the base predictions fixed and assess an additive residual predictor on later past blocks; do not claim independent Kalman information gain. A later fusion estimator must model/calibrate the relevant covariance and errors in variables.

Make the update semantics explicit before any navigation run:

- Specify half-open four-second supports, actual timestamps, minimum usable samples, derivative/filter support and a gap-reset rule. A backward derivative or explicitly delayed estimate is required; a centered derivative or zero-phase filter cannot use future samples without reporting latency.
- Commit a correction only after the whole block and every preprocessing input are available. Integrate the previous speed state until then; never recompute the completed path using the new correction. Include latency in evaluation. An informative final block with no remaining travel does not demonstrate a useful correction.
- Distinguish an absolute correction relative to a frozen base from an increment relative to an already corrected state. Repeatedly adding the former double-counts the same offset. Shared nuisance uncertainty persists across blocks; do not treat reuse of the same 180-second prior as repeated independent evidence. Define correction persistence/expiry, process uncertainty and fallback on rejection.
- Limit prefix fitting to reliable GNSS actually available before each blackout. Include label differencing, clock fitting, normalization, mounting alignment and all filter brackets in the support audit. Do not refresh from outage GNSS speed/course or labels, or from predictions treated as truth. A missing/poorly excited prefix needs a declared fallback. Simulator episodes reset from the same permitted information for every method.

D2 is conventional trip calibration with an additional validation guard, not established novelty. Fit an affine map on an earlier prefix portion, assess the frozen candidate against the frozen incumbent on a later portion that is still before commitment, and only then apply it prospectively. Retrospective acceptance and reuse of the validation portion for repeated tuning break that guard. Keep a fallback when affine slope/offset are not identifiable. If both D1 and D2 are considered, select using development/validation, not whichever wins each test group.

## Evaluation selection needs one correction

Maintain three explicitly different populations: all prespecified blackout IDs; a common observable-regime subset; and the D1-accepted subset. Freeze the common regime using sensor geometry and a fixed baseline/prefix calibration, without D1's fitted correction, robust residual or realized acceptance. Evaluate every method on that same subset. An outage containing two D1-accepted blocks defines the candidate's selective operating coverage, not an independent test population. Even with a frozen, label-free gate, reporting only that subset answers a conditional question.

The equal-weight mean of acquisition-group median drift is reasonable, alongside the requirement for at least 20% relative improvement over the validation-selected strongest baseline in **each** test group. Preserve the frozen model, same-prefix affine calibration and a competent NHC-EKF with bias/alignment uncertainty as comparators, with identical allowed inputs and initialization. A weak newly written EKF would not satisfy that contract.

Specify whether the ≥30 blackouts and ≥12 target outages apply per group or in total, and define the ≥20% coverage denominator before inspecting results. Publish counts for all three populations by group, every rejected/failed outage, and short-travel absolute errors. Keep the ≥50 m rule for percentage drift. Report all eligible-outage P90 drift against the selected baseline, where the permitted worsening is 2 **percentage points**; also report all-outage absolute-error tails. A common regime identified over the whole blackout is a retrospective evaluation stratum, not information available at blackout start. Thirty windows within a drive are not thirty independent acquisition groups; two test groups support limited replication, not a broad population guarantee.

## Data and adapter readiness

| Item | Evidence checked on 12 September | Consequence |
|---|---|---|
| Existing local benchmark data | Historical manifest names `/tmp/iovnbd`; that directory is now absent. A bounded filename inventory of the workspace and `/tmp` found no paired IO-VNBD CSVs or dataset archive. | Raw inputs were not available at the inspected locations; availability elsewhere is unverified. Retained result tables cannot substitute for raw-block diagnostics. |
| Existing split | S1/S2/S3a/S4 have already informed the [ablation](DHRUVA_ALIGNED_ABLATION_FINDINGS_2026-09-10.md), [quality audit](DHRUVA_REFERENCE_QUALITY_FINDINGS_2026-09-10.md) and [speed-state design](DHRUVA_SPEED_STATE_DESIGN_2026-09-11.md). | Development only. Renaming windows does not create new tests. |
| Public candidates | Author tree visibly lists paired [M](https://github.com/onyekpeu/IO-VNBD/tree/master/Synchronised%20V%20abd%20S%20datasets/Categorised%20IOVNB%20Dataset/M%20%28Driver%20B%29) and [Y1](https://github.com/onyekpeu/IO-VNBD/tree/master/Synchronised%20V%20abd%20S%20datasets/Categorised%20IOVNB%20Dataset/Y%20%28Driver%20D%29/Y1) CSVs and a [Vta family](https://github.com/onyekpeu/IO-VNBD/tree/master/Synchronised%20V%20abd%20S%20datasets/Categorised%20IOVNB%20Dataset/Vta%20%28Driver%20E%29). | There are concrete public acquisition candidates; it would be wrong to claim no data exists. File contents, usable counts, quality and prior project exposure were not verified here. |
| Acquisition grouping | Paper metadata assigns M to 7 September 2019, Y1 to 30 August 2019, and paired Vta1a to 14 November 2019. It puts S3a/b/c on 4 September 2019. [Dataset paper, appendices](https://arxiv.org/pdf/2005.01701). | M, Y1 and a conservatively grouped Vta acquisition are candidates for three reserved groups, not yet certified validation/tests. Keep S3a/b/c together pending acquisition provenance. Do not split continuous Vta fragments into independent groups. |
| Loader and calibration | [time_alignment.py](../prototypes/dhruva/time_alignment.py) hardcodes `S (Driver A)/{name}`. Alignment interpolates with right brackets. The [evaluator](tools/audit_dhruva_aligned.py) uses 140-second clock prefixes, 120-second VBOX-yaw bias histories and privileged initial state. | No inspected adapter implements the proposed other-driver paths, 180-second reliable-GNSS policy, causal mounting/gravity treatment or D1. Existing timing/oracle handling cannot silently become phone-only deployment evidence. |
| Strong baseline | No NHC-EKF or AI-IMU adapter was found in the inspected DHRUVA implementation. [AI-IMU author code](https://github.com/mbrossar/ai-imu-dr) is public/MIT; its supplied checkpoint has only KITTI sequence 02 held out. | Code availability is distinct from a validated 10 Hz smartphone adaptation. A published score or supplied checkpoint is not the matched baseline. |

The [dataset paper](https://arxiv.org/pdf/2005.01701) also reports manual synchronization and GPS outages; its total public duration does not certify enough usable, independent phone/reference blackout episodes. Existing satellite-field semantics and reference-channel disagreements remain unresolved. Establish initialization, endpoint and distance-reference quality separately; indicated vehicle speed is corroboration, not position truth. Different acquisition groups alone also do not establish unseen-device transfer. No held-out group should be discarded or reassigned because its model results disappoint.

## Duplication map and smallest diagnostic before 15 September

| Proposed work | Existing ownership/prior work | Distinguishing value still open |
|---|---|---|
| Absolute versus delta-speed propagation | [Fixed speed-state design](DHRUVA_SPEED_STATE_DESIGN_2026-09-11.md), numerical module and [Task 1 report](evidence/dhruva-speed-state-task-1-report.md); original Sol Ultra lab owns the matched pilot. The shared ledger is stale about Task 1; its report says complete. No Task 2 fit result was found in the inspected shared evidence. | Do not rerun or duplicate the pilot. Await its results/provenance. |
| Learned increments, mounting and timing compensation | [DVSE](https://arxiv.org/html/2505.18490v1) already learns velocity changes with mounting/noise treatment and GNSS timing compensation. Its reference-velocity input uses GNSS during training and estimated velocity during inference. | D1's specific identifiable residual subspace and calibrated causal benefit remain hypotheses; increment learning alone is not new. |
| Motion constraints and adaptive confidence | [AI-IMU](https://github.com/mbrossar/ai-imu-dr) uses lateral/vertical velocity constraints and learned covariance adaptation. | D1 resembles a local differentiated nonholonomic constraint; claim novelty only after a dedicated prior-art review and matched evidence. |
| Prefix affine adaptation | Original Sol brief already includes guarded trip-prefix calibration as a possible pilot. | D2 overlaps that scope; coordinate through the owner, not a second competing fit. |

The smallest useful next artifact is a **feasibility and provenance sheet**, not a production filter:

1. Freeze the corrected centered equations, coordinate/lever-arm conventions, data-only information gate and future-only update timing. Record analytic witnesses for straight motion, constant turns with free bias, nonzero prior means, degree/radian conversion, gyro/bias steps and a correction first available at the block end. These are diagnostic contracts, not results from tests run in this review.
2. Inventory M, Y1 and one conservatively grouped Vta acquisition using metadata only; establish file identity/schema, acquisition relationships, untouched status and whether the 180-second prefix plus required blackout counts is plausible. Reserve one validation and two test groups before outcome inspection. Do not fit merely to discover a split.
3. If raw development data are recovered through the existing owner, run one frozen, small prefix-only excitation check: earlier reliable prefix for nuisance/noise estimates, later past blocks for prospective residual/uncertainty checks. Show I0 versus Iv, rank, conditioning, rejection reasons and same-IMU dependence limitations. Hold the existing speed predictor fixed; do not train another delta-speed model or run a new full navigation sweep. Freeze the mapping/quality rules before checking outcomes; retain failures.

If raw data, reference semantics or a reliable prefix remain unavailable, the honest pre-deadline result is the analytic/provenance diagnostic and an explicitly untested D1 hypothesis. A 20% gain, coverage target, novelty claim or end-to-end drift claim must wait for the specified matched evaluation; this review supplies none of those results.
