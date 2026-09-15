# SIH26237 — NISHAN-PQ

> Replace every bracketed field before upload. The registered team name must not contain the institute name.

## Portal fields

**Problem Statement ID:** SIH26237  
**Problem Statement:** Cryptographic Attribution and Immutable Decryption Provenance for Multi-Recipient Encrypted Document Distribution  
**Organization:** Ministry of Defence — Indian Navy (WESEE)  
**Category:** Software  
**Theme:** Blockchain & Cybersecurity  
**Idea title:** NISHAN-PQ — Accountable decryption with verifiable source-copy evidence  
**Team ID:** [TEAM ID]  
**Registered team name:** [TEAM NAME]  
**Public repository:** [PUBLIC REPOSITORY URL]

## Paste-ready idea description (100 words)

NISHAN-PQ turns each authorized decryption into a recipient- and session-specific PDF release. A managed offline process allocates a unique Tardos row, adds a domain-separated layout tag, obtains an ML-DSA-65 recipient receipt and commits the event to a local 3-of-4 log. In configured mode, a separately provisioned witness pin gates both release and trace before atomic publication. A clean PDF is associated with a source copy only when visual and layout evidence agree; rasterized or low-capacity PDF matches remain research leads. Fresh real-PQC scenarios verify concurrent issuance, rollback rejection, read-only trace and fail-closed publication without claiming human guilt or production certification.

## Thirty-second internal-round pitch

“Access logs tell us who opened a document; they do not tell us which released
copy later appeared in a leak. NISHAN-PQ gives every authorized decryption a
session-specific mark and a signed release record before publishing the copy.
For a supported clean PDF, two differently encoded channels must name the same session.
If a rasterized transplant removes that corroboration, the system returns
inconclusive and keeps the visual match only as a research lead. Our fresh
offline demonstration uses real ML-KEM and ML-DSA, issues concurrent distinct
rows, blocks a wrong witness pin and coordinated rollback, and publishes nothing
new when checkpointing fails.”

## Problem and decision improved

The user is a defence document controller or leak investigator. The decision is:
**which authorized release session is supported by this leaked copy, and is the
evidence strong enough to report an association rather than an inconclusive
result?**

Encrypt-once distribution gives every authorized recipient the same readable
content. Conventional access logs record access, but a privileged administrator
may alter local history and a log entry does not bind a later leaked artifact to
one source copy. NISHAN-PQ adds release-specific evidence while keeping the
content usable and the workflow offline.

## Proposed solution

1. Encrypt the source once with AES-256-GCM and wrap the content key per recipient
   with ML-KEM-768.
2. Inside the managed viewer, authenticate and classify the plaintext, then hold
   the ledger transaction lock across history validation, row/session allocation,
   marking, signing, append, checkpoint and publication.
3. Embed a Tardos rendering row and, where PDF capacity permits, a 72-bit HMAC
   session tag in live text layout.
4. Bind the document, recipient, session, row, output hash and release-assurance
   mode in an ML-DSA-65 recipient-signed event.
5. Commit to a local 3-of-4 hash-linked demonstrator. In configured mode, verify
   the actual witness key against a caller-provisioned pin and require a healthy,
   retained signed checkpoint chain.
6. Publish the marked copy only after append, re-audit, checkpoint and final
   consistency checks. A checkpoint failure may leave a committed release
   authorization, but creates no new output and preserves any existing destination.
7. During trace, verify the signed ledger and configured witness snapshot without
   updating it. All PDF-source traces require visual/layout set equality; missing
   channels, inadequate capacity, disagreement or an unissued row force abstention.

## Three key capabilities

- **Accountable release:** serialized recipient/session allocation and signed
  source-copy hashes before publication.
- **Configured rollback gate:** wrong witness pins and the tested coordinated
  valid-prefix rollback stop release and trace when the separately retained pin
  and witness state are trustworthy.
- **Conservative PDF evidence:** clean digital PDFs can corroborate; raster-only
  and low-capacity PDF matches remain research leads with empty attribution.

## Evidence status — 12 September 2026

### Fresh selection safeguards on current code

- All 12 named offline safeguard scenarios passed on public synthetic fixtures;
  these are scenario checks, not population experiments.
- The final Task 1 code suite passed 59/59 tests with no skips, failures or errors.
- The fresh demo reports real OpenSSL 3.6.4 support for ML-KEM-768 and ML-DSA-65.
- All 19 code hashes recorded by the demo were checked against the current files.
- Two concurrent releases received distinct rows; the next successful release
  used row 2; all three output hashes matched their signed receipts.
