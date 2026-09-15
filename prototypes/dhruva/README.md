# Dhruva preliminary benchmark

**Target:** SIH26168, ISRO — AI/ML-based intelligent dead reckoning for seamless navigation.

This directory contains the historical preliminary S1 benchmark and a timestamp-preserving loader used by the newer research evaluator. The historical runner is retained for reproducibility; use the corrected results below for the current diagnostic. Neither is a finished navigation engine.

Run from the repository root:

```bash
MPLCONFIGDIR=/tmp/sih-matplotlib \
  .venv/bin/python prototypes/dhruva/benchmark.py \
  --data-root /path/to/extracted/iovnbd \
  --output artifacts/dhruva
```

The script:

1. determines a contiguous 40/60 temporal split before fitting and records the exact indices and input hashes;
2. estimates phone/VBOX lag only from the training prefix;
3. builds causal phone-IMU features with no GPS columns in the model input;
4. trains a small gradient-boosted velocity model;
5. learns the phone-to-vehicle gyro mapping on training data;
6. injects non-overlapping 15/30/60/120-second outages in the holdout;
7. writes every window, aggregate metrics, input hashes and two figures.

Absolute endpoint error is reported for every sampled window. Percentage drift is
reported only for windows that travel at least 50 m; the excluded count and minimum
distance remain visible. This prevents a stopped vehicle's near-zero denominator
from turning a small position error into a meaningless percentage.

Three curves are reported. The constant-speed/heading curve is the naïve baseline. The “speed component with reference heading” curve substitutes reference heading **and corrects learned speed using reference speed at outage start**; it does not isolate heading alone and must never be presented as full navigation. The phone-IMU curve uses learned speed and phone gyro during the outage, but retains ideal reference initialization and pre-outage VBOX yaw-bias calibration. It is a reference-assisted preliminary benchmark, not a validated phone-only deployment.

## Data-integrity findings

- The smartphone CSV header labels GPS speed as km/h, but paired VBOX values show the phone numbers are numerically consistent with m/s. The script records that ratio explicitly.
- The paired streams retain a sequence-specific IMU lag. S1's lag is estimated from training-only turn-rate correlation rather than assumed.
- VBOX yaw rate has the opposite sign to compass-heading rate in this sequence. The conversion is explicit in code.
- A subsequent [timestamp audit](../../research/DHRUVA_ALIGNMENT_FINDINGS_2026-09-10.md) found journey-specific clock offsets and phone logger restarts, including a **312.142-second S4 gap**. The historical loader discards clocks and pairs rows, so its transfer results confound timing and estimator errors. The separate [timestamp-preserving loader](time_alignment.py) has 13 passing tests and completed independent review, including a backward-restart correction. It is integrated into the corrected research evaluator below; the legacy runner above remains unchanged.
- The independent [reference-quality audit](../../research/DHRUVA_REFERENCE_QUALITY_AUDIT_2026-09-10.md) found GPS channel disagreements and zero-satellite rows in training and a few evaluation intervals. Timestamp correctness does not certify reference labels. No historical samples or results were silently removed.

These details are submission evidence: they show that the team actually loaded and audited the named dataset instead of copying a model diagram into the deck.

## Corrected diagnostic and current boundary

The [timestamp-aligned factorial experiment](../../research/DHRUVA_ALIGNED_ABLATION_FINDINGS_2026-09-10.md)
has completed independent task and final review: 400 candidate 60-second
outages, 370 valid common windows, 355 drift-eligible windows, and 13 fixed
methods. With frozen-S1 gyro calibration and unadjusted learned speed,
median drift is 16.110%, 21.855%, 45.412% and 20.347% on S1/S2/S3a/S4.
These are reference-assisted development results, not a clean improvement
from the old 18.342% S1 number: alignment, fit samples and windows changed.

The [corrected runner](../../research/tools/audit_dhruva_aligned.py) accepts
`--data-root` and a fresh `--output` directory. The retained
[full run and test record](../../research/evidence/dhruva-aligned-ablation-implementation.md)
contains its exact successful invocation. All reference-oracle branches,
failures and per-window outcomes are retained; oracle speed/heading results
must not be presented as deployable navigation.

The [10 September transfer audit](../../research/INDEPENDENT_GOAL_AUDIT_2026-09-10.md)
reproduced S1, then applied the same fitted model, lag and gyro map to S2, S3a
and S4. Their 60-second median drifts were **47.49%, 63.67% and 56.34%**.
The complete [results and limitations](../../research/evidence/dhruva-transfer-2026-09-10/results.json)
and [runner](../../research/tools/audit_dhruva_transfer.py) are retained.
These are historical, timing-confounded diagnostics with ideal reference initialization
and pre-outage VBOX calibration, not clean transfer or field performance. The PS's less-than-10%
requirement is not automatically satisfied by a median below 10%.

The benchmark has no road graph, non-holonomic factor graph, fixed-lag smoother,
uncertainty calibration, device-transfer test, or Indian road recordings.
The current phone-IMU result is above ISRO's 10% drift target. The user's
[current decision](../../research/ORIGINAL_IDEAS_FIRST_2026-09-10.md) restores
Dhruva and NISHAN as the first research priorities, ahead of alternatives.
Timestamp alignment and the matched speed/heading comparison are complete.
Next resolve reference-quality sensitivity and test cause-driven speed
improvements with valid initialization and strong comparable baselines.

The historical runner's corrected 60-second bucket contains 51 non-overlapping windows from one S1
holdout, with 71.8 m median absolute endpoint error and 18.3% median drift. The
120-second bucket contains only 25 windows. The earlier overlapping-window count
must not be quoted as an independent sample size. The manifest also says plainly
that it was written after the run; an immutable pre-fit Git commit does not yet
exist because repository initialization is reserved for the internal-hackathon day.

Dataset and paper: [IO-VNBD repository](https://github.com/onyekpeu/IO-VNBD) and [arXiv:2005.01701](https://arxiv.org/abs/2005.01701).
