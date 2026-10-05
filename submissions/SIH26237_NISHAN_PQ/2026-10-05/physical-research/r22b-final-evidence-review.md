# R22B final evidence review

## Verdict

**ACCEPT as bounded negative evidence.** I found no material inconsistency in the frozen clean or physical evidence at commit `952e268f4f5e90c85e18dead467e2ca4a30b7de0`.

The six-row clean gate is complete and passes exactly as required: all four marked rows decode the expected identity/session exactly, and both controls abstain. The corresponding 24-row physical replay is also complete, with 16 marked rows and eight controls, no dropped case, and a zero process exit for every child. Its outcome is negative: **0/16 marked rows decode exactly**, while **8/8 controls abstain**. The raw-bit changes are diagnostically meaningful but do not establish a physical gain or success.

This acceptance is limited to the recorded known-image development component ablation. It does not establish a faithful CoreMark reproduction, a general false-positive rate, held-out performance, physical robustness, collusion resistance, content authentication, or any production/security guarantee.

## Scope and review basis

I reviewed, for both `cm-paper-r22-clean-v1` and `cm-paper-r22-physical-v1`:

- `evaluation.json`
- `run-manifest.json`
- `vector-freeze.json`
- `runner-events.jsonl`
- focused result-record fields needed to distinguish process completion, producer abstention, truth inputs, and raw-vector cardinality

I also relied on the completed source/controller reviews:

- `r22-source-and-controller-fix-review.md`, which accepted the source changes and identified two residual controller issues;
- `r22-controller-fix2-review.md`, which verified that the resolved clean-evaluation path/hash is retained and rechecked and that controller hashes are verified immediately before each individual launch, closing the final two Important findings with no new Critical/Important breakage.

This was an evidence review, not a new source review or experiment. I did not run images, suites, or producers. The coordinator had already checked all recorded file bindings with `sha256sum --check` and reported exit 0; I used that byte-binding result rather than repeat it.

## Clean gate and physical authorization

The clean manifest, freeze, evaluation, and event log contain the same six unique cases:

- marked: `clean-reservoir-A`, `clean-reservoir-B`, `clean-orchard-A`, `clean-orchard-B`;
- controls: `clean-reservoir-control`, `clean-orchard-control`.

There are six starts and six matching completes, all with child exit 0. All six focused producer records have `status: complete`, contain 152 raw bits, carry the frozen commit, leave associated identity/session null, and report no expected-bit, expected-identity, route, or registry-content input.

The clean evaluation reports `clean_gate_passed: true` and `physical_execution_authorized_by_this_report: true`. Its four marked rows are 4/4 exact with matching expected/decoded 72-bit tag hex and 608/608 correct raw bits; its two controls are 2/2 `abstain_pilots`. There are no wrong accepted rows.

The physical manifest records the resolved authorizing report as:

`cm-paper-r22 / outputs / cm-paper-r22-clean-v1 / evaluation.json` (logical origin; local absolute path omitted in this public derivative)

with SHA-256 `4a17639dcf6316ecbd4d08950727c66b0914b0af8f5a3283b5bf6947296ad0f5`. Its authorization also binds the exact six case IDs, clean measurement-manifest hash `52e3fcacc70627e024f60cfc282f4085b8332508cd00fa1cda971b600a21e9f4`, clean vector-freeze hash `34466aaaa8a3a45be0724d6a4f46daf27e938c7fac40fb3ec3a475a7cb515046`, clean vector-row hash `b5c90276f4c56f06eeffa201e47cfad30007afe36df62b8f084ce9ca167546cd`, controller-set canonical hash `53956e5e9a5fd1440ceda111d6f2d329b173a6b8e72ae8dcf0baa50712d1499f`, and tracked-source canonical hash `990c8cf14293a3930507716d0efda174db57b6a6f6ebed381437b4f6876ab84f`.

The physical evaluation's own `clean_gate_passed` and `physical_execution_authorized_by_this_report` fields are false because it is not the authorizing clean report; the clean authorization is instead carried by its measurement manifest. That is not a contradiction with the recorded authorization path above.

## Completeness, joins, and bindings

For each phase, the case sets in the manifest, vector freeze, evaluation, start events, and complete events are identical and unique. The clean bundle has 6 rows/6 starts/6 completes; the physical bundle has 24 rows/24 starts/24 completes. There are no duplicate starts or completes, and every complete event records exit 0. Evaluation result hashes agree per case with the corresponding vector-freeze result hashes.

The physical cohort is the full balanced set of six capture identities (`01`, `04`, `05`, `06`, `07`, `08`) across four routes (`normal`, `scanner`, `tilted`, `whatsapp`): 24 rows total. Truth mapping marks cases `04`, `05`, `07`, and `08` (16 rows) and treats `01` and `06` as controls (8 rows). No row is omitted after either producer abstention or packet abstention.

At the producer-record level, physical status is 21 `complete` and three `abstain_upstream_geometry` (`01-tilted`, `05-tilted`, and `07-tilted`). All three upstream abstentions are retained as 152-erasure vectors and remain in the manifest, freeze, evaluation, and event log; their processes exited 0. Thus “all child exits zero” means no process failure, not that every producer reached extraction.

