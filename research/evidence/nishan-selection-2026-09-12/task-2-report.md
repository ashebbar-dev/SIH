# Task 2 — evidence-led six-slide NISHAN-PQ selection presentation

Status: complete for source handoff on 12 September 2026. The controller owns
final PDF export, rendered-slide inspection and artifact-level draft/strict
verification after source review.

## Result

Rebuilt the editable six-slide presentation from the official SIH template,
regenerated complete embedded/exported speaker notes, replaced stale pre-fix
claims, added a five-minute offline demo runbook, and rewrote the paste-ready
submission around the accountable-decryption value proposition.

Fresh claims are now gated by `validate_safeguard_evidence(evidence: dict) -> dict`.
The validator requires:

- version `nishan-selection-safeguards/v1`;
- exactly the 12 reviewed unique scenario names;
- Boolean `passed: true` for every case and `all_passed: true`;
- real-PQC readiness with Boolean ML-KEM-768 and ML-DSA-65 flags plus a nonempty
  OpenSSL version;
- a nonempty command/profile/limitations record;
- coverage of all 16 `nishan/*.py` modules, the safeguard runner and the two
  reviewed safeguard/PDF-policy test files;
- valid lowercase SHA-256 strings matching every recorded current file.

Malformed non-string or unhashable case names are type-checked before set/hash
operations and raise a clean `ValueError`. The builder validates the fresh report
before constructing a deck, and the submission verifier separately requires and
validates it.

## Presentation and editorial result

The official six-section order, 13.333 × 7.5-inch dimensions, background, logo
and footer are preserved. New content uses native editable shapes. Visible copy
is pitch-first and keeps detailed audit material in notes:

1. value proposition: “Accountable decryption. Verifiable source-copy evidence.”;
2. solution and three capabilities: session-specific release, commit before
   release, and conservative trace;
3. managed-process release gate with configured pinned-checkpoint enforcement;
4. clearly separated fresh safeguards, historical visual fixtures and physical
   evidence;
5. judge-driven five-minute demo and narrow second-round roadmap;
6. primary prior art and a scoped engineering-integration claim.

The deck distinguishes differently encoded visual/layout channels from
independent security authorities. It says the wrong-pin scenario covers release,
while coordinated rollback is demonstrated on both release and trace. It labels
the historical 30/30 JPEG-Q55 evidence as a one-document/codebook visual-channel
study and physical evidence as shipped-threshold 0/4 with the same exploratory
1/4 capture in both profiles.

Speaker notes contain each R1–R14 and P1–P24 label exactly once. Corrected
semantics include serialized allocation, configured witness calls, strict PDF
corroboration for raster/low-capacity sources, content-parser enforcement, legacy
generic-PDF rejection, checkpoint failure without publication, and retained
co-located custody/authority-framing/non-blind/human-guilt boundaries.

## TDD record

### Safeguard contract RED

Command:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.SafeguardEvidenceTests -v 2>&1 | tee research/evidence/nishan-selection-2026-09-12/task-2-safeguard-red.txt
```

Observed unittest result before implementation:

```text
Ran 7 tests in 0.034s
FAILED (errors=19)
AttributeError: module 'deck_evidence' has no attribute 'validate_safeguard_evidence'
```

The 19 errors are subtests exercising the absent interface, not 19 independent
test methods. Because the shell pipeline did not use `pipefail`, its process exit
was tee's zero status even though unittest correctly reported failure. Full output
is in `task-2-safeguard-red.txt`.

### Safeguard contract GREEN

Same focused unittest target after implementation:

```text
Ran 7 tests in 0.027s
OK
```

Full output: `task-2-safeguard-green.txt`.

### Builder hash-drift RED → GREEN

Focused command:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.DeckAndVerifierTests.test_build_rejects_safeguard_code_hash_drift -v
```

Before builder integration:

```text
Ran 1 test in 0.421s
FAILED (errors=1)
TypeError: build() got an unexpected keyword argument 'safeguard_path'
```

After integration:

```text
Ran 1 test in 0.636s
OK
```

Full outputs: `task-2-build-evidence-red.txt` and
`task-2-build-evidence-green.txt`. As above, the tee pipeline recorded the
unittest RED even though the pipeline status itself followed tee.

### Covering and final suite

An initial covering suite passed all 26 then-existing tests:

