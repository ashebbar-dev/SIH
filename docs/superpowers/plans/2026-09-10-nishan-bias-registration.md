# NISHAN Bias-Only Registration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test whether the analytical shared carrier mean improves physical fingerprint recovery without recipient-dependent registration.

**Architecture:** First implement and independently review a pure image/bias registration module and synthetic gates. Then use it in a two-process physical experiment: freeze transforms and decoded words before generating the recipient roster for attribution. Keep every fixed profile and failure in new evidence.

**Tech Stack:** Existing Python `.venv`, NumPy, OpenCV, PyMuPDF, SciPy and unittest; no installation or GPU.

**Spec:** `research/NISHAN_BIAS_SYNC_DESIGN_2026-09-10.md`. The first experiment and synthetic gates in that note bind this plan. The details below fix numerical tolerances and process boundaries before any new physical scores.

## Global Constraints

- NISHAN and Dhruva remain the active projects; no alternative problem statements.
- Do not modify production code, raw inputs, the printed PDF or any prior evidence.
- No Git initialization/commits, downloads, installs, firmware or external writes.
- Registration must not generate, load or consult recipient rows or their scores.
- Use the actual fixture strength 4.0, 144 DPI and 6-pixel blocks; do not substitute the default strength 2.2.
- No score-based choice of transform, mask, source model or decoder.
- Preserve failed gates and all physical outcomes. Do not loosen a gate after seeing results.
- A positive alignment objective is not attribution. Conditional-null assumptions, public fixture limitations and lack of novelty/physical-security proof remain explicit.
- Use apply_patch for source changes and fresh exclusive output paths for generated evidence.

---

### Task 1: Registration module and synthetic gates

**Files:**
- Create `research/tools/nishan_bias_registration.py`: image/bias math, response construction and deterministic translation search only.
- Create `research/tools/check_nishan_bias_registration.py`: fixed synthetic gate CLI, no physical capture paths or roster scoring.
- Create `prototypes/nishan_pq/tests/test_bias_registration.py`: light focused tests; the full 256-case gate runs once separately.
- Create `research/evidence/nishan-bias-registration-task-1-report.md`.
- Generate new `research/evidence/nishan-bias-registration-synthetic-2026-09-10/`, retaining manifest.json and results.json plus response arrays if needed.

**Interfaces and exact settings:**

```python
def keyed_biases(config, secret: bytes, context: str) -> np.ndarray: ...
def endpoint_expectation(r0: np.ndarray, r1: np.ndarray,
                         q_image: np.ndarray) -> tuple[np.ndarray, np.ndarray]: ...
def prepare_projection(source: np.ndarray, pilot: np.ndarray,
                       coverage: np.ndarray, active_blocks: np.ndarray) -> dict: ...
def project(values: np.ndarray, prepared: dict) -> np.ndarray: ...
def search_translation(capture: np.ndarray, source: np.ndarray,
                       baseline_raw_to_reference: np.ndarray,
                       midpoint: np.ndarray, pilot: np.ndarray,
                       active_blocks: np.ndarray) -> dict: ...
```

Source, midpoint and pilot are scalar luma arrays at reference resolution.
Capture may have different dimensions and be either scalar or RGB. Preserve
its input dtype/channels during warping and convert RGB to existing
`watermark._luma` only AFTER rendering, so actual RGB8 baseline arithmetic is
not silently changed. Use float64 for response/objective math.
`search_translation` takes no secret row, roster or score argument. Its result
includes status, chosen dx/dy and raw-to-reference transform when accepted,
all 289 objective values including invalid flags, mask and energy statistics,
tie/runner-up information and elapsed seconds. It does not score a codebook.

Use existing codebook bias generation without producing any recipient rows:

```python
from dataclasses import replace
empty_config = replace(config, roster_size=0)
p, empty = tardos.generate_keyed(empty_config, secret, context)
assert empty.shape == (0, config.code_length)
return p
```

This is a research-only zero-row view of the existing generator, not a valid
enrollment profile or a change to theorem parameters. Unit-test that p is
bit-identical to the ordinary generator for a tiny fixed test configuration;
that ordinary tiny roster exists only in the test process. Do not copy the
generator implementation or change production APIs.

- [ ] **Step 1: Write light focused failing tests.**

Cover endpoint response and erasure exactly:

