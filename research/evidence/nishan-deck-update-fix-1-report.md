# NISHAN deck update — review round 1 fix report

Date: 11 September 2026  
Review source: `research/evidence/nishan-deck-update-task-review-1.md`  
Fix base: `submissions/SIH26237_NISHAN_PQ/archive/2026-09-11-review-round-1/`

## Outcome

All three Important findings and the one Minor finding were implemented together without changing the six-slide structure or the `R1:`–`R14:` / `P1:`–`P24:` audit mapping.

The report-creation workflow kept the official template as the visual authority, retained editable PowerPoint text/shapes, and required a rebuilt PPTX/notes pair plus ZIP/hash verification. No PDF export was run by the implementer; the controller owns the final conversion and scoped visual reinspection.

## Finding resolutions

### 1. Historical competing-score validation

The unreachable/inverted check was corrected. A scored record now fails when `highest_other_score` crosses the historical threshold but no competing row appears in `historical_accused`, symmetric with the conditional-threshold check. The fixed-study rule that no competing row is accused remains enforced separately.

Regression: `test_unaccused_competing_score_above_historical_threshold_is_rejected` sets a competing score above historical `Z=2100` but below a raised conditional threshold. This isolates the historical path and now produces an explicit `ValueError`.

### 2. Fixed capture and recovery identities

`load_physical()` now requires the exact capture set:

```text
akshay.jpeg
akshay1.jpeg
akshay2.jpeg
akshay3.jpeg
```

Errors identify missing and unexpected capture names before slide/notes code can reach a dictionary `KeyError`. The loader also requires:

- no historical recovered capture;
- `akshay3.jpeg` as the sole conditional recovery in `affine_baseline`;
- `akshay3.jpeg` as the sole conditional recovery in `affine_bias_translation`;
- the two fixed boundary failures at `(akshay.jpeg, affine_bias_translation)` and `(akshay1.jpeg, affine_bias_translation)`.

The summary now exports the recovery capture names and boundary-failure keys as well as counts. The verifier compares all of them with the reviewed fixed-study contract.

Capture/profile setting entries and record identity fields are also required to be strings before any set membership or dictionary-key operation. Malformed JSON objects/lists therefore produce actionable `ValueError` messages rather than escaping as raw unhashable-value `TypeError` exceptions.

Regressions:

- `test_renamed_capture_is_rejected_explicitly`
- `test_recovery_swapped_to_wrong_capture_is_rejected_explicitly`
- `test_malformed_identity_names_raise_explicit_value_error` (capture settings, profile settings and record identity subcases)

The recovery-swap test moves a complete, internally consistent scored outcome between `akshay2` and `akshay3`; it therefore exercises identity enforcement rather than failing on score/threshold consistency first.

### 3. JSON-derived displayed experimental counts

`build_deck.digital_summary()` now derives the shared slide/notes values once from the existing JSON inputs:

- exact/total JPEG sessions, roster rows, extra accusations, mean and population SD;
- issued-session count, minimum/maximum issued rows, null/non-null other-issued scores;
- codebook count, strategy count, code-case count and all-five recovery count;
- recorded digital attack count;
- released-PDF count, common pages per PDF and mean PSNR;
- layout encoded-symbol count.

Physical slide/notes counts continue to come from `load_physical()`. The remaining manual visible forms were replaced:

- slide 2: `4 captures` is generated from `physical['captures']`;
- slide 4: `1-page fixture / 4 captures` is generated from saved PDF page metrics and physical capture count;
- slide 4: code-level/physical-trial comparison uses the derived code-case count;
- slide 4: PDF-count caption uses the derived released-PDF count;
- notes: R3, R9, P4, P10, P11, P12, P13 and P19 use the shared derived summary.

Context-only Tardos parameter comparisons remain fixed and explicitly labelled as comparisons, not measured experiments.

Regression `test_displayed_counts_follow_mutated_json_copies` builds a real temporary PPTX from copied JSON with 31 issued sessions, 29 exact results, 999 roster rows, 31 codebooks, four strategies, 124 code cases and six PDF metrics. It verifies that both editable slide text and embedded notes change accordingly, including rows `0..30` and the `1` null / `30` non-null other-issued-score counts.

### 4. Dead/compatibility inputs

- Removed the unused `jpeg_violation_rate` calculation.
- `metrics_path` is now actively used to derive the saved 126-symbol layout count.
- Kept positional `evidence_chart` for compatibility with the archived builder and existing callers. Its builder docstring and CLI help now state that it is intentionally ignored because slide 2 uses editable evidence cards.
- Removed unused `measured`/raw evidence arguments from internal slide helper signatures; the helpers consume the shared derived summary.

## RED

Command:

