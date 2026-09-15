# NISHAN Compact Carrier Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run one reproducible, isolated comparison of original, repeated compact, and larger-block compact carriers and prepare matched physical-test inputs.

**Architecture:** A small empirical profile/scoring module reuses the frozen NISHAN carrier without changing it. A runner produces a preregistered matrix and replay state; a read-only capture command later scores fresh artifacts against that exact run.

**Tech Stack:** Existing Python `.venv`, NumPy, PyMuPDF, Pillow, unittest; no installs.

**Spec:** `research/NISHAN_COMPACT_CARRIER_SPEC_2026-09-12.md`

## Global Constraints

- New implementation writes only `research/experiments/compact_carrier_v1/` and new run outputs only `research/evidence/nishan-compact-carrier-2026-09-12/`; all prototypes, submissions, existing evidence and `parallel_research/` are read-only.
- No dependency installation, network compute, git initialization, publication, deletion, or production integration. Use the existing `.venv` with `PYTHONDONTWRITEBYTECODE=1`.
- All authored edits use `apply_patch`. Generated experiment artifacts may be written by the implemented runner. Keep private run secrets out of terminal output and chmod their file to 0600.
- One fixed pilot run; no threshold, strength, transform or seed tuning after results. A failed run is preserved and reported, not overwritten. Destination must not exist before a new run.
- Every report says empirical, one source document, two issued copies per profile, no physical result, no probability certification, no collusion guarantee, no production attribution, and no novelty/superiority claim.

---

### Task 1: Empirical compact-code carrier matrix and capture replay

**Read first:** `research/NISHAN_COMPACT_CARRIER_SPEC_2026-09-12.md` is the complete binding experimental design. Read its entire text, plus current `prototypes/nishan_pq/nishan/tardos.py`, relevant carrier interfaces, and the local precision note. All numeric and matrix requirements in that spec apply verbatim.

**Files:**
- Create `research/experiments/compact_carrier_v1/profiles.py`: fixed profiles, logical-score aggregation, observation summaries and replay validation.
- Create `research/experiments/compact_carrier_v1/run_study.py`: one-shot source/copy generation, fixed transformations, manifest/replay, metrics/results and physical instructions.
- Create `research/experiments/compact_carrier_v1/score_capture.py`: read-only replay CLI.
- Create `research/experiments/compact_carrier_v1/test_profiles.py`: focused behavioral tests.
- Create `research/experiments/compact_carrier_v1/README.md`: commands, expected artifact structure and limitations.
- Generate only `research/evidence/nishan-compact-carrier-2026-09-12/run-01/` for the full pilot; unit-test temporary outputs also remain within this plan's evidence directory.

**Interfaces:**
- Consumes existing `tardos.parameters`, `tardos.generate_keyed(config,key,context)`, `tardos.accusation_scores`, `tardos_carrier.embed_pdf`, `decode_word_with_diagnostics`, `measure_pdf_pair`, `marking_condition_errors`, and `watermark.load_pages`; do not edit these.
- Produces `symmetric_scores(codebook, biases, word) -> np.ndarray`, `collapse_correlations(correlations, logical_positions, repetitions) -> tuple[np.ndarray,np.ndarray]`, immutable `PROFILES`, and the two CLIs above. Other helper names are internal, not downstream contracts.

- [ ] **Step 1: Write behavior tests before implementations.** Include the following literal numerical tests and add shape/binary/finiteness validation, matched-area/profile constants, replay-state hash rejection, no-overwrite output, and fixed matrix count/identity tests. Tests exercise real functions, not only CLI mocks.

```python
def test_symmetric_uses_both_output_symbols(self):
    p = np.array([0.2, 0.8])
    x = np.array([[1, 0], [0, 1]], dtype=np.uint8)
    np.testing.assert_allclose(symmetric_scores(x, p, np.array([1, 0])), [4.0, -1.0])
    np.testing.assert_allclose(symmetric_scores(x, p, np.array([0, 1])), [-4.0, 1.0])

def test_repetition_sums_analog_correlations_before_threshold(self):
    # Majority hard decisions would give the wrong first bit.
    corr = np.array([9., -2., -1., 1., -1., 1., -1., -2.])
    word, summed = collapse_correlations(corr, 2, 4)
    np.testing.assert_allclose(summed, [6., -2.])
    np.testing.assert_array_equal(word, [1, 0])

def test_zero_correlation_tie_is_zero(self):
    word, summed = collapse_correlations(np.array([1., -1.]), 1, 2)
    self.assertEqual(int(word[0]), 0)
    self.assertEqual(float(summed[0]), 0.)
```

