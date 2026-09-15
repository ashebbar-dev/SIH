# NISHAN evidence-led deck update — Task 1 implementation report

Date: 11 September 2026  
Scope: presentation builder, evidence adapter, package verifier, focused tests, editable PPTX and exported speaker notes only.  
Binding requirements: `research/evidence/nishan-deck-update-task-1-brief.md` and `research/NISHAN_DECK_UPDATE_SPEC_2026-09-11.md`.

## Outcome

The existing official six-slide, 16:9 deck was rebuilt as an editable PPTX while preserving its template background, logos and footers. The slide narrative now separates implemented mechanisms, measured evidence, unresolved boundaries and proposed hardening. The stale physical-pending claims were removed. Physical numbers come from a strict loader for the fixed eight records/four captures/two profiles; no best-profile selection or score-only recovery inference is used.

The PPTX embeds six speaker-note blocks and the builder exports the same blocks to Markdown. The notes preserve the official `R1:`–`R14:` requirement mapping and the original corrected Claude-review `P1:`–`P24:` mapping. Unknown team ID, registered team name and public repository URL remain explicit CLI-replaceable placeholders.

The report-creation skill affected the work by requiring the existing template to remain the visual authority, retaining an editable source, and validating the archive/output rather than treating file existence as success.

## Task-owned files

- Modified: `submissions/SIH26237_NISHAN_PQ/build_deck.py`
- Modified: `submissions/SIH26237_NISHAN_PQ/verify_submission.py`
- Created: `submissions/SIH26237_NISHAN_PQ/deck_evidence.py`
- Created: `submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py`
- Generated: `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx`
- Generated: `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md`
- PDF conversion and final PDF validation are delegated to the controller after the final PPT build; see Pending controller checks.

No prototype, runner, experiment output, original image, source PDF or recorded evidence file was modified. No dependency was added, Git repository initialized, commit created, file deleted, experiment run, publication made or upload attempted.

## RED — focused tests before implementation

Command:

```bash
.venv/bin/python -B -m unittest discover -s submissions/SIH26237_NISHAN_PQ/tests -p 'test_deck_update.py' -v
```

Tool chunk: `5b65b5`  
Exit: `1`  
Result: 11 expected errors before `deck_evidence.py` and the new build arguments existed.

```text
test_build_has_six_editable_slides_and_complete_matching_notes (test_deck_update.DeckAndVerifierTests.test_build_has_six_editable_slides_and_complete_matching_notes) ... ERROR
test_slide_claims_are_evidence_derived (test_deck_update.DeckAndVerifierTests.test_slide_claims_are_evidence_derived) ... ERROR
test_verifier_rejects_missing_physical_evidence (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_missing_physical_evidence) ... ERROR
test_verifier_rejects_stale_pdf_claim (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_stale_pdf_claim) ... ERROR
test_verifier_rejects_stale_pptx_claim (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_stale_pptx_claim) ... ERROR
test_duplicate_record_is_rejected (test_deck_update.PhysicalEvidenceTests.test_duplicate_record_is_rejected) ... ERROR
test_exact_physical_summary (test_deck_update.PhysicalEvidenceTests.test_exact_physical_summary) ... ERROR
test_false_counted_success_is_rejected (test_deck_update.PhysicalEvidenceTests.test_false_counted_success_is_rejected) ... ERROR
test_missing_input_is_explicit (test_deck_update.PhysicalEvidenceTests.test_missing_input_is_explicit) ... ERROR
test_missing_profile_is_rejected (test_deck_update.PhysicalEvidenceTests.test_missing_profile_is_rejected) ... ERROR
test_scored_record_requires_finite_threshold (test_deck_update.PhysicalEvidenceTests.test_scored_record_requires_finite_threshold) ... ERROR

ERROR: test_build_has_six_editable_slides_and_complete_matching_notes
TypeError: build() got an unexpected keyword argument 'physical_path'

ERROR: test_slide_claims_are_evidence_derived
TypeError: build() got an unexpected keyword argument 'physical_path'

ERROR: test_verifier_rejects_missing_physical_evidence
TypeError: build() got an unexpected keyword argument 'physical_path'

ERROR: test_verifier_rejects_stale_pdf_claim
TypeError: build() got an unexpected keyword argument 'physical_path'

ERROR: test_verifier_rejects_stale_pptx_claim
TypeError: build() got an unexpected keyword argument 'physical_path'

ERROR: test_duplicate_record_is_rejected
ModuleNotFoundError: No module named 'deck_evidence'

ERROR: test_exact_physical_summary
ModuleNotFoundError: No module named 'deck_evidence'

ERROR: test_false_counted_success_is_rejected
ModuleNotFoundError: No module named 'deck_evidence'

ERROR: test_missing_input_is_explicit
ModuleNotFoundError: No module named 'deck_evidence'

ERROR: test_missing_profile_is_rejected
ModuleNotFoundError: No module named 'deck_evidence'

ERROR: test_scored_record_requires_finite_threshold
ModuleNotFoundError: No module named 'deck_evidence'

----------------------------------------------------------------------
Ran 11 tests in 0.049s

FAILED (errors=11)
```

