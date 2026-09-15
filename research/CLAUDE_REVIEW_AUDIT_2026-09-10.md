---
title: "Adversarial audit of Claude's NISHAN-PQ and Dhruva review"
date: 2026-09-10
status: "Verified; Tardos/live-PDF recommendations implemented and re-audited; Git publication deferred"
---

> Historical checkpoint: this file records the state reviewed before the
> deterministic-source, enrollment-root, replay, and external-witness hardening.
> Current measured values live in `artifacts/nishan/` and the current strategy
> document; do not copy numbers from this checkpoint into the final deck.

# Decision

Claude's review was materially correct for the version it inspected. It found
weaknesses that changed both the evidence and the story. Its main conclusion at
that point was:

> The current NISHAN-PQ prototype is a strong proof of feasibility and careful
> execution. Its original “atomic coupling” claim is not a defensible novelty
> claim, because SIH26237 specifies that coupling and closely related systems
> already exist.

NISHAN-PQ remains the best **internal-hackathon entry**. The conversion path
Claude recommended has now been implemented far enough to replace the reviewed
prototype: the live PDF carries a full configured collusion code plus an
domain-separated HMAC tag in text-layout operators, while retaining
searchable/selectable text. Editable PDFs require channel agreement, so deletion
or transplantation produces a lead, a conflict, or no signal rather than a
one-channel accusation. Both carriers remain removable, and real print/camera
results are pending, so it is stronger but not finale-ready.

Dhruva remains the second submission. Correcting its evaluation protocol leaves
the 60-second median drift at 18.3%, above ISRO's 10% target, and reveals that the
bucket contains 51 non-overlapping windows rather than 305 heavily overlapping
ones.

# Post-review implementation result

The PDF release path now assigns every session a row from an original Tardos
reference profile with `n = 1,000`, `c = 5`, `epsilon = 10^-6`, `m = 52,500` and
`Z = 2,100`, plus a 72-bit HMAC tag expanded to 126 layout symbols. It embeds both
at decryption, retains the original PDF text, fonts and vector objects, signs both
commitments with the recipient's ML-DSA key, commits that event to the quorum
ledger, and scores all 1,000 rows when a leak is submitted.

Fresh measured results on the declared synthetic page are:

| Attack | Carrier result | Final decision | Boundary |
|---|---|---|---|
| Digital marked PDF | Tardos row 0 + layout row 0 | Attribute row 0 | Dual-channel corroboration on one fixture |
| Two-/three-/five-copy aligned raster average | 2/2, 3/3, 5/5; zero other rows | Tardos channel only | Named raster fixtures; theorem condition observed |
| JPEG quality 55 | 1/1; zero other rows; 5,904 marking violations | Tardos channel only | Empirical recovery; theorem not transferred |
| Delete visual overlay | Layout row 0 survives | Abstain; record row 0 lead | Removal resistance not proved |
| Normalize layout | Tardos row 0 survives | Abstain; record row 0 lead | Removal resistance not proved |
| Transplant Alice visual onto Bob layout | Tardos row 0, layout row 1 | Abstain on conflict | Cross-recipient splicing detected in fixture |
| Delete both carriers | No signal | No attribution | Attribution availability lost |
| Synthetic perspective photo | Row 0 after ORB/RANSAC; zero other rows | Tardos channel only | Synthetic geometry only; hardware pending |

The five generated PDFs average 41.820 dB rendered PSNR. Their extracted text
and word sequence match the source, the search query still resolves, and the
source vector drawing remains. The end-to-end run separately confirms the
ML-KEM delivery, ML-DSA event signatures and quorum linkage for the JPEG and
two-/three-copy traces.

This result corrects the two biggest product defects in the reviewed version:
the random-correlation cutoff has been replaced on the PDF path by a declared
code profile, and the document is no longer rasterized. It does not license a
broad `10^-6` physical-watermark claim. The theorem is conditional on its random
construction and marking assumption, while the keyed implementation is finite
precision and the attack layer can violate the assumption. The evidence records
that distinction mechanically.

# Finding-by-finding ruling on Claude's reviewed version

