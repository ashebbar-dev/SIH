# Task 1 — NISHAN release safeguards and fresh demonstration

Current handoff includes **fix round 1 for Important I1**, documented at the end of this report: all 59 final-code tests passed, and the regenerated real-PQC demonstration passed 12/12 scenarios. Earlier sections preserve the initial Task 1 validation history; its successful demo is now retained at [demo-before-fix1/results.json](demo-before-fix1/results.json). The current [demo/results.json](demo/results.json) is the post-fix run.

Scope: the binding `research/NISHAN_SELECTION_READINESS_SPEC_2026-09-12.md` security/evidence contract and `task-1-brief.md`. No Git repository was initialized; the controller's `before.tar.gz` remains the comparison point. DHRUVA, carrier implementations, mathematical code, thresholds, historical artifacts and submission deck files were not edited.

## Result

Implemented serialized release transactions, opt-in independently provisioned witness pin enforcement, conservative PDF-source attribution, and the fresh real-PQC scenario runner. Final stable-code validation passed all 55 NISHAN tests with no skips or failures. The required fresh demonstration reports `pqc_ready: true`, twelve observed cases, and `all_passed: true` in [demo/results.json](demo/results.json).

### Release and trace behavior

- Public release validates paired witness arguments before locking, rejects a witness root resolving to the ledger root, and uses the small public wrapper/private locked-helper structure. The ledger lock precedes the witness lock and spans validation, row allocation, embedding, signing, append, postchecks, checkpoint and publication. Calls to `ledger.append` and `witness.checkpoint` use `lock_held=True`.
- Strict witness helpers validate a 64-character hexadecimal pin, compare it with the actual public-key bytes using `hmac.compare_digest`, require a valid nonempty signed checkpoint chain, and accept only an exactly `consistent` pre/post state. There is no bootstrap or extension repair in release/trace. After append, the existing pinned anchor must still be healthy and anchor an extension, then the new checkpoint must validate consistently.
- Signed events carry versioned `release_assurance` with `pinned_witness` or explicit `unwitnessed` mode and the pin when supplied. Return values add the checked checkpoint metadata. Signed assurance contains no local absolute paths and explicitly means authorization, not delivery/reading proof.
- Checkpoint exception, no-op checkpoint, corrupt checkpoint or post-append pin substitution prevents publication. The appended authorization remains committed; an existing destination remains unchanged. Further strict calls reject the unwitnessed extension until deliberate checkpoint recovery. Tests exercise recovery and later successful release.
- Trace verifies the healthy signed ledger and optional consistent pinned witness under both locks, then extracts against that captured state after releasing the locks. It never checkpoints. Evidence adds `ledger_witness`; it identifies the checked snapshot, not perpetual freshness.
- Every Tardos PDF-source trace passes `require_corroboration=True`, including rasters and low-capacity releases. Existing clean/full-PDF decision names remain. Rasters explicitly produce `abstain_missing_layout_channel`; low-capacity releases produce `abstain_inadequate_release_capacity`. `attribution` is empty and `visual_only_research_leads` retains positive visual candidates. The compatibility observation key remains, with unambiguous `corroboration_required: true` added. Signed fingerprints state `pdf-all-formats-corroboration/v1` and the capacity limitation. Generic-image screening remains supported.
- CLI decrypt/trace expose both witness flags. The explicit checkpoint command now obtains ledger then witness locks and validates recipient-signed history before checkpointing. The checkpoint API also refuses a replaced ledger trust root.
- A real first demo exposed an existing cross-filesystem publication defect. `/tmp` and the workspace are different mounts: `os.replace` raised `EXDEV` after commit/checkpoint. Release now creates its private temporary directory on the destination filesystem, after security prechecks, so final publication stays atomic. The failed attempt is retained at [demo-failed-cross-device/results.json](demo-failed-cross-device/results.json), including its original code hashes and nonzero outcome. It was moved, not overwritten.

## TDD and verification record

