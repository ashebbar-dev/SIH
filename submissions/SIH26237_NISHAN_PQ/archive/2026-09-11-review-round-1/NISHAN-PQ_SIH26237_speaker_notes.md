# NISHAN-PQ speaker notes and audit record

## Slide 1

Slide 1 — scope and official requirements
Team ID: [ENTER TEAM ID]; team name: [ENTER REGISTERED TEAM NAME]; repository: [INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]. Status date: 11 September 2026. This is an audit record, not marketing copy.
R1: Unique invisible watermark at decryption — demonstrated on the controlled release path; the trusted viewer and allocation-race caveats remain.
R2: Recipient/session specificity — each release has an explicit session and row; initial row allocation can still race.
R3: Visually identical / forensically distinct — five PDFs preserve extracted text and average 41.87 dB PSNR; this is not universal invisibility.
P22: Team ID, registered team name and repository URL remain explicit placeholders unless supplied through the build CLI; strict verification then fails.

## Slide 2

Slide 2 — workflow and extraction evidence
R9: Extract mark from leak — digital fixtures recover, while shipped physical evidence is historical 0/4 and experimental 1/4 per profile; this is not robust deployment.
P10: Physical evidence is historical 0/4 and experimental 1/4 in each profile, with the same akshay3 capture recovered in both—not two recovered captures. Latest akshay3 is 1827.334 vs 1096.290; baseline is 1709.941 vs 1097.482. akshay2 latest is 835.191 vs 1021.632; neither first capture recovered, refinement adds no capture, and 2 boundary failures remain failures. These are visual-code-row results on one printed single-page public fixture, not end-to-end signed physical attribution or independent documents.
P11: The 30/30 end-to-end JPEG-Q55 runs are one person across 30 accumulated issued sessions (rows 0..29); other-issued score is null once and non-null 29 times, not a 20-person test.
P12: All 30 end-to-end trials reuse the same document, authority secret and codebook; no independent-document or independent-authority inference follows.
P13: The 30-codebook × 4-strategy study has 120 code-level cases; it is not carrier, PDF or physical evidence.
Digital context: all 1,000 rows were scored per session; 0 extra row was accused; mean 13433.337, population SD 128.216.
Sources: artifacts/nishan/end-to-end-jpeg-trials.json; artifacts/nishan/tardos-independent-codebook-study.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.

## Slide 3

Slide 3 — architecture, binding and audit limits
R4: Cryptographic binding to recipient identity — enrollment-bound prototype receipts are checked; identity and key custody remain a deployment assumption.
R5: Recipient's own private signing key — ML-DSA signing is demonstrated, but exclusive human custody of that key is unproven.
R6: NIST PQC KEX/signatures — ML-KEM-768 and ML-DSA-65 are used, with no classical fallback in the measured path.
R7: Blockchain/DLT audit — only a local, co-located 3-of-4 quorum demonstrator is implemented.
R8: No single administrator can alter/delete history — NOT MET; independent key/peer custody and an enforced witness are absent.
R10: Ledger lookup — implemented for available valid records, but coordinated valid-prefix rollback can erase the association unless the separate witness is consulted.
P1: A separate witness detects the recorded rollback; trace/release do not enforce it, so integration alone does not prevent or recover deletion.
P2: Allocation race — append locks start too late; protect the initial read through commit and avoid nested lock reacquisition.
P3: A rasterized transplant bypasses layout corroboration; the parser already rejects renamed or prefixed PDF content masquerading as a raster/image.
P4: Insufficient 126-symbol layout capacity disables that protection; shortness is only one cause. Fail/restrict release policy is proposed, not implemented.
P5: The authority can regenerate both carriers for an existing signed session without forging a fresh recipient signature.
P6: Removing both carriers leaves readable content and no attribution signal on the tested fixture.
P7: The trusted viewer can access clean plaintext before marking; ordinary output is released only after commit.
P8: Non-blind extraction requires the retained original and the correct version.
P17: Witness capability remains a separate audit tool, not enforced trace-path protection.
P18: Unconditional transplant-abstention is false for raster or low-capacity paths where layout corroboration is unavailable.
Carrier correction (unnumbered): tardos_carrier.py uses fixed 6x6 Tardos templates; watermark.pattern() is not the carrier, and shorter code does not enlarge blocks.
Sources: artifacts/nishan/measured-results.json; artifacts/nishan/tardos-pdf-benchmark.json.

