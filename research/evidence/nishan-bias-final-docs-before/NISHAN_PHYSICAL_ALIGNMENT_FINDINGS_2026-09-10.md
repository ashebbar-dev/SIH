# NISHAN physical alignment controls — 10 September 2026

## Outcome

The simpler affine refinement strengthens the correct-recipient match in
`akshay3.jpeg`, but neither tested refinement recovers another supplied image.
The more flexible homography improves page-content similarity while losing
the watermark decision on akshay3. Better text alignment is therefore not a
sufficient objective for this carrier on these captures.

These are development experiments on four captures of one printed fixture,
not a physical robustness rate or a novel algorithm. No original image,
previous evidence or production decoder was changed.

## Fixed experiments and retained evidence

Both experiments predeclare all four supplied captures, three profiles
(`orb`, `orb_ecc_affine`, `orb_ecc_homography`), all 1,000 recipient rows,
epsilon=1e-6 and H=12,000. Thresholds consequently differ from the earlier
four-profile conditional experiment, which used H=4,000. Each family has its
own modeled budget; this is not a global budget covering all research.

ECC uses only source/capture pixels, with 200 iterations, stopping epsilon
1e-6 and Gaussian size 5. Affine and homography fits start independently from
the same ORB-aligned image and identity correction. Recipient scores do not
select a transform, settings or a preferred profile. All outcomes are retained.

- [Initial two-resampling runner](tools/probe_nishan_physical_registration.py)
  and [evidence](evidence/nishan-physical-registration-2026-09-10.json).
- [Single-final-resampling control](tools/probe_nishan_physical_registration_single.py)
  and [evidence](evidence/nishan-physical-registration-single-2026-09-10.json).

The initial experiment resamples the ORB result again after ECC. An independent
review identified this as a potential confound. The control retains exactly
the same estimated ECC transforms but composes the maps and samples the
original capture once for final rendering:

`raw_to_reference = inverse(ECC_inverse_warp) @ ORB_raw_to_reference`.

ECC estimation still consumes the ORB-resampled image. This control removes
the second final-image resampling, not every possible interpolation effect.
Both scripts run synthetic warp-direction checks before physical scoring;
the control additionally checks composition against an exact translation.

## Single-final-resampling results

| Capture | Profile | Correct-row score | Conditional threshold | Highest other score | Content similarity | Accused rows |
|---|---|---:|---:|---:|---:|---|
| akshay2 | ORB | 683.938 | 1030.895 | 604.472 | 0.674 | None |
| akshay2 | ORB + affine | 788.315 | 1030.165 | 534.078 | 0.689 | None |
| akshay2 | ORB + homography | 811.494 | 1031.811 | 560.115 | 0.806 | None |
| akshay3 | ORB | 1357.130 | 1103.752 | 588.274 | 0.671 | Only row 0 |
| akshay3 | ORB + affine | 1709.941 | 1107.231 | 549.394 | 0.698 | Only row 0 |
| akshay3 | ORB + homography | 975.122 | 1103.573 | 516.950 | 0.803 | None |

The first two captures (`akshay.jpeg`, `akshay1.jpeg`) accuse no row in any
profile. The historical threshold of 2100 accuses no row in any profile of
either experiment. No other-recipient accusation is observed. Every full
1,000-score vector remains in the evidence, including failed profiles.

In the initial two-resampling experiment, akshay3 affine scores 1698.274
against 1106.594, while homography scores 847.622 against 1101.105. Thus the
content-similarity/decoding mismatch persists after removing the second
final-image resampling. The experiment does not establish its physical cause.

## Independent checks

The scoped reviewer verified all eight composed transforms, with maximum
residual 3.6e-15 for `ECC_inverse_warp @ composed = ORB`. ECC matrices and
coefficients match the initial experiment exactly; all ORB score arrays match
the previous baseline exactly. Input, source, helper and script hashes match.
All twelve 1,000-score arrays, summaries, strict accusation sets and stored
positive-theta threshold witnesses are internally consistent. No blocking
defect was reported. Review did not rerun image decoding or the self-checks.

The conditional bound still assumes independent innocent codewords given
biases and the capture/decoder. Public deterministic fixture keys, arithmetic
and real adversarial capture processes are not certified by these checks.
No empirical one-in-a-million wrongful-attribution claim follows.

## Next hypothesis, not a result

A recipient-blind alignment objective derived from the analytical expected
carrier, using shared biases and geometry rather than any recipient row or
an empirical roster average, has completed the
[design/prior-art audit](NISHAN_BIAS_SYNC_DESIGN_2026-09-10.md) and independently
reviewed synthetic implementation gates. All256 fixed synthetic translations
were recovered; this is not physical recovery evidence. The separate physical
preparation/scoring task has now produced
[physical results](NISHAN_BIAS_PHYSICAL_FINDINGS_2026-09-11.md): a stronger
akshay3 match, no new recovery, and two retained boundary failures. Its
independent implementation review is pending. Settings were frozen before
recipient scores. A synchronization/pilot construction must still be compared with
existing work before making any novelty claim.

The separate [symmetric parameter audit](NISHAN_SYMMETRIC_PARAMETER_AUDIT_2026-09-10.md)
supports an ideal-model 12,331-position candidate with a different symmetric
decoder. It is not a drop-in parameter change to the current asymmetric
decoder, an implemented finite-precision guarantee or a result on these
already printed pages.
