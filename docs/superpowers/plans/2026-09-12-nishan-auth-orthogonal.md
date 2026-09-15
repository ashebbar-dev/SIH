# Orthogonal Authenticator Falsification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce a fixed-rule, fresh-key digital carrier study that can reject the proposed authenticator's content-binding claim before further protocol investment.

**Architecture:** An isolated carrier helper reuses NISHAN's existing templates and reference registration. A fixed runner produces paired Tardos-only/auth artifacts, recovery measurements and a copied-observed-overlay falsification. Nothing enters the production release path or final presentation.

**Tech Stack:** Existing `.venv`, Python, NumPy, PyMuPDF, Pillow, OpenSSL ML-DSA-65, read-only NISHAN modules.

**Spec:** `research/NISHAN_AUTH_ORTHOGONAL_SPEC_2026-09-12.md`

## Global Constraints

- This is a carrier-only research experiment, not a recipient-controlled or asymmetric protocol.
- Render at 144 DPI; 6-by-6 blocks; Tardos n=1000, c=5, epsilon=1e-6, 52,500 symbols; Tardos strength 4.0.
- Authenticator strength 4.0; 72 HMAC bits; 126 Hamming bits; 200 repetitions; exact 72-bit acceptance. No tuning or result-selected reruns.
- All outputs go under a fresh, non-existing run directory. Refuse an existing destination rather than overwriting.
- Do not modify prototype modules, submission files, old captures or historical benchmarks. No new dependencies, external services or hardware.
- Implement only the four named experiment files; preserve all experimental outputs and evidence. No Git repository exists; use file hashes and snapshots, not Git initialization, commits or destructive cleanup.

---

### Task 1: Isolated carrier, study runner and complete first run

**Files:**
- Create: `research/experiments/auth_orthogonal_v1/carrier.py`
- Create: `research/experiments/auth_orthogonal_v1/run_study.py`
- Create: `research/experiments/auth_orthogonal_v1/test_carrier.py`
- Create: `research/experiments/auth_orthogonal_v1/README.md`
- Evidence: `research/evidence/nishan-auth-orthogonal-2026-09-12/`

**Interfaces:**
- Consumes: `nishan.tardos_carrier._plan(secret, context, capacity, symbols)`, `_templates(block_size)`, `_prf_bytes(secret, context, purpose, length)`, `_transparent_overlay(pattern, strength)`, `embed_pdf`, `measure_pdf_pair`, `decode_word_with_diagnostics`, `marking_condition_errors`; `nishan.layout_tag.hamming74_encode/decode`; `nishan.watermark.load_pages`, `_luma`, `average_collusion`; `nishan.registration.align_page`; `nishan.pqc.generate_keypair` and `support`; `nishan.tardos.parameters/generate_keyed/accusation_scores/accuse`. Read their signatures before use.
- Produces: CLI `PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python research/experiments/auth_orthogonal_v1/run_study.py --output FRESH_PATH`.
- Carrier public functions: `canonical_context(source_hash: str, recipient_key_hash: str, session_id: str, row: int) -> str`; `auth_bits(secret: bytes, context: str) -> numpy.ndarray`; `make_plan(secret: bytes, context: str, tardos_order: numpy.ndarray, tardos_orientation: numpy.ndarray)` returning a dataclass containing raw/encoded bits, positions, orientations, polarities; `embed_auth(base: Path, destination: Path, plan, shapes: list[tuple[int,int]]) -> None`; `residual_blocks(reference: Path, suspect: Path) -> numpy.ndarray`; `decode(blocks: numpy.ndarray, plan) -> dict`; `copy_observed_overlays(donor: Path, target: Path, destination: Path) -> None`.

- [x] **Step 1: Read the spec and recovered source, then write focused failing tests.** The full matrix and second-fixture definition in the spec are binding. Use actual arrays and PDFs, not mocks. For example:

