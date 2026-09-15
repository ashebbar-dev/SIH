# NISHAN Tone Probe Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Test a fixed identity-independent tone-normalization baseline against unchanged and unavailable-oracle residuals on the existing synthetic fixture.

**Architecture:** A standalone research probe estimates monotone source-to-capture curves using two spatial folds, assembles a cross-fitted transformed-source prediction, and applies the existing hard carrier score plus known conditional thresholds. Every prespecified condition/profile is reported; production code and historical evidence remain unchanged.

**Tech Stack:** Existing `.venv`, NumPy, OpenCV, scikit-learn IsotonicRegression, unittest and existing NISHAN modules.

**Spec:** `research/NISHAN_CAPTURE_DECODER_FINDINGS_2026-09-10.md`, especially Oracle profile and Next evidence needed. This is an exploratory baseline, not a novel watermark method.

## Global Constraints

- No alternative problem-statement work; NISHAN and Dhruva are the active tracks.
- No production changes, input changes, downloads, package installs, Git initialization or commits.
- Keep `research/tools/probe_nishan_capture_channel.py` and existing evidence unchanged.
- No codebook, recipient, decoded-bit or score inputs to tone estimation or spatial folds.
- Report all eight conditions and four profiles; do not select a winner for accusation.
- Conditional modeled budget is epsilon=1e-6 across H=8*4*1000=32000 opportunities; no empirical probability or production-security guarantee.
- Fit parameters and fold geometry must be fixed before first scoring. This same-fixture follow-up is exploratory, not untouched confirmation.
- Use `apply_patch` for source edits and the existing `.venv` for runs.

---

### Task 1: Cross-fitted tone estimator and fixed diagnostic

**Files:**
- Create `research/tools/probe_nishan_tone_channel.py`.
- Create `research/tools/tests/test_nishan_tone_channel.py`.
- Create report `research/evidence/nishan-tone-channel-implementation.md`.
- Generate new evidence `research/evidence/nishan-tone-channel-2026-09-10.json` once, through the program's exclusive-create output mode.
- Own no other files. Import existing helpers; do not refactor the old probe.

**Interfaces:**
- `spatial_folds(shape: tuple[int, int], tile_size: int = 72, buffer: int = 12) -> tuple[np.ndarray, np.ndarray]`: return 0/1 checkerboard tile labels and Boolean interior fitting mask. Coordinates modulo tile_size must be >=buffer and <tile_size-buffer. All fixed values align to the 6-pixel carrier grid. Reject nonpositive sizes, negative buffers or buffers consuming a whole tile.
- `fit_curve(source_values: np.ndarray, captured_values: np.ndarray) -> np.ndarray`: return 256 monotone predicted capture intensities. Clip and round source bins into 0..255; compute captured-intensity mean and count per populated bin using bincount; fit increasing IsotonicRegression with sample_weight=counts and out_of_bounds='clip'; predict all 256 bins. One supported bin returns a constant curve, empty fitting samples raise ValueError. Reject nonfinite/mismatched inputs.
- `crossfit_source(source: np.ndarray, captured: np.ndarray) -> np.ndarray`: for grayscale or RGB same-shaped arrays, predict each fold using curves fitted exclusively to interior pixels of the OTHER fold, channel by channel. Predictions use linear interpolation in the 256-point curve at actual source intensity, clipped at bounds. Output has same shape, float dtype. Fail if either fitting fold has no pixels; never silently fit evaluation pixels.

- [ ] **Step 1: Add focused tests before implementation.**

Test real numerical behavior, not mocked sklearn calls:

```python
source = np.tile(np.arange(144, dtype=float), (144, 1))
capture = 0.5 * source + 10
prediction = crossfit_source(source, capture)
np.testing.assert_allclose(prediction[20:120, 20:120], capture[20:120, 20:120], atol=1e-8)
```

In addition: assert fixed fold/buffer geometry; monotonicity for nonmonotone captured bin means; one-bin constant fallback; empty fitting set and NaN rejection; grayscale/RGB shapes; matching dimensions required. Mutate only held-out fold-0 captured pixels and assert fold-0 predictions remain identical (fold-1 predictions may change). The provided affine test may need a source construction covering all bins in BOTH training folds: use `source = (np.indices((288,288)).sum(axis=0) % 128).astype(float)` and compare only source levels supported by both folds, determined from source/fold masks alone. Record any such test-construction correction explicitly.

