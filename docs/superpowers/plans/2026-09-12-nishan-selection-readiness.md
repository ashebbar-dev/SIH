# NISHAN Selection Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strengthen and demonstrate NISHAN's release safeguards, then produce an evidence-led six-slide selection presentation.

**Architecture:** Reuse the existing Python/PQC/watermark pipeline and ledger/witness locks. Add opt-in pinned witness enforcement and conservative PDF verdicts; generate fresh demonstration evidence without altering historical benchmarks. The existing deck builder consumes verified evidence and retains the official six-slide layout.

**Tech Stack:** Existing Python virtual environment, unittest, OpenSSL ML-KEM/ML-DSA, python-pptx, local PDF renderer and LibreOffice export.

**Spec:** research/NISHAN_SELECTION_READINESS_SPEC_2026-09-12.md

## Global Constraints

- Keep before snapshots because there is no Git repository. Do not initialize Git, publish a repository, install dependencies or change DHRUVA.
- Do not change the carrier, thresholds, frozen benchmark data or mathematical code.
- Preserve the existing SIH template/section order, logos and slide dimensions.
- Team name, team ID and public repository URL remain explicit missing fields unless supplied. The strict submission verifier must fail for missing required fields; draft mode may pass with those listed.
- State co-located validator/witness administration, trusted software/key custody, operator reproduction/framing, removal/retyping, non-blind reference and session-not-human-guilt limits.
- Historical 30/30 JPEG-Q55 result is a visual-channel experiment on one document/codebook with repeated sessions, not the current strict corroborated-PDF verdict and not physical performance.

### Task 1: Enforced release safeguards and reproducible demonstration

**Files:**
- Modify: prototypes/nishan_pq/nishan/core.py, witness.py, cli.py, README.md
- Create: prototypes/nishan_pq/tests/test_release_safeguards.py
- Update covering tests: prototypes/nishan_pq/tests/test_pdf_format_policy.py and other tests only where revised PDF verdict semantics require it.
- Create: prototypes/nishan_pq/tools/demo_release_safeguards.py
- Fresh generated output: research/evidence/nishan-selection-2026-09-12/demo/

**Interfaces:**
- Consumes existing ledger.exclusive(root), ledger.append(root, record, lock_held=True), witness.exclusive(root), witness.checkpoint(root, state, lock_held=True), witness.audit(root, state).
- Produces keyword-only witness_root and witness_public_key_sha3_256 arguments on decrypt_and_attribute and trace_leak, CLI flags --witness-root and --witness-public-key-sha3-256, explicit release_assurance in signed event/return and ledger_witness in trace evidence.
- Produces demo/results.json with version nishan-selection-safeguards/v1, pqc_ready boolean, cases list of objects {name, passed, observed}, all_passed boolean, code_sha256 object and limitations list. Tests/cases represent security scenarios, not independent population trials.

- [x] Read the security contract in the spec and existing call sites. Add failing tests before implementation. Reuse small public PDF fixtures from nishan.demo._sample_pdf and identity/ledger setup from test_pdf_format_policy. A core acceptance assertion is:

```python
with self.assertRaises(RuntimeError):
    decrypt_and_attribute(package, identities, "alice", secret, ledger_root,
                          output, witness_root=witness_root,
                          witness_public_key_sha3_256="0" * 64)
self.assertFalse(output.exists())
```

Concurrency test uses independently started processes, a barrier before entering decrypt (not inside the serialized allocation section), bounded joins and explicit worker error propagation. Force overlap through a deterministic hold/signal at the first allocation so the unpatched implementation allocates a duplicate while the patched process waits. Test a third successful release and distinct row assignments. Do not rely on chance timing alone.

- [x] Run focused tests RED using `.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -v`; retain command/output in the report.
- [x] Implement a small public wrapper/private locked helper rather than manually duplicating the release body. The transaction shape is:

```python
with ledger.exclusive(ledger_root):
    with witness.exclusive(witness_root) if witness_root is not None else nullcontext():
        return _decrypt_and_attribute_locked(...)
```

The helper uses append(lock_held=True), performs prechecks before plaintext materialization, and verifies checkpoint after append before publication. Reject witness_root resolving to ledger_root to avoid self-deadlock. Validate the paired keyword arguments before acquiring locks. Trace only holds these locks while auditing the consistent snapshot; extraction consumes that captured state.