```text
Ran 26 tests in 4.960s
OK
```

Full output: `task-2-deck-green-initial.txt`.

After adding handoff/verifier coverage, the first 28-test run found one wording
assertion mismatch in the new handoff test:

```text
Ran 28 tests in 13.207s
FAILED (failures=1)
```

That log is retained as `task-2-deck-suite-final.txt`; it is not presented as a
successful final run. The wording check was aligned with the actual scoped
handoff language, and controller feedback corrected “independent channels” to
“differently encoded channels” plus the wrong-pin/rollback case scope.

Final stable-source command:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update -v 2>&1 | tee research/evidence/nishan-selection-2026-09-12/task-2-deck-suite-stable.txt
```

Actual final result:

```text
Ran 28 tests in 7.746s
OK
```

All 28 test methods passed with no skips, failures or errors. Coverage includes
historical physical identity/numerical checks, strict fresh-evidence schema and
hash checks, malformed-name errors, builder drift rejection, six-slide/editable
deck structure, exact R/P note coverage, evidence-derived mutated inputs,
matching-package verifier success, missing/failed evidence rejection, stale-claim
rejection, and current handoff/runbook wording.

The final deck was regenerated after the editorial correction with:

```text
.venv/bin/python submissions/SIH26237_NISHAN_PQ/build_deck.py
```

It completed successfully and wrote
`submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx` plus the matching
speaker-notes Markdown.

## Source self-review

- `unzip -t` reported no errors in the PPTX compressed data.
- Programmatic inspection found six slides at 13.333 × 7.5 inches, six nonempty
  embedded note blocks and 230 editable text-bearing shapes.
- Notes contain 14 R labels and 24 P labels, each expected label exactly once.
- Current generated PPTX/notes contain none of the checked stale phrases:
  witness-not-enforced, non-atomic/racing allocation, independent-channel wording,
  proposed-but-unimplemented PDF abstention, or a 30/30 exact PDF attribution claim.
- Only the expected unsupplied team/team-ID/repository placeholders remain.
- `tar -dzf task-2-before.tar.gz prototypes/nishan_pq` produced no differences:
  Task 2 did not modify prototype source, tests or historical evidence.
- Scoped tar comparison reports content changes only for the requested builder,
  evidence module, verifier, tests, paste-ready prose, PPTX and notes. The runbook
  is new. The preserved task snapshot and all archive directories remain intact.
- The current submission PDF SHA-256 is
  `280d3d00f7fe3fd9ba8d64b5f2c3cd87d6c4877d7c84bd853da6135777eb8a2c`,
  exactly matching the PDF in `task-2-before.tar.gz`. No final PDF export was
  performed in Task 2.
- No Git repository was initialized, and no Git commands, dependency installs,
  prototype runs or new safeguard demo runs were performed.

### Temporary preview attempt

For visual self-review only, two sandboxed LibreOffice commands attempted to
write a PDF under `/tmp/nishan-task2-preview.2n7K0W`; both returned without output
and created no PDF. A permission-escalated repeat was then requested, remained
pending for 503.6 seconds and was interrupted by the controller/user. It did not
change the submission PDF. A later process check found no `soffice`,
`libreoffice` or deck-unittest process running, and no approval remains pending.
Per controller direction, the preview was not retried; rendered inspection and
final PDF export remain controller-owned.

## Changed files

Modified:

- `submissions/SIH26237_NISHAN_PQ/build_deck.py`
- `submissions/SIH26237_NISHAN_PQ/deck_evidence.py`
- `submissions/SIH26237_NISHAN_PQ/verify_submission.py`
- `submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py`
- `submissions/SIH26237_NISHAN_PQ/paste_ready_submission.md`
- `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx`
- `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md`

Created:

- `submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md`
- this report and the Task 2 RED/GREEN test logs in the evidence directory.

## Remaining manual actions and concerns

1. Supply the registered team name, team ID and public repository URL. Draft mode
   may warn; strict verification must fail until those fields are supplied.
2. Controller must review the editable source, export the matching six-page PDF,
   render/inspect all six slides, then run draft and strict artifact verification.
   The matching-package unit test passes both verifier modes with synthetic filled
   fields; the actual current PDF is intentionally still the preserved baseline.
3. No final render was visually inspected in this task because the temporary
   LibreOffice attempt was interrupted. Programmatic layout/source checks passed,
   but controller visual inspection remains necessary before submission.

No source blocker remains.

## Visual fix round 2 — slide 2 headline clears the SIH logo

Controller render inspection found one overlap: the long green headline on slide
2 extended into the official SIH logo area. The reviewed pre-fix state is
preserved in `task-2-render-before.tar.gz`. No other slide, copy, style,
cryptographic logic or verifier rule was changed in this round.

### Targeted RED

Added one regression that locates the single slide-2 shape beginning `One
encrypted source.`, measures its native editable textbox geometry and requires
the right edge to be at or before 10.3 inches.

Command:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.DeckAndVerifierTests.test_slide_two_headline_clears_official_logo -v
```

