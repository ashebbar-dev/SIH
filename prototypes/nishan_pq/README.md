# NISHAN-PQ

**Target:** Smart India Hackathon 2026, SIH26237  
**Problem owner:** Ministry of Defence, Indian Navy (WESEE)  
**Pitch:** Give authorized users the same encrypted document. If a copy leaks,
identify the release session through two separately encoded, domain-separated PDF carriers, reject
transplanted or incomplete PDF-source evidence, and return the signed,
quorum-committed result without leaving the air-gapped network.

This is an evidence prototype. Its PDF path now performs the complete sequence:

1. Encrypt one document with AES-256-GCM.
2. Wrap the same document key for each authorized recipient using ML-KEM-768
   (NIST FIPS 203).
3. At decryption, assign the session one row from a per-document binary Tardos
   codebook declared for 1,000 rows, coalitions up to five, and family-wide target
   `epsilon = 10^-6`.
4. Carry all 52,500 symbols in a subtle rendered-page overlay and a separate
   72-bit HMAC session authenticator in 126 error-corrected text-layout positions,
   while retaining the original PDF text, fonts and vector objects.
5. Bind each recipient ID to its KEM and signature public-key hashes in a
   validator-signed enrollment trust root; reject self-asserted substitute keys.
6. Have the enrolled recipient key sign the canonical decryption event using
   ML-DSA-65 (NIST FIPS 204).
7. Serialize validation, row allocation, signing and commit across local processes.
   Commit to four offline replicas with a three-validator endorsement quorum.
   In explicitly pinned witness mode, verify and checkpoint the new head before
   publishing the marked copy.
8. Decode a leaked rendering, score all 1,000 codebook rows using the original
   Tardos accusation score, and connect positive rows to signed ledger sessions.
9. Require both channels to agree for every PDF-source trace, including raster
   suspects and releases too short for the layout tag. Treat a single surviving
   channel as a research lead and abstain; also abstain on a conflict or an unissued row.

OpenSSL supplies the real ML-KEM and ML-DSA implementations. The program stops
if they are unavailable; it has no RSA or elliptic-curve fallback hidden behind
post-quantum labels.

## Run the proof

From the repository root:

```bash
.venv/bin/python -m nishan doctor
.venv/bin/python -m nishan demo --work-dir demo-run
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
.venv/bin/python -m nishan init-witness --root external-witness
.venv/bin/python -m nishan checkpoint-witness --root external-witness --ledger demo-run/ledger
.venv/bin/python -m nishan audit-witness --root external-witness --ledger demo-run/ledger
```

The `demo` command and frozen artifacts predate the current strict PDF policy.
For the fresh release safeguards demonstration, use a new output directory:

```bash
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py \
  --output research/evidence/nishan-selection-2026-09-12/demo
```

This runner refuses a populated directory, requires real PQC, and records twelve
observed security scenarios, code hashes and explicit limitations in `results.json`.
Its cases are protocol scenarios, not independent population trials.

### Explicit pinned-witness operation

`init-witness` creates a key and an empty chain; it does not establish a trusted
ledger head. An operator must review a healthy signed ledger and run
`checkpoint-witness` explicitly, as above. At provisioning, securely retain the
SHA3-256 digest of the actual witness `public.pem` bytes outside the ledger and
witness directories. The initialization command prints that digest. For local
demonstration this is co-located provisioning, with no independent administration
or hardware isolation. A real verifier must receive its pin independently, not
read a claimed digest from a suspect directory when verifying it.

Set `WITNESS_PIN` to that independently provisioned 64-character hexadecimal
digest, then provide both arguments for every strict release and trace:

```bash
.venv/bin/python -m nishan decrypt \
  --package demo-run/broadcast.nishan.json --identities demo-run/identities \
  --recipient alice --authority-secret demo-run/authority/watermark-secret.bin \
  --ledger demo-run/ledger --output strict-alice.pdf \
  --witness-root external-witness --witness-public-key-sha3-256 "$WITNESS_PIN"
.venv/bin/python -m nishan trace \
  --reference demo-run/source.pdf --suspect strict-alice.pdf \
  --authority-secret demo-run/authority/watermark-secret.bin --ledger demo-run/ledger \
  --evidence strict-evidence.json --witness-root external-witness \
  --witness-public-key-sha3-256 "$WITNESS_PIN"
```

Adjust the package, source and secret paths to your fixture. Both flags are
required together; wrong/malformed pins, empty/missing history, forks, rollback
and unwitnessed extensions fail before decryption. The comparison uses the
actual public-key bytes and requires an exactly consistent checkpoint.
Without these options, existing APIs remain usable and explicitly report
`release_assurance.mode = "unwitnessed"`. Generic-image attribution remains
research screening; the two-channel rule applies to PDF-source Tardos tracing.

Source classification uses the existing content parser at encryption and again
on authenticated plaintext before release-profile selection. Renaming a PDF or
editing the package media-type label cannot select the generic-image profile;
an inconsistent label is rejected before embedding, signing or append. Actual
PDF references backed by legacy generic-image receipts are rejected before
generic screening and require a new PDF-profile release. Genuine raster sources
retain the existing screening path. This is a profile-selection guard, not a
new signed-manifest protocol.