## Implementation

### Physical evidence loader

`deck_evidence.load_physical(path)` now:

- requires schema `nishan.bias-physical-scores/v1`;
- requires exactly four unique named captures, the exact profiles `affine_baseline` and `affine_bias_translation`, eight unique `(capture, profile)` records and full Cartesian coverage;
- distinguishes `scored` from `boundary_failure` records;
- rejects missing/non-finite scores, competing score, BER and conditional threshold in scored records;
- rejects score-bearing or accusing boundary failures;
- validates historical and conditional accusations against the saved expected row and the relevant saved threshold;
- validates `row0_accused` against the saved accusation rather than trusting it as a success flag;
- rejects unexpected competing-row accusations and inconsistent competing-score crossings;
- derives counts per named profile, without selecting a best score/profile.

Validated summary:

```text
captures=4
historical_recovered=0
baseline_recovered=1
refined_recovered=1
boundary_failures=2
```

The visible physical wording explicitly says `Experimental 1/4 per profile` and that the same `akshay3` capture recovered in both, so it cannot be read as two recovered captures.

### Slide allocation

1. Title: corrected session-provenance tagline, `RESEARCH PROTOTYPE`, evidence date, official PS/team fields.
2. Proposed solution: qualified five-stage flow, digital evidence card, real-capture card, same-capture limitation and non-deployment caveat. Channel checking is conditional on available channels.
3. Technical approach: trusted-viewer assumption, co-located 3-of-4 demonstrator, accurate visual/layout/reference/receipt path, current boundaries and explicitly unimplemented hardening.
4. Feasibility: compact measured outcomes and four unresolved risk groups; visible statement that session evidence is not proof of who leaked it.
5. Impact: investigative assistance/offline/PQC benefits, explicit non-accusation readiness and three gates including multi-page plus signed/tagged PDFs.
6. Research: prescribed/known components, physical baselines, measured-integration/failure-analysis contribution, unvalidated hypotheses and repository placeholder.

The old chart file was retained but is no longer placed on slide 2. Slide content remains native editable PowerPoint text/shapes.

### Notes and verifier

- Notes use the exact embedded/export loop required by the brief.
- `R1:`–`R14:` and `P1:`–`P24:` occur exactly once and include semantic mapping checks for R8, R14, P1, P3, P10, P11, P23 and P24.
- The verified Tardos primary-paper URL is `https://www.renyi.hu/~tardos/fingerprint.pdf`; the unverified DOI was not retained.
- Verifier keeps the historical digital evidence, attack-matrix, signature, ledger and secret-file checks.
- Verifier adds physical-evidence load/summary checks, six embedded-note checks, Markdown consistency checks, current slide/PDF anchors and stale-claim rejection in PPTX/PDF text.
- Forbidden stale phrases are not searched in notes, so a negated/contextual audit quotation cannot be mistaken for an asserted slide claim.
- Strict placeholder behavior is unchanged in principle: draft mode warns; strict mode rejects until team/repository details are supplied.

## GREEN — focused tests

Final command and build/ZIP-integrity sequence:

```bash
.venv/bin/python -B -m unittest discover -s submissions/SIH26237_NISHAN_PQ/tests -p 'test_deck_update.py' -v
.venv/bin/python -B submissions/SIH26237_NISHAN_PQ/build_deck.py
unzip -t submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx
```

Tool chunk: `96299d`  
Exit: `0`

```text
test_build_has_six_editable_slides_and_complete_matching_notes (test_deck_update.DeckAndVerifierTests.test_build_has_six_editable_slides_and_complete_matching_notes) ... ok
test_slide_claims_are_evidence_derived (test_deck_update.DeckAndVerifierTests.test_slide_claims_are_evidence_derived) ... ok
test_verifier_rejects_missing_physical_evidence (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_missing_physical_evidence) ... ok
test_verifier_rejects_stale_pdf_claim (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_stale_pdf_claim) ... ok
test_verifier_rejects_stale_pptx_claim (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_stale_pptx_claim) ... ok
test_duplicate_record_is_rejected (test_deck_update.PhysicalEvidenceTests.test_duplicate_record_is_rejected) ... ok
test_exact_physical_summary (test_deck_update.PhysicalEvidenceTests.test_exact_physical_summary) ... ok
test_false_counted_success_is_rejected (test_deck_update.PhysicalEvidenceTests.test_false_counted_success_is_rejected) ... ok
test_missing_input_is_explicit (test_deck_update.PhysicalEvidenceTests.test_missing_input_is_explicit) ... ok
test_missing_profile_is_rejected (test_deck_update.PhysicalEvidenceTests.test_missing_profile_is_rejected) ... ok
test_scored_record_requires_finite_threshold (test_deck_update.PhysicalEvidenceTests.test_scored_record_requires_finite_threshold) ... ok

----------------------------------------------------------------------
Ran 11 tests in 3.710s

OK
```