| Claude finding | Ruling | Evidence and action |
|---|---|---|
| `0.035` is an unjustified fixed threshold | **Agree** | Independently reproduced the broader collusion null and first replaced it with an honestly labelled 400-decoy screening calibration. The integrated PDF path now retires that score entirely: it uses the declared Tardos `Z = 2,100` threshold and records the theorem/carrier boundary. The empirical rule remains only for legacy image input. |
| “400 decoys + 4.9σ” can support roughly `10^-6` | **Reject that inference** | Four hundred exchangeable decoys have best one-sided empirical resolution `1/401 ≈ 0.00249`. A Gaussian tail extrapolation may guide screening but does not prove a rare-event probability, especially when the tail model has not been validated. The code now labels this explicitly as **not a formal familywise bound**. |
| Three-copy averaging already works | **Agree, narrowly** | A fresh run recovered Alice, Bob and Charlie at scores 0.464–0.476. It is now in the demo, tests, evidence and deck. The wording says “three-copy pixel-average fixture,” not general three-colluder security. |
| Dhruva's outage count is inflated by overlap | **Agree** | A 600-row 60-second window advanced only 100 rows, so adjacent windows shared 83% of their samples. The benchmark now uses a duration-sized stride. Counts are 206, 103, 51 and 25 for 15/30/60/120 seconds. “Effective n ≈ 51” was a useful warning, though overlap does not mathematically make every six windows one identical observation. Non-overlapping reporting removes the ambiguity. |
| Near-stationary windows corrupt percentage drift | **Agree; change the proposed fix** | The old 15-second set reached 0.17 m travelled, where error/distance is meaningless. A blanket 100 m cutoff would select only faster 15-second windows and introduce a new bias. The corrected benchmark reports absolute endpoint error for every window and percentage drift only for distance ≥50 m, matching ISRO's shortest stated distance example. Excluded counts remain visible. |
| One S1 sequence is inadequate | **Agree** | Same sequence, device, mount and route family appear on both sides of the temporal split. This remains an explicitly named blocker. Extending the loader is quick; producing a valid group holdout with per-sequence time alignment, unit checks, training and diagnosis is not honestly a “30-minute fix.” No transfer claim is made yet. |
| Four validator keys on one machine weaken the ledger claim | **Agree** | The demo proves detection of an edit that was not re-endorsed and survival of one divergent replica. An operator holding a quorum of private keys can create an alternative valid history. All spoken and written claims now require separately controlled peers and keys for the production guarantee. |
| Recipient non-repudiation is mechanism-only | **Agree** | The demo process holds synthetic recipients' private keys. ML-DSA proves that the corresponding key signed; it does not yet prove employee identity or exclusive custody. Offline CA binding, hardware-backed keys and an issuance ceremony remain gates. |
| Rasterizing the PDF is a serious product defect | **Agree; fixed with a new boundary** | The integrated path retains extracted text, word order, search and vector content. It now carries a visual Tardos word and a structural HMAC tag. Removing either forces abstention; removing both removes attribution. Tagged/complex PDFs remain untested. |
| Detection is non-blind | **Agree** | The tracer needs the original to form a residual. That is operationally possible because the authority distributed the source, but it affects storage, chain of custody and attack handling. It is now stated before a jury can expose it. |
| No Git repository / commit hash | **Factually correct** | Git initialization and public push are deliberately reserved for the internal-hackathon day at the user's request. Until then, no immutable pre-fit commit exists and no text claims otherwise. `.gitignore` and a publication checklist are prepared. |
| Stale second PDF | **Agree** | The duplicate under `rendered/` had a different score and must be removed. Only the reviewed root PPTX/PDF paths are canonical. |
| Split Python environments | **Agree** | A single `.venv` now imports PyMuPDF, cryptography, python-pptx, NumPy, Pillow, Matplotlib, scikit-learn and the editable NISHAN package. Root requirements and commands document it. |
| One random UUID score should not be a benchmark | **Agree** | The earlier 30-trial study remains as legacy evidence. The deck now uses the configured coded profile, its fixed `Z`, five marked-PDF PSNR values, all-row scoring, and the separate attack fixture rather than presenting one correlation as a general benchmark. |
| Deck date and placeholders | **Agree** | The run date is corrected to 10 September. Placeholders remain intentionally because team ID/name/repository URL are unknown; the verifier must fail without `--allow-placeholders` until they are filled. |

# Independent threshold reproduction

The new evidence was regenerated rather than copying Claude's table:

| Query | Issued-session score(s) | 400-decoy null SD | Worst decoy | Selected screening threshold |
|---|---:|---:|---:|---:|
| Bob JPEG Q55 | Bob 0.331 | 0.00402 | 0.01157 | 0.01157 |
| Alice + Bob pixel average | 0.605 / 0.577 | 0.00992 | 0.03170 | 0.03170 |
| Alice + Bob + Charlie pixel average | 0.476 / 0.464 / 0.463 | 0.01011 | 0.02724 | 0.02724 |

