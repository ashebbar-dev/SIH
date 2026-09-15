### Task 2: Separate physical registration and attribution processes

**Files:**
- Create `research/tools/probe_nishan_bias_physical.py`.
- Create `prototypes/nishan_pq/tests/test_bias_physical_boundary.py`.
- Create `research/evidence/nishan-bias-registration-task-2-report.md`.
- Generate fresh `research/evidence/nishan-bias-physical-2026-09-10/`.

**Prerequisite:** Task1 independently reviewed, `physical_gate_passed=true`,
and current module hashes match the successful gate manifest. If not, do not
run this task; report the gate failure and retain the hypothesis as unproven.

**Interfaces:** CLI subcommands `prepare --gate PATH --output PATH` and
`score --prepared PATH --output PATH`. Use Task1 public module APIs and the
existing conditional-null helper. No new physical tuning parameters.

```python
def validate_gate(gate_directory: Path) -> dict: ...
def validate_prepared(prepared_directory: Path) -> dict: ...
def prepare(gate_directory: Path, output_directory: Path) -> dict: ...
def score(prepared_directory: Path, output_file: Path) -> dict: ...
```

Use exactly `preparation.json`, `prepared.npz` and `commitment.json` for the
preparation output. The commitment is written last and includes SHA256 of the
first two files. Validate gate `results.json` has completed=true and
physical_gate_passed=true, its manifest_sha256 matches actual manifest.json,
and every `manifest.json` code_sha256 dependency matches the current file.
Resolve recorded code paths within the workspace; reject paths outside it.
The physical source response uses existing `tardos_carrier.embed_pdf` on the
original source PDF with artificial all-zero/all-one binary words in a scoped
temporary directory, never Task1's raster-source PDF replacement. Load their
actual rendered luma and derive midpoint/pilot with Task1 endpoint_expectation
and the fixed blur. Preserve these response arrays and the q image in the npz.

- [ ] **Step 1: Write and run focused failing process-boundary tests.**

Test preparation rejects a failed gate or mismatched module hash, exclusive
paths cannot overwrite existing evidence, and scoring rejects changed prepared
words/hashes. Test scoring consumes stored words, not image registration. Test
the two declared profile names and H=8000 survive preparation/scoring. Use
tiny in-memory words and local temporary evidence, not real images.

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python -m unittest discover \
  -s prototypes/nishan_pq/tests -p 'test_bias_physical_boundary.py' -v
```

- [ ] **Step 2: Freeze and prepare all physical profiles without a roster.**

Use exact files akshay.jpeg, akshay1.jpeg, akshay2.jpeg, akshay3.jpeg from
`/home/user_end4/Downloads`, source `artifacts/nishan/synthetic-source.pdf`,
fixture SHA3 secret from `b'NISHAN Tardos carrier public fixture v1'`, contexts
`public-benchmark-codebook/v1` and `synthetic-source/full-tardos-profile-v1`,
config(1000,5,1e-6), and the strength4 geometry from Task1. Predeclare only
`affine_baseline` and `affine_bias_translation`.

Recompute ORB and ECC-affine with the exact existing registration-single
runner's `refine` and `compose_and_render`. Do not load prior score-bearing
JSON in preparation; baseline comparisons are deferred to the scoring process.
Do not call that runner's `run`, which generates a roster. Render from original
capture once. A failed initialization becomes explicit failure for both
profiles. Call the reviewed search for the second profile without fallback
to a score-preferred transform. A refinement failure remains no accusation.

Decode both profiles using existing keyed block-sign correlations on the
original-source residual, all52500 symbols, without scores. Save full decoded
words and correlations in an npz, all objective surfaces/selected transforms,
mask and energy counts, source/input/module hashes, complete settings and
warnings in preparation.json, then write a hash manifest last. Original
images never leave their current locations. Do not generate/load a roster in
this process, even after registration. No per-image recipient label is needed.

- [ ] **Step 3: Score the frozen prepared words in a fresh process.**

Verify hashes, generate the original1000-row roster, assert p matches the
prepared biases exactly, score every successful word and retain all scores.
All profile failures are represented. Use the existing helper with
epsilon=1e-6,H=8000 and strict score>threshold; oldZ2100 is a retained control.
Report correct row0, highest other score, all accused rows, BER against row0,
zero-correlation fraction, objective and content similarity. Row0 is for
evaluation only. Do not feed scores back into preparation or choose a profile.

In this scoring process, compare every affine-baseline score vector to the
`orb_ecc_affine` records of the retained single-resampling evidence, with
rtol0/atol1e-9, and its matrices to the stored ones. All matches or failures
must be explicit. This check is not a transform selection mechanism.

Preserve existing hard-decoder arithmetic for both physical profiles: warp
original RGB8 first, then use `watermark._luma`; cast Task1's returned luma
tofloat32 (its RGB luma values were computed in that dtype). Subtract original
source luma in float32, use the existing float32 signed block templates, and
sum each block product with dtypefloat32 before `word=(corr>0).astype(uint8)`.
This prevents a summation-precision change from being confused with geometric
refinement. Save full correlations and words for successful profiles; failed
profiles have explicit statuses and no successful word.

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python \
  research/tools/probe_nishan_bias_physical.py prepare \
  --gate research/evidence/nishan-bias-registration-synthetic-2026-09-10 \
  --output research/evidence/nishan-bias-physical-2026-09-10
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python \
  research/tools/probe_nishan_bias_physical.py score \
  --prepared research/evidence/nishan-bias-physical-2026-09-10 \
  --output research/evidence/nishan-bias-physical-2026-09-10/scores.json
```