Actual pre-fix result:

```text
AssertionError: 12.52 not less than or equal to 10.3
Ran 1 test in 0.864s
FAILED (failures=1)
```

Full output: `task-2-fix2-slide2-headline-red.txt`. The saved command used
`tee`, so the unittest text above is the RED result even though the pipeline's
last process returned successfully.

### Fix and focused GREEN

The headline is now exactly:

```text
One encrypted source. Signed, session-specific releases.
```

Its builder geometry is `x=2.30in`, `w=8.00in`, so its right edge is exactly
`10.30in` and clears the right-side logo.

The same focused test then reported:

```text
Ran 1 test in 0.783s
OK
```

Full output: `task-2-fix2-slide2-headline-green.txt`.

### Complete stable suite and regeneration

After the two stable source edits, the complete deck suite ran once:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update -v 2>&1 | tee research/evidence/nishan-selection-2026-09-12/task-2-fix2-deck-suite-final.txt
```

Actual result:

```text
Ran 33 tests in 17.563s
OK
```

All 33 methods passed with no skips, failures or errors. The final PPTX and notes
were then regenerated with the existing builder. Source inspection of the saved
PPTX confirmed the exact new headline, left edge `2.3in`, width `8.0in`, right
edge `10.3in`, six slides and six nonempty note blocks. `unzip -t` reported no
compressed-data errors.

Comparison with `task-2-render-before.tar.gz` reports content changes only for
`build_deck.py`, `tests/test_deck_update.py` and the regenerated PPTX; the speaker
notes were regenerated but their content is unchanged. No PDF export,
LibreOffice, preview, escalation, subagent, prototype/historical evidence edit or
unrelated cleanup was performed. Controller still owns the final PDF export and
render validation.

## Fix round 1 — three Important review findings resolved

Review basis: `task-2-review.md`; preserved reviewed base:
`task-2-after.tar.gz`. This round addresses all three Important findings and the
requested six-person feasibility polish. The dead-helper/parameter Minor finding
was deliberately deferred to avoid unrelated churn before export.

### 1. Fresh-evidence observations and profile now gate the claims

`validate_safeguard_evidence` now validates the bounded current demo schema rather
than accepting any observation object/list. The profile requires the reviewed
1,000-row, coalition-limit-five, familywise-1e-6, public synthetic one-page PDF,
PDF-corroboration and pin-provisioning fields with strict types/values.

Each of the exact 12 cases now enforces its minimal claim invariant:

- two concurrent processes, rows 0/1 and two distinct sessions;
- later row 2 and a third distinct session;
- three current release sessions whose actual and signed 64-hex hashes agree;
- one clean Alice PDF selection, valid recipient signature, layout match,
  corroborated decision and valid enforced/consistent witness snapshot;
- identical before/after checkpoint hashes for read-only trace;
- empty high-assurance attribution, expected decision and retained signed visual
  research leads for raster transplant and low-capacity PDF;
- a signed inadequate-capacity policy for the low-capacity case;
- release-only wrong-pin rejection with no output;
- rollback detection/rejection for release with no output and for trace;
- checkpoint failures with a one-record committed extension, no publication,
  correct existing-destination state and `unwitnessed_extension` status.

The implementation stays specific to the recorded `v1` report; it adds no schema
framework, prototype or cryptographic redesign.

#### Focused RED

Command:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.SafeguardEvidenceTests.test_required_profile_fields_and_types_are_strict submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.SafeguardEvidenceTests.test_each_case_observation_enforces_claim_invariants submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.DeckAndVerifierTests.test_build_rejects_counterfactual_safeguard_observation submissions.SIH26237_NISHAN_PQ.tests.test_deck_update.DeckAndVerifierTests.test_verifier_rejects_malformed_safeguard_observation -v
```

