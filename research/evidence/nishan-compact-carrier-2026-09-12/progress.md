# SDD ledger — plan: docs/superpowers/plans/2026-09-12-nishan-compact-carrier.md

Spec: research/NISHAN_COMPACT_CARRIER_SPEC_2026-09-12.md

Ruling: Retain the current uncertified keyed sampler in an explicitly empirical compact-carrier pilot rather than implement a new certification protocol now — the pilot tests spatial carrier behavior independently of the proposed arithmetic proof — cost if wrong: no theorem-level claim can be made and results may not transfer to a later sampler.

Ruling: Use a new evidence directory, hashes, and tar snapshots instead of git worktrees/commits and retain it after review — this workspace is not a Git repository and existing user files must remain untouched — cost if wrong: extra disk space and manual recovery instead of Git history.

## Preflight

| Pair/task | Produced versus consumed | Check |
|---|---|---|
| Task 1 internal profile → runner/capture | Full symmetric score; repeated correlation order; fixed profile keys | Exact same module consumed by both paths; original remains separate. |
| Task 1 runner → capture | Source and private replay hashes, arrays, fixed threshold | Capture validates before loading, no pickle and no writes; manifest is not signed provenance. |
| Task 1 tests → code | [4,-1] and [-4,1] symmetric cases; analog repetition sum [6,-2]; zero tie | Arithmetic manually checked; tests differ from old one-sided scorer and majority voting. |
| Task 1 matrix → decision | 30 positives + 15 unmarked + 6 wrong-key + 6 wrong-context | 57 explicit identities; two issued rows per profile; no broad physical/generalization claim. |
| Task 1 scope → global constraints | Five new code/docs files and own new run only | Prototype/submissions/old evidence/Sol lab read-only; no installs/commits. |

Self-review: spec sections all map to Task 1; no unresolved numerical or interface placeholders. Generic worktree/finish/review helper skills are not installed; task-review rubric will be used for the final broad review with a most-capable reviewer. No deletion on completion because snapshots are the recovery record.

The SDD workspace helper was invoked and stopped at Git discovery before writing a workspace; the previously recorded non-Git evidence-directory ruling applies. The supplied task-brief helper succeeded with the explicit evidence-directory output path. Baseline snapshot and 21 frozen input hashes are retained; all checked successfully before implementation.

Task 1: running — implementer `/root/compact_carrier_study`, `gpt-5.6-sol`, high effort, isolated context. Full report: `task-1-report.md`.

Task 1 implementation reported DONE_WITH_CONCERNS: expected RED, 10/10 GREEN, sole 127.543-second run completed 57/57 observations, 30/30 expected-only positives and 27/27 empty negatives. Concerns are scope limitations rather than omitted implementation. No physical outcome or probability certification. Report and source snapshot retained; five-file full new-file diff generated (diff exit 1 is normal for new content, not a packaging failure).

Task 1 review running: `/root/compact_carrier_review`, Sol high. Exact task brief/report/diff supplied; no repeated suite requested. Controller wrote the result decision, explicitly noting unchanged attribution success counts, original-versus-compact construction differences and the repeated compact carrier's blur regression.

Task 1 review returned spec FAIL / quality Needs fixes: four Important findings (optional replay commitments, omitted marking diagnostics for twelve source-bearing negative controls, missing manifest on preparation failure, incomplete identity-set test); no Critical/Minor findings. Core scoring and stored advancement were independently checked. Process cannot-verify items: controller retained expected RED before implementation, sole run artifact chronology and before/after frozen hashes; authored code was delegated under explicit apply_patch/no-network/no-install/no-git instructions. The root does not claim an exhaustive independent audit of every worker action beyond these records.

Ruling: Repair missing diagnostics for the completed run in a separately hashed addendum derived only from its saved words and codebook, while fixing the generator for future runs — overwriting the original results or repeating the pilot would violate the frozen one-run evidence rule — cost if wrong: consumers must read the addendum with the original record, and any changed score outcome would require a separately declared experiment rather than this correction.

Task 1: fix round 1/5 starting — original implementer will address all four findings, run covering tests and one replay smoke only; no repeat embeddings, transformations, new keys or full pilot. Original run stays read-only; new repair evidence stays outside run-01.
