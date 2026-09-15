# NISHAN-PQ speaker notes and audit record

## Slide 1

Slide 1 — value proposition and scope
Team ID: [ENTER TEAM ID]; team name: [ENTER REGISTERED TEAM NAME]; repository: [INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]. Status date: 12 September 2026. Selection deadline supplied by the team: 15 September. This is a tested research prototype, not production certification or a competition-outcome claim.
R1: Unique invisible watermark at decryption — the controlled release path generates a marked, signed session copy before publication; the managed-process and authority-framing boundaries remain.
R2: Recipient/session specificity — transaction-wide serialization now covers history validation, row allocation, signing, append, checkpoint and publication; the fresh concurrent scenario produced distinct rows and a later row 2.
R3: Visually identical / forensically distinct — 5 one-page PDFs preserve extracted text and average 41.87 dB rendered PSNR; PDFs are not byte-identical, and this was not a human invisibility study.
P22: Team ID, registered team name and repository URL remain explicit placeholders unless supplied through the build CLI; strict verification then fails.

## Slide 2

Slide 2 — proposed solution and capabilities
R4: Cryptographic binding to recipient identity — enrollment-bound recipient keys and an ML-DSA-signed canonical release event bind document, session, row and assurance mode; identity proofing and key custody remain deployment assumptions.
R5: Recipient's own private signing key — ML-DSA receipt verification is implemented, but exclusive human custody is not established while demo keys remain local.
R6: NIST PQC KEX/signatures — the fresh readiness check used real ML-KEM-768 and ML-DSA-65 through OpenSSL 3.6.4, with no classical fallback in the measured path; algorithm use does not certify the prototype.
R9: Extract mark from leak — a supported clean PDF returns a signed source-copy session only when both channels corroborate; raster-only and inadequate-capacity PDF scores remain research leads with empty attribution.
P5: The authority can reproduce both carriers for an already issued session without forging a new recipient receipt; exact source-copy evidence does not eliminate operator framing.
P6: Removing both carriers or retyping content can leave readable material with no attribution signal.
P7: The managed viewer can access authenticated clean plaintext before marking; publication is gated, but trusted software and endpoint control remain assumptions.
P8: Extraction is non-blind and requires the retained original and correct source version.
Source: research/evidence/nishan-selection-2026-09-12/demo/results.json.

## Slide 3

Slide 3 — technical approach and release gates
R7: Blockchain/DLT audit — the prototype implements a hash-linked, quorum-signed local 3-of-4 demonstrator; it is not independently administered blockchain infrastructure.
R8: No single administrator can alter/delete history — NOT MET. All validator keys, replicas and witness material remain co-located. A configured pin helps only when the witness key and retained state are independently provisioned and trustworthy.
R10: Ledger lookup — available valid records map rows to signed sessions. In configured witness mode, release rejects the tested wrong pin; release and trace both reject the tested coordinated valid-prefix rollback. Legacy unconfigured mode is explicitly unwitnessed.
P1: The separate witness is now called on configured release and trace paths. It detects the tested rollback only while the pinned key and retained external state remain trusted; rolling back the witness too is outside the local guarantee.
P2: Allocation race — corrected. The existing ledger transaction lock is held from history validation and row allocation through append, checkpoint and publication; fresh concurrent releases used distinct rows and a third release succeeded.
P3: PDF policy — rendered/rasterized transplant now returns empty high-assurance attribution and retains only a research lead. Authenticated plaintext parsing prevents a metadata-only type bypass; renamed/prefixed PDFs cannot select generic-image handling.
P4: Insufficient 126-symbol layout capacity now yields a signed capacity limitation and abstention rather than PDF attribution.
P17: Configured witness enforcement is implemented and tested on release and trace; the default compatibility mode remains explicitly unwitnessed, and trace records a checked snapshot rather than perpetual freshness.
P18: All PDF-source traces now require visual/layout set equality, including raster suspects and low-capacity releases. Genuine raster-image screening is preserved and remains a different, research-only assurance class.
Release ordering: validate → allocate/mark → recipient-sign → quorum append/re-audit → checkpoint/re-verify → atomic publication. A checkpoint failure leaves a committed authorization but publishes no new output.

## Slide 4

