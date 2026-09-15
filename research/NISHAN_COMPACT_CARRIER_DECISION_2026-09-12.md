# Compact carrier pilot — decision and limits

12 September 2026. Implementation and one run are complete; independent task/final reviews are pending. Do not promote this pilot into production.

## Decision

**Prepare a fresh matched print/camera check, prioritizing the larger-block compact profile. No physical improvement has yet been demonstrated.** Both compact profiles passed the frozen synthetic advancement rule. The rule is a prioritization device, not a significance test or certified false-accusation comparison.

The experiment uses one synthetic source PDF and two actually issued rows per profile. All 1,000 codebook rows were scored in each of 57 observations. All 30 positive observations selected exactly the intended row, including all original-baseline observations; all 27 negative observations selected none. Therefore there is **no observed improvement in attribution success count** in this pilot.

## What changed and what was matched

The two compact profiles share the same 12,331-position symmetric codebook. One repeats each bit in four dispersed 6×6 blocks; the other uses one 12×12 block. Both occupy 1,775,664 nominal pixels at strength 4. The original comparator uses 52,500 6×6 blocks, occupying 1,890,000 nominal pixels. All are rendered at 144 DPI. This changes code/scorer/carrier allocation relative to original, not the roster size or nominal coalition design cap.

The symmetric construction is established prior art, not our invention. The current keyed sampler is not certified against the ideal theorem. No theorem probability or noisy-channel collusion guarantee is imported into these results. [Primary symmetric-code paper](https://deweger.net/papers/%5B47%5DLdW-OptTTTS-DCC%5B2014%5D.pdf).

## Measured results

Ranges span the two issued rows; they are not confidence intervals.

| Profile | JPEG Q55 logical bit error | Blur radius 2 logical bit error | PDF PSNR |
|---|---:|---:|---:|
| Original 6×6 | 10.02–10.23% | 5.20–5.23% | 41.868–41.870 dB |
| Compact, four 6×6 placements | 2.51–2.53% | 15.28–15.34% | 42.137 dB |
| Compact, one 12×12 placement | 0.99–1.01% | 5.38–5.51% | 42.140–42.142 dB |

The larger compact carrier had lower bit error than the repeated compact carrier in the tested non-clean transformations. It did **not** improve blur-radius-2 BER over the original; the repeated compact carrier was substantially worse there. Score/threshold ratios alone should not hide those results, and ratios from different scorers are not calibrated confidence values.

Extracted text was unchanged in all six PDFs. A visual inspection of the larger-block clean rendering found readable text and a faint background texture; this is not a blinded invisibility assessment. Preparation timings and output sizes are recorded, but one sequential run does not establish a latency benchmark. The full pilot took 127.543 seconds; focused tests passed 10/10. A separate read-only capture-CLI smoke test recovered row 0 from a generated clean raster with registration enabled; it is not a physical capture.

## Reproducibility

- [Frozen specification](NISHAN_COMPACT_CARRIER_SPEC_2026-09-12.md).
- [Implementation report](evidence/nishan-compact-carrier-2026-09-12/task-1-report.md), including actual RED/GREEN output and all condition results.
- [Raw results](evidence/nishan-compact-carrier-2026-09-12/run-01/results.json), committing 102 run-completion artifacts. SHA3-256: `6551658be185470954dc3a14238a5e72c6f14496de7abace9194e3f75ec7583b`.
- [Capture instructions](evidence/nishan-compact-carrier-2026-09-12/run-01/physical-capture-instructions.md). Private replay keys stay local and must not be shared.
- [Numerical precision research note](NISHAN_SYMMETRIC_PRECISION_BRIDGE_2026-09-12.md): conditional proposed bridge, not implemented certification.

No threshold, transform, strength or seed was changed after viewing outcomes. No existing prototype or submission file was edited. This is an empirical single-document, two-issued-copy-per-profile experiment with no physical result, probability certification, collusion guarantee, production attribution, novelty claim or superiority claim.

## Relationship to the new GPT-6 Pro lead

Its N1 proposal keeps all 52,500 positions and compares global versus local soft receivers on identical embedded pages. This pilot does not pass that requirement and does not claim to. It supplies a separately named carrier-allocation comparison and fresh original-profile controls. Review of that proposal is in [the NISHAN receiver assessment](GPT6_PRO_NISHAN_REVIEW_2026-09-12.md). Both lines need fresh physical measurements before stronger claims.
