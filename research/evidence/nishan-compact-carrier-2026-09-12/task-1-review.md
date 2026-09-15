### Spec Compliance

- ❌ Issues found. The symmetric scoring kernel and repetition collapse follow the prescribed formulas (`research/experiments/compact_carrier_v1/profiles.py:133`, `research/experiments/compact_carrier_v1/profiles.py:160`); the runner constructs and validates the exact 57-case matrix (`research/experiments/compact_carrier_v1/run_study.py:54`, `research/experiments/compact_carrier_v1/run_study.py:331`); and the frozen advancement comparison is correctly gated and evaluated per profile, transform, and both issued rows (`research/experiments/compact_carrier_v1/run_study.py:383`, `research/experiments/compact_carrier_v1/run_study.py:450`). However, replay does not fail closed on missing commitment sections, twelve controls omit required marking-condition diagnostics, early failures can lack a manifest, and the required matrix-identity test is incomplete.
- ⚠️ Cannot verify from diff: test-first authorship, use of `apply_patch` for every authored edit, absence of dependency/network/git/publication activity, and the claims that the destination was initially absent and the pilot was run only once without post-result tuning. The controller should check retained command/session evidence for these process requirements. The supplied public run data does verify 57 unique identities, the reported 30 positive and 27 negative selection outcomes, the stored advancement winners, result SHA3-256, and replay-state mode; it cannot prove the historical one-run/no-tuning claims (`research/evidence/nishan-compact-carrier-2026-09-12/task-1-report.md:82`).

### Strengths

- The numerical kernels preserve the required ordering: physical words are whole-word tiled (`research/experiments/compact_carrier_v1/run_study.py:572`), analog correlations are reshaped and summed before a strict-positive decision (`research/experiments/compact_carrier_v1/profiles.py:160`), and symmetric scores include both output symbols (`research/experiments/compact_carrier_v1/profiles.py:133`).
- The manifest is written before the observation-scoring loop in a successful run, and completed observations are checked against the declared identities rather than only counted (`research/experiments/compact_carrier_v1/run_study.py:722`, `research/experiments/compact_carrier_v1/run_study.py:750`).
- Capture replay uses the frozen profile, validates the normal run's source/replay commitments before decoding, forces `registration_mode="always"`, and emits a null identity verdict (`research/experiments/compact_carrier_v1/score_capture.py:33`, `research/experiments/compact_carrier_v1/score_capture.py:55`, `research/experiments/compact_carrier_v1/score_capture.py:92`).
- The documentation and report state the empirical scope and all required limitations: one source, two issued copies per profile, no physical result, probability certification, collusion guarantee, production attribution, or novelty/superiority claim (`research/experiments/compact_carrier_v1/README.md:25`, `research/evidence/nishan-compact-carrier-2026-09-12/task-1-report.md:217`).
- Focused read-only result recomputation found 57 unique identities, 30/30 positives selecting only the intended row, 27/27 negatives clear, advancement winners matching the stored result, SHA3-256 `6551658be185470954dc3a14238a5e72c6f14496de7abace9194e3f75ec7583b`, and replay mode 0600 (`research/evidence/nishan-compact-carrier-2026-09-12/task-1-report.md:92`, `research/evidence/nishan-compact-carrier-2026-09-12/task-1-report.md:156`). The supplied 10-test GREEN output is pristine (`research/evidence/nishan-compact-carrier-2026-09-12/task-1-report.md:60`).

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- `research/experiments/compact_carrier_v1/profiles.py:210` and `research/experiments/compact_carrier_v1/profiles.py:258`: source and family commitment sections are optional during replay validation. A manifest without `source` reaches `np.load`, and a manifest without `families` skips bias/codebook commitment checks entirely, violating the fail-closed and validate-before-private-load requirements in `research/NISHAN_COMPACT_CARRIER_SPEC_2026-09-12.md:51`. A focused test with a valid replay-file hash, no source section, and a patched loader printed `NPZ_LOAD_REACHED`, confirming private loading occurs first. Require and validate both sections (including the frozen source path and both family entries) before calling `np.load`; reject missing or malformed data.
- `research/experiments/compact_carrier_v1/run_study.py:292` and `research/experiments/compact_carrier_v1/run_study.py:319`: marking-condition diagnostics are computed only for `kind == "positive"`; all negatives receive the reason "no participating source row." The 12 wrong-key/wrong-context cases do have declared source rows 0 or 7, so they omit the required single-participant diagnostics and the reason is false. The report repeats the false generalization at `research/evidence/nishan-compact-carrier-2026-09-12/task-1-report.md:119`. Keep negative BER null as specified, but compute `marking_condition_errors(logical_word, codebook[[row]])` whenever `row is not None`; reserve the no-participant reason for unmarked cases and correct the report.
- `research/experiments/compact_carrier_v1/run_study.py:722` and `research/experiments/compact_carrier_v1/run_study.py:799`: the manifest is not created until after source copying, key/codebook generation, capacity checks, six embeds, rendering, and transformations. Any exception in those stages writes only `failure.json`, despite the binding requirement that failures retain both manifest and traceback (`research/NISHAN_COMPACT_CARRIER_SPEC_2026-09-12.md:51`). Ensure the failure path also creates a schema-valid failure manifest containing all available frozen configuration/commitments and explicit null-with-reason entries for unavailable values, while preserving the original exception.
- `research/experiments/compact_carrier_v1/test_profiles.py:119` and `research/experiments/compact_carrier_v1/test_profiles.py:126`: the purported identity test asserts only uniqueness, total count, and per-kind counts. It would pass if a profile, issued row, or transform name were replaced consistently, so it does not satisfy the explicitly required fixed matrix identity test (`research/evidence/nishan-compact-carrier-2026-09-12/task-1-brief.md:17`). Compare the produced identity set to an independently constructed literal/product expected set containing the exact three profiles, rows, transforms, and negative-control identities.

#### Minor (Nice to Have)

- None.

### Assessment

**Task quality:** Needs fixes

**Reasoning:** The saved scores and advancement conclusions are internally consistent and the core numerical implementation is correct, but replay integrity and required evidence behavior have merge-blocking gaps. The missing control diagnostics and incomplete identity regression test also leave the frozen empirical contract only partially implemented.