- [ ] **Step 2: Run RED and retain actual failing output.**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python -m unittest discover -s research/experiments/compact_carrier_v1 -p 'test_*.py' -v
```

Expected initial failure: absent `profiles` implementation, not environment/import dependency failure.

- [ ] **Step 3: Implement the fixed scoring/profile/replay functions.** Use validation then the numerical kernels below; add no theorem probability output. Original scoring stays in the imported original function. For replay inputs validate hashes before loading private arrays; never use pickle-enabled loading.

```python
signed_output = 2.0 * word.astype(np.float64) - 1.0
weights = signed_output / np.sqrt(biases * (1.0 - biases))
scores = np.empty(codebook.shape[0], dtype=np.float64)
for start in range(0, codebook.shape[0], 32):
    chunk = codebook[start:start + 32].astype(np.float64)
    scores[start:start + 32] = ((chunk - biases) * weights).sum(axis=1)

summed = correlations.reshape(repetitions, logical_positions).sum(axis=0)
word = (summed > 0.0).astype(np.uint8)
```

- [ ] **Step 4: Implement the frozen runner matrix and capture CLI.** Use the exact source, profiles, two issued rows and five transforms in the spec. Save fresh keys and array replay in one private NPZ (`allow_pickle=False` on reads); metadata strings can be UTF-8 byte arrays or fixed string arrays. Write manifest before scoring. Public commitments and versions, not secrets, go in JSON. Save each observation's all-row scores, physical correlations and logical decoded bits. Use `ImageFilter.GaussianBlur(radius=1.0/2.0)` for separate transforms, and `Image.Resampling.LANCZOS` for both half-resize stages. The run guard is `output.mkdir(parents=True, exist_ok=False)` before generating any artifacts. Within a created run, catch exceptions only to retain a failure record and re-raise. Capture CLI loads that run read-only, validates source/replay hashes and reports always-registration. Document that local manifests aren't independently signed provenance.

```python
expected = {(kind, profile, row, transform)
            for kind, profile, row, transform in declared_matrix}
observed = {(o['kind'], o['profile'], o['row'], o['transform']) for o in observations}
if len(observations) != 57 or len(expected) != 57 or observed != expected:
    raise RuntimeError('fixed observation matrix is incomplete or duplicated')
```

- [ ] **Step 5: Run GREEN once on complete implementation and record exact evidence.** Use the Step 2 command. No prototype/deck regression-suite rerun is required because these are read-only imports and isolated new files.

- [ ] **Step 6: Execute the one full pilot.**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python research/experiments/compact_carrier_v1/run_study.py --output research/evidence/nishan-compact-carrier-2026-09-12/run-01
```

Then run the capture CLI once against the generated row-0 `symmetric-12-r1` clean PNG. Report this as replay smoke validation with registration, not physical evidence. Preserve stdout as a generated evidence artifact without leaking keys. Do not rerun the full pilot to improve outcomes.

- [ ] **Step 7: Self-review, package evidence, and report.** No git exists, so no commit/init. Use hashes and controller snapshots. In `task-1-report.md`, include RED/GREEN outputs, full-run command and duration, all 57 observation counts, profile-by-transform intended-row ratio/BER/selected-row summary, negative results, actual PSNR and text equality, replay smoke output, frozen advancement results and all limitations. Return concise DONE/DONE_WITH_CONCERNS status and path. You must not spawn subagents or change this plan/spec; ask the controller about design conflicts.

- [ ] **Step 8: Controller task review then broad final review.** Generate new-file diff package, dispatch separate task spec/quality review, address Important/Critical findings under SDD. A separate final review includes decision prose and deferred findings; reviewers do not repeat reported suites.

- [ ] **Step 9: Controller handoff.** Write `research/NISHAN_COMPACT_CARRIER_DECISION_2026-09-12.md`, preserve raw results and snapshots, and link the physical packet only if the advancement gate warrants it. Do not promote research into production or revise slides based only on this pilot.
