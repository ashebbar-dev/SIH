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

