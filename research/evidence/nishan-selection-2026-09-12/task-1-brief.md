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

- [ ] Read the security contract in the spec and existing call sites. Add failing tests before implementation. Reuse small public PDF fixtures from nishan.demo._sample_pdf and identity/ledger setup from test_pdf_format_policy. A core acceptance assertion is:

```python
with self.assertRaises(RuntimeError):
    decrypt_and_attribute(package, identities, "alice", secret, ledger_root,
                          output, witness_root=witness_root,
                          witness_public_key_sha3_256="0" * 64)
self.assertFalse(output.exists())
```

Concurrency test uses independently started processes, a barrier before entering decrypt (not inside the serialized allocation section), bounded joins and explicit worker error propagation. Force overlap through a deterministic hold/signal at the first allocation so the unpatched implementation allocates a duplicate while the patched process waits. Test a third successful release and distinct row assignments. Do not rely on chance timing alone.

- [ ] Run focused tests RED using `.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -v`; retain command/output in the report.
- [ ] Implement a small public wrapper/private locked helper rather than manually duplicating the release body. The transaction shape is:

```python
with ledger.exclusive(ledger_root):
    with witness.exclusive(witness_root) if witness_root is not None else nullcontext():
        return _decrypt_and_attribute_locked(...)
```

The helper uses append(lock_held=True), performs prechecks before plaintext materialization, and verifies checkpoint after append before publication. Reject witness_root resolving to ledger_root to avoid self-deadlock. Validate the paired keyword arguments before acquiring locks. Trace only holds these locks while auditing the consistent snapshot; extraction consumes that captured state.

Add a reusable witness pin/check helper that validates a 64-character hexadecimal digest, the configured actual public-key bytes, a nonempty valid chain and comparison exactly `consistent`. Bootstrap remains the explicit existing checkpoint-witness command. Use `hmac.compare_digest` for digest comparisons. After append, check the pin and healthy extending state before checkpoint, then use the strict helper to validate the resulting head. Fail closed without silently rolling back appended records.

For PDF tracing, set `require_corroboration=True` independently of suspect type/capacity; retain the legacy observation key for compatibility but add a clearly named `corroboration_required` key and `visual_only_research_leads`. Maintain existing full-PDF decision names where true; use an explicit missing-channel/inadequate-release-capacity reason for rasters/short documents. Signed fingerprint policy states this versioned behavior. New release assurance records distinguish witnessed and unwitnessed modes; do not insert local absolute paths into signed trust data.

- [ ] Test real PQC happy paths and negative paths: pin mismatch/partial args, absent/empty checkpoint, coordinated rollback, checkpoint exception after append, existing-output preservation, trace makes no checkpoint, locks released after error, actual concurrent PDF issuance and raster-transplant/short-PDF abstention. Test exact clean PDF remains corroborated. Run focused tests then the complete NISHAN test suite once; document any skipped/unrelated failing cases explicitly.
- [ ] Build the fresh demo runner using the same API, real PQC and public synthetic fixture. It refuses an already populated output root. It records actual distinct sessions/rows, signed-copy hash match, correct clean trace, rendered transplant abstention, low-capacity abstention, wrong-pin rejection, rollback rejection in release AND trace, checkpoint-failure no publication, plus code hashes. Failure results must exit nonzero; no fixed success strings independent of observations. Run:

```bash
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py --output research/evidence/nishan-selection-2026-09-12/demo
```

- [ ] Update README examples for explicit witness initialization/checkpoint, pin provisioning, strict release/trace, crash recovery and trust limits. Self-review and write the report with RED/GREEN commands/output, files, new demo case counts and current caveats. No Git commit is possible; controller retains snapshots and review diff.