## Slide 4

Slide 4 — feasibility and unresolved risks
R11: Verifiable associated recipient/event — signature checks work; authority framing and copy-to-human inference limits remain.
P9: Evidence identifies a session/copy association, not which human intentionally leaked it.
P14: Signed-PDF preservation is an expected compatibility issue because changed bytes normally invalidate signatures; damage to tagged PDF structure is untested, not demonstrated.
P15: Main published experiments are single-page. Page loops exist in code, but there is no validated multi-page benchmark.
P16: This task corrects PPT/PDF/verifier stale physical-pending wording only; other historical prose is not claimed updated.
P19: Registration and 1,000-row scoring do not prove photo robustness; fine cell alignment and measured few-thousand-symbol physical capacity remain unresolved.
P20: Co-located quorum is a real limitation and was already partly disclosed on slide 4; it is not administrator-resistant DLT.
P21: No Git repository was initialized. Local version history and publishing are distinct actions; controller backups are retained.
Additional limits: requiring current layout on every raster would lose legitimate screenshot/JPEG verdicts; no zero-operational-loss policy, 35 dB invisibility guarantee or population safety rate is claimed.

## Slide 5

Slide 5 — operational value and remaining requirements
R12: Offline/air-gapped operation — demonstrated in a local architecture, not an audited hardened deployment.
R13: No cloud KMS — the implemented workflow has no required external KMS dependency.
R14: No public blockchain — the local demonstrator has no public-chain dependency.
Gate 1: security boundaries and claims. Gate 2: independent documents, keys, recipients, signed/tagged PDFs and negative attacks. Gate 3: held-out physical comparisons at matched visibility/security budgets.
Required future scope: multi-page material, protected key custody, external checkpoints, release-bound policy and real printer/camera validation. This is investigative assistance, not operational accusation readiness.

## Slide 6

Slide 6 — research boundary and sources
P23: The stray file '=4.11' is retained outside presentation scope because this update is non-destructive; it was not silently deleted.
P24: Novelty is unestablished. TRACE concerns trajectory watermarking, physical comparators already exist, and set equality has not been shown novel; no competitor-superiority or winning-probability inference is supported.
Parameter context (unnumbered): current n=1000,c=5,epsilon=1e-6 gives m=52500; roster-only n=20 gives m=42500; n=20,c=4,epsilon=1e-3 gives m=16000 but changes three assumptions. Rows are sessions. Ideal symmetric m=12331 is a separate audit requiring another decoder and implementation proof, not physical evidence or novelty.
Shorter-code and stronger/lower-frequency carrier ideas remain unvalidated hypotheses.
URLs: https://www.sih.gov.in/sih2026PS ; https://arxiv.org/abs/2607.08400 (TRACE is LLM-agent trajectories, not direct PDF physical comparison) ; https://www.matthewtancik.com/stegastamp ; https://arxiv.org/abs/2304.12682 ; https://doi.org/10.1145/3494106.3528674 ; https://www.renyi.hu/~tardos/fingerprint.pdf ; https://doi.org/10.1109/49.464718 ; https://doi.org/10.1109/83.951542 ; https://doi.org/10.1109/ICIP.2001.958536 ; https://csrc.nist.gov/pubs/fips/203/final ; https://csrc.nist.gov/pubs/fips/204/final.
Evidence paths: artifacts/nishan/measured-results.json; artifacts/nishan/tardos-pdf-benchmark.json; artifacts/nishan/tardos-independent-codebook-study.json; artifacts/nishan/end-to-end-jpeg-trials.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.
Team ID: [ENTER TEAM ID]; team name: [ENTER REGISTERED TEAM NAME]; repository: [INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]. Status date: 11 September 2026. This is an audit record, not marketing copy.
