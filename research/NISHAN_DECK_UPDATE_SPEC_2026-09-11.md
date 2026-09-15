# NISHAN evidence-led deck update

User request: update the PPT with everything from the immediately preceding
Claude-review evaluation. This is a presentation/documentation change only.

## Binding constraints

- Preserve the official six-slide submission order, 16:9 format, logos and footers using the existing builder and template.
- Produce updated editable PPTX, matching six-page PDF, and exported speaker notes; preserve the old artifacts before replacement.
- Do not modify prototype code, experiment runners, original images, source PDFs or recorded research evidence. Do not run new watermark/security experiments, install dependencies, initialize Git, publish or upload.
- Keep unknown team name, team ID and repository link as explicit placeholders unless supplied by the user; support all three as build arguments.
- Present implemented behavior, measured evidence, current defects and proposed work as distinct categories. No claim of full compliance, production readiness, world-leading novelty, guaranteed winning, empirical one-in-a-million safety, or fixed defects.
- Visible slides must carry the material caveats; speaker notes contain the complete 14-requirement assessment and corrected P1-P24 review. Notes are not a substitute for visible caveats.
- All displayed numerical experimental results must be derived from existing JSON artifacts, not copied as unexplained manual constants.
- Update the package verifier to reject stale physical-pending claims, check new physical evidence and notes, retain historical evidence checks, and keep placeholder failures in strict mode.
- Missing or malformed physical evidence must fail the build/verification explicitly, not fall back to optimistic numbers.

## Sources and exact interpretations

Existing digital evidence:
`artifacts/nishan/{measured-results,tardos-pdf-benchmark,tardos-independent-codebook-study,end-to-end-jpeg-trials}.json`.
Physical evidence:
`research/evidence/nishan-bias-physical-2026-09-10/scores.json`.
Physical records have capture, profile, status, expected_score,
conditional_null.threshold, historical_accused, conditional_accused,
bit_error_fraction, highest_other_score. Profiles are affine_baseline and
affine_bias_translation. Two boundary_failure records must remain failures.

Exact physical narrative: 4 supplied captures of one printed, single-page public
fixture; 0/4 recovered under historical Z=2100 in these fixed profiles; 1/4 under
each experimental conditional profile (only akshay3). Latest akshay3 score
1827.334 versus 1096.290, baseline 1709.941 versus 1097.482. akshay2 latest
835.191 versus 1021.632, no recovery. Neither first capture recovered. Refinement
adds no recovered capture. No other row accused here; no population safety rate.
These are visual-code-row research results, not end-to-end signed physical
attribution, no production decoder change, and not independent-document trials.

Digital narrative: 30/30 exact JPEG-Q55 sessions, all 1000 rows scored, no extra
row accused; one recipient (Bob), one document and authority secret/codebook,
successive rows 0..29 retained in one ledger. Other-issued score null only in
first trial, present in remaining 29. Score mean 13433.337 and SD128.216 from
JSON. 30 codebooks x4 strategies =120 code-level cases with all five recovered;
not120 physical trials. Five PDF copies average about41.87dB; equal extracted
text, not byte-identical PDF, universal invisibility or preserved signatures.

Security facts (all still unresolved unless explicitly described as measured
existing boundary): witness audits separately, not in trace/release; co-located
validator keys and replicas do not establish administrator-resistant DLT;
append lock does not cover initial audit/row allocation; raster conversion
and insufficient layout capacity bypass corroboration; authority can regenerate
both carriers for an existing signed session without forging a new signature;
both removable; plaintext available to a controlled viewer process before
marking; non-blind reference retention; session evidence is not human culpability.

Policy change is proposed, not implemented: freeze assurance policy at release,
distinguish visual-only leads from corroborated evidence, and fail/restrict
low-capacity releases. Requiring current layout on every raster would also lose
legitimate digital screenshot/JPEG verdicts. Cannot promise no operational loss.