Locks are acquired in ledger-then-witness order. Release holds them through
publication; trace audits a consistent snapshot under them and releases them
before extraction. `ledger_witness` identifies that snapshot, not perpetual
freshness. All writers must cooperate with these local advisory locks.

If a checkpoint fails after append, the signed release authorization remains
committed but no new output is published, and any existing destination is
preserved. Strict release and trace then reject the unwitnessed extension. After
deliberately reviewing the ledger, witness and intended release, an operator may
run `checkpoint-witness` to recover, then retry release (which allocates a new
session/row). There is no automatic rollback or repair. A crash after checkpoint
but before publication can also leave an authorized record without delivery;
receipts never prove delivery or reading.

Generate the public evidence and the full five-colluder carrier benchmark:

```bash
.venv/bin/python prototypes/nishan_pq/tools/export_submission_evidence.py
.venv/bin/python prototypes/nishan_pq/tools/benchmark_tardos.py
.venv/bin/python prototypes/nishan_pq/tools/benchmark_tardos_trials.py
.venv/bin/python prototypes/nishan_pq/tools/benchmark_end_to_end_trials.py --trials 30
.venv/bin/python prototypes/nishan_pq/tools/benchmark_tardos_pdf.py
.venv/bin/python prototypes/nishan_pq/tools/score_physical_capture.py \
  physical_captures/scan_150dpi.png
```

The end-to-end demo creates three recipient identities, one encrypted package,
three dual-carrier live-text PDFs, raster leaks, two- and three-copy pixel
averages, PDF carrier removal/transplant attacks, signed evidence, and a
one-replica ledger edit. It also inserts a quorum-endorsed receipt with a broken
recipient signature into an isolated ledger copy and verifies that tracing and
the next plaintext release both stop. The separate carrier benchmark generates
all 1,000 rows and five marked PDFs, then executes 25 named transformations and
decision checks.

## Measured evidence on the synthetic one-page fixture

- The original conservative profile produces `m = 52,500` symbols and accusation
  threshold `Z = 2,100` for `n = 1,000`, `c = 5`, and family target `10^-6`.
- One 595 x 842 point page rendered at 144 DPI provides 55,440 non-overlapping
  6 x 6 blocks, enough to carry the full profile.
- Five generated marked copies retain byte-for-byte identical extracted text and
  measure 41.867–41.870 dB rendered PSNR in the deterministic fixture.
- The historical visual-channel end-to-end run selects the JPEG-Q55 session and recovers all known
  participants in its two- and three-copy averages; every returned ledger event
  has a valid ML-DSA signature.
- Across 30 historical successive releases, the JPEG-Q55 visual-channel path selects the exact signed
  session 30/30 times with zero extra codebook rows. The correct-row score is
  13,433.3 ± 128.2 (population SD) against `Z = 2,100`; the 95% Wilson interval
  for the observed exact-session rate is 88.65–100%. These repeated sessions use
  one document/codebook, not independent document trials or physical captures.
  The current strict PDF-source policy abstains on such raster-only evidence
  while retaining these scores as research leads.
- A deliberately corrupted recipient signature is rejected even after the
  generic replica layer endorses its record: tracing and the next plaintext
  release both fail closed, and no output file is created.
- A valid ML-DSA signature made with a substitute key cannot claim Alice: the
  key hash disagrees with Alice's validator-signed enrollment entry, so tracing
  and the next release stop. Editing the registry itself invalidates its trust
  root and also blocks release.
- Replaying an otherwise valid signed receipt creates a duplicate session and
  document-row assignment; tracing and the next release both stop, and no
  plaintext output is created.
- Truncating all four replicas to the same older, fully valid prefix still fools
  the ledger by itself. A separately signed ML-DSA head checkpoint detects that
  rollback. The public fixture keeps the witness key locally for demonstration;
  production must place it under separate administration or an HSM.
- The full carrier fixture scores all 1,000 rows. Its two-, three-, and five-copy
  pixel averages recover 2/2, 3/3, and 5/5 coalition rows, accuse zero of the
  other rows, and record marking-condition errors separately. The current two-,
  three-, and five-copy renderings have zero errors in 38,843, 32,126, and
  24,947 unanimous positions respectively.
- A separate 30-codebook study randomly selects five roster rows per codebook and
  runs interleaving, majority, minority and coin-flip strategies. All five rows
  cross threshold in all 120 recorded attack/codebook pairs, with zero innocent
  accusations. Per-strategy 95% Wilson intervals are 88.65–100% for all-five
  recovery and 0–11.35% for a trial containing any innocent accusation; these
  finite intervals are descriptive and do not replace the theorem.
- JPEG-Q55 still recovers the single source row in the fixture, but flips about
  11.2% of its symbols. The marking condition therefore fails for that attack,
  so the Tardos theorem is not applied to the JPEG result.
