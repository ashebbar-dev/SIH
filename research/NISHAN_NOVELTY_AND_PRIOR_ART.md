# NISHAN-PQ novelty and prior-art boundary

**Audit date:** 10 September 2026  
**Target:** SIH26237, Ministry of Defence — Indian Navy (WESEE)

## Verdict

The first NISHAN-PQ framing was not novel. Decryption-time recipient marking,
signed provenance, a tamper-evident ledger, post-quantum algorithms, and offline
operation are substantially prescribed by SIH26237. Watermark-based traitor
tracing connected to blockchain also predates this project.

The new prototype has a narrower, defensible contribution:

> **A conflict-aware, dual-domain release fingerprint for live PDFs:** a full
> recipient-specific Tardos word in the rendered page and a domain-separated
> HMAC session authenticator in text-layout operators are committed to the same
> ML-DSA-signed release event. Editable PDFs require agreement between the two
> channels; a disagreement, a missing channel, or an unissued Tardos row forces
> abstention. Rasterized leaks use the rendered Tardos path and record the
> theorem's carrier assumptions separately.

This is a **project contribution**, supported by running code and attack
fixtures. It is not currently claimed as the first publication or as patentably
new. A targeted search found no exact implementation of this complete protocol,
but absence from a finite search is not proof that none exists.

## What is already known

