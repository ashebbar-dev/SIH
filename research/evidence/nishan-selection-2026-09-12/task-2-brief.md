### Task 2: Evidence-led six-slide presentation and handoff package

**Files:**
- Modify: submissions/SIH26237_NISHAN_PQ/build_deck.py, deck_evidence.py, verify_submission.py, tests/test_deck_update.py, paste_ready_submission.md
- Regenerate: NISHAN-PQ_SIH26237.pptx and NISHAN-PQ_SIH26237_speaker_notes.md
- Create: submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md
- Controller exports and validates matching NISHAN-PQ_SIH26237.pdf after source review.

**Interfaces:**
- Consume Task 1 demo/results.json schema and original benchmark JSON already consumed by deck_evidence.py. Check all_passed agrees with every case and real pqc_ready; verify current code hashes against demo code_sha256 before claiming new tests are current.
- Required scenario names from the Task 1 interface: concurrent_distinct_sessions_rows, third_release_row, signed_copy_hash_match, clean_pdf_trace, trace_read_only, rendered_transplant_abstains, low_capacity_pdf_abstains, wrong_pin_rejected, rollback_release_rejected, rollback_trace_rejected, checkpoint_failure_no_publication, checkpoint_failure_preserves_existing_output. Validate exact coverage, not only a count of true booleans. Match the finalized report if a reviewed interface correction occurs.
- Preserve all existing source provenance/numerical-evidence and strict-placeholder checks while replacing stale claim wording. The builder stays repeatable with native editable shapes, complete slide notes and six slides.

- [ ] Read the current builder/evidence/verifier/tests. Add tests that fresh safeguard evidence is required for implemented claims and that wrong/missing case verdicts or code-hash drift reject the build. Preserve historical source identity and numerical checks. Example malformed-evidence assertion:

```python
bad = deepcopy(evidence)
bad["cases"][0]["passed"] = False
with self.assertRaises(ValueError):
    validate_safeguard_evidence(bad)
```

Define `validate_safeguard_evidence(evidence: dict) -> dict` in deck_evidence.py; it validates field types/schema, unique expected scenario names, all true verdicts, real PQC and code hashes. Return the validated dictionary. Reject unhashable/non-string case names with a clean ValueError, not a type error. Run focused RED tests, then implement.

- [ ] Rework visible slide copy into the official sections: (1) title + accountable decryption value proposition; (2) proposed solution + three key capabilities; (3) technical approach/release gate diagram with managed-process trust boundary; (4) feasibility + fresh safeguards / historical visual results / unresolved physical evidence clearly separated; (5) impact + judge-driven demo + narrow second-round validation roadmap; (6) prior art/references + differentiated integration claim. Retain template headings even if their exact wording differs. Lead with value, not a wall of defects. Keep material limitations beside the relevant claim and full details in notes.

Use exact truthful headline phrases where helpful: `Accountable decryption. Verifiable source-copy evidence.`, `Commit and witness before release (configured mode)`, `Digital PDF corroboration; raster-only matches are research leads`, `Physical recovery remains experimental: 0/4 at the shipped threshold`. Never call new strict raster abstention a 30/30 attribution success. Label numerical studies by fixture/condition and experimental scope.

- [ ] Update notes and paste-ready prose with user-relevant pitch, current test evidence, all retained R1–R14 and P1–P24 audit context corrected for implemented fixes, and explicit remaining boundaries. Remove stale “pending physical captures”, “witness not called”, “allocation nonatomic” claims only when new evidence supports the correction. Retain historical dates/conditions. No unsupported competitor performance figures or guaranteed winning language.
- [ ] Write DEMO_RUNBOOK.md for a five-minute offline demonstration: prerequisites, invocation above with a new output path, two recipients/repeated session, clean PDF source association, rendered transplant inconclusive, rollback blocks strict release/trace, witness failure publishes nothing, then explain boundaries. Name team fields still needed. Do not ask user to overwrite historical evidence or expose private keys.
- [ ] Run deck tests GREEN and build. Controller exports PDF, renders all six slides and checks layout/text/ZIP, draft verifier passes, strict verifier fails only for unsupplied team/repository fields. Report exact results and any remaining manual actions.
