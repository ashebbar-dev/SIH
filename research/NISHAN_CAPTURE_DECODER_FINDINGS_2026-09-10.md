# NISHAN capture-decoder findings — 10 September 2026

## Outcome

A known conditional-threshold baseline recovers the correct recipient on one
simulated white-background-cleanup case that the historical threshold misses.
With the existing source residual, correct-only recovery changes from **6/8 to
7/8 fixed conditions** on one public synthetic document and codebook. Every
condition scores all 1,000 rows; no additional rows are accused in this run.

This is useful development evidence, **not novelty, physical robustness,
production security or a measured rare-event false-accusation rate**. No
production carrier, decoder or decision threshold was changed.

## Reproduction and unchanged baseline

Runner: [probe_nishan_capture_channel.py](tools/probe_nishan_capture_channel.py).

- Original evidence: [fixed historical threshold](evidence/nishan-capture-channel-2026-09-10.json).
- Extended evidence: [conditional thresholds](evidence/nishan-capture-channel-conditional-2026-09-10.json).
- Source: `artifacts/nishan/synthetic-source.pdf`.
- Marked copy: `artifacts/nishan/tardos-user-0000-live-text.pdf`.

Both JSON files retain input hashes. All original per-condition scalar fields
and historical decisions in the extended run exactly match the original run;
the main agent and an independent reviewer checked this. The experiment uses
52,500 symbols, a 1,000-row roster, public fixture keys, 144-DPI rasterization,
6×6 carrier blocks and exact shared image geometry.

The eight conditions were fixed before the first run: identity, affine
brightness, gamma 1.5, white clipping at 250, binary thresholding at 200, and
Gaussian blur at three scales. They are repeated observations of one fixture,
not eight independent documents.

## What changed

| Existing source residual | Correct-row score | Highest other score | Historical threshold | Conditional threshold | Correct-only recovery |
|---|---:|---:|---:|---:|---|
| White clipping at 250 | 1374.907 | 152.593 | 2100 | 302.177 | No → yes |
| Binary thresholding at 200 | −53.198 | 141.104 | 2100 | 311.770 | No → no |

White clipping leaves 91.45% of carrier correlations exactly zero. Its lower
score does not imply the same innocent-score distribution as an intact copy.
The conditional baseline accounts for the surviving active symbols rather
than selecting a threshold using the known guilty row or the observed maximum
innocent score. All rows receive the same threshold.

Brightness and blur already recover the correct row at the historical
threshold; better signal metrics there are not additional attribution wins.

## Conditional-null calculation and limits

For fixed decoded word y and biases p, the calculation assumes each innocent
row remains a product of independent Bernoulli(q) variables after conditioning
on the capture and its preprocessing. Here q = floor(p × 2^32) / 2^32 matches
the generator's discretization under ideal uniform-word sampling. Merely
removing recipient labels is not enough to establish this independence.

For active symbols y = 1, score contributions are sqrt((1−p)/p) or
−sqrt(p/(1−p)). The script sums their exact log moment-generating functions
K(theta), then uses a positive finite numerical witness theta and threshold
(K(theta) + log(H/epsilon)) / theta, with a small positive padding and strict
score comparison. Empty active sets accuse nobody.

The modeled epsilon = 10^-6 is shared over H = 8 × 2 × 1,000 = 16,000
condition/profile/row hypotheses, not separately spent on each. Correlated
conditions do not invalidate that union bound under the stated null. It does
not cover an unbounded sequence of future captures or adaptive, row-dependent
decoder searches. This controls modeled soundness, not guaranteed recovery.

The public deterministic fixture does not itself establish the conditional
independence assumptions. Known-key framing and a malicious distributor fall
outside them. Numerical padding of 10^-9 is not an interval-arithmetic error
certificate. Neither this small run nor the theoretical model certifies a
deployed probability of wrongful attribution.

The root also enumerated all 256 rows of an eight-symbol toy code for three
active-word patterns and three error budgets; all nine exact-mass checks were
within the specified budget. This checks small-model arithmetic, not deployed
rare-event calibration. The independent reviewer verified all 16 recorded
finite witnesses and the absence of identity/score inputs to threshold
selection; it did not rerun the full diagnostic or toy enumeration.

Conditional thresholding and soft-output fingerprint decoding are established
prior art. Meerwald and Furon discuss thresholds conditional on the observed
fingerprint and bias sequence in Section III-C and soft watermark outputs in
Section V of [Towards joint decoding of Tardos fingerprinting codes](https://wavelab.at/papers/Meerwald11d.pdf).
The present Chernoff calculation is a stronger baseline, not an invention.

## Oracle profile: a diagnostic only

The runner also subtracts a source image passed through the **exact known
capture transformation**. A real investigator does not know that transformation.
Its conditional binary-threshold result recovers row 0, but the existing
source residual does not; reporting this as an available decoder gain would
be misleading. The oracle distinguishes source mismatch from signal erasure
and can motivate a separately tested channel estimator.

## Next evidence needed

Use independent documents, private independent codebooks, different recipients,
collusions, unmarked negatives and held-out real print/scan/photo captures.
Predeclare preprocessing and test-family budgets. Compare any candidate
estimator against this conditional baseline and relevant soft decoders at
matched visual distortion and attribution risk; preserve failure conditions.
The current dual-carrier printed-page request is a separate end-to-end test,
not a physical replication of this pure-Tardos fixture.