Research corrections: fixed6x6 Tardos templates in tardos_carrier.py are the
actual carrier, not watermark.pattern(). Shorter code does not enlarge blocks.
Current n1000,c5,epsilon1e-6 ->m52500; roster-only n20 ->m42500;
Claude n20,c4,epsilon1e-3 ->m16000 changes three assumptions. Rows are sessions.
Existing ideal symmetric m12331 audit preserves nominal original budgets but
requires different decoder and implementation proof; not physical evidence or
novelty. Registration similarity does not certify cell alignment; no measured
few-thousand-symbol capacity. More strength/lower spatial frequencies remain
hypotheses. No guarantee35dB is invisible/acceptable. All details may be notes.

Official PS: https://www.sih.gov.in/sih2026PS, SIH26237,14 requirements;
https://arxiv.org/abs/2607.08400 TRACE is LLM-agent trajectories, not a direct PDF
physical comparator. https://www.matthewtancik.com/stegastamp and
https://arxiv.org/abs/2304.12682 show existing physical/screen-camera research;
none establishes comparison superiority for this prototype. Keep older Tardos,
T-Tracer, text-layout and dual-mark sources in notes. Do not assert an exclusive
novel contribution, competitor capabilities or numerical winning probability.

## Six-slide content allocation

1. Title/project/PS/team fields; replace unconditional tagline with
   "At-decryption session provenance for air-gapped documents." Hero label
   "RESEARCH PROTOTYPE" and clear "Evidence update: 11 September 2026".
2. IDEA TITLE / PROPOSED SOLUTION: preserve encrypt-authorize-mark-sign-trace
   workflow but qualify optional layout and co-located ledger demo. Lower half:
   two large readable evidence cards, DIGITAL DEVELOPMENT and REAL CAPTURES.
   Digital30/30 and physical0/4 versus experimental1/4; latest akshay3 comparison;
   common caveat: limited fixtures; not a deployed reliability guarantee.
   Remove old chart if it makes the new comparison illegible; its evidence
   remains in notes and files.
3. TECHNICAL APPROACH: existing architecture; visibly label trusted-process
   assumption and co-located3-of-4 demonstrator. Describe reference+visual/layout
   scoring+receipt verification accurately. Bottom cards CURRENT BOUNDARIES and
   PROPOSED HARDENING (NOT IMPLEMENTED): witness not enforced, allocation not
   atomic; protected custody/external checkpoints, transaction-wide allocation,
   release-bound policy. Do not portray Fabric/HSM/SDK as implemented.
4. FEASIBILITY AND VIABILITY: compact measured outcomes plus four risk groups:
   physical unvalidated; raster/low-capacity policy; rollback/row race;
   operator framing/removable carriers. All unresolved. Visibly state
   "Recipient session evidence is not proof of who leaked it."
5. IMPACT AND BENEFITS: investigative assistance/offline operation/PQC; a
   proposal not ready for operational accusations. Gate1 security/claims;
   Gate2 independent documents/keys/recipients and attack negatives;
   Gate3 held-out physical comparisons at matched visibility/security budgets.
   Multi-page, signed/tagged PDF, key custody and real-world validation listed.
6. RESEARCH AND REFERENCES: known/prescribed components, physical baselines,
   honest contribution as measured integration and failure analysis, not novel
   best-in-world performance. Shorter-code/stronger-carrier ideas unvalidated.
   Public repo placeholder or supplied link. Full source URLs in notes.

## Notes coverage

The identifiers below retain the official-requirement and Claude-review numbering;
they are not arbitrary labels for newly ordered presentation points.

