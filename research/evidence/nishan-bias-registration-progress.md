# SDD ledger — plan: docs/superpowers/plans/2026-09-10-nishan-bias-registration.md

Previous goal turn classification: progress — the corrected Dhruva real
diagnostic completed, its task review started, the single-resampling physical
NISHAN control was documented, and the shared-bias design/prior-art audit was
completed. No blocking condition is active.

## Task state

Task1 is handed off by `/root/nishan_bias_registration` (gpt-6-astra, high
reasoning), with brief `nishan-bias-registration-task-1-brief.md` and report
`nishan-bias-registration-task-1-report.md`. Independent review by
`/root/nishan_bias_registration_review` approves spec and quality with no
findings; package `nishan-bias-registration-task-1-review.diff` includes all
four new files. Task2 may now execute the fixed physical experiment.

The one frozen full synthetic run (session15398) completed in553.164s:
256/256 exact shift recoveries,8/8 renderer cases, toy null, composition,
independence and erasure gates pass;13 focused tests pass. Source-only
positive objective peaks and wrong-geometry boundary failure are retained
concerns, not recipient evidence. All73,984 recovery-candidate records and
all controls remain in the fresh evidence directory. No gate tuning or
source correction occurred during the full run.

Task1: complete (new-file snapshots, independent spec and quality review clean).
Reviewer independently checked all7 dependency/code hashes, manifest and
array/results linkage, all256 unique cases and73,984 candidates, null and
control records. Original-PDF response remains Task2's responsibility, not
something the synthetic raster-source gate already proves. The action record
and retained prior hashes support preservation; the new-file diff alone
cannot prove unrelated historical state.

Task2 was implemented by fresh implementer `/root/nishan_bias_physical`
(gpt-6-astra, high reasoning), with the extracted Task2 brief and separate
Task2 report. Its scope is the process-boundary runner/tests and fresh physical
evidence only. The reviewed Task1 code and old physical evidence remain fixed.
Eight focused tests pass; the one prepare and one separate score process
completed without retry. All four affine baseline matrices and1000-score
vectors match retained controls exactly. Akshay3 attribution is retained;
akshay2 remains below threshold; two bias profiles hit boundary failures.
No other row is accused. Independent Task2 review completed in
`/root/nishan_bias_physical_review` using the complete three-file package
`nishan-bias-registration-task-2-review.diff`.

Task2: complete (new-file snapshots; independent spec and quality gate approved).
Reviewer verified all30 array digests, six words/correlation vectors, four
289-candidate surfaces, six1000-score vectors, both failure records, and every
recorded code/input/source hash. Root's run/milestone history supports the one
prepare and one score invocation; no reviewer repeated either experiment.
The commitment remains local and unsigned; its chronology is an action-record
claim, not external authentication. Broader scientific/security claims are
outside the task gate and remain unestablished.

Task2: minor (deferred for final triage): missing prior evidence file aborts
`load_prior_baselines()` at script line278 rather than emitting missing_prior
records. The required prior exists and matches its recorded hash in this run.
Final whole-plan review must assess this caveat; current results are unaffected.

Final whole-plan review by `/root/nishan_bias_registration_review` approves
the fixed experiment with no Critical/Important issues. It confirms all
cross-task hashes/interfaces and all eight outcomes without rerunning tests
or experiments. The missing-prior caveat is accepted for deferral; the only
new finding is stale review-status wording in the physical findings note.
A single documentation-only final fix wave will update related status notes
and document the reuse caveat without changing hash-bound experiment code.

Ruling: defer missing-prior-file structured failure handling for this frozen run — the required prior exists, its hash and all comparisons pass, and final review recommends preserving the hash-bound code — cost: a future reuse without that file aborts instead of writing missing_prior records; add handling and a focused test before such reuse.

## Preflight

| Interface/task | Agreement check | Result |
|---|---|---|
| Task1 response→search | Actual endpoint expectation and fixed blur | Native renderer gate prevents unverified fractional-alpha shortcut |
| Task1 search→Task2 | Bias/image inputs only and explicit failure states | No score-based fallback or boundary expansion |
| Task1 gates→Task2 | Hash-bound successful gates before physical use | Failed scientific gate is retained evidence, not permission to tune |
| Task1 tests→code | Small unit suite separate from full256-case experiment | All conditions fixed, heavy run once per source revision |
| Task1 capture→Task2 baseline | Warp original RGB8, then luma | Arithmetic ordering preserved rather than confounded with geometry |
| Task2 prepare→score | Separate processes with hashed words/transforms | Roster is available only after preparation completes |

Ruling: retain snapshots/reports instead of Git worktrees/commits — initialization is reserved — cost: no commit-based recovery.

Ruling: use a zero-row view of the unchanged keyed generator for bias-only access — avoid copied cryptographic logic and recipient-row generation — cost: relies on current zero-length generation behavior, covered by a focused equivalence test.

Ruling: first test the bounded global translation model rather than expanding to local warps — isolate the proposed objective on known initial geometry — cost: cannot establish recovery from page curvature or larger alignment errors.

Ruling: require fixed synthetic gates before physical scoring — prevent an unverified response/geometry model from being selected by known-recipient outcomes — cost: a gate failure delays physical testing and may require a separately specified model.

Ruling: fix additional controls at shift(+1,0), near-white255 with nearest4-level quantization, clipping>=250 on255-source endpoints, a source-only one-pixel black line atx120, independent wrong geometry and unquantized shared-only expectation — close unspecified nuisance details before construction;245-source clipping would not erase the carrier — cost: results cover only these fixed nuisance constructions. Baseline words on abstained controls are diagnostics, never successful decoder outputs.

Ruling: compare prior affine-baseline matrices/scores only after the new preparation commitment — prior JSON includes recipient scores and must stay out of registration — cost: a baseline mismatch is detected after preparation rather than before it. Hard-decoder float32 arithmetic remains unchanged while the registration objective uses float64.

## Final completion

Final fix wave: documentation only, implemented by `/root/nishan_bias_final_docs`
(gpt-5.6-luna, medium), package `nishan-bias-registration-final-docs-fix.diff`.
Scoped re-review `/root/nishan_bias_docs_rereview` (gpt-5.6-sol, medium)
approved the status corrections and accurate deferral language, with no new
breakage or changed numerical/scientific claims. Runner, commitment and score
hashes remain unchanged. No tests or experiments were repeated for this fix.

Plan: complete — both task gates and final whole-plan review approved;
one nonblocking robustness caveat remains explicitly deferred. The frozen
physical result is negative for additional recovery and is retained as such.
Keep every snapshot/report/evidence artifact: no Git recovery exists and no
deletion or commit is authorized. The broader SIH novelty/performance goal
remains active and has not been achieved by this experiment.
