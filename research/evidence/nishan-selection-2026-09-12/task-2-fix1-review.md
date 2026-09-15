# Task 2 fix round 1 — scoped re-review

## Overall round verdict

**APPROVED for the source fix round.** All three original Important findings and
the requested Minor feasibility finding are addressed. I found no new breakage
in the six-file fix diff.

This was a bounded re-review against `task-2-after.tar.gz`. I reviewed only the
four requested findings, their tests/logs, and regressions introduced by the fix
diff. I did not rerun tests, export PDF, render slides or perform a broader audit.

## Original findings

### Important 1 — shallow profile/observation validation: ADDRESSED

**Evidence:**

- `submissions/SIH26237_NISHAN_PQ/deck_evidence.py:59-92` now requires the exact
  bounded profile values and rejects Boolean-as-integer or nonnumeric epsilon
  substitutions.
- `submissions/SIH26237_NISHAN_PQ/deck_evidence.py:95-330` validates the minimal
  claim invariants for all 12 named observations: concurrency/session identity,
  signed-copy hashes, clean corroboration and witness state, read-only trace,
  raster/low-capacity abstention, wrong-pin release rejection, rollback release
  and trace rejection, and both checkpoint/publication outcomes.
- `submissions/SIH26237_NISHAN_PQ/deck_evidence.py:378-394` invokes both bounded
  validators from the existing exact-name evidence gate.
- Tests cover profile mutations, one counterfactual for every case, and explicit
  builder/verifier rejection at
  `submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py:245`, `:261`, `:424`
  and `:572`.
- The supplied focused log records the intended RED (`4` methods, `20` failures)
  and final GREEN (`4` methods, `OK`). The supplied full fix log records `32`
  tests in `5.123s`, `OK`.

The new validation is deliberately coupled to the reviewed v1 result structure;
that is appropriate for this source gate and does not add prototype scope.

### Important 2 — judge run inside future repository tree: ADDRESSED

**Evidence:** `submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md:27`, `:146` and
`:153` use `/tmp/nishan-judges-run-01` for invocation and both inspection
commands. The fresh-suffix/no-overwrite and synthetic-key warnings remain, and
no cleanup/deletion command or relocation of reviewed Task 1 evidence was added.
The regression assertion is at
`submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py:604-607`.

### Important 3 — checkpoint-pin and ML-KEM role labels: ADDRESSED

**Evidence:**

- `submissions/SIH26237_NISHAN_PQ/build_deck.py:427` now says configured mode
  checks signed witness state under a caller-provisioned key pin; it no longer
  says the signed checkpoint itself is pinned.
- `submissions/SIH26237_NISHAN_PQ/build_deck.py:448` now labels ML-KEM-768 as
  `Wrap key`, not `Authorize`.
- Generated-copy assertions are present at
  `submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py:398-400`.

The corrected phrases preserve the original security boundary: the actual
witness verification key is pinned, the signed state is checked, and ML-KEM is
used for key encapsulation rather than authorization policy.

### Minor 1 — six-person feasibility context: ADDRESSED

**Evidence:** `submissions/SIH26237_NISHAN_PQ/build_deck.py:553` adds the compact
visible line `Six-person team · existing offline laptop prototype · repeatable
saved evidence`. The regenerated note at
`submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md:53` adds the
same feasibility context and retains the no-GPU/no-ESP32 qualification.

## New breakage

**None found.** The stricter validator matches the current runner's recorded v1
field meanings, preserves clean `ValueError` failures, and leaves the existing
exact-case/PQC/current-hash gate in place. The runbook and visible-copy changes
remain within the requested presentation/documentation scope.

## Out-of-scope, non-blocking observations

- The original Minor 2 dead helpers/parameters remain deferred as explicitly
  directed. They do not block this fix round.
- The regenerated PPTX is a binary change. Visual layout, matching PDF export,
  six-page render inspection and actual artifact draft/strict verification were
  not part of this source re-review and remain controller-owned. The currently
  unchanged baseline PDF is therefore not a fix-round regression.

## Quality verdict

**APPROVED.** The source fixes are bounded, evidenced and adequate for the
controller to proceed to the separate render/export/artifact gate.