| Label | Required assessment topic |
|---|---|
| R1 | Unique invisible watermark at decryption: demonstrated controlled release path; trusted viewer/race caveats |
| R2 | Recipient/session specificity: explicit session and row, allocation race remains |
| R3 | Visually identical/forensically distinct: measured extracted-text equality and PSNR, not universal invisibility |
| R4 | Cryptographic binding to recipient identity: enrollment-bound prototype receipts, custody caveat |
| R5 | Recipient's own private signing key: ML-DSA mechanism demonstrated; exclusive human custody unproven |
| R6 | NIST PQC KEX/signatures: ML-KEM-768 and ML-DSA-65, no classical fallback |
| R7 | Blockchain/DLT audit: local co-located3-of-4 demonstrator only |
| R8 | No single administrator can alter/delete history: NOT MET; independent custody and enforced witness absent |
| R9 | Extract mark from leak: digital fixture successes; physical0/4 shipped, experimental1/4, not robust deployment |
| R10 | Ledger lookup: implemented for available valid records, rollback can erase association |
| R11 | Verifiable associated recipient/event: signature checks work, framing/copy-to-human inference limits |
| R12 | Offline/air-gapped operation: demonstrated local architecture, not an audited hardened deployment |
| R13 | No cloud KMS: no required external KMS in implemented workflow |
| R14 | No public blockchain: local demonstrator has no public-chain dependency |

| Label | Required corrected Claude-review topic |
|---|---|
| P1 | Separate witness detects rollback, trace/release do not enforce it; integration alone does not prevent/recover deletion |
| P2 | Allocation race: append locks too late; cover initial read through commit and avoid nested lock reacquisition |
| P3 | Actual rasterized transplant bypasses layout corroboration; parser already rejects renamed/prefixed PDF masquerading |
| P4 | Insufficient126-symbol layout capacity disables protection; shortness is only one cause; release-policy fix proposed |
| P5 | Authority regeneration of existing signed-session marks; no fresh signature forgery required |
| P6 | Removal of both carriers leaves readable content and no attribution signal on tested fixture |
| P7 | Trusted viewer can access clean plaintext before marking; ordinary output is released only after commit |
| P8 | Non-blind extraction needs retained original and correct version |
| P9 | Evidence identifies a session/copy association, not which human intentionally leaked it |
| P10 | Actual physical0/4 historical, experimental1/4; latest scores and limits, not uniformly coin-flip bits |
| P11 | One person across30 accumulated issued sessions; other-issued score null once, non-null29 times; not20-person test |
| P12 | Same document/authority secret/codebook in30 end-to-end trials |
| P13 | Independent30-codebook study is code-level only, not carrier/PDF/physical evidence |
| P14 | Existing signed-PDF preservation is an expected compatibility issue; tagged-PDF damage is untested, not demonstrated |
| P15 | Published main experiments single-page; code has page loops but no validated multi-page benchmark |
| P16 | This update corrects PPT/PDF/verifier stale physical-pending wording; other historical prose is not claimed updated |
| P17 | Witness claim must remain separate-tool capability, not enforced trace-path protection |
| P18 | Unconditional transplant-abstention claim is false for raster/low-capacity paths |
| P19 | Registration and1000-row scoring do not prove photo robustness; fine alignment remains unresolved |
| P20 | Co-located quorum is real limitation and was already partly disclosed on slide4 |
| P21 | No initialized Git; local version history and publishing are separate; backups retained |
| P22 | Unknown team/repository placeholders remain unless user supplies them; strict verification then fails |
| P23 | Stray=4.11 retained outside presentation scope, not silently deleted |
| P24 | Novelty unestablished; TRACE is trajectory watermarking, physical comparators already exist; set equality not proven novel |

Export the same notes that are embedded in PPTX to Markdown. Include each
requirement1..14 with prototype-level status and caveats, not a misleading green
count. Include P1..P24 labels with corrected findings, including P11 correction,
P14 expected signature issue versus untested tagged structure, P15 validation
gap versus multi-page loops, P16 updated deck/verifier only (other old prose is
not silently claimed updated), P20 co-location already disclosed, P21 Git versus
publishing, P22 unknown details, P23 retained stray file not deleted, P24 limits
of novelty inference. This is the audit record, not marketing copy.

## Acceptance

Six slides/pages with readable text and no collisions/overflow on visual review.
PPTX ZIP integrity, exact notes coverage and matching PDF content verified.
Verifier passes with explicit --allow-placeholders and remains false in strict
mode while team/repo fields are missing. Missing physical input and stale claims
are covered by focused negative tests. Original prototype/evidence hashes remain
unchanged. No claim of all software defects fixed.
