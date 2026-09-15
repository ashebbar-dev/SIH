# Orthogonal authenticator: prospective carrier falsification gate

Frozen before new measurements on 12 September 2026. This is a **carrier-only research experiment**, not a recipient-controlled or asymmetric protocol. The reviewed selection presentation and production prototype are out of scope and remain unchanged.

## Question and interpretation

Can the recovered second visual channel reproduce exact digital recovery with fresh randomness, and does copying an observed overlay defeat its apparent content binding? The old probe's source is in `research/SOL_ULTRA_RECOVERED_EXPERIMENT_HANDOFF.md`; its artifacts are gone. This is prospective reimplementation against current dependencies, not exact historical reproduction.

The harness owns all experimental keys. Real ML-DSA public keys supply identity fingerprints in the tag context, but there is no enrollment, signing protocol, independent custody, escrow, ledger or adjudicator. Random keys do not repair that security limitation. Do not call a provider-only negative a malicious-provider forgery test.

## Fixed configuration

- Render at 144 DPI; 6-by-6 blocks; Tardos n=1000, c=5, epsilon=1e-6, 52,500 symbols; Tardos strength 4.0.
- Authenticator strength 4.0, selected from the historical exploration before this run. HMAC-SHA3-256 truncated to 9 bytes (72 bits), Hamming(7,4) to 126 bits, repeated 200 times (25,200 placements). Orthogonal orientation at selected Tardos positions, as in the recovered source.
- Acceptance is exact equality of all 72 decoded bits, after summed-correlation sign decisions and Hamming decoding. No radius, tuning, retry-selected seeds or post hoc profile changes.
- For each document generate a fresh 32-byte authority secret and five fresh 32-byte authenticator secrets with `secrets.token_bytes`. Use fresh UUID sessions and actual newly generated ML-DSA-65 public-key SHA3-256 fingerprints. Save experimental material locally for reproducibility, chmod secrets 0600, and label it non-production and not for submission/publication.
- Canonical context is JSON with sorted keys, separators `(',', ':')`, ASCII encoding, containing protocol `nishan-auth-carrier-study/v1`, source_sha3_256, recipient_public_key_sha3_256, session_id, row, and profile `orthogonal-144-6-4-exact72`. Context changes must change both expected tag and auth plan.
- Exactly two one-page source PDFs: the existing `artifacts/nishan/synthetic-source.pdf`, copied into the fresh run; and a new fixed A4 text/table fixture defined below. Each document has its own fresh authority/codebook and five issued rows 0–4. This tiny convenience sample is not a population estimate or a genuinely independent externally held-out set.
- All outputs go under a fresh, non-existing run directory. Refuse an existing destination rather than overwriting. Record failures as failures; preserve partial evidence if interrupted. Do not modify old captures, old benchmarks, prototype modules or submission files.

## Second fixture

Generate an A4 page with Helvetica title `AUTHENTICATOR RESEARCH FIXTURE B`, subtitle `Synthetic logistics record - not operational data`, and at least 24 numbered lines beginning at (48, 100), spaced 17 points, font size 10. Alternate short sentences and tabular rows: `Item NN | quantity 120 | bay 04 | release 09:30` for odd rows, and `Check NN: verify seal, reference number, and dispatch count.` for even rows. Add a ruled four-column table below the text, within the page. Content and coordinates are fixed before measurements; no randomized text selection or carrier-strength changes. Confirm capacity for 52,500 blocks. Store generated source and its text/hash.

## Measurement matrix

For **each** document, make five matched Tardos-only baselines and five baseline-plus-auth copies. Report source-to-output PSNR and extracted-text equality for all ten files. Do not infer human invisibility or signed-PDF preservation from these measurements.

For coalition prefixes of size 1, 2, 3 and 5, create a PNG average and then JPEG Q55 (`optimize=True`) from it, separately for baseline and auth copies. That is eight artifacts per channel per source. Use the same rounding/rendering policy and same coalition for matched comparisons. For each artifact:

1. Decode and score the complete 1000-row Tardos codebook at fixed Z=2100; report selected, participating and nonparticipating row sets and marking-condition diagnostics.
2. On auth artifacts, evaluate all five issued auth candidates with the original reference; retain exact-match boolean, decoded 72-bit distance, encoded-bit distance, corrected blocks and raw 126 summed correlations per candidate. Report expected members and extra matches separately. These are channel observations, not the current production tracer's attribution decisions.

Negative controls, independently for each source:

- Decode the five Tardos-only baseline PDFs and the unmarked source against all five auth candidates (30 decisions per document).
- On row-0 auth copy, try three changed contexts using the same recipient secret: changed source hash, fresh session UUID, and another recipient public-key fingerprint. All must be reported, not pre-assumed rejected.
- On row-0 auth copy, evaluate 100 freshly generated wrong secrets with its otherwise unchanged context (200 wrong-key controls total). Save each distance and match. These correlated candidate trials do not establish a false-attribution probability.

## Copied-overlay attack (critical falsification)

On source B only, create a content-modified target with identical page geometry by changing `quantity 120` to `quantity 920` in at least one visible line (redact and insert changed text, no donor-image access needed for editing). It must have different extracted text and bytes from the genuine source. From the **observed row-0 marked PDF**, copy its two full-page image objects (Tardos and auth) including their alpha masks onto this modified source. The attack helper receives only donor PDF, modified target and output paths; it must not receive secrets, plans, correlations, codewords or original overlay arrays. Reconstruct image streams from donor objects; no regeneration with a secret.

Evaluate both resulting PDF and its JPEG Q55 raster against the genuine source B, donor context and all five issued auth candidates. Also test donor secret with the changed-source context. Record output/target/donor text and hash distinctions, exact donor-tag matches, Tardos-selected rows, and exact-file-hash mismatch. A donor tag surviving changed content falsifies the claim that hashing content into this visual tag alone prevents overlay transplantation. It does not automatically establish a human guilt verdict from the full unchanged production system, which is not being invoked.

## Evidence and promotion gates

Write machine-readable `manifest.json` before measuring, including configuration, seed/material hashes, fixture hashes, source-code hashes, Python/package/OpenSSL versions and creation time. Write `results.json` after measurements with complete per-case observations and artifact SHA256 hashes; preserve every artifact. No uncaught warning suppression or success-only filtering.

Gate A (limited digital replication): every participating auth candidate exactly matches on all 16 positive artifacts across both sources, no other issued candidate matches, and all direct/changed-context/wrong-key negatives reject. Report actual fractions even when gate fails.

Gate B (content-binding hypothesis): neither copied-overlay artifact may produce an exact donor-tag match under donor context. Failure means **no-go for a transplant-resistant-content-authentication claim**.

Even both gates passing would not establish asymmetric security, independent custody, physical recovery, deployment generalization, novelty or superiority to another product. No automatic promotion to the final PPT. The next protocol phase is conditional on results and primary-literature review.

## Implementation boundary and verification

Create only `research/experiments/auth_orthogonal_v1/carrier.py`, `run_study.py`, `test_carrier.py`, and `README.md`, plus this plan's fresh evidence outputs. Reuse current NISHAN helper modules read-only; no new dependencies, external services or hardware. Carrier module handles tag/plan/embed/decode and observed-overlay copying; runner handles fixed fixtures, attacks and evidence; tests cover real tiny synthetic arrays/PDF behavior and fixed-profile validation. No benchmark success assertion may replace recorded failure outcomes. Run focused RED/GREEN tests, then the new suite once and one full prescribed study. No repeated runs to select favorable results.