Observed before implementation:

```text
Ran 4 tests in 1.948s
FAILED (failures=20)
```

The 20 failures comprise six profile mutations, one counterfactual for each of
the 12 cases, and representative proof that the builder and verifier still
accepted malformed/counterfactual observations. Full output:
`task-2-fix1-observation-red.txt`. The logged command used `tee`, so the unittest
failure text—not the pipeline's final tee status—is the RED result.

#### Focused GREEN

After the first implementation pass the same four methods passed in `1.076s`;
that output is retained as `task-2-fix1-observation-green.txt`. After strengthening
the current fixture, clean layout/witness and low-capacity-policy invariants, the
final focused run reported:

```text
Ran 4 tests in 0.707s
OK
```

Full final focused output: `task-2-fix1-observation-green-final.txt`. The builder
rejects a wrong-pin observation claiming an output exists; the verifier rejects
a read-only-trace observation missing its post-trace hash.

### 2. Judge-run output is external to a future repository

All three runbook commands now use exactly `/tmp/nishan-judges-run-01`: the demo
invocation, JSON summary inspection and SHA-256 check. The no-overwrite/new-suffix
rule and synthetic-only key warning remain. No cleanup/deletion command was added,
and the reviewed Task 1 evidence was not moved or rewritten.

### 3. Visible crypto roles and feasibility are corrected

Slide 2 now says configured mode “checks signed witness state under a
caller-provisioned key pin”; it no longer says a signed checkpoint itself is
pinned. The ML-KEM flow step is `Wrap key / ML-KEM-768`, not `Authorize`.

Slide 4 adds: `Six-person team · existing offline laptop prototype · repeatable
saved evidence`. The corresponding unnumbered note also states that neither GPU
nor ESP32 is required for this measured workflow.

### Fix-round final validation

Final complete deck-suite command after all source edits:

```text
.venv/bin/python -m unittest submissions.SIH26237_NISHAN_PQ.tests.test_deck_update -v 2>&1 | tee research/evidence/nishan-selection-2026-09-12/task-2-fix1-deck-suite-final.txt
```

Actual result:

```text
Ran 32 tests in 5.123s
OK
```

All 32 methods passed with zero skips, failures or errors. The suite covers the
new profile/12-case invariants, representative builder/verifier rejection, exact
external runbook paths, corrected slide-2 roles and the six-person line in
addition to all retained Task 2 checks.

The final PPTX and notes were regenerated after the stable suite with:

```text
.venv/bin/python submissions/SIH26237_NISHAN_PQ/build_deck.py
```

It completed successfully. Source self-review then confirmed:

- PPTX ZIP integrity is clean; six slides and six nonempty note blocks remain;
- corrected slide-2 key-pin copy, `Wrap key / ML-KEM-768` and the six-person line
  are present in the generated PPTX;
- every R1–R14 and P1–P24 label remains present exactly once;
- the current `demo/results.json` passes the stronger validator;
- `/tmp/nishan-judges-run-01` occurs exactly three times in the runbook, and the
  old repository-tree judge-run path is absent;
- comparison with `task-2-after.tar.gz` shows changes only to `build_deck.py`,
  `deck_evidence.py`, `tests/test_deck_update.py`, `DEMO_RUNBOOK.md`, the generated
  PPTX and generated notes;
- the reviewed snapshot contains only submission files; a separate comparison of
  `prototypes/nishan_pq` with `task-2-before.tar.gz` reports no differences.

No LibreOffice, PDF, preview, escalation, subagent, separate reviewer, prototype
run, demo rerun, historical-evidence edit or Git operation occurred in this fix
round. The submission PDF remains controller-owned and unchanged.

Fix-round changed files:

- `submissions/SIH26237_NISHAN_PQ/deck_evidence.py`
- `submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py`
- `submissions/SIH26237_NISHAN_PQ/build_deck.py`
- `submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md`
- `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx`
- `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md`

Remaining manual actions are unchanged: supply team name, team ID and public
repository URL; then the controller reviews/renders the source, exports the
matching PDF and runs artifact-level draft/strict verification. No source blocker
remains.
