# NISHAN selection readiness — final whole-plan review

**Overall: APPROVED for the declared draft scope.** No Critical or Important findings remain. This approves the tested prototype and presentation handoff, not upload readiness, competition acceptance or production security.

## Spec compliance

The aggregate implementation matches the binding selection-readiness specification and its reviewed PDF-classification amendment:

- Release acquires ledger then witness locks around the entire transaction; allocation uses the audited state, append uses `lock_held=True`, and publication follows signed-history re-audit and configured witness checkpoint/re-verification (`prototypes/nishan_pq/nishan/core.py:165`, `:193`, `:403`). The witness compares the actual verification-key bytes with the caller's pin, requires an existing nonempty chain and exact head consistency, and rejects an unwitnessed extension on entry (`prototypes/nishan_pq/nishan/witness.py:40`, `:54`). A failed checkpoint can retain an authorization record while withholding publication; the API and prose disclose this distinction.
- PDF classification comes from authenticated plaintext parsing before profile selection, with inconsistent package metadata rejected. Trace rejects actual PDF references carrying legacy generic receipts and requires set-equality corroboration for PDF-source evidence, including raster suspects and inadequate-capacity releases (`prototypes/nishan_pq/nishan/core.py:255`, `:854`, `:1029`). Genuine image screening retains its separately disclosed research status. No carrier, threshold or mathematical changes appear in the net diff.
- Trace verifies the signed ledger and configured pinned snapshot under the same lock order, then extracts from captured state without checkpointing (`prototypes/nishan_pq/nishan/core.py:978`). The result describes a checked snapshot, not indefinite freshness.
- Fresh evidence is gated by the exact 12 unique scenario names, strict real-PQC/profile fields, bounded per-case observation invariants and current hashes of all 19 required files. Both builder and verifier use this gate (`submissions/SIH26237_NISHAN_PQ/deck_evidence.py:59`, `:95`, `:333`; `build_deck.py:712`; `verify_submission.py:228`). The gate supports reproducibility of the reviewed local demonstration; it is not an independent cryptographic proof verifier.
- The six official sections, editable deck, matching PDF, exported/embedded notes and complete R1–R14/P1–P24 audit mapping are retained. Current safeguards, historical one-document/codebook JPEG results and exploratory physical results are distinguished. The runbook uses a fresh external `/tmp` root and forbids publishing or reusing generated private material (`submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md:14`, `:27`).

## Strengths

- The security change and pitch tell the same story: serialized authorized release, optional independently provisioned key-pin enforcement, conservative PDF association and explicit abstention. The fresh demonstration derives verdicts from observed outcomes rather than fixed success strings.
- Regression coverage targets the previously demonstrated race, media-type policy bypass, rollback, checkpoint failures, existing-destination preservation and read-only tracing. Recorded stable logs show **59/59 prototype tests in 63.472s** and **33/33 presentation tests in 17.563s**, with `OK` (`task-1-fix1-suite-final.txt:62`; `task-2-fix2-deck-suite-final.txt:36`, relative to this review directory).
- The materials retain the material limits: co-located administration and R8 NOT MET, trusted software/key custody, operator reproduction/framing, removal/retyping, non-blind reference use and session evidence without human guilt or delivery/read proof (`submissions/SIH26237_NISHAN_PQ/paste_ready_submission.md:127`). Physical recovery remains historical 0/4 and exploratory same-capture 1/4; the recovered Sol Ultra probe is not represented as implemented evidence.

## Findings

**Critical:** none identified.

**Important:** none identified.

**Minor — previously accepted deferral:** unused slide helpers and parameters remain after the presentation rewrite (`submissions/SIH26237_NISHAN_PQ/build_deck.py:397`, `:514`, `:520`, `:567`). This is maintenance clutter, with no observed behavior or artifact defect. Keep the recorded post-submission cleanup deferral; no final fix wave is warranted.

## Review evidence and limits

Reviewed the binding spec, plan, progress rulings and the complete 17-file net diff from `before.tar.gz` to current files. Additional unchanged-source inspection was limited to three named integration risks: healthy signed-history validation before trace, unissued-row/set-equality fusion behavior, and witness checkpoint comparison/extension behavior. No new material defect emerged from those checks.

Independently ran read-only checksum checks: all four entries in `final-artifacts.sha256` and all 19 current demo code hashes matched. Read the saved final test logs and actual artifact verifier reports; no suites, experiments, exports or render jobs were rerun. Artifact visual assessment relies on the controller's recorded inspection of all six pages, final slide-2 correction and byte-identical remaining five final renders (`artifact-validation.md:15`). This is a source/integration review plus review of recorded artifact validation, not a fresh visual or adversarial certification.

The saved draft verifier has exit 0, `ok:true` and no errors. Strict verification has exit 1 only for four placeholder tokens representing three missing user values: registered team name, team ID and public repository URL (`artifact-validation.md:21`; `draft-verification.json`; `strict-verification.json`). Those deliberately unresolved fields prevent strict submission readiness and require user-supplied values before final regeneration/verification. They are not implementation failures in this approved draft. No upload or acceptance occurred.