```bash
.venv/bin/python -B -m unittest discover -s submissions/SIH26237_NISHAN_PQ/tests -p 'test_deck_update.py' -v
```

Tool chunk: `2d4c4a`  
Exit: `1`  
Elapsed: 8.60 s

Actual status output:

```text
test_build_has_six_editable_slides_and_complete_matching_notes ... ok
test_displayed_counts_follow_mutated_json_copies ... FAIL
test_slide_claims_are_evidence_derived ... ok
test_verifier_rejects_missing_physical_evidence ... ok
test_verifier_rejects_stale_pdf_claim ... ok
test_verifier_rejects_stale_pptx_claim ... ok
test_duplicate_record_is_rejected ... ok
test_exact_physical_summary ... ok
test_false_counted_success_is_rejected ... ok
test_missing_input_is_explicit ... ok
test_missing_profile_is_rejected ... ok
test_recovery_swapped_to_wrong_capture_is_rejected_explicitly ... FAIL
test_renamed_capture_is_rejected_explicitly ... FAIL
test_scored_record_requires_finite_threshold ... ok
test_unaccused_competing_score_above_historical_threshold_is_rejected ... FAIL

FAIL: test_displayed_counts_follow_mutated_json_copies
AssertionError: 'All 999 rows scored; 2 extra rows accused' not found

FAIL: test_recovery_swapped_to_wrong_capture_is_rejected_explicitly
AssertionError: ValueError not raised

FAIL: test_renamed_capture_is_rejected_explicitly
AssertionError: ValueError not raised

FAIL: test_unaccused_competing_score_above_historical_threshold_is_rejected
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 15 tests in 7.203s

FAILED (failures=4)
```

The raw tool output also showed the generated temporary slide text for the count failure. Its relevant values proved the partial pre-fix state: `29/31` and `124` were derived, but the slide still contained manual `All 1,000 rows`, `MEAN PSNR · 5 PDFs`, `120 code-level cases` and `One page / four captures` strings.

## GREEN

Command:

```bash
.venv/bin/python -B -m unittest discover -s submissions/SIH26237_NISHAN_PQ/tests -p 'test_deck_update.py' -v
```

Tool chunk: `42c176`  
Exit: `0`  
Elapsed: 6.38 s

Actual output:

```text
test_build_has_six_editable_slides_and_complete_matching_notes (test_deck_update.DeckAndVerifierTests.test_build_has_six_editable_slides_and_complete_matching_notes) ... ok
test_displayed_counts_follow_mutated_json_copies (test_deck_update.DeckAndVerifierTests.test_displayed_counts_follow_mutated_json_copies) ... ok
test_slide_claims_are_evidence_derived (test_deck_update.DeckAndVerifierTests.test_slide_claims_are_evidence_derived) ... ok
test_verifier_rejects_missing_physical_evidence (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_missing_physical_evidence) ... ok
test_verifier_rejects_stale_pdf_claim (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_stale_pdf_claim) ... ok
test_verifier_rejects_stale_pptx_claim (test_deck_update.DeckAndVerifierTests.test_verifier_rejects_stale_pptx_claim) ... ok
test_duplicate_record_is_rejected (test_deck_update.PhysicalEvidenceTests.test_duplicate_record_is_rejected) ... ok
test_exact_physical_summary (test_deck_update.PhysicalEvidenceTests.test_exact_physical_summary) ... ok
test_false_counted_success_is_rejected (test_deck_update.PhysicalEvidenceTests.test_false_counted_success_is_rejected) ... ok
test_missing_input_is_explicit (test_deck_update.PhysicalEvidenceTests.test_missing_input_is_explicit) ... ok
test_missing_profile_is_rejected (test_deck_update.PhysicalEvidenceTests.test_missing_profile_is_rejected) ... ok
test_recovery_swapped_to_wrong_capture_is_rejected_explicitly (test_deck_update.PhysicalEvidenceTests.test_recovery_swapped_to_wrong_capture_is_rejected_explicitly) ... ok
test_renamed_capture_is_rejected_explicitly (test_deck_update.PhysicalEvidenceTests.test_renamed_capture_is_rejected_explicitly) ... ok
test_scored_record_requires_finite_threshold (test_deck_update.PhysicalEvidenceTests.test_scored_record_requires_finite_threshold) ... ok
test_unaccused_competing_score_above_historical_threshold_is_rejected (test_deck_update.PhysicalEvidenceTests.test_unaccused_competing_score_above_historical_threshold_is_rejected) ... ok

----------------------------------------------------------------------
Ran 15 tests in 5.197s

OK
```

An intermediate run, chunk `83592c`, passed all four original regression cases and 14/15 total tests; the sole failure was the old P11 semantic-anchor wording. The test and verifier anchor were aligned to the more precise derived phrase `one recipient identity across 30 accumulated issued sessions`, after which `42c176` passed.

