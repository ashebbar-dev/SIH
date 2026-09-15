# Compact carrier comparison — frozen pilot specification

Date: 12 September 2026. This is an isolated empirical carrier experiment, not a production change, novel fingerprint construction, or certified finite-precision implementation.

## Question and boundary

Does a known shorter symmetric fingerprint make a larger-feature PDF carrier worth testing through a real printer and phone? Compare spatially distributed repetition with larger blocks while holding nominal carrier area and overlay strength equal. Synthetic blur is a diagnostic, not a print/camera simulator or physical result.

Use the established symbol-symmetric score from Laarhoven and de Weger, *Optimal symmetric Tardos traitor tracing schemes*, Section 2.1 and Theorems 3–5: https://deweger.net/papers/%5B47%5DLdW-OptTTTS-DCC%5B2014%5D.pdf . Local ideal parameter audit: `research/NISHAN_SYMMETRIC_PARAMETER_AUDIT_2026-09-10.md`. Local precision assessment: `research/NISHAN_SYMMETRIC_PRECISION_BRIDGE_2026-09-12.md`. Neither certifies the current keyed generator. Retain its existing 53-bit/float64 bias and 32-bit Bernoulli mechanism for this empirical pilot only; do not claim the ideal theorem probabilities apply to measurements or noisy decoded words.

## Global constraints

- New implementation writes only `research/experiments/compact_carrier_v1/` and new run outputs only `research/evidence/nishan-compact-carrier-2026-09-12/`; all prototypes, submissions, existing evidence and `parallel_research/` are read-only.
- No dependency installation, network compute, git initialization, publication, deletion, or production integration. Use the existing `.venv` with `PYTHONDONTWRITEBYTECODE=1`.
- All authored edits use `apply_patch`. Generated experiment artifacts may be written by the implemented runner. Keep private run secrets out of terminal output and chmod their file to 0600.
- One fixed pilot run; no threshold, strength, transform or seed tuning after results. A failed run is preserved and reported, not overwritten. Destination must not exist before a new run.
- Every report says empirical, one source document, two issued copies per profile, no physical result, no probability certification, no collusion guarantee, no production attribution, and no novelty/superiority claim.

## Fixed profiles

Common roster size 1000, coalition design cap 5, DPI 144, overlay strength 4.0. Source is `artifacts/nishan/synthetic-source.pdf`, copied unchanged into the new run. Issue actual marked PDFs for rows 0 and 7 for each profile; all other rows are unissued candidates, not real recipients. Separate source and codebook commitments are retained.

| Profile | Logical positions | Carrier block | Repetitions | Physical placements | Nominal pixels | Fixed diagnostic threshold |
|---|---:|---:|---:|---:|---:|---:|
| original-6-r1 | 52500 | 6 | 1 | 52500 | 1890000 | 2100 |
| symmetric-6-r4 | 12331 | 6 | 4 | 49324 | 1775664 | 837.2843088602898 |
| symmetric-12-r1 | 12331 | 12 | 1 | 12331 | 1775664 | 837.2843088602898 |

Original configuration and scorer are unchanged `tardos.parameters()` / `tardos.accusation_scores`. Symmetric bias cutoff is `1 / 141.55`. Its threshold derives from `40.4*ln(1e9) + 0.098*(12331 - 595*ln(1e9))`. Build a separate empirical configuration using `dataclasses.replace`, record `theorem_certified: false`, and do not mislabel inherited original theorem-profile metadata. Use a fresh random codebook key for each of original and symmetric families, fresh common carrier key, fresh context UUID. Both symmetric profiles use the SAME biases and codebook; all three profile carrier contexts are explicitly distinct. Do not search for a favorable codebook.

For repeated embedding use `np.tile(logical_word, repetitions)`. Sum decoded floating-point correlations in `(repetitions, logical_positions)` order BEFORE deciding bits with strict `> 0`; no majority vote on thresholded bits. Symmetric scoring includes both output values:

`sum_i (2*y_i-1)*(X_ji-p_i)/sqrt(p_i*(1-p_i))`.

Check actual rendered capacities before embedding. Measure actual PSNR, text extraction equality, file size and preparation/embedding/decode/scoring time. Equal nominal area is not equal perceptual fidelity; report both.

## Fixed observation matrix

Render each of 6 issued PDFs at 144 DPI, then independently produce 5 observations from that clean rendering:

1. Clean RGB PNG.
2. JPEG quality 55, subsampling 0, no optimize.
3. Pillow GaussianBlur radius 1.0 PNG.
4. Pillow GaussianBlur radius 2.0 PNG.
5. Resize to half each integer dimension with LANCZOS then back to original dimensions with LANCZOS, PNG.

No geometry transform here: decode all diagnostic observations with `registration_mode="off"`, so registration cannot confound frequency/repetition. Produce the same five transforms of the unmarked source and score each under every profile. For each issued clean PNG also decode once with a fresh wrong carrier key and once with a wrong context, using normal codebook/scorer. Thus the expected matrix is 30 positive, 15 unmarked, 6 wrong-key, 6 wrong-context observations = 57. Assert identities and cardinalities, not only vacuous `all` calls. Every observation must retain selected rows, all 1000 raw scores in a binary artifact, score/threshold ratios, intended-row rank, other-issued maximum, unissued maximum, logical BER for positives, correlation summaries, and declared marking-condition violation diagnostics for the single participating source row. Save correlations and decoded bits for repeatable scoring. Negative BER is null, not a claimed random-bit test.

## Reproducibility, capture and decision

Before any observation is scored, save manifest with schema/profile versions, source hash, hashes of experiment and imported carrier/generator source, environment versions, profile configurations, fixed matrix, codebook/bias commitments, secret commitments and private replay-state hash. Save replay arrays and keys in a private 0600 file; keys never in public manifests. At end save all output artifact hashes in results (excluding results itself; its hash belongs in the controller report). Failures retain manifest and traceback. Use finite valid JSON: unavailable metrics null with a reason, never NaN/Infinity.

Provide `score_capture.py --run RUN --profile PROFILE --suspect PATH` that verifies replay-state and source commitments, uses exactly that profile and threshold, decodes with `registration_mode="always"`, and prints an explicitly empirical extraction JSON report with no identity verdict. It must not tune, write back into the run, or accept arbitrary code parameters. Missing/tampered replay state fails closed. Its registration mode differs intentionally from the controlled synthetic study and must be reported. It can be tested against the generated clean raster without calling that a physical test.

Write a physical-capture instruction file pointing to the three row-0 PDFs. Print at actual size with the same printer settings; photograph full page from the same distance and lighting, retain unfiltered original camera files, and identify the profile. Do not ask the user to send private replay state. No result can be reported until fresh images are actually supplied and evaluated.

Fixed advancement rule: both compact profiles must select only their intended row in both clean cases with unchanged text, and negatives must select no rows. Under those prerequisites, a profile is worth a fresh physical test if its intended-row score/threshold ratio exceeds original-6-r1 on BOTH issued rows in at least two of blur1, blur2 and half-resize, without extra selected rows on those winning cases. Compare the two compact profiles separately. This is a pilot prioritization rule, not a statistical significance or superiority test. Show all rows even if this rule fails; do not change the rule after seeing results. A completed test, including a negative result, is success for the experiment—not for the global SIH goal.