### Initial focused RED, before implementation

Command:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -v
```

Observed output excerpts and actual terminal summary:

```text
test_concurrent_issuance_has_distinct_rows_and_third_release_succeeds ... FAIL
AssertionError: Lists differ: [0, 0] != [0, 1]
test_rendered_transplant_retains_leads_without_attribution ... FAIL
AssertionError: Lists differ: [{'recipient_id': 'alice', ...}] != []
test_short_pdf_abstains_with_signed_capacity_limitation ... ERROR
KeyError: 'fusion_policy_version'
TypeError: decrypt_and_attribute() got an unexpected keyword argument 'witness_root'
TypeError: decrypt_and_attribute() got an unexpected keyword argument 'witness_public_key_sha3_256'
Ran 8 tests in 43.195s
FAILED (failures=2, errors=15)
```

The fifteen errors include subtests exercising absent APIs and the missing signed policy, not fifteen independent test methods. Actual unpatched rendered-transplant attribution selected Alice with visual score `17396.173273`. The concurrency RED result is deterministic: two independently spawned processes meet a barrier before decrypt; the first holds at allocation while the second reaches its ledger-lock attempt. Before the fix both had already allocated row 0; after the fix the second process blocks before allocation. Bounded event waits/joins and explicit worker traceback propagation prevent silent worker failures. A third successful release verifies the history remains usable.

### Focused GREEN and additional security coverage

The same focused command initially passed all 8 tests in `107.907s` (exit 0). Three additional security tests then covered no-op/corrupt checkpoints, actual-key pin substitution after append, and foreign ledger root/invalid witness signatures. The expanded focused command passed all 11 tests in `82.796s` (exit 0). Its complete output is [task-1-focused-green.txt](task-1-focused-green.txt).

The real demo's cross-filesystem failure was converted into an additional RED regression before the staging fix:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -k workspace_destination -v
OSError: [Errno 18] Invalid cross-device link
Ran 1 test in 8.219s
FAILED (errors=1)
```

After the fix, the identical command passed: `Ran 1 test in 7.843s`, `OK`, exit 0. Complete outputs: [RED](task-1-cross-filesystem-red.txt), [GREEN](task-1-cross-filesystem-green.txt).