- Clean PDF trace returned two-channel corroboration. A rendered transplant and
  an inadequate-capacity PDF returned empty attribution while retaining research leads.
- Configured release rejected a wrong pin; configured release and trace both
  rejected the tested coordinated rollback.
  Trace left checkpoint bytes unchanged.
- Injected checkpoint failure published no new output and preserved an existing
  destination. The committed authorization remains and requires deliberate review.
- Authenticated content parsing closes the media-type-only PDF bypass. Actual PDF
  references backed only by legacy generic-image receipts fail closed; genuine
  raster-image screening remains available as research screening.

Evidence: `research/evidence/nishan-selection-2026-09-12/demo/results.json`.

### Historical digital visual-channel evidence

- The historical JPEG-Q55 study completed 30/30 visual-channel trials for one
  document, one authority/codebook and one recipient identity across repeated
  sessions. It is not the current strict PDF verdict, a multi-person experiment
  or physical performance.
- Five one-page marked PDFs preserved extracted text and averaged about 41.87 dB
  rendered PSNR. They are not byte-identical PDFs, a human invisibility study or
  proof that pre-existing PDF signatures survive.
- The 30-codebook × 4-strategy study contains 120 code-level cases. These are not
  120 carrier, PDF or physical trials.

Evidence: `artifacts/nishan/end-to-end-jpeg-trials.json`,
`artifacts/nishan/tardos-independent-codebook-study.json` and
`artifacts/nishan/tardos-pdf-benchmark.json`.

### Physical evidence remains experimental

- The shipped historical threshold recovered 0/4 real captures.
- Both exploratory conditional profiles recovered the same one capture,
  `akshay3.jpeg`, so the result is 1/4 per profile—not two captures.
- The study uses one printed single-page public fixture and is visual code-row
  research, not end-to-end signed physical attribution or a reliability rate.

Evidence: `research/evidence/nishan-bias-physical-2026-09-10/scores.json`.

## Remaining boundaries

- All four validator keys, replicas and witness material are co-located. R8 is
  not met against an administrator controlling the whole local environment.
- Pinned rollback detection depends on independently provisioned key material and
  trusted retained external state. Rolling back the witness too is outside this
  local guarantee; legacy unconfigured mode remains explicitly unwitnessed.
- Trusted software and local key custody remain compromise boundaries. The
  authority can reproduce or plant an already issued copy.
- A signed session shows release authorization and source-copy association, not
  successful delivery, reading, human guilt or intent.
- Trace is non-blind and needs the retained original. Removal or retyping can
  defeat both carriers; transformed-artifact association is not exact-file integrity.
- Current evidence is mainly single-page. Robust physical recovery, multi-page and
  signed/tagged-PDF compatibility, independent governance, hardware-isolated
  signing and a portable independent evidence verifier remain future work.

## Five-minute demonstration

Use the checked-in `DEMO_RUNBOOK.md`. Run the safeguard tool with a new output
root, never overwrite the reviewed demo, and never publish or reuse its synthetic
private keys. The sequence shows two recipients plus a repeated session, clean
PDF corroboration, raster transplant abstention, rollback rejection and
checkpoint failure with no publication.

## Engineering contribution and prior-art boundary

SIH26237 prescribes decryption-time marking, PQ signatures and DLT provenance.
ML-KEM, ML-DSA, Tardos codes, document watermarking and permissioned PQ ledgers
have prior art. The scoped engineering contribution is the tested integration of
a PQ-signed marked release, configured pinned-checkpoint gating and conservative
two-channel PDF evidence. This is not a first-ever or competitor-superiority claim.

The recovered Sol Ultra session provides no preserved authenticator artifacts,
hashes or independently controlled secrets. Its numeric and recipient-controlled
security claims are not used here. Future research may evaluate independently
controlled robust corroboration under fixed predeclared digital and physical tests.

## Primary references

- [SIH 2026 official portal](https://www.sih.gov.in/sih2026PS)
- [NIST FIPS 203 — ML-KEM](https://csrc.nist.gov/pubs/fips/203/final)
- [NIST FIPS 204 — ML-DSA](https://csrc.nist.gov/pubs/fips/204/final)
- [FontCode](https://www.cs.columbia.edu/cg/fontcode/)
- [PQFabric](https://arxiv.org/abs/2010.06571)
- [Gábor Tardos, Optimal probabilistic fingerprint codes](https://www.renyi.hu/~tardos/fingerprint.pdf)