```python
r0 = np.array([[251., 255.]])
r1 = np.array([[255., 251.]])
b, w = endpoint_expectation(r0, r1, np.array([[.25, .75]]))
np.testing.assert_array_equal(b, [[253., 253.]])
np.testing.assert_array_equal(w, [[-1., -1.]])
b0, w0 = endpoint_expectation(np.full((2, 2), 255.),
                             np.full((2, 2), 255.), np.full((2, 2), .9))
np.testing.assert_array_equal(w0, np.zeros((2, 2)))
```

Test positive finite bias bounds, shape mismatch errors, no-active/zero-energy
abstention, deterministic tie ordering, projection linearity and removal of a
plane followed by block DC. A constructed source edge must exclude the full
corresponding block before candidate evaluation. Test transform composition
on an exactly shifted rectangle: baseline translates raw by (-5,+3), residual
correction (-2,+1) gives combined (-7,+4). A fixed image and p passed before
and after replacing unrelated test roster arrays must return identical
transform/objective/mask hashes. Do not put unrelated rosters in module state.

- [ ] **Step 2: Run only the new unit-test file and record the expected missing-module failure.**

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python -m unittest discover \
  -s prototypes/nishan_pq/tests -p 'test_bias_registration.py' -v
```

- [ ] **Step 3: Implement response and projection without recipient data.**

Construct both counterfactual native responses by applying the existing
`_transparent_overlay` through PyMuPDF at exact 144-DPI geometry, with binary
all-zero/all-one words or explicit keyed templates. These are artificial
symbol endpoints, not real recipient rows. In the physical task use the source
PDF and existing `_plan` mapping; unused pixels receive no overlay.

```python
midpoint = (r0.astype(np.float64) + r1.astype(np.float64)) / 2
pilot = (2 * q_image - 1) * (r1.astype(np.float64) - r0.astype(np.float64)) / 2
midpoint = cv2.GaussianBlur(midpoint, (0, 0), .75)
pilot = cv2.GaussianBlur(pilot, (0, 0), .75)
```

Keep q assigned by symbol-to-block order, including correct orientation and
polarity in the rendered endpoints. Do not render fractional-alpha means.
The renderer gate below must establish whether this pixelwise approximation
is accurate enough before physical use.

Retain complete marked 6×6 blocks only if the source-luma range across their
18×18 neighborhood is <=8, the neighborhood is inside the page, and all block
pixels have interpolation support under every candidate transform. Include
a 4-pixel original-capture support margin for Lanczos. Build the common mask
before objectives; never let a candidate choose its own pixel support.

Before examining candidates, discard 96×96 tiles whose masked [1,x,y] design
has rank below 3. Require >=1000 remaining blocks and masked pilot squared
energy >=20% of full-page pilot squared energy, with a nonzero denominator.
The remaining mask consists of complete blocks; tile boundaries are multiples
of both 6 and 96, so discarding a tile preserves whole blocks. Precompute the
masked plane projection per tile. Project by subtracting each tile's masked
least-squares plane, then each remaining block's mean. Reuse exactly this
linear operator for every residual and pilot. Use vectorized block means and
precomputed plane design; no per-candidate least-squares decomposition.

- [ ] **Step 4: Implement the fixed translation search.**

```python
grid = np.arange(-2., 2.0001, .25)
translation = np.array([[1., 0., dx], [0., 1., dy], [0., 0., 1.]])
combined = translation @ baseline_raw_to_reference
border = 255 if capture.ndim == 2 else (255, 255, 255)
rendered = cv2.warpPerspective(capture, combined, (width, height),
    flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_CONSTANT, borderValue=border)