The clean and physical bundles agree on:

- commit `952e268f4f5e90c85e18dead467e2ca4a30b7de0`;
- tracked-source canonical SHA-256 `990c8cf14293a3930507716d0efda174db57b6a6f6ebed381437b4f6876ab84f`;
- runner `fad5b9485ccd32a7b9901f7d8bdb1391e8c4569aa7f5d5c48012a7cb4a9dc513`;
- evaluator `af3afca47ad2c757a4b6f5e9e1d4fa889cb176950c932c5f7ffbc0484c817544`;
- `measure_child.py` `0a1a61233dae35b539d7a30c94f2e29043ca838d76c09450d145c886b8a71753`;
- resource guard `67e153f6a1dd0eaa36665857798980be3176713ccf8e689420e52571b11e1054`;
- frozen R21 roots: manifest `f2a4f02b4cab8440bfa539305eabed7be3a12eb8d54972d4a3f3777cef7ca56c`, evaluation `a44fabf1240b722758e0dd9179a38a68f16217506d26474e614843b4f62c9075`, and execution audit `cf4fe23b091ae4f8c2d39c77ade43ac0b2812dee0f5a43662361a19dda0247aa`.

The physical manifest hash is `1bdc58157dca88bf2bede39909b6cad329d6824d06d5e72474c5083bcccaa581`; it is repeated by the physical freeze and evaluation. The physical freeze is `604cfb6728b01781bf3d43490e2b40b58fb11ccbae90a204ba567b9a2307dad6`, with row hash `f9578cb7916ee7d8e5ac6eea24cbcedd32a12facd0d644757d5aad018a9e563b`. The coordinator's byte check records the final physical evaluation as `dee3f2cb83fb285f711945a104736112fcb3a5afa371b08238f2e8b8d404aa97`.

## Freeze and later truth join

Both manifests exclude truth fields and state that expected identity was not passed to the producer. The focused result records confirm null associated identity/session fields and false expected-bit, expected-identity, route, and registry-content inputs. Both freezes state `completed_before_truth_join: true`; both evaluations state `vectors_frozen_before_truth: true` and `truth_mapping_loaded_after_freeze: true`.

This ordering is accepted as **checked-code evidence plus internally consistent saved assertions**, not as an independently witnessed historical chronology. The prior controller review statically verified that the evaluator writes the freeze before parsing the truth-bearing/R21 records and that the producer cannot receive the excluded truth fields. There is no separate historical observer or external timestamp attestation, so the evidence should not be described more strongly than that.

## Physical result and denominator audit

The physical evaluation reports:

- 16 marked rows, **0 exact**, 0 wrong accepted tokens, and 0 fully compatible marked raw vectors;
- 8 controls, **8 abstentions**;
- packet status `abstain_pilots` on all 24 rows; every marked decoded tag is null;
- raw denominator `16 × 152 = 2,432` marked bits, with no successful-row filtering.

The aggregate arithmetic recomputes from all 16 marked rows without discrepancy:

| Metric | Frozen R21 comparison | R22B | Interpretation |
|---|---:|---:|---|
| Correct bits / 2,432 | 519 | 1,354 | More bits are classified correctly, but no token decodes |
| Erased bits | 1,737 | 456 | Many prior erasures become observations |
| Observed bits | 695 | 1,976 | Coverage changes from 28.58% to 81.25% |
| Accuracy among observed bits | 74.68% | 68.52% | Conditional accuracy decreases |
| Correct fraction over full denominator | 21.34% | 55.67% | Diagnostic fraction only; not an exact-recovery result |

The transition totals are also consistent: 836 prior erasures become correct, 445 prior erasures become wrong, 456 remain erased, 509 prior correct bits remain correct, 10 correct bits flip wrong, 9 wrong bits flip correct, and 167 wrong bits remain wrong. These totals account for the full denominator and explain why fewer erasures coexist with worse conditional observed accuracy.

Accordingly, the defensible result is a bounded negative one: the fixed-axis/hard-reference component exposes substantially more bits on these existing development captures, but still recovers **no complete marked physical token**, and the newly observed bits are noisier. This is not evidence of a physical gain, much less physical robustness.

## Claim boundary

The artifacts themselves set `faithful_coremark_reproduction`, `held_out_evaluation`, `physical_robustness_established`, `physical_success_claim`, `collusion_resistance_established`, and the remaining security/production claims to false. The manifest labels the run a “known-image development component ablation; not held-out.” Those limits are supported by the evidence:

- 8/8 control abstentions describe only these eight retained control captures; they do not estimate a general false-positive rate.
- The test isolates a CoreMark-inspired component on inherited pixels/support and is not a faithful CoreMark implementation claim.
- No collusion experiment or adversarial population is present.
- No exact marked physical recovery occurred, so no success or robustness claim is available.

## Material inconsistencies

**None found within the bounded review scope.** The evidence supports retention of R22B as a complete, hash-bound, negative development-set component result, subject to the claim limits above.
