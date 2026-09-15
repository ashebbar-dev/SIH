# SDD ledger — plan: docs/superpowers/plans/2026-09-12-nishan-auth-orthogonal.md

## Setup and preflight

Spec: `research/NISHAN_AUTH_ORTHOGONAL_SPEC_2026-09-12.md`. Prior Sol Ultra handoff recovered, not newly requested. No existing experiment directory or prior task ledger was found. Production and deck remain frozen.

Ruling: Start with carrier falsification, not a recipient/adjudicator protocol — copied-overlay failure could invalidate the premise cheaply; a one-process harness cannot prove key separation — costs one limited experiment before any stronger protocol evaluation.

Ruling: Use a fresh research/evidence directory and non-Git snapshots/hashes; do not initialize Git or delete evidence — the workspace has no repository and historical artifacts belong to the user — costs disk space and manual rather than commit-based recovery.

| Check | Producer/consumer or internal agreement | Finding |
|---|---|---|
| Task 1 internal | Four files; carrier functions consumed only by runner/tests; fixed CLI and evidence destination consistent | No conflict |
| Task 1/spec | Two sources, five rows each, eight transforms each/channel, fixed exact threshold, negative and observed-copy attacks | Covered; outcomes recorded even if failure |
| Task 1/frozen release | Reads NISHAN helpers; does not write prototype or presentation | No shared writable interface |
| Implementation/research review | Independent literature agent writes one separate report only | No shared implementation state |

Preflight tooling: `sdd-workspace` returned no-Git error as expected; `task-brief` succeeded. `before.tar.gz` preserves source/deck inputs; `frozen-inputs.sha256` pins all NISHAN modules, PPTX/PDF, old fixture, spec and plan. Placeholder scan returned no matches.

Task 1: dispatched to `/root/auth_carrier_study` (gpt-5.6-sol, high). Read-only primary-source review dispatched separately to `/root/auth_prior_art`.

Task 1 progress: implementer reports RED (`ModuleNotFoundError: No module named 'carrier'`), then GREEN (8/8 tests, 2.349s). First prescribed full study `run-01` started after confirming that output path was absent. These are worker updates, pending report/diff review; no scientific outcomes accepted yet.

Expected accounting before execution: 16 positive auth artifacts, 44 participating and 36 other-issued candidate decisions; 60 baseline/unmarked, 6 changed-context and 200 wrong-key negative decisions; copied-overlay PDF and JPEG each evaluated against 5 candidates plus changed-source context (12 observations). Complete Tardos scoring on 32 matched positive artifacts plus 2 copied-overlay artifacts. Counts are correlated observations, not independent trials or a false-attribution bound.

Primary-source review complete: `research/NISHAN_AUTH_ORTHOGONAL_PRIOR_ART_2026-09-12.md`. Controller independently opened asymmetric Tardos (2010) and Deguillaume/Voloshynovskiy/Pun hybrid watermarking (2002). The former needs protocol-level control of embedding and accusation state; the latter already separates robust identity and content-authentication channels and rejects copy attacks. This finite search does not establish patentability or implementation equivalence. Important interpretation: rejecting a changed candidate context is not the same as verifying the content of an edited artifact presented under the donor's genuine context. The planned observed-overlay attack measures the latter distinction. No run results yet.

Review workflow fallback: the generic `requesting-code-review/code-reviewer.md` is absent in this environment; final review will use the fully read task-review rubric expanded to the entire isolated experiment and its claims. No production suite rerun is needed while its hashes remain unchanged.

Task 1: implementer DONE_WITH_CONCERNS. Sole run completed in 114.054313s; Gate A true and Gate B false. Concerns are scientific boundaries (marking-condition violations) and retained runtime caches, not reported code failures. Full four-file new-source diff and source snapshot saved. Task-scoped review dispatched to `/root/auth_study_review` (Sol high).

Controller artifact checks: all 97 run-relative artifact hashes pass (after correcting an initial checksum-command cwd error); all 10 study/import code hashes pass; all 21 frozen baseline entries pass. Attack JPEG visually confirms the first line changed quantity 120 to 920, while machine results retain exact donor tag and Tardos row 0. No keys displayed or exported. Draft decision memo written outside production/submission, pending reviews.

Task 1: complete (no Git; snapshot `task-1-reviewed-source.tar.gz`; Spec PASS, Task Quality Approved; no Critical/Important findings).

Task 1: minor (deferred): report's phrase “Both 0/2” is awkward; counts and conclusion are unambiguous in the machine data and decision memo.
Task 1: minor (deferred): orientation test uses identity Tardos order; implementation was checked against the true symbol-indexed dependency contract but future permutation-regression coverage should improve.
Task 1: minor (deferred): gate aggregation does not independently assert cardinalities; reviewer recomputed all leaf counts and confirmed the sole run is complete.
Task 1: minor (deferred): dynamic changed_source_hash state and unused other_source_hash local are maintenance cleanup.

Cannot-verify items resolved within scope: this is a locally witnessed engineering run, not independent proof of entropy, an immutable history of every possible invocation, or proof of no transient edit-and-restore. The actual reported RED/GREEN and run output, file/source hashes and preserved results support the limited statement made. Subjective fidelity, physical recovery and protocol-level claims remain explicitly unestablished. No spec gap requires a fix wave.

Final review: `/root/auth_study_final_review` (Astra high), Spec PASS and Quality Approved. No Critical/Important findings. All four deferred issues independently triaged as Minor. One additional Minor: decision memo calls the 97 artifacts “manifest-listed”; their hash map is actually `results.json.generated_artifact_sha256`. The correctly located command and full successful check are in `artifact-hash-check.txt`. No fix wave or study rerun warranted for the declared one-run research scope.

Plan complete. Final tracking edits only mark checkboxes and update the decision memo's review status; the initial frozen plan remains in `before.tar.gz`, and scientific spec/profile, implementation, results, prototype and deck are unchanged. Evidence retained under the no-Git ruling; no deletion or publication. Overall SIH novelty/superiority/winning goal remains unachieved.