candidate = rendered.astype(np.float64) if rendered.ndim == 2 else watermark._luma(rendered).astype(np.float64)
r = project(candidate - midpoint, prepared)
w = project(pilot, prepared)
objective = float(r @ w / (np.linalg.norm(r) * np.linalg.norm(w)))
```

Each candidate samples original capture pixels once. Norm zero/nonfinite is
invalid; all invalid or best objective <=0 causes explicit abstention. Sort
by highest objective, then smallest dx²+dy², then dx, then dy; exact ties only.
A maximum with abs(dx)==2 or abs(dy)==2 is `boundary_failure`, not a refined
image. Keep its transform/objective for diagnosis but do not issue its decoded
word as a successful profile. Return mask/energy counts and all objectives
even for gates/failures where they exist. Use cv2 threads=2 in the runner.

- [ ] **Step 5: Implement and run the fixed synthetic gate suite once.**

Create the exclusive output directory and write manifest.json before gates.
It records settings, code hashes, RNG seed 2026091007, libraries and all fixed
test cases. Code bugs are corrected with retained failed results and a fresh
numbered output directory, never by changing gate values.

Renderer gate: a native 12×12 source with a 2×2 grid of 6×6 symbols, fixed
orientations [0,1,0,1], polarities [1,1,-1,-1] and q=[.1,.3,.7,.9]. Enumerate
all 16 binary words, probability-weight their actual PyMuPDF renderings, and
compare with endpoint expectation before blur. Repeat for black, white, gray
128, and a 12-column 0-to-255 grayscale ramp, strengths 4.0 and 2.2. Record
maximum and RMS error for every case; gate at <=1.01 gray level maximum and
<=0.25 RMS. These fixed limits accommodate 8-bit output without fitting the
strength. Also record errors separately within blocks and at boundaries.

Translation recovery gate: use a 240×240 flat source at luma245, all1600
blocks marked, one fresh truncated-arcsine bias vector (cutoff1/1500) and fixed
fresh geometry. Generate32 independent ideal rows using q. Make native binary
responses using the checked response construction. For each row use shifts
(+1,0),(-1,0),(0,+1),(0,-1) and both identity and sigma0.75 blur channels:
256 cases. Baseline is identity, so expected correction is the negative shift.
At least95% of all256 cases must accept and recover both coordinates within
0.25 pixel. Save every selected transform and error; no best-row selection.
Include separate deterministic half-pixel and integer composition checks.

Null gate: p=[.01,.03,.08,.15,.25,.4,.6,.75,.85,.92,.97,.99], q=floor(p*2^32)/2^32.
Enumerate4096 rows and their exact product probabilities. For words all-one,
all-zero, 1[p>.5], 1[p<.5], and each word produced by the source-only controls,
check direct weighted MGF against the product CGF at theta=.01,.1,1 with
relative tolerance1e-10 (log-domain comparison), and strict tail against the
existing helper's epsilon=.05,H=1 threshold. Empty active set abstains. Do not
describe this as a physical rare-event measurement.

Retain additional no-tuning controls on the first synthetic row: gain.85+15,
planar shading 8*x/width+5*y/height, near-white integer quantization, unmarked
source, white endpoint clipping at250, B+W only, independent wrong geometry,
and source-edge-only content. Save objective surfaces, displacement/errors,
decoded words (for source-only null checks use the first12 symbol positions)
and explicit limitations. Only renderer/recovery/null/composition/independence
tests determine `physical_gate_passed`; nuisance failures prevent claims about
that nuisance but do not silently alter the fixed model. Erased endpoint
pilot must have zero energy and abstain when supplied as such. Positive noise
objectives must not be reported as recipient evidence.

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python -m unittest discover \
  -s prototypes/nishan_pq/tests -p 'test_bias_registration.py' -v
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python \
  research/tools/check_nishan_bias_registration.py \
  --output research/evidence/nishan-bias-registration-synthetic-2026-09-10
```

- [ ] **Step 6: Report and hand off for independent review.**

Report exact red/green output, all gate totals, failed controls, artifact paths
and hashes, runtime and concerns. Do not load physical images or run Task2.
If a scientific gate fails, keep it as a valid completed experiment; report
that physical scoring remains disabled. No assertion or gate may be removed
just to obtain a pass.

#### Task1 additional-control clarification, fixed before construction

All additional controls use imposed shift(+1,0). Near-white quantization uses
source255 with native strength4 response, rounded to nearest4 gray levels and
clipped to[0,255]. Erasure uses source255 endpoint responses then maps every
value>=250 to255; the original245 source would not test this erasure. The
source-edge-only reference is245 with a one-pixel black vertical line atx120,
and the capture is that same source with no carrier, shifted(+1,0). The line
is present in the reference used for the smooth-source mask. Wrong geometry
uses an independent fresh context. Shared-only uses the unquantized native
B+W expectation before the fixed blur approximation, without a recipient
residual. Baseline-decoded words from abstained controls are retained only as
source-only/null diagnostics, never as successful selected-profile outputs.

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