The null broadening under averaging is real. It also shows why a fixed cutoff
chosen on a single-copy JPEG cannot be transported silently to collusion queries.
The selected prototype rule is the larger of (a) the maximum observed decoy score
and (b) a Gaussian Bonferroni estimate using the number of issued sessions scored.
That is a practical screening guardrail. It is not a theorem: the finite decoy
set does not establish the tail law, and choosing the maximum decoy does not
certify a low familywise error for a large future roster.

The correct evidentiary route is to declare the maximum roster `n`, maximum
coalition `c`, and tolerated familywise false accusation `ε` before generating a
collusion-secure code. Tardos codes were designed for this setting and have code
length on the order of `c² log(n/ε)` under their proof model. Their bounds depend
on assumptions such as the marking assumption; those assumptions must be stated,
then the embedded carrier must be tested separately against physical and digital
distortion. [Tardos, *Optimal probabilistic fingerprint codes*](https://doi.org/10.1145/1346330.1346335) and [Simone & Škorić on accusation-tail modelling](https://link.springer.com/article/10.1007/s10623-011-9563-4)

# Novelty audit

## Why the old claim fails

SIH26237 itself tells teams to create a unique invisible mark at decryption, bind
the event with the recipient's private-key signature, commit it to an immutable
DLT, trace a leaked copy to the record, use NIST post-quantum algorithms, and run
air-gapped. Repeating those boxes in the same order proves careful compliance; it
cannot be the novel contribution.

Prior art makes the broader integration claim weaker:

- **T-Tracer (2022)** describes a blockchain-aided watermarking scheme for traitor
  tracing in non-repudiation data delivery. It is the closest cited work and is
  enough by itself to defeat “watermark + blockchain + non-repudiation is new.”
  [ACM DOI 10.1145/3494106.3528674](https://doi.org/10.1145/3494106.3528674)
- A 2022 Sensors paper integrates blockchain and fingerprinting for online/offline
  traceability of digital-product lifecycles, demonstrated on audio. It is related
  integration prior art, though it is not the same recipient-decryption/PQC/air-gap
  protocol. [Gonzalez-Compean et al.](https://www.mdpi.com/1424-8220/22/21/8400)
- The cited anti-leak patent family generates a unique value when a document is
  viewed/downloaded, records the request in a distributed ledger and applies a
  pixel-level visual code. That overlaps access-time marking plus DLT, but its
  published claims are not identical to an invisible, collusion-secure,
  recipient-signed PQ system. Treat it as boundary evidence, not proof that every
  NISHAN detail is patented. [US11816756B1](https://patents.google.com/patent/US11816756B1/en) and [US12462321B1](https://patents.google.com/patent/US12462321B1/en)
- Seclore, Fasoo and Locklizard ship dynamic user watermarks at access/view/print
  time. Their cited product pages describe visible identity watermarks; they do
  not establish the invisible collusion-secure DLT design Claude's shorthand may
  imply. [Seclore](https://adoption.seclore.com/help-center/seclore-for-interoperable-design-files/protecting-interoperable-caddesign-files), [Fasoo](https://en.fasoo.ai/products/fasoo-smart-screen/), [Locklizard](https://www.locklizard.com/pdf_security/)
- Keeping text usable while encoding marks through word/line/glyph layout is also
  not new by itself; Brassil and colleagues published line/word-shift document
  marking in the 1990s. [IEEE DOI 10.1109/49.464718](https://doi.org/10.1109/49.464718)

Claude is therefore correct about the old framing and somewhat too sweeping about
the individual patents and commercial products. They show crowded territory, not
an exact duplicate of the complete SIH protocol.

## The defensible contribution after implementation

Use this claim, and keep the words **proposed** and **measured** accurate:

> NISHAN-PQ evaluates a conflict-aware dual-domain evidence protocol for live
> PDFs. A full recipient-specific Tardos word in the rendered page and an
> a domain-separated HMAC session tag in text-layout operators are committed to
> the same PQ-signed release. Editable PDFs are attributed only when both channels
> agree; removal, transplantation or an unissued row forces abstention. Raster
> leaks use the rendered path and report its proof assumptions separately.

This is not “Tardos is new,” “dual watermarking is new,” or “transplant attacks
are new.” The engineering contribution is the fail-closed identity-consensus
protocol and its measured boundary: all 52,500 symbols fit into a usable live
PDF, every one of 1,000 rows is scored, a second structural identity binds to the
same signed event, and manipulation produces an explicit abstention. It is
implemented on one synthetic page. Removal resistance, physical robustness and
dishonest-distributor protection remain open.

# Corrected Dhruva result

| Duration | Non-overlapping windows | Windows ≥50 m | Phone-IMU median absolute error | Phone-IMU median drift on ≥50 m |
|---:|---:|---:|---:|---:|
| 15 s | 206 | 168 | 15.4 m | 15.3% |
| 30 s | 103 | 97 | 31.4 m | 16.1% |
| 60 s | 51 | 51 | 71.8 m | 18.3% |
| 120 s | 25 | 25 | 171.0 m | 22.9% |

The correction does not rescue Dhruva's target, but it makes the result suitable
for an honest second proposal. The 60-second median absolute error of 71.8 m is
below 100 m, yet the median distance in that bucket is only 394.8 m; it must not
be presented as satisfying ISRO's “100 m over 1 km” example. The 120-second bucket
travels a median 817.6 m and has 171.0 m median error.

# Selection and winning assessment

No evidence supports an exact probability for this team. The defensible judgments
are conditional:

- **Internal round:** strong. A cold, offline, working forensic demo with real PQ
  algorithms and explicit limitations should compare well with slide-only teams.
- **National shortlist:** plausible, especially while the statement remains at a
  very low counter. The evidence now includes the hard coded-carrier work rather
  than only the prescribed block diagram. The proposal still must not relabel
  known primitives as inventions.
- **Grand finale today:** not ready. The engine now handles single-carrier removal
  safely by abstaining and detects a visual/layout transplant in the fixture, but
  a domain jury can delete both carriers, demand real print/camera results,
  challenge the trusted endpoint, and reject the single-machine key custody.
- **Grand finale after the stated gates:** credible. A working live-text coded
  carrier with declared error control and an adversarial attack matrix gives the
  jury a measurable comparison that most block-diagram implementations will lack.

# Non-negotiable gates

1. **Live-document gate — passed on the synthetic fixture:** the marked PDF remains searchable and selectable;
   extracted text matches the source; tagged accessibility and vector/text objects
   are retained where present; size growth and rendering differences are reported.
2. **Code gate — reference implementation passed:** declare roster `n`, coalition limit `c`, error target `ε`, code
   length and proof assumptions. Unit tests reproduce code generation and scoring.
3. **Attack gate — digital/synthetic matrix passed on one fixture:** 24 predeclared
   transformations include averaging, code-level majority/minority/interleaving,
   JPEG, re-save, resize, crop, screenshot, rotation, transplantation, carrier
   deletion and synthetic perspective. Independent codebooks/documents and real
   print-scan/camera captures remain required.
4. **Statistics gate — enforced in artifacts:** distinguish a theoretical bound from an empirical rate.
   Never infer `10^-6` from hundreds or thousands of trials.
5. **Identity gate:** offline CA binding and hardware-backed or separately operated
   recipient-key custody.
6. **Ledger gate:** peers and endorsement keys controlled separately; demonstrate
   deletion, re-signing attempts, equivocation, outage and refusal to release when
   quorum is unavailable.
7. **Trusted-viewer gate:** document exactly what prevents or detects capture before
   marking; do not imply that a ledger repairs a compromised endpoint.

# Work status after this audit

Completed now: the original threshold audit; full 1,000-row Tardos generation and
scoring; dual-domain live-PDF embedding; exact text/search/vector retention on the
fixture; 30 separately derived codebooks covering 120 code-level attack pairs;
24 predeclared digital/synthetic decisions; cross-recipient transplant
and deletion attacks; ORB/RANSAC page registration; explicit proof-boundary
reporting; end-to-end PQ and ledger integration; corrected Dhruva evaluation;
one environment; revised deck source; secret-safe `.gitignore`; and the
GitHub-day checklist.

Deliberately deferred: Git initialization, commit and public push. The user reserved
those actions for the internal-hackathon day. Unfinished gates are real
printer/scanner and phone-camera capture, stronger content binding against
both-carrier removal, independent codebook/document trials, tagged/complex PDF
coverage, dishonest-distributor protection, separate identity/validator custody,
and hardened endpoint enforcement.
