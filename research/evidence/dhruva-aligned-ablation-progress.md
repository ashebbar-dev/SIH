# SDD ledger — plan: docs/superpowers/plans/2026-09-10-dhruva-aligned-ablation.md

Previous goal turn classification: progress — four physical NISHAN captures
tested, one new correct-only recovery independently checked, and timestamp
loader final review/fix completed. No blocking condition is active.

## Task state

Task 1 implementation was handed off by `/root/dhruva_aligned_ablation`
(gpt-5.6-sol, high reasoning). Existing time_alignment.py is reviewed and
unchanged input to this task. The unexecuted NISHAN tone plan is not part of
this workspace or task. Independent task review completed in
`/root/dhruva_aligned_task_review` (gpt-5.6-sol, high reasoning); final review
and its report-format fix are also complete, as recorded below.
Review package: `dhruva-aligned-ablation-review.diff`.

The first real diagnostic invocation failed at the direct-script import of
`prototypes`, before any output directory was created. The implementer is
fixing the entry-point import path and rerunning focused tests; the next real
attempt uses the fresh `dhruva-aligned-2026-09-10-2` output directory. This is
an implementation failure, not a data result; preserve its report. That
correction succeeded: the only fitted/evaluated run has 400 candidates,
370 valid windows and 13 methods. Full exact red/green transcripts and all
results are in `dhruva-aligned-ablation-implementation.md`; 10 tests pass.

Root independently checked the current manifest, runner, legacy benchmark,
alignment module and all eight raw data hashes against the manifest. All
match. Review is now complete; reuse must preserve the reference-assisted,
development-data and reference-quality limitations documented below.

Ruling: use retained new-file snapshots and reports instead of Git worktrees/
commits — initialization remains reserved — cost: no commit-based recovery.

Ruling: test60s outages with12 prespecified factorial branches plus a constant
baseline — isolate the measured60s issue first — cost: no claims for other
outage durations from this diagnostic.

Ruling: retain explicitly privileged reference initialization/calibration and
use matched left-endpoint integration — isolate errors before implementing a
deployment path — cost: improved numbers still require deployment-valid tests.

## Preflight

| Task/interface pair | Agreement check | Result |
|---|---|---|
| Task1 loader→manifest | Raw provenance and clock spans | Duplicate rows and gap/cadence exclusions explicitly covered |
| Task1 manifest→13methods | Common window IDs and initialization | Intentional reference-heading duplicate controls, no method-specific exclusions |
| Task1 tests→integrator | L+1 times and L left-endpoint samples | Explicit elapsed-time and heading tests; straight fixture corrected to600m per60s |
| Task1 training→evaluation | First40% S1 time and bracket limits | Refit/changed windows disclosed, not a single-variable comparison to old18.342% |

No independent code tasks share files; the current NISHAN worker only audits
theory and writes its own research note.

## Task review and evidence fix

Task review found no numerical/source-code defect. It raised Important: the
authoritative new-file snapshot omitted the separately supplied required
implementation report. Minor: focused-test transcripts had matplotlib cache
warnings. Original implementer completed an evidence-only fix: one clean
10/10 focused run with writable MPLCONFIGDIR and retained original successful
fit tool identifiers/output. No real diagnostic rerun or source change.

Supplemental package `dhruva-aligned-ablation-evidence-fix.diff` adds the
report's complete new-file hunk; the original runner/test snapshot is retained.
Scoped re-review approved both findings. Root's raw/source-hash checks resolve preservation
within this scoped task; action history shows no Git/install/firmware/network
mutation by the worker. The original successful session was78308, completed
chunk f39423; this provenance is retained in the report rather than inferred
solely from generated results.

Task1: fix round1/5 (2 addressed,0 open — report snapshot and clean test evidence; no source-code changes).

Task1: complete (new-file snapshots instead of commits, task review clean).

Final whole-change numerical/source review passed in
`/root/dhruva_aligned_final_review` (gpt-6-astra, high reasoning). Independent
recomputation confirms all52 sequence/method aggregate groups,5200 CSV rows,
400 candidates,370 valid windows and355 drift-eligible windows. No critical
or important issue was found. The only minor report issue was unescaped pipes
inside code spans in all48 factorial table rows. The original implementer
completed the evidence-only fix; scoped final re-review approved all four
tables with15 rows and seven cells each. Removing the96 added escapes restores
the original report prefix exactly. No source/model rerun occurred. The
pre-fix report and `dhruva-aligned-ablation-final-format-fix.diff` are retained.

Final review: complete, all findings addressed, no remaining implementation
findings. This completes the diagnostic plan, not the broader SIH goal.

The final review's referenced skill template is not installed; the retained
full package, binding brief, loader interfaces and evidence ledger supplied
the concrete cross-file review scope. Keep snapshots/ledgers because there
is no Git recovery history.

The later independent raw-reference-quality finding is a separate research
issue, not a failure of the implemented numerical spec. See
`research/DHRUVA_REFERENCE_QUALITY_FINDINGS_2026-09-10.md`; no benchmark
exclusions or source data have been changed in response.