### Supplemental malformed-name RED/GREEN

After the final PPT handoff, controller spot-checking found that unhashable JSON values in identity-name positions could still raise raw `TypeError`. No slide or note text was affected.

RED command: the same focused discovery command above.  
RED chunk: `2ea6dd`; exit `1`.

```text
test_malformed_identity_names_raise_explicit_value_error ...
  (label='capture settings') ... ERROR
  (label='profile settings') ... ERROR
  (label='record identity') ... ERROR

TypeError: cannot use 'dict' as a set element (unhashable type: 'dict')
TypeError: cannot use 'list' as a set element (unhashable type: 'list')
TypeError: cannot use 'tuple' as a dict key (unhashable type: 'dict')

----------------------------------------------------------------------
Ran 16 tests in 6.194s

FAILED (errors=3)
```

GREEN command: the same focused discovery command plus hashes of the two changed source/test files.  
GREEN chunk: `726ac1`; exit `0`.

```text
test_build_has_six_editable_slides_and_complete_matching_notes ... ok
test_displayed_counts_follow_mutated_json_copies ... ok
test_slide_claims_are_evidence_derived ... ok
test_verifier_rejects_missing_physical_evidence ... ok
test_verifier_rejects_stale_pdf_claim ... ok
test_verifier_rejects_stale_pptx_claim ... ok
test_duplicate_record_is_rejected ... ok
test_exact_physical_summary ... ok
test_false_counted_success_is_rejected ... ok
test_malformed_identity_names_raise_explicit_value_error ... ok
test_missing_input_is_explicit ... ok
test_missing_profile_is_rejected ... ok
test_recovery_swapped_to_wrong_capture_is_rejected_explicitly ... ok
test_renamed_capture_is_rejected_explicitly ... ok
test_scored_record_requires_finite_threshold ... ok
test_unaccused_competing_score_above_historical_threshold_is_rejected ... ok

----------------------------------------------------------------------
Ran 16 tests in 6.511s

OK
```

## Final build and integrity

Commands:

```bash
.venv/bin/python -B submissions/SIH26237_NISHAN_PQ/build_deck.py
unzip -t submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx
sha256sum submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md submissions/SIH26237_NISHAN_PQ/build_deck.py submissions/SIH26237_NISHAN_PQ/deck_evidence.py submissions/SIH26237_NISHAN_PQ/verify_submission.py submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py
sha256sum -c research/evidence/nishan-deck-update-protected.sha256
```

Tool chunk: `864dd2`  
Exit: `0`

Results:

- Canonical PPTX and Markdown notes rebuilt.
- PPTX ZIP: `No errors detected in compressed data`.
- All protected prototype/evidence hashes: `OK`.
- No LibreOffice conversion was run.

Final hashes:

```text
43189cec6406875c77183481671330e18c6a722f4adcf64739823a06d641f1b2  submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx
e667055fbcb987d269764201d57af37fb183754661cf9de47865f0c12a1023e2  submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md
b8fb0b65b59527604d78fd9409ed59ad8b48fae261dbd403c373819a9dbc0140  submissions/SIH26237_NISHAN_PQ/build_deck.py
370407b83083a7a1f19bbf88217a7b921fb7e5f7a2e2c0ede55c581648273a7d  submissions/SIH26237_NISHAN_PQ/deck_evidence.py
299b859dad9333f18594e4de29f19581043a4c0935d35bf8cebff2fe17cbdf35  submissions/SIH26237_NISHAN_PQ/verify_submission.py
8488d91bdee8c815318561e4687cac252a9e16a450ffcb3882ec015dee913749  submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py
```

The supplemental validation-only change did not alter or rebuild the final PPTX/notes, whose hashes remain the values shown above.

## Visual/PDF handoff

The user-facing narrative and six-slide layout were not redesigned. Canonical visible wording changes are limited to:

- slide 2: `Four captures` → `4 captures`;
- slide 4: `One page / four captures` → `1-page fixture / 4 captures`.

The PDF count and code-case strings are now generated but render to the same canonical values (`5 PDFs`, `120`). The controller only needs to re-export the final PPTX and reinspect slides 2 and 4. The current PDF predates this fix-wave build and is not claimed as final here.

The previous complete artifact-validation record remains at `research/evidence/nishan-deck-update-controller-validation.md`; it establishes that the pre-fix six-page PDF/PPT package and verification path worked before these bounded source changes.

## Remaining limitation

Team ID, registered team name and repository URL remain explicit placeholders because no values were supplied. Draft verification should pass with warnings after controller export; strict verification should fail only on those placeholders.