- A direct digital PDF produces matching Tardos and HMAC-layout identities.
  Deleting either channel leaves a visible screening lead but the editable-PDF
  policy abstains; deleting both produces no signal.
- Transplanting Alice's visual carrier onto Bob's layout carrier produces a
  conflict and abstention. Stripping Bob's layout after the transplant also
  abstains because an editable PDF no longer has both expected channels.
- The raster fixture recovers the expected row after half-size resampling, a
  two-degree rotation, JPEG quality 40, a deterministic perspective/lighting
  simulation, and a centered crop removing 30% from every edge. It fails at JPEG
  quality 20 and a crop removing 40% from every edge; those boundaries remain in
  the evidence.

Exact values and commitments are in:

- `artifacts/nishan/measured-results.json`
- `artifacts/nishan/tardos-reference-simulation.json`
- `artifacts/nishan/tardos-pdf-benchmark.json`
- `artifacts/nishan/tardos-independent-codebook-study.json`
- `artifacts/nishan/end-to-end-jpeg-trials.json`
- `artifacts/nishan/live-text-carrier-evidence.json`

## What the prototype proves

It proves that the SIH-required PQ key delivery, decryption-time fingerprint,
recipient signature and offline quorum receipt can run in one release path. It
also proves that the full conservative code profile fits on this one-page
rendering, the marked PDF stays searchable and selectable, all roster rows can be
scored in well under a second on this machine, and the named aligned averaging
fixtures produce the recorded outcomes.

The mathematical and carrier claims remain separate. The original Tardos result
provides a code-level probability bound under a randomized construction, a
coalition of at most `c`, and the marking condition. A real leak does not reveal
whether those assumptions held. Every known attack fixture therefore records
unanimous-position violations. The AES-CTR keyed codebook generator is a
finite-precision engineering construction and has not received an independent
DRBG or cryptographic review.

## Current boundary and known failures

The PDF's visual mark remains a separately addressable overlay and the layout tag
remains removable by content-stream normalization. Redundancy does not make
either primitive non-removable. It creates a second observation and a safe
decision state: PDF-source leaks are attributed only when both channels agree.
Removal of one becomes a flagged lead, removal of both still defeats attribution,
and copying both of Alice's carriers simply makes the object an Alice-derived
copy. A controlled viewer remains necessary to limit editable export and capture
unmarked plaintext.

Detection is non-blind: the authority retains the source to calculate the page
residual. JPEG, resize, rotation, crop and one synthetic perspective transformation
have measured synthetic fixture outcomes. The historical shipped physical
threshold recovered 0/4 captures; experimental profiles recovered the same 1/4
capture. That small exploratory set does not establish robust print/scan or phone
recovery. OCR and re-pagination remain open boundaries. Only named, saved attacks
may be described as measured.

The four demo replicas, validator private keys, and external-witness private key
live on one machine. The ledger demonstration proves that an unendorsed edit is
detected and one changed replica is outvoted by three unchanged replicas. The
separately signed checkpoint detects a coordinated rollback to a valid prefix,
provided the retained checkpoint and provisioned key cannot also be rolled back. An
operator holding both a validator quorum and the local demo witness key can still
build another valid history. Production needs separately administered peers,
hardware-backed keys and an externally retained checkpoint.

Recipient signatures are mechanism evidence. The demo process owns the synthetic
private keys. The signed enrollment root now proves that each accepted receipt
used the key registered for that synthetic identity; it does not prove a real
employee exclusively controlled that key. Deployment needs an offline CA,
employee binding and HSM/TPM-backed custody. Session-row assignment is now
transactionally serialized for cooperating processes on this one filesystem;
distributed consensus-backed allocation remains future work.

The distributor currently controls the codebook and both carrier secrets. It can
therefore manufacture a copy that points to an enrolled session. Recipient
signatures bind the recorded release event; they do not solve dishonest-provider
framing. A production accusation path needs a buyer-involved asymmetric
fingerprinting protocol and an independent adjudicator, as described in the
asymmetric Tardos literature.

## Finale gates

1. Replace removable carriers with content-bound primitives, or formally retain
   the current two-channel corroboration policy and controlled-viewer boundary.
2. Publish results for OCR, 150/300-DPI
   print-scan and perspective phone photographs, including synchronization errors.
3. Repeat coalition tests across independent codebooks and source documents;
   distinguish empirical rates from the theorem at every step.
4. Validate tagged PDFs, complex fonts, scanned documents, forms, signatures,
   links and multi-page files without claiming properties the fixture lacks.
5. Separate validator control, bind recipient keys to identities, and refuse
   release when the quorum or identity hardware is unavailable.

The project does not claim that Tardos codes, dual watermarking, text-layout
marks, PDF watermarking, PQ signatures or DLTs are new. Its defensible
contribution is a measured conflict-aware protocol: both carriers bind to one
signed session, all PDF-source traces require identity agreement, raster leaks retain
collusion-code research leads, and transplantation/removal states are exercised instead of
being silently turned into accusations. The complete prior-art boundary is in
`research/NISHAN_NOVELTY_AND_PRIOR_ART.md`.
