# Dhruva aligned ablation: numerical result and remaining limits

The corrected experiment isolates useful next work: learned speed remains a
large limitation, especially on S3a. Better heading alone does not bring the
learned-speed branches below10% median drift on any of the four journeys.
Reference-speed branches are much stronger, but use unavailable outage-time
truth and are not a deployable solution or a performance claim.

The task review and final numerical review found no calculation, timestamp
integration or label-isolation defect. The report-table formatting fix also
passed scoped re-review; all implementation findings are closed and numerical
code/results are unchanged. A separate
[reference-quality audit](DHRUVA_REFERENCE_QUALITY_FINDINGS_2026-09-10.md) then
found invalid GPS samples in the source data. Code correctness does not certify
the validity of every reference label.

## Fixed common windows

All4 journeys are existing development data. One refitted, unchanged-parameter
S1 gradient-boosting model uses20,495 timestamp/bracket-constrained samples.
The pre-fit manifest freezes400 candidate60s outages, of which370 satisfy the
time/history requirements. All13 methods have exactly those same candidates;
355 valid windows travel at least50m and have defined drift ratios. All15
short-distance valid windows still retain absolute errors.

| Sequence | Valid/candidate outages | Drift-eligible outages | Learned speed + phone gyro | Learned speed + reference heading | Reference speed + phone gyro | Both reference oracles |
|---|---|---:|---:|---:|---:|---:|
| S1 | 48/52 | 46 | 16.110% | 11.695% | 6.739% | 0.426% |
| S2 | 144/154 | 139 | 21.855% | 17.947% | 7.923% | 0.353% |
| S3a | 37/39 | 36 | 45.412% | 41.665% | 5.312% | 0.276% |
| S4 | 141/155 | 134 | 20.347% | 16.587% | 6.623% | 0.361% |

Values are median eligible drift, using the frozen-S1 gyro-calibration profile
and unadjusted learned speed. These are prespecified branches, not a choice of
each journey's best result. Error components interact; differences between
these medians cannot be interpreted as additive independent error components.

Journey-prefix gyro calibration changes the learned-speed/phone-gyro medians
to16.124%,20.187%,44.878%,23.729% respectively: it is not uniformly better.
Outage-start speed-offset correction also has mixed outcomes: with frozen-S1
gyro it yields17.971%,23.473%,21.822%,20.331%. All branches, tails and per-window
records remain in the evidence; neither calibration was selected by a favorable
median. Reference-speed/reference-heading results are coordinate/velocity
consistency checks only.

## What can and cannot be claimed

The earlier18.342% S1 result is not an accuracy ceiling. However, presenting it
as an isolated18.342→16.110% model improvement would be misleading: alignment,
training samples and physical window boundaries changed. The old transfer
figures likewise mix estimator and timing errors. Both old and new evidence
remain available.

All branches retain ideal reference initial position/heading and pre-outage
VBOX yaw calibration. The reference-speed and reference-heading branches use
truth during outages. Constant residual clock estimation and interpolation
are offline preprocessing. There is no phone-only field validation, new
algorithm, novel best-in-world result or automatic satisfaction of the PS's
less-than10% requirement.

## Evidence

- [Full implementation and test record](evidence/dhruva-aligned-ablation-implementation.md).
- [Pre-fit manifest](evidence/dhruva-aligned-2026-09-10-2/manifest.json),
  [all candidate/method rows](evidence/dhruva-aligned-2026-09-10-2/windows.csv),
  [all summaries](evidence/dhruva-aligned-2026-09-10-2/results.json).
- [Runner](tools/audit_dhruva_aligned.py),
  [tests](../prototypes/dhruva/tests/test_aligned_ablation.py),
  [review/progress ledger](evidence/dhruva-aligned-ablation-progress.md).

The only fitted real run was the numbered`-2` run: the first invocation failed
at import before creating an output directory. Tests pass10/10, with a clean
focused transcript retained. Independent final review recomputed all52
sequence/method summary groups from5200 CSV rows and verified the manifest
hash and duplicate-control invariants. Raw data and old source were preserved.

## Next evidence needed

The independent [raw-reference audit](DHRUVA_REFERENCE_QUALITY_AUDIT_2026-09-10.md)
has quantified the reference-quality issue without refitting an estimator.
Next evaluate cause-driven speed improvements on the frozen physical
windows with explicit quality sensitivity, strong comparable baselines and
valid initialization. Do not treat a larger network or generic filter as
novelty; confirmation requires new journeys/devices and a matched comparison.