Slide 4 — feasibility, evidence separation and boundaries
Fresh evidence: 12/12 named safeguard scenarios passed; all_passed=True; pqc_ready=True; 19 recorded SHA-256 entries match current files. These are scenario checks on public synthetic fixtures, not population experiments.
P10: Physical evidence is historical shipped-threshold 0/4 and exploratory 1/4 in each profile, with the same akshay3 capture recovered in both—not two recovered captures. Latest akshay3 is 1827.334 vs 1096.290; baseline is 1709.941 vs 1097.482. akshay2 latest is 835.191 vs 1021.632; the first two refined-profile captures are boundary failures. This is one printed single-page public fixture, not end-to-end signed physical attribution.
P11: The 30/30 end-to-end JPEG-Q55 runs use one recipient identity across 30 accumulated issued sessions (rows 0..29); other-issued score is null 1 time and non-null 29 times, not a multi-person test.
P12: All 30 end-to-end trials reuse the same document, authority secret and codebook; no independent-document or independent-authority inference follows.
P13: The 30-codebook × 4-strategy study has 120 code-level cases; it is not carrier, PDF or physical evidence.
P14: Signed-PDF preservation is an expected compatibility issue because changed bytes normally invalidate signatures; damage to tagged PDF structure is untested, not demonstrated.
P15: Main published experiments are single-page. Page loops exist in code, but there is no validated multi-page benchmark.
P16: This selection update corrects deck, notes, verifier, paste-ready prose and runbook semantics; historical evidence artifacts and prototype code are not rewritten by Task 2.
P19: Registration and 1,000-row scoring do not prove photo robustness; physical synchronization and useful capacity remain unresolved.
P20: Co-located validator and witness administration remains a material limitation; the local quorum is not administrator-resistant DLT.
P21: No Git repository was initialized. Local version history and publishing are distinct actions; controller backups are retained.
Feasibility context (unnumbered): a confirmed six-person team has an existing offline laptop prototype, repeatable tests and saved evidence; neither GPU nor ESP32 is required for this measured workflow.
Sources: demo/results.json; artifacts/nishan/end-to-end-jpeg-trials.json; artifacts/nishan/tardos-independent-codebook-study.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.

## Slide 5

Slide 5 — impact, judge demo and next-round gates
R11: Verifiable associated recipient/event — signature and ledger checks support a source-copy/session association; authority framing and copy-to-human inference limits remain.
R12: Offline/air-gapped operation — demonstrated in a local architecture, not an audited hardened deployment.
R13: No cloud KMS — the implemented workflow has no required external KMS dependency.
R14: No public blockchain — the local demonstrator has no public-chain dependency.
P9: Evidence identifies a released session/copy association, not which human intentionally disclosed it, received it successfully or read it.
Five-minute judge flow: create a fresh demo output root; issue two recipients plus a repeated/third session; trace a clean PDF; show raster transplant and low-capacity PDF abstention; show wrong-pin release rejection and rollback rejection on both release and trace; inject checkpoint failure and show no new publication while explaining the committed authorization record.
Next-round validation is narrow: independent administrative/key custody; larger multi-recipient and multi-page corpus; representative held-out print/camera testing; and a portable independent proof verifier. Neither GPU nor ESP32 is required for the measured workflow.
Do not publish or reuse demo private keys. The runbook names new output roots and preserves historical evidence.

## Slide 6

Slide 6 — prior art, references and differentiated integration
P23: The stray file '=4.11' is retained outside presentation scope because this update is non-destructive; it was not silently deleted.
P24: Novelty is unestablished. The engineering contribution is the tested integration of PQ-signed marked release, configured pinned-checkpoint gating and conservative two-channel PDF evidence. No component-level invention, competitor superiority or winning-probability claim is made. TRACE concerns LLM-agent trajectories and is omitted from scarce visible slide space.
Parameter context (unnumbered): current n=1000,c=5,epsilon=1e-6 gives m=52500; roster-only n=20 gives m=42500; n=20,c=4,epsilon=1e-3 gives m=16000 but changes three assumptions. Rows are sessions. Ideal symmetric m=12331 is a separate audit requiring another decoder and implementation proof, not physical evidence or novelty.
The recovered Sol Ultra session supplies no preserved authenticator probe artifacts, environment hashes or independently controlled secrets. Its adaptive strength-3 exact verifier recovered 3/5 after five-copy JPEG and failed perspective/10% crop; none of those numeric or recipient-controlled security claims are current deck evidence.
URLs: https://www.sih.gov.in/sih2026PS ; https://csrc.nist.gov/pubs/fips/203/final ; https://csrc.nist.gov/pubs/fips/204/final ; https://www.cs.columbia.edu/cg/fontcode/ ; https://arxiv.org/abs/2010.06571 ; https://www.renyi.hu/~tardos/fingerprint.pdf.
Evidence paths: artifacts/nishan/measured-results.json; artifacts/nishan/tardos-pdf-benchmark.json; artifacts/nishan/tardos-independent-codebook-study.json; artifacts/nishan/end-to-end-jpeg-trials.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.
Team ID: [ENTER TEAM ID]; team name: [ENTER REGISTERED TEAM NAME]; repository: [INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]. Status date: 12 September 2026. Selection deadline supplied by the team: 15 September. This is a tested research prototype, not production certification or a competition-outcome claim.