The same chunk reports the canonical build path and `No errors detected in compressed data` for the PPTX.

An earlier complete GREEN run after implementing the core interfaces was chunk `7fc77a` (11/11, exit 0). The final run adds the clarified P3/P10/P23 semantic checks and the slide-2/4/5 visible wording checks.

## Build, conversion and verification record

| Operation | Tool evidence | Result |
|---|---|---|
| Initial canonical PPTX + notes build | `1200fd` | Exit 0 |
| First sandboxed LibreOffice export | `91c537` | Exit 1, no output; sandbox/profile restriction |
| Controller PDF export before final notes/visible wording corrections | `5e5fcc` session `29349`, completion `ef7842` | Exit 0; superseded as final handoff because PPT was subsequently rebuilt |
| Notes-only corrected build | `3a2f31` | Exit 0 |
| Final focused test + canonical PPTX/notes rebuild + ZIP check | `96299d` | Exit 0; PPT is final input for one controller export |
| Independent controller protected-input check | `7197dc` | All 21 protected prototype/evidence entries passed |
| Implementer protected-input check | `d719ab` | All protected entries passed |

No LibreOffice process is active from the implementer. The controller was told that the final editable PPTX is ready for exactly one final export.

## Final editable-artifact hashes

Recorded by chunk `d33664` after the final rebuild:

```text
a6d194e11fb589c8831829407b6c702860735433a4e337dc169119ce1981ef88  submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx
67b6b85d5c74a1f422be4dcd1ed4821ab0d67ceeb27da300004ba9bc735c396a  submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md
a761dacc232a4f6a64de247c85b3ae0330078faf54235e24aca693d4690dc5e1  submissions/SIH26237_NISHAN_PQ/build_deck.py
ebe2b061f7200c6fab1c8d4c1b0a2921a76139962a68e563c386c9083393c72f  submissions/SIH26237_NISHAN_PQ/deck_evidence.py
783cb2c8401b78ce7ea18d847c5b212e86ff926579e8dbeed7145cc197d439b1  submissions/SIH26237_NISHAN_PQ/verify_submission.py
5a915f637ca5ccef0cada3af1fce32b43f4db543a4457361d3194eacf6c09da0  submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py
```

The final PDF hash is intentionally not recorded yet because the final controller export has not occurred.

## Visual review

Controller review of the preceding render found slides 1–3 otherwise readable and later reported all six pages readable with no visible overlap. It requested the final wording changes now present in the PPTX:

- slide 2: `Experimental 1/4 per profile`, same-capture/no-added-recovery bullet, and conditional available-channel wording;
- slide 4: `1/4 per profile, same capture`;
- slide 5: visible multi-page plus signed/tagged PDF validation scope.

Because these visible edits occurred after that render, final visual confirmation of slides 2, 4 and 5 is pending on the controller’s final PDF export. Slides 1, 3 and 6 had no remaining visual findings.

## Pending controller checks

The following are deliberately pending rather than represented as completed:

1. Export the final `a6d194e…` PPTX once with headless LibreOffice.
2. Run `verify_submission.py --allow-placeholders`; expected result: success with placeholder warnings.
3. Run strict `verify_submission.py`; expected result: failure only for the unknown team ID/name/repository placeholders.
4. Run `pdfinfo` and confirm six 960 × 540 point pages.
5. Render all six pages, re-inspect changed slides 2, 4 and 5, and confirm no collision/overflow.
6. Record the final PDF SHA-256 and, if desired, append the final verifier/render results to this report.

## Concerns / limitations

- Team ID, registered team name and repository URL were not provided. Placeholders are therefore intentionally retained and strict upload-readiness verification must fail.
- Physical evidence is four captures of one printed, single-page public fixture. Historical recovery is 0/4; each experimental profile recovers the same one capture. This is not a population reliability/safety rate or end-to-end signed physical attribution.
- The deck and verifier are updated; unrelated older prose is not silently claimed corrected.
- Final PDF export and post-export visual/strict verification remain controller-owned at this report checkpoint.