```python
def test_context_is_canonical_and_each_field_binds(self):
    original = canonical_context('a' * 64, 'b' * 64, 'session-0', 0)
    self.assertEqual(original, canonical_context('a' * 64, 'b' * 64, 'session-0', 0))
    for altered in [canonical_context('c' * 64, 'b' * 64, 'session-0', 0),
                    canonical_context('a' * 64, 'c' * 64, 'session-0', 0),
                    canonical_context('a' * 64, 'b' * 64, 'session-1', 0),
                    canonical_context('a' * 64, 'b' * 64, 'session-0', 1)]:
        self.assertNotEqual(original, altered)
        self.assertFalse(np.array_equal(auth_bits(b'x' * 32, original), auth_bits(b'x' * 32, altered)))
```

Also test plan capacity rejection, unique placements and orthogonal orientations, exact decoding from synthetic signed blocks, rejection on an intentionally mismatched decoded tag, real observed-PDF image/mask copying onto changed text without plan/key parameters, and CLI refusal to overwrite an existing output directory. Use smaller synthetic block geometry only for unit-level decode tests; the CLI profile remains fixed.

- [x] **Step 2: Run targeted tests and save RED evidence.**

```bash
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python -m unittest discover -s research/experiments/auth_orthogonal_v1 -p 'test_*.py' -v
```

Expected before implementation: import/function failure. Preserve command, failure output and explanation in the report.

- [x] **Step 3: Implement the recovered carrier with fixed real context and complete observations.** Follow the recovered algorithm; compact core of tag generation:

```python
payload = hmac.new(secret, b'NISHAN-RECIPIENT-AUTH/v1|' + context.encode('ascii'), hashlib.sha3_256).digest()[:9]
raw = np.unpackbits(np.frombuffer(payload, dtype=np.uint8))
encoded = layout_tag.hamming74_encode(raw)
```

Plan uses the recovered PRF sort over 52,500 Tardos positions and selects 25,200 without replacement, flips orientation with `1 - tardos_orientation`, and applies recipient PRF polarity. Decode sums the 200 repeated correlations, Hamming-decodes and compares exact bits; retain the raw sums. Reuse code rather than duplicate embed/decode per attack. The copied-overlay function must reconstruct donor `get_images()` objects including soft masks using PyMuPDF and insert them on the changed target. It receives no secrets. Reject unexpected page counts/geometry rather than silently zip-truncate. Validate the profile and context types at entry points; JSON output must contain finite numbers or explicitly encoded unavailable values, never bare NaN/Infinity.

- [x] **Step 4: Implement the fixed runner, local material retention, matrix and README.** Generate all fixed inputs and randomness once, save premeasurement manifest, and print per-document/case progress. Compute Tardos baseline and auth measurements on the same source/coalition/transform. Save the complete positive/negative/copying observations, exact file and text mismatches, generated-artifact hashes, run times and Gate A/B booleans. The README gives the command, data/key warning and every security boundary from the spec. Gate failure is valid research output, not a program exception or reason to retune. Missing files, unsupported PQC, malformed inputs and overwrite requests are errors. No new result graph or presentation change is requested.

- [x] **Step 5: Run focused GREEN, then the complete new suite once and the one full study.**

```bash
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python -m unittest discover -s research/experiments/auth_orthogonal_v1 -p 'test_*.py' -v
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python research/experiments/auth_orthogonal_v1/run_study.py --output research/evidence/nishan-auth-orthogonal-2026-09-12/run-01
```

Preserve first-run results, including failure gates. If code crashes, preserve partial output and report the cause before a distinctly named repaired run; never select best outcomes. Hash the four experiment source files and all imported NISHAN modules. Do not rerun unrelated production or deck suites.

- [x] **Step 6: Self-review and report.** State test commands/outputs, exact case counts, Gate A/B outcomes, copied-overlay observations and all limitations. Save full report at `research/evidence/nishan-auth-orthogonal-2026-09-12/task-1-report.md`; return only concise status, test summary, concerns and report path. No commit is possible; preserve hashes and evidence for controller review. Do not spawn subagents.

## Controller closeout

- [x] Review the task's complete new-file diff, fixed-rule adherence and manifest/results integrity using a fresh reviewer.
- [x] Obtain a broad final review on code, evidence interpretation and primary-source comparison. Do not promote the experiment to the presentation solely because a test suite passed.
- [x] Record the evidence-backed go/no-go decision and preserve the reviewed submission artifact hashes unchanged.