If Task1 requires a numbered successful gate directory, use that exact path
instead and record it. Code failures preserve prior outputs and use a new
numbered directory after correction; scientific failure does not trigger a
new scoring attempt. No image, codeword or parameter selection using scores.

- [ ] **Step 4: Focused tests, one physical preparation/scoring run and review.**

Run the new boundary tests green, then the two real commands once. Report all
eight outcomes, including failure statuses, without narrowing to successful
captures. Note whether akshay3 attribution is retained and akshay2 is newly
recovered; other outcomes still count as evidence. Hand off exact test output,
fresh artifact paths, hashes and code for independent review.

## Preflight and rulings

| Interface/task | Agreement check | Result |
|---|---|---|
| Task1 response→search | Native midpoint/mean, fixed blur, original capture sampling | Renderer gates precede physical use; no fractional-alpha shortcut |
| Task1 search→Task2 | No roster input; explicit accepted/failure statuses | Failures cannot silently use a favorable score or enlarged search |
| Task1 gates→Task2 | Successful immutable code/gate hashes | Failed scientific gates disable physical run |
| Task1 tests→code | Fast unit tests separate from256-case research suite | Heavy validation runs once, all outcomes retained |
| Task1 capture→Task2 baseline | Preserve RGB8 warp then luma order | Avoid changing interpolation/rounding along with translation |
| Task2 prepare→score | Hashed words/transforms fixed before roster generation | Separate processes and validation make information flow inspectable |

Ruling: retain snapshots/reports instead of Git worktrees/commits — initialization is reserved — cost: no commit-based recovery.

Ruling: use a zero-row view of the unchanged keyed generator for bias-only access — avoid copied cryptographic logic and recipient-row generation — cost: relies on current zero-length generation behavior, covered by a focused equivalence test.

Ruling: first test the bounded global translation model rather than expanding to local warps — isolate the proposed objective on known initial geometry — cost: cannot establish recovery from page curvature or larger alignment errors.

Ruling: require fixed synthetic gates before physical scoring — prevent an unverified response/geometry model from being selected by known-recipient outcomes — cost: a gate failure delays physical testing and may require a separately specified model.

Ruling: compare prior affine-baseline matrices/scores only after the new preparation commitment — prior JSON includes recipient scores and must stay out of registration — cost: a baseline mismatch is detected after preparation rather than before it. Hard-decoder float32 arithmetic remains unchanged while the registration objective uses float64.

Self-review: the response, projection, all289 candidates, deterministic
abstention rules, all256 recovery cases, toy null and erasure checks map to
Task1. The four captures, both profiles, separate preparation/scoring and
immutable words map to Task2. Task2 is conditional on actual Task1 success,
not merely completion of code. No placeholder settings remain. RGB/luma
ordering was corrected above before execution. Public helper signatures are
shared consistently; Task2 owns its CLI process serialization boundary.