Add a reusable witness pin/check helper that validates a 64-character hexadecimal digest, the configured actual public-key bytes, a nonempty valid chain and comparison exactly `consistent`. Bootstrap remains the explicit existing checkpoint-witness command. Use `hmac.compare_digest` for digest comparisons. After append, check the pin and healthy extending state before checkpoint, then use the strict helper to validate the resulting head. Fail closed without silently rolling back appended records.

For PDF tracing, set `require_corroboration=True` independently of suspect type/capacity; retain the legacy observation key for compatibility but add a clearly named `corroboration_required` key and `visual_only_research_leads`. Maintain existing full-PDF decision names where true; use an explicit missing-channel/inadequate-release-capacity reason for rasters/short documents. Signed fingerprint policy states this versioned behavior. New release assurance records distinguish witnessed and unwitnessed modes; do not insert local absolute paths into signed trust data.

- [x] Test real PQC happy paths and negative paths: pin mismatch/partial args, absent/empty checkpoint, coordinated rollback, checkpoint exception after append, existing-output preservation, trace makes no checkpoint, locks released after error, actual concurrent PDF issuance and raster-transplant/short-PDF abstention. Test exact clean PDF remains corroborated. Run focused tests then the complete NISHAN test suite once; document any skipped/unrelated failing cases explicitly.
- [x] Build the fresh demo runner using the same API, real PQC and public synthetic fixture. It refuses an already populated output root. It records actual distinct sessions/rows, signed-copy hash match, correct clean trace, rendered transplant abstention, low-capacity abstention, wrong-pin rejection, rollback rejection in release AND trace, checkpoint-failure no publication, plus code hashes. Failure results must exit nonzero; no fixed success strings independent of observations. Run:

```bash
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py --output research/evidence/nishan-selection-2026-09-12/demo
```

- [x] Update README examples for explicit witness initialization/checkpoint, pin provisioning, strict release/trace, crash recovery and trust limits. Self-review and write the report with RED/GREEN commands/output, files, new demo case counts and current caveats. No Git commit is possible; controller retains snapshots and review diff.

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

- [x] Read the current builder/evidence/verifier/tests. Add tests that fresh safeguard evidence is required for implemented claims and that wrong/missing case verdicts or code-hash drift reject the build. Preserve historical source identity and numerical checks. Example malformed-evidence assertion:

```python
bad = deepcopy(evidence)
bad["cases"][0]["passed"] = False
with self.assertRaises(ValueError):
    validate_safeguard_evidence(bad)
```

Define `validate_safeguard_evidence(evidence: dict) -> dict` in deck_evidence.py; it validates field types/schema, unique expected scenario names, all true verdicts, real PQC and code hashes. Return the validated dictionary. Reject unhashable/non-string case names with a clean ValueError, not a type error. Run focused RED tests, then implement.

- [x] Rework visible slide copy into the official sections: (1) title + accountable decryption value proposition; (2) proposed solution + three key capabilities; (3) technical approach/release gate diagram with managed-process trust boundary; (4) feasibility + fresh safeguards / historical visual results / unresolved physical evidence clearly separated; (5) impact + judge-driven demo + narrow second-round validation roadmap; (6) prior art/references + differentiated integration claim. Retain template headings even if their exact wording differs. Lead with value, not a wall of defects. Keep material limitations beside the relevant claim and full details in notes.

Use exact truthful headline phrases where helpful: `Accountable decryption. Verifiable source-copy evidence.`, `Commit and witness before release (configured mode)`, `Digital PDF corroboration; raster-only matches are research leads`, `Physical recovery remains experimental: 0/4 at the shipped threshold`. Never call new strict raster abstention a 30/30 attribution success. Label numerical studies by fixture/condition and experimental scope.

- [x] Update notes and paste-ready prose with user-relevant pitch, current test evidence, all retained R1–R14 and P1–P24 audit context corrected for implemented fixes, and explicit remaining boundaries. Remove stale “pending physical captures”, “witness not called”, “allocation nonatomic” claims only when new evidence supports the correction. Retain historical dates/conditions. No unsupported competitor performance figures or guaranteed winning language.
- [x] Write DEMO_RUNBOOK.md for a five-minute offline demonstration: prerequisites, invocation above with a new output path, two recipients/repeated session, clean PDF source association, rendered transplant inconclusive, rollback blocks strict release/trace, witness failure publishes nothing, then explain boundaries. Name team fields still needed. Do not ask user to overwrite historical evidence or expose private keys.
- [x] Run deck tests GREEN and build. Controller exports PDF, renders all six slides and checks layout/text/ZIP, draft verifier passes, strict verifier fails only for unsupplied team/repository fields. Report exact results and any remaining manual actions.