| Element | Prior art | Ruling |
|---|---|---|
| Collusion-secure recipient codes | Tardos constructs binary fingerprint codes with length `O(c² log(n/epsilon))`. [Original paper](https://www.renyi.hu/~tardos/fingerprint.pdf) | Established; cite it. |
| Text-layout document marking | Brassil, Low, Maxemchuk and O'Gorman alter line/word layout to mark electronic text documents. [IEEE paper](https://doi.org/10.1109/49.464718) | Established; do not call layout shifts new. |
| Tardos words embedded by robust watermarking | Shahid, Chaumont and Puech embed Tardos codes using spread spectrum in H.264/AVC. [ICIP paper](https://doi.org/10.1109/ICIP.2010.5652607) | Established connection between code and carrier. |
| Two complementary watermarks | Lu and Liao simultaneously embed robust and fragile marks for protection and authentication. [IEEE paper](https://ieeexplore.ieee.org/document/951542/) | Dual watermarking has existed since at least 2001. |
| Watermark transplantation/cut-and-paste | Barreto, Kim and Rijmen describe transplantation attacks against fragile authentication marks and propose signature-dependent defenses. [IEEE paper](https://ieeexplore.ieee.org/document/958536/) | The attack class is established. Our value is executing it against this release protocol and failing closed. |
| Collusion-aware in-band fingerprinting | Earlier systems already distribute marking symbols pseudorandomly and discuss erasure, alteration, and recipient collusion. [WO2004070585A2](https://patents.google.com/patent/WO2004070585A2/en) | A generic anti-collusion watermark claim is not novel. |
| Recipient-specific dynamic marks | Existing patents generate a mark for each file and recipient, including identity and timestamp information. [US11170078B2](https://patents.google.com/patent/US11170078B2/en) | Per-recipient/session marking is established. |
| Watermark + blockchain traitor tracing | T-Tracer explicitly combines a blockchain-aided watermarking scheme with traitor tracing and non-repudiation. [ACM paper](https://doi.org/10.1145/3494106.3528674) | “Watermark plus blockchain” is not a contribution. |
| Asymmetric Tardos protocols | Charpentier, Fontaine, Furon and Cox address dishonest-provider framing in a Tardos-specific asymmetric protocol. [Author preprint](https://arxiv.org/abs/1010.2621) | NISHAN must not claim that a signed receipt alone proves the recipient caused a leak. |

## What the implemented contribution actually adds

The contribution is the **decision protocol across two representations of the
same released PDF**, not either carrier by itself.

1. The rendered channel carries all 52,500 symbols of one configured Tardos row
   for a declared `n=1,000`, `c=5`, family target `10^-6`, and threshold
   `Z=2,100`.
2. The structural channel carries a 72-bit HMAC tag expanded to 126 positions by
   Hamming(7,4). It binds the source hash, session identifier, and Tardos row while
   retaining searchable/selectable text.
3. The signed event commits the codebook, row, structural tag, released-file hash,
   recipient identity key, and quorum block.
4. The tracer treats an editable PDF and a rendered leak differently. An
   editable PDF is expected to retain both channels and requires agreement. A
   JPEG, screenshot, scan, or photograph has no PDF operators, so it is evaluated
   through the Tardos carrier with explicit preprocessing and marking-condition
   diagnostics.
5. A disjoint result is a security event. The tracer does not choose the stronger
   score or the more convenient identity; it returns no attribution.

The code exercises the distinction. Alice's visual carrier transplanted onto
Bob's layout carrier yields `Tardos={Alice}`, `layout={Bob}`, and an abstention.
Stripping the layout tag after that transplant still causes an editable-PDF
abstention. This blocks the tested one-channel remove-and-transplant route in the
first fusion rule. It does not solve dishonest-distributor framing: the authority
still controls both carrier secrets and can construct a fully consistent copy.

## Current measured boundary

The deterministic public fixture executes 25 attacks or transformations and
scores all 1,000 Tardos rows. The current results include:

- direct digital PDF: both channels identify row 0;
- two-, three-, and five-copy aligned averages: 2/2, 3/3, and 5/5 known rows
  cross threshold, with zero other roster rows;
- four carrier realizations of five-user interleaving, majority, minority and
  coin-flip pirate words: every known row crosses threshold in this one codebook
  fixture, with no other row;
- 30 separately derived codebooks with random five-row coalitions: all five rows
  recovered in all 120 code-level attack/codebook pairs across interleaving,
  majority, minority and coin-flip, with zero innocent accusations. The finite
  Wilson intervals are recorded and do not replace the theorem;
- 30 successive end-to-end releases through real PQ operations and JPEG-Q55:
  exact signed session selected 30/30 times, zero extra codebook rows, and a
  correct-row score of 13,433.3 ± 128.2 against `Z=2,100`. The Wilson interval is
  88.65–100%, so this remains finite fixture evidence;
- removal of either editable-PDF carrier: a single-channel lead remains, but the
  policy abstains;
- removal of both: no attribution signal;
- visual carrier transplant: channel conflict and abstention;
- Alice/Bob visual recombination over Bob's layout: partial overlap still
  produces conflict and abstention rather than returning Bob;
- raster crop: row 0 survives removal of 30% from every edge (84% of page area),
  but not 40% from every edge;
- JPEG: row 0 survives quality 40, but not quality 20;
- deterministic perspective/lighting/photo simulation: ORB/RANSAC registration
  reaches 0.983 gradient similarity and recovers row 0 with no other row.
- a valid signed receipt replay is rejected as a duplicate session and row;
  tracing and the next plaintext release stop;
- coordinated truncation of all four ledger replicas remains a valid prefix to
  the ledger itself, while a separately signed ML-DSA head checkpoint detects
  the rollback. This result depends on keeping the witness outside the ledger
  administrators' control; the public demonstrator does not provide that
  physical separation.

These are one-fixture outcomes. They are not success probabilities. Real
printer/scanner and phone-camera measurements remain pending, and the formal
Tardos bound is not applied when the decoded carrier violates the marking
condition.

## Claims that remain prohibited

Do not say any of these in the deck or pitch:

- “We invented decryption-time watermarking.”
- “We invented dual watermarking.”
- “Blockchain makes the record immutable.”
- “A Tardos threshold proves the leaker's identity.”
- “The false-accusation probability is below `10^-6` for JPEG, scans, or photos.”
- “A valid recipient signature proves that employee leaked the document.”
- “No one has done this before.”

The system traces a released **copy/session**. It does not by itself prove which
human later disclosed that copy, and a dishonest distributor remains a distinct
threat addressed by asymmetric fingerprinting literature.

## Submission-safe novelty language

Use this wording:

> The ingredients are established and the problem statement prescribes the
> overall architecture. Our differentiator is an implemented, conflict-aware
> evidence protocol for live PDFs: a full collusion-code carrier and a
> cryptographic layout tag are bound to one PQ-signed release; editable PDFs are
> attributed only when both agree; transplant and removal attacks produce
> explicit abstentions. Every attack reports the code/carrier boundary rather
> than inheriting a mathematical guarantee silently.

## Falsification plan

The contribution should be demoted if a primary source is found that already
combines all of the following: a recipient-specific collusion code, an independent
live-document structural authenticator, common signed session binding, and an
explicit fail-closed identity-consensus rule tested against cross-recipient
carrier transplantation. Even then, the implementation may remain a strong SIH
prototype, but the claim must change from contribution to reproduction and
deployment engineering.

Before the national finale, search IEEE Xplore, ACM DL, Springer, Espacenet,
Google Patents and Indian patent records with the exact protocol terms, and ask a
watermarking researcher to review both the claim and attack matrix. Record every
close result here.