- [ ] **Step 2: Run the tests and record expected missing-module failure.**

```sh
.venv/bin/python -m unittest discover -s research/tools/tests -p 'test_nishan_tone_channel.py' -v
```

- [ ] **Step 3: Implement the small estimator and diagnostic.**

Use `np.bincount` for bin counts/sums and fit the weighted isotonic means. A lookup prediction is `np.interp(source, np.arange(256), curve)` with default clipped endpoints. Cross-fitting uses large spatial tiles to avoid pixelwise interleaving; the fixed interior buffer reduces nearby blur contamination but is not a proof of independent capture noise or innocent codewords.

Reuse `conditional_null_threshold` and NISHAN imports from the old probe. Use the exact source, marked PDF, public fixture secret and contexts from that probe. Keep 144 DPI, block size 6, 1,000 rows, c=5 and 52,500 symbols unchanged. A small duplicated fixture setup is preferable to mutating the reproducible old runner. Assert source and marked dimensions match.

Conditions must match the old runner, in order: identity; affine 0.85*x+15 rounded/clipped; gamma 1.5 rounded/clipped; white_clip_250; binary_threshold_200; gaussian_sigma0.75; gaussian_sigma1.5; gaussian_sigma2.5. Every image-valued transform receives uint8 RGB.

For each condition compute four predictions of transformed unmarked source:

1. `unchanged_source`: original source luma.
2. `crossfit_rgb`: crossfit_source(original RGB, captured RGB), then luma conversion without forced uint8 quantization.
3. `crossfit_luma`: crossfit_source(original luma, captured luma).
4. `unavailable_oracle`: luma of exact known transform applied to original RGB.

The fit never receives the oracle. Decode captured_luma - prediction with the same carrier block correlations >0 and Tardos scoring as the old probe. Report all 1,000 scores in each profile, historical and conditional accusation sets, expected-row score, maximum other score, bit error fraction, zero-correlation fraction, active-symbol count, threshold/witness, and prediction RMSE against oracle_source over the whole cross-fitted output. All recipients use the same threshold. Do not label oracle recovery as a candidate improvement.

Use a fixed `config` object in output for all transforms, fit bins/means/weights, tile size, buffer, folds, epsilon and H. Include source/marked/script/helper hashes; explicitly describe public fixture, shared geometry, only one document/codebook, adaptive research direction, conditioning assumptions, finite-precision threshold arithmetic and lack of physical captures/novelty. No printed binary image artifacts are required.

- [ ] **Step 4: Run covering tests; score once in a fresh evidence file.**

```sh
.venv/bin/python -m unittest discover -s research/tools/tests -p 'test_nishan_tone_channel.py' -v
.venv/bin/python research/tools/probe_nishan_tone_channel.py --output research/evidence/nishan-tone-channel-2026-09-10.json
```

Exclusive-create output must reject an existing path before expensive scoring. Keep per-condition compact stdout updates. Preserve all outcomes, including worse results. Root will compare unchanged/oracle score fields against historical evidence; thresholds intentionally differ due to the enlarged budget.

- [ ] **Step 5: Self-review and hand off.**

Report exact red/green commands/results, evidence path, all-profile recovery counts, numerical/code concerns, and any pre-run test-construction correction. No source/capture score tuning or repeated parameter search. Root performs independent review before treating gains as reliable evidence.

## Preflight and execution decisions

| Task/interface pair | Producer and consumer | Finding |
|---|---|---|
| Task 1 estimator and tests | fit_curve and spatial_folds feed crossfit_source | Fixed geometry and bin behavior; test source support may need the explicit correction above |
| Task 1 diagnostic and existing probe | Imports unchanged conditional threshold; copies fixed fixture setup | Threshold budget changes intentionally; scores must still reproduce unchanged/oracle fields |

Ruling: use retained snapshots/reports, not Git worktrees or commits — initialization is reserved — cost: no commit-based recovery, so evidence is retained.

Ruling: use a deterministic source pattern with adequate bin support for the affine test if needed — out-of-support clipping is required behavior, not an affine extrapolator — cost: narrower test claim, with support mask fixed without capture scores.
