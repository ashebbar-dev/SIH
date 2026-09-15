# Task 1 fix round 1 re-review

## I1 — ADDRESSED

The enforcement fix closes both paths in the original finding.

- Encrypt-time metadata now comes from the existing content parser rather than the filename suffix (`prototypes/nishan_pq/nishan/core.py:140`; parser at `prototypes/nishan_pq/nishan/watermark.py:68`).
- Release authenticates the encrypted bytes, verifies their source hash, parses those staged plaintext bytes, rejects any disagreement with the package's untrusted `media_type`, and dispatches on the parsed result (`prototypes/nishan_pq/nishan/core.py:235`, `prototypes/nishan_pq/nishan/core.py:240`, `prototypes/nishan_pq/nishan/core.py:253`, `prototypes/nishan_pq/nishan/core.py:256`, `prototypes/nishan_pq/nishan/core.py:258`, `prototypes/nishan_pq/nishan/core.py:261`). The carrier's suffix requirement is handled only after PDF content validation by private staging-name canonicalization (`prototypes/nishan_pq/nishan/core.py:262`). Thus editing only `source.media_type` cannot select or sign the generic profile, and renamed or prefixed parser-accepted PDFs still select the PDF/Tardos profile.
- Trace parses the actual reference and rejects PDF references whose matching signed receipts are anything other than the Tardos scheme before generic preparation or scoring (`prototypes/nishan_pq/nishan/core.py:1028`, `prototypes/nishan_pq/nishan/core.py:1032`, `prototypes/nishan_pq/nishan/core.py:1053`). This covers legacy generic and absent PDF receipts while leaving non-PDF references on the established generic-image path.
- The README continues to make the enforced all-PDF-source claim (`prototypes/nishan_pq/README.md:31`, `prototypes/nishan_pq/README.md:232`); the code now implements that claim rather than narrowing it.

Covering regressions exercise media-label tampering with no publication/ledger/checkpoint mutation, renamed and prefixed PDF release/trace, legacy generic-PDF rejection before the scoring sentinel, parser-based encrypt metadata, and genuine raster compatibility (`prototypes/nishan_pq/tests/test_release_safeguards.py:146`, `prototypes/nishan_pq/tests/test_release_safeguards.py:157`, `prototypes/nishan_pq/tests/test_release_safeguards.py:169`, `prototypes/nishan_pq/tests/test_pdf_format_policy.py:18`, `prototypes/nishan_pq/tests/test_pdf_format_policy.py:39`, `prototypes/nishan_pq/tests/test_end_to_end.py:49`).

## New Breakage

None identified at Critical or Important severity in the fix-only changes. The content parser is shared by encryption, release, and trace, and the unchanged genuine-image release and attribution path remains covered (`prototypes/nishan_pq/tests/test_end_to_end.py:49`, `prototypes/nishan_pq/tests/test_end_to_end.py:67`, `prototypes/nishan_pq/tests/test_end_to_end.py:76`).

## Out-of-Scope Observations

None.

## Checks

- Reviewed the amended security/evidence contract, original I1, appended fix report, the supplied fix-only diff, and current affected files against the stated `task-1-after.tar.gz` base.
- Did not rerun tests. The supplied final-suite log names the new parser, tampering, renamed-PDF, legacy-receipt, and raster-compatibility tests as passing and records `Ran 59 tests in 63.472s` followed by `OK` (`research/evidence/nishan-selection-2026-09-12/task-1-fix1-suite-final.txt:32`, `research/evidence/nishan-selection-2026-09-12/task-1-fix1-suite-final.txt:34`, `research/evidence/nishan-selection-2026-09-12/task-1-fix1-suite-final.txt:45`, `research/evidence/nishan-selection-2026-09-12/task-1-fix1-suite-final.txt:47`, `research/evidence/nishan-selection-2026-09-12/task-1-fix1-suite-final.txt:49`, `research/evidence/nishan-selection-2026-09-12/task-1-fix1-suite-final.txt:62`).
- Current hashes match the appended fix report for `core.py` (`da4ac2487aad358df7ff0e9512a1d22a006906934e51c188b3a6cae823534b99`) and `test_end_to_end.py` (`95e2404882344fcd61e5f72650b9602a74f4f52605b0318b5978dd86a0f19a4b`). The current demo report records 12 cases, `all_passed: true`, and `pqc_ready: true`; the controller separately reports all 19 recorded code hashes checked.

## Round Verdict

**All findings addressed; no Critical or Important findings remain open.**