An initial full-suite command had already started when the demo exposed that publication issue. It completed 54 tests in `217.303s`, `OK`, no skips/failures, with its original imported release code. Its output is retained in [task-1-suite-before-publication-fix.txt](task-1-suite-before-publication-fix.txt); it is not presented as final-code validation. The final full-suite command was restarted after all code and the twelfth safeguards test were stable:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
```

Final stable-code result (exit 0):

```text
Ran 55 tests in 314.746s
OK
```

All 55 passed, with zero skips, failures or errors, including all twelve safeguards test methods. Complete output: [task-1-suite-final.txt](task-1-suite-final.txt). No further source changes were made after this final run began.

CLI flag availability was checked with `.venv/bin/python -m nishan decrypt --help` (exit 0), which listed both witness flags. The final suite includes the existing generic-image JPEG/collusion screening, recipient-signature/enrollment/replay safeguards, PDF parser variants, original carrier/math tests and the physical-boundary tests; no thresholds or frozen evidence were rewritten.

## Fresh demo and provenance

Command:

```text
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py --output research/evidence/nishan-selection-2026-09-12/demo
```

Actual final stdout, exit 0:

```json
{
  "results": "research/evidence/nishan-selection-2026-09-12/demo/results.json",
  "pqc_ready": true,
  "cases": 12,
  "all_passed": true
}
```

The profile is real `OpenSSL 3.6.4 25 Aug 2026`, ML-KEM-768 and ML-DSA-65 available, the existing 1,000-row / coalition-limit-five / familywise-target-1e-6 Tardos profile, and public synthetic PDFs. The runner exits nonzero for unavailable PQC, unexpected harness errors or any failed scenario. Running the same command again against the populated root returned exit 1 with `FileExistsError: refusing populated output root`; the evidence was preserved.

| Scenario | Actual observation | Passed |
| --- | --- | --- |
| concurrent_distinct_sessions_rows | Two real processes; rows 0 and 1; distinct sessions | yes |
| third_release_row | Next release row 2 and a new session | yes |
| signed_copy_hash_match | All three published copies match signed SHA3-256 receipts | yes |
| clean_pdf_trace | `corroborated_channels`, correct Alice session | yes |
| trace_read_only | Checkpoint bytes unchanged; checkpoint call patched to fail if invoked | yes |
| rendered_transplant_abstains | `abstain_missing_layout_channel`, empty attribution, visual research lead retained | yes |
| low_capacity_pdf_abstains | `abstain_inadequate_release_capacity`, empty attribution, signed capacity limitation and visual lead retained | yes |
| wrong_pin_rejected | RuntimeError before output publication | yes |
| rollback_release_rejected | All replicas truncated consistently; quorum remains valid; strict release rejects `rollback_detected` | yes |
| rollback_trace_rejected | Strict trace rejects the same rollback | yes |
| checkpoint_failure_no_publication | Ledger length 4 → 5; `unwitnessed_extension`; no destination created | yes |
| checkpoint_failure_preserves_existing_output | Ledger length 4 → 5; `unwitnessed_extension`; existing destination unchanged | yes |

Actual first two sessions: `5cadc5a5-25a8-49e3-abf4-17472a70989f` and `490057fc-748f-48da-bcef-2bbcca70d3c2`. Third session: `2d84d7e2-306c-41e9-9d0e-d66b26030ed4`. The runner records observations, signed release returns and complete clean/raster/short-PDF evidence rather than synthesizing success strings. These are twelve security scenarios on synthetic fixtures, not twelve independent population trials.

`code_sha256` contains 19 nonempty entries: all sixteen `nishan/*.py` modules, the runner, safeguards tests and PDF policy tests. This includes changed `core.py`, `witness.py`, `cli.py` and unchanged `ledger.py`. Validation command:

```text
jq -r '.code_sha256 | to_entries[] | "\(.value)  \(.key)"' research/evidence/nishan-selection-2026-09-12/demo/results.json | sha256sum -c -
```

All 19 entries returned `OK` (exit 0). Random synthetic keys/session IDs are fresh; report structure/profile is reproducible, not byte-for-byte cryptographic outputs. Demo key material is synthetic-only and is not a production trust anchor.

## Changed files and self-review

Modified existing files: `prototypes/nishan_pq/nishan/core.py`, `witness.py`, `cli.py`; `prototypes/nishan_pq/README.md`; `prototypes/nishan_pq/tests/test_pdf_format_policy.py`. Created: `prototypes/nishan_pq/tests/test_release_safeguards.py` and `prototypes/nishan_pq/tools/demo_release_safeguards.py`. Fresh generated output/report/logs are confined to this evidence directory; one temporary cross-filesystem test directory was automatically cleaned up.

Self-review inspected unified diffs against the controller's tar snapshot for core, witness, CLI and README, plus the new test/runner code. `tar -dzf .../before.tar.gz prototypes/nishan_pq` reported changed contents only for the five intended existing files listed above. Carrier, ledger implementation, math, registration and historical artifacts remain unchanged. Reviewed lock acquisition and release, absence of recursive append/checkpoint locking, pre-decryption checks, post-append pin checking, post-checkpoint checking, existing-output preservation, release authorization semantics, read-only trace snapshots, CLI argument forwarding, and the conservative attribution rule. The fresh cross-filesystem failure was retained and fixed with a failing regression before the fix. No dependency installs, Git initialization/commits or deployment occurred.

## Limits retained

Local advisory locks serialize cooperating processes on this filesystem; they are not distributed consensus. Witness and validator keys/administration remain co-located, without hardware isolation. Independently provisioned pins and externally retained witness state are deployment requirements; rolling back the witness itself along with the ledger is outside this local guarantee. Software/key custody is trusted, the authority can reproduce carriers and frame a session, and a session candidate is not proof of human guilt, delivery or reading. Trace is non-blind; removal/retyping can defeat both carriers. PDF raster and short-document signals are research leads only. Generic-image results remain research screening.

Historical JPEG-Q55 30/30 was one document/codebook with repeated sessions and a visual-channel verdict, not the current strict PDF verdict or physical performance. Historical shipped physical threshold recovered 0/4; experimental profiles recovered the same 1/4 capture. These facts do not establish held-out population or robust physical recovery. Independent witness governance, hardware-isolated signing, a portable independent proof verifier, larger held-out tests and robust physical recovery remain future work. There is no claim of competition acceptance or production certification.

## Fix round 1 — Important I1 resolved

Read the independent review's I1 verbatim and the amended binding security/evidence contract before editing. The controller chose enforcement of the actual PDF-source policy rather than narrowing claims. The exact reviewed base remains `task-1-after.tar.gz`.

### What changed and why

`encrypt_once` now obtains type metadata from the existing content parser instead of the filename suffix. After AES-GCM authentication and source-hash validation, release classifies the actual plaintext bytes in private staging, rejects an inconsistent package `media_type`, and selects the release profile from that parsed result. Editing only `source.media_type` before first strict issuance now raises `RuntimeError: package media type does not match authenticated plaintext`; no output, signed append or checkpoint update is produced.

Parser-recognized renamed/prefixed PDFs take the PDF profile. The unchanged PDF carrier requires `.pdf` input/output staging names, so the already-validated PDF bytes are renamed within the private staging directory to `source.pdf`, with `marked.pdf` as the carrier destination. This changes neither document bytes nor the carrier implementation. The source commitment remains bound to the original authenticated bytes.

Trace classifies its reference with the same content parser. Actual PDF references backed by legacy generic or absent receipts raise a clear RuntimeError before generic scoring, including a prefixed PDF with a non-PDF suffix. Signed legacy-style fixtures are still valid signed-ledger history; they cannot grant access to generic PDF attribution. Existing genuinely raster sources continue to produce `image` metadata, generic-image release fingerprints and the established JPEG/collusion screening results.

README documents the classification guard and legacy-PDF rejection. There is no signed-manifest redesign, new threshold, mathematical change or carrier change. Witness enforcement and transaction ordering are unchanged.

### Focused RED before implementation

All commands ran with real available PQC and exited 1 on the reviewed implementation:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -k 'pdf_source' -v
Ran 2 tests in 13.502s
FAILED (failures=2)
```

Actual failures: media-type-only tampering produced no expected RuntimeError, and a renamed/prefixed PDF package was labeled `image` instead of `application/pdf`. Full output: [task-1-fix1-source_red.txt](task-1-fix1-source_red.txt).

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_pdf_format_policy.py -k encrypt_classifies -v
Ran 1 test in 0.808s
FAILED (failures=2)
```

The two failed subcases were PDF bytes with `.bin` suffix, both with and without a newline preamble. Full output: [task-1-fix1-encrypt_red.txt](task-1-fix1-encrypt_red.txt).

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -k legacy_generic_pdf -v
Ran 1 test in 19.923s
FAILED (failures=2)
```

Both normal and renamed/prefixed PDF-reference subcases reached the sentinel `AssertionError: legacy PDF reached generic screening`, proving that the guard was absent before the fix. These fixtures use real generic-carrier PDF output, valid recipient signatures and a healthy explicitly checkpointed witness; scoring was intercepted to test rejection before screening, not to claim an empirical default-threshold attack rate. Full output: [task-1-fix1-legacy_red.txt](task-1-fix1-legacy_red.txt).

### Covering GREEN and staging correction

The first amended-code covering commands were:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -v
Ran 15 tests in 60.726s
FAILED (errors=1)

.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_pdf_format_policy.py -v
Ran 4 tests in 25.473s
OK

.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_end_to_end.py -v
Ran 1 test in 23.142s
OK
```

The single remaining release error was the unchanged carrier's explicit `.pdf` input/output suffix precondition. After canonicalizing only the validated PDF staging filenames, the targeted command passed:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p test_release_safeguards.py -k renamed_prefixed_pdf -v
Ran 1 test in 3.438s
OK
```

Complete actual outputs: [initial covering release run](task-1-fix1-covering-initial-release.txt), [PDF policy GREEN](task-1-fix1-pdf-green.txt), [genuine-image GREEN](task-1-fix1-image-green.txt), [renamed PDF GREEN](task-1-fix1-renamed-green.txt). Existing generic-image assertions still verify exact Bob JPEG attribution and the two-/three-copy coalition screening results; new assertions explicitly verify `image` metadata and the generic-image fingerprint scheme.

After all source edits were complete, exactly one full suite ran for this fix round:

```text
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
Ran 59 tests in 63.472s
OK
```

Exit 0, all 59 tests passed, zero skips/errors/failures, including all fifteen safeguards methods, all four PDF-policy methods and the genuine-image end-to-end test. Full output: [task-1-fix1-suite-final.txt](task-1-fix1-suite-final.txt). No source changes followed this final run.

### Regenerated actual demo and provenance

Preserved the previous successful demo recoverably by moving it to `demo-before-fix1/`; no historical result was overwritten. Ran the unchanged twelve-case runner again on the stable amended code:

```text
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py --output research/evidence/nishan-selection-2026-09-12/demo
```

Actual stdout, exit 0:

```json
{
  "results": "research/evidence/nishan-selection-2026-09-12/demo/results.json",
  "pqc_ready": true,
  "cases": 12,
  "all_passed": true
}
```

The current real-PQC report retains the same twelve actual scenarios and limitations. In this fresh run Alice/Bob are recorded with rows `[1, 0]` because process ordering is deliberately unconstrained, and distinct sessions `b852c2de-6ce3-4727-b820-5edeabc0ad78` and `9bb88924-d0ba-4943-b113-4ae1bc2e6174`. The third successful release takes row 2 with session `70c3bcc8-e4a4-42a2-8e93-adf64106e7f5`. Clean corroboration, raster/short-PDF abstention with retained leads, pin/rollback rejection and both checkpoint-publication failures all pass. These are scenarios, not independent population trials.

All nineteen current demo code hashes were verified using the same `jq ... | sha256sum -c -` command recorded above; every entry returned `OK`. Current core SHA-256: `da4ac2487aad358df7ff0e9512a1d22a006906934e51c188b3a6cae823534b99`. The additionally updated generic-image covering test has SHA-256 `95e2404882344fcd61e5f72650b9602a74f4f52605b0318b5978dd86a0f19a4b` (`prototypes/nishan_pq/tests/test_end_to_end.py`); that test is recorded here because the existing demo manifest covers its two original test files.

### Fix self-review and concerns

Inspected the delta against `task-1-after.tar.gz`: only `core.py`, the three requested covering test files, and README differ. No deck, carrier, mathematical, witness, ledger, historical evidence or DHRUVA source changes occurred in this fix. Reviewed that classification happens on authenticated plaintext before profile selection, media mismatch fails before embedding/signing/append, canonical PDF staging follows content validation, trace rejects legacy generic PDF references before generic scoring, and actual image dispatch remains generic. No Git operations, dependency installation or subagents were used.

I1 is resolved in code and covered by observed RED→GREEN tests. No validation is pending and no new blocker remains. Existing trust/physical/evidence limitations above still apply. Legacy generic-PDF receipts intentionally cannot produce fresh attribution; a new supported PDF-profile release is required. The package as a whole remains the existing format; this change enforces profile selection rather than claiming a redesigned authenticated manifest.
