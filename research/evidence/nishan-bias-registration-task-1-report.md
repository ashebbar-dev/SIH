# NISHAN bias registration — Task1 implementation report

Date: 2026-09-10. Synthetic research only; no physical images loaded, no Task2
implementation, no production changes, no novelty or security claim.

## Scope and fixed interpretation

Implemented only `research/tools/nishan_bias_registration.py`,
`research/tools/check_nishan_bias_registration.py`, and
`prototypes/nishan_pq/tests/test_bias_registration.py`, plus this report and the
fresh evidence directory. Existing codebook generation is called with a
zero-row `dataclasses.replace` view; no cryptographic generator was copied.
Registration exposes no recipient-row, roster, or score argument. Its math is
float64; original capture channels/dtype are preserved through the single
Lanczos warp, with existing RGB luma conversion afterward.

The module uses complete smooth-source 6×6 blocks, common support across all
289 candidate transforms including a four-pixel original-capture margin,
rank-valid 96×96 tile plane projections followed by block DC removal, and the
fixed feasibility/objective/tie/boundary rules. It retains all candidate values
and invalid reasons even on feasibility abstention. Native synthetic responses
use production `_transparent_overlay`, synthetic binary templates, and actual
PyMuPDF rendering at exact 144-DPI geometry. An original source-PDF response
path remains outside Task1 and must be handled in separately authorized Task2.

Before controls were constructed, the controller ruled: use (+1,0) displacement
for all controls; quantize the white255 source's native strength4 response to
nearest four gray levels then clip to [0,255]; for erasure, map both white
source endpoints (251/255) at or above250 to255; use independently generated
wrong geometry; and define source-edge-only as a one-pixel black vertical
line x=120 on source245 with that line also present in the reference mask.
The B+W control uses the unquantized native expectation, before the fixed blur.
Abstained controls retain only baseline diagnostic words, never successful
selected words. These choices are recorded in the manifest before execution.

## Exact TDD commands and output

Red command, exit1:

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p 'test_bias_registration.py' -v
```

```text
test_bias_registration (unittest.loader._FailedTest.test_bias_registration) ... ERROR

======================================================================
ERROR: test_bias_registration (unittest.loader._FailedTest.test_bias_registration)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_bias_registration
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/user_end4/MySpace/SIH/prototypes/nishan_pq/tests/test_bias_registration.py", line 13, in <module>
    import nishan_bias_registration as reg
ModuleNotFoundError: No module named 'nishan_bias_registration'


----------------------------------------------------------------------
Ran 1 test in 0.001s

FAILED (errors=1)
```

Initial green used the same command, exit0:

```text
test_common_support_margin (test_bias_registration.BiasRegistrationTests.test_common_support_margin) ... ok
test_deterministic_exact_ties_and_roster_independence (test_bias_registration.BiasRegistrationTests.test_deterministic_exact_ties_and_roster_independence) ... ok
test_edge_excludes_whole_block_and_neighborhood (test_bias_registration.BiasRegistrationTests.test_edge_excludes_whole_block_and_neighborhood) ... ok
test_endpoint_response_and_erasure (test_bias_registration.BiasRegistrationTests.test_endpoint_response_and_erasure) ... ok
test_keyed_biases_zero_rows_equal_existing_generator (test_bias_registration.BiasRegistrationTests.test_keyed_biases_zero_rows_equal_existing_generator) ... ok
test_no_active_and_zero_energy_abstain (test_bias_registration.BiasRegistrationTests.test_no_active_and_zero_energy_abstain) ... ok
test_projection_linearity_and_plane_then_block_dc (test_bias_registration.BiasRegistrationTests.test_projection_linearity_and_plane_then_block_dc) ... ok
test_rgb8_warp_before_luma_different_capture_shape (test_bias_registration.BiasRegistrationTests.test_rgb8_warp_before_luma_different_capture_shape) ... ok
test_transform_composition_exact_rectangle (test_bias_registration.BiasRegistrationTests.test_transform_composition_exact_rectangle) ... ok

----------------------------------------------------------------------
Ran 9 tests in 2.663s

OK
```

Final focused suite expanded support/boundary/invalid-objective/native-unused
coverage before the full gate began. Same command, exit0:

```text
test_boundary_maximum_is_failure_with_diagnostic_transform (test_bias_registration.BiasRegistrationTests.test_boundary_maximum_is_failure_with_diagnostic_transform) ... ok
test_common_support_margin (test_bias_registration.BiasRegistrationTests.test_common_support_margin) ... ok
test_deterministic_exact_ties_and_roster_independence (test_bias_registration.BiasRegistrationTests.test_deterministic_exact_ties_and_roster_independence) ... ok
test_edge_excludes_whole_block_and_neighborhood (test_bias_registration.BiasRegistrationTests.test_edge_excludes_whole_block_and_neighborhood) ... ok
test_endpoint_response_and_erasure (test_bias_registration.BiasRegistrationTests.test_endpoint_response_and_erasure) ... ok
test_keyed_biases_zero_rows_equal_existing_generator (test_bias_registration.BiasRegistrationTests.test_keyed_biases_zero_rows_equal_existing_generator) ... ok
test_native_unused_pixels_have_no_overlay (test_bias_registration.BiasRegistrationTests.test_native_unused_pixels_have_no_overlay) ... ok
test_no_active_and_zero_energy_abstain (test_bias_registration.BiasRegistrationTests.test_no_active_and_zero_energy_abstain) ... ok
test_nonpositive_and_zero_residual_are_not_accepted (test_bias_registration.BiasRegistrationTests.test_nonpositive_and_zero_residual_are_not_accepted) ... ok
test_projection_linearity_and_plane_then_block_dc (test_bias_registration.BiasRegistrationTests.test_projection_linearity_and_plane_then_block_dc) ... ok
test_rgb8_warp_before_luma_different_capture_shape (test_bias_registration.BiasRegistrationTests.test_rgb8_warp_before_luma_different_capture_shape) ... ok
test_single_unsupported_pixel_excludes_entire_block (test_bias_registration.BiasRegistrationTests.test_single_unsupported_pixel_excludes_entire_block) ... ok
test_transform_composition_exact_rectangle (test_bias_registration.BiasRegistrationTests.test_transform_composition_exact_rectangle) ... ok

----------------------------------------------------------------------
Ran 13 tests in 5.306s

OK
```

## Fixed full synthetic gate

Command:

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python research/tools/check_nishan_bias_registration.py --output research/evidence/nishan-bias-registration-synthetic-2026-09-10
```

Completed once on the frozen source revision, exit0, elapsed553.164320565993s
(about9.22 minutes). No failed full run or corrected-source rerun occurred.
Exact CLI output:

```text
renderer: {"passed": true, "cases": 8}
recovery: 8/256 complete; 8 recovered; elapsed=17.988s
recovery: 16/256 complete; 16 recovered; elapsed=34.423s
recovery: 24/256 complete; 24 recovered; elapsed=51.083s
recovery: 32/256 complete; 32 recovered; elapsed=65.488s
recovery: 40/256 complete; 40 recovered; elapsed=79.151s
recovery: 48/256 complete; 48 recovered; elapsed=92.492s
recovery: 56/256 complete; 56 recovered; elapsed=107.828s
recovery: 64/256 complete; 64 recovered; elapsed=120.410s
recovery: 72/256 complete; 72 recovered; elapsed=133.786s
recovery: 80/256 complete; 80 recovered; elapsed=149.265s
recovery: 88/256 complete; 88 recovered; elapsed=165.409s
recovery: 96/256 complete; 96 recovered; elapsed=182.106s
recovery: 104/256 complete; 104 recovered; elapsed=198.255s
recovery: 112/256 complete; 112 recovered; elapsed=214.672s
recovery: 120/256 complete; 120 recovered; elapsed=231.128s
recovery: 128/256 complete; 128 recovered; elapsed=248.585s
recovery: 136/256 complete; 136 recovered; elapsed=265.686s
recovery: 144/256 complete; 144 recovered; elapsed=282.835s
recovery: 152/256 complete; 152 recovered; elapsed=299.231s
recovery: 160/256 complete; 160 recovered; elapsed=317.735s
recovery: 168/256 complete; 168 recovered; elapsed=334.369s
recovery: 176/256 complete; 176 recovered; elapsed=350.926s
recovery: 184/256 complete; 184 recovered; elapsed=367.687s
recovery: 192/256 complete; 192 recovered; elapsed=386.017s
recovery: 200/256 complete; 200 recovered; elapsed=400.206s
recovery: 208/256 complete; 208 recovered; elapsed=415.580s
recovery: 216/256 complete; 216 recovered; elapsed=431.503s
recovery: 224/256 complete; 224 recovered; elapsed=449.735s
recovery: 232/256 complete; 232 recovered; elapsed=468.408s
recovery: 240/256 complete; 240 recovered; elapsed=487.159s
recovery: 248/256 complete; 248 recovered; elapsed=504.671s
recovery: 256/256 complete; 256 recovered; elapsed=521.992s
control: {"name": "gain_0.85_plus15", "status": "accepted", "dx": -1.0, "dy": 0.0, "recovered": true}
control: {"name": "planar_shading", "status": "accepted", "dx": -1.0, "dy": 0.0, "recovered": true}
control: {"name": "near_white_quantization", "status": "accepted", "dx": -1.0, "dy": 0.0, "recovered": true}
control: {"name": "unmarked_source", "status": "accepted", "dx": 0.0, "dy": 0.0, "recovered": false}
control: {"name": "white_endpoint_clipping250", "status": "abstain", "dx": null, "dy": null, "recovered": false}
control: {"name": "B_plus_W_only", "status": "accepted", "dx": -1.0, "dy": 0.0, "recovered": true}
control: {"name": "independent_wrong_geometry", "status": "boundary_failure", "dx": 2.0, "dy": 2.0, "recovered": false}
control: {"name": "source_edge_only", "status": "accepted", "dx": 0.0, "dy": 0.0, "recovered": false}
final: {"renderer": true, "recovery": true, "null": true, "composition": true, "independence": true, "erasure": true}
physical_gate_passed=True; elapsed=553.164s; results_sha256=9941ec6b312e5bbd6481bcf0ad460191c681a60a7b1407387f5bc5402dd34aee
```

### Gate totals and retained failures

Renderer8/8, recovery256/256 (100%, versus fixed95% requirement), null8/8
selected words×3 MGFs each, half-pixel composition4/4, exact integer rectangle
composition1/1, roster-swap invariance, and zero-pilot erasure all passed.
All256 recovery cases have exactly zero coordinate error, with all73,984
candidate records retained. Each case keeps its chosen transform, decoded
word, mask/projection hashes, energy statistics, runner-up and elapsed time.
All four half-pixel corrections are also exact. Integer baseline(-5,+3) and
residual(-2,+1) compose to(-7,+4) and restore the shifted rectangle exactly.

The flat-page common mask retains1444/1600 marked blocks (51,984 pixels), with
full pilot squared energy59905.730254216396, masked energy53942.70699038887,
and retention0.9004598852476583. No tile loses blocks through rank rejection.
The independence check preserves transform, objective, mask, projection, and
decoded-word hashes when unrelated local test rosters are replaced.

| Control | Status | Selected(dx,dy) | Best objective | Coordinate error |
|---|---|---|---:|---|
| gain0.85+15 | accepted | (-1,0) | 0.6600587190591443 | (0,0) |
| planar shading | accepted | (-1,0) | 0.6600587190591484 | (0,0) |
| near-white quantization | accepted | (-1,0) | 0.6600587190591467 | (0,0) |
| unmarked source | accepted by alignment rule | (0,0) | 0.01208844773804123 | (1,0) |
| white endpoint clipping250 | abstain | none | none | undefined |
| B+W only | accepted | (-1,0) | 0.9457801140214802 | (0,0) |
| independent wrong geometry | boundary_failure | (2,2), diagnostic only | 0.0036151618664093917 | (3,2) |
| source-edge-only | accepted by alignment rule | (0,0) | 0.007516841393649334 | (1,0) |

Unmarked and edge-only inputs fail displacement recovery despite positive
objectives. These positives are not recipient evidence. The wrong-geometry
boundary result is a registration failure. Clipping correctly erases the
white source's251/255 endpoints: supplied pilot squared energy is exactly0,
and registration abstains. B+W synchronizes strongly despite containing no
recipient residual. The fixed controls are not an empirical physical-noise
distribution and establish no real capture robustness.

Null enumeration uses all4096 rows with exact product probabilities for the
declared finite-q model. Its maximum observed relative MGF discrepancy is
3.5527136788004946e-15, below1e-10. Every strict tail is below the helper's
modeled Chernoff bound and0.05. Empty active sets abstain.

| Fixed/selected word | Threshold | Exact strict-tail probability |
|---|---:|---:|
| all-one | 10.585383596985247 | 0.005573842040253524 |
| all-zero | abstain | not tested |
| p>0.5 | 2.4201795979131777 | 0 |
| p<0.5 | 9.671741363686309 | 0.007554789842541798 |
| unmarked source | abstain | not tested |
| clipped white | abstain | not tested |
| B+W only, first12 symbols | 8.552668179782655 | 0.00907999979656655 |
| source-edge-only | abstain | not tested |

`physical_gate_passed` is true under the fixed conjunction of renderer,
recovery, null, composition, and independence gates. Physical scoring remains
unperformed and pending the controller's independent review; this Task1
handoff is not an authorization to bypass that review.

### Renderer details

All eight cases passed the fixed maximum1.01/RMS0.25 gray-level gates.
The renderer enumerates all16 words per case (128 probability-weighted
renderings in total). Errors below reflect the native source-raster embedding
geometry and do not establish a response model for an arbitrary source PDF.
Boundary pixels are the first/last pixel row or column in each6×6 block.

| Source | Strength | Maximum error | RMS error |
|---|---:|---:|---:|
| black | 4.0 | 4.440892098500626e-16 | 2.8643431294259467e-16 |
| black | 2.2 | 1.1102230246251565e-16 | 5.928593550334434e-17 |
| white | 4.0 | 5.684341886080802e-14 | 3.759838749409412e-14 |
| white | 2.2 | 8.526512829121202e-14 | 6.029155041345696e-14 |
| gray128 | 4.0 | 5.684341886080802e-14 | 2.842170943040401e-14 |
| gray128 | 2.2 | 1.4210854715202004e-14 | 1.3293037379376718e-14 |
| ramp | 4.0 | 5.684341886080802e-14 | 2.3386860201671365e-14 |
| ramp | 2.2 | 8.526512829121202e-14 | 2.846793127927916e-14 |

The results artifact retains maximum/RMS errors separately for block interiors
and block boundaries for every case. Largest observed renderer error is
8.526512829121202e-14; no strength fitting was performed.

### Concerns and limits

The tiny null enumeration checks the existing numerical Chernoff helper under
an explicitly ideal conditional-independent model. Its `+1e-9` threshold margin
is not a certified arithmetic bound. The seed and synthetic keys are public
fixtures, not a security experiment. Mechanical roster-swap invariance is not
a cryptographic independence proof. Positive image-correlation objectives are
alignment criteria only and must never be reported as recipient evidence.

The module's synthetic native renderer embeds a raster source at exact pixel
geometry. Physical Task2 must preserve the original source PDF and existing
`_plan` symbol mapping; Task1 does not implement that path. Illumination,
nonlinear clipping, print/camera distortion, larger affine errors, and local
page warps remain outside what these gates can establish. Source-only and
shared-only words are retained solely to exercise the conditional null.

No gate or assertion was removed. No downloads, installs, external writes,
Git commands, GPU use, production edits, or physical-input reads were needed.

## Artifacts and final hash audit

Evidence directory:
`research/evidence/nishan-bias-registration-synthetic-2026-09-10/`.
The manifest precedes all gates and records RNG seed2026091007, all fixed case
constructions/settings, code/dependency hashes and versions: Python3.14.4,
NumPy2.5.3, OpenCV5.0.0 (two threads), PyMuPDF1.28.2, Pillow12.3.0,
SciPy1.18.1. Final read-only hashing confirms every manifest code/dependency
hash still matches its file. No full gate was repeated during that audit.

| Artifact | SHA-256 |
|---|---|
| manifest.json | `703c640df2379a2f0096f70cd1a240237e946534eb137ec8757a16176b23fd48` |
| results.json | `9941ec6b312e5bbd6481bcf0ad460191c681a60a7b1407387f5bc5402dd34aee` |
| synthetic_inputs.npz | `79d0ce2024b8fa1fb5b9e21fb7b786746cff205b737fd6840f4b4a4319f0a9d6` |
| control_inputs.npz | `3678992f2d420f7f2c2358cad99ea86eecf370ab0222dce29c99b801a2994234` |
| research/tools/nishan_bias_registration.py | `2991323b8fbe9c8fc7e8a435dae9b777e2f739eda8d9353be8be574c6f6446eb` |
| research/tools/check_nishan_bias_registration.py | `60488494e9b4c74d1b84150f7522c91a63a53497477e3e3e13ab4a01f9ee6269` |
| prototypes/nishan_pq/tests/test_bias_registration.py | `437d029022c2b567a4d746cac0885440b5866a4a76921ef75839987b65d17b4c` |

The input archive retains p/q, all32 synthetic ideal rows, native responses,
blurred midpoint/pilot, geometry, source, common mask and reproducible public
synthetic keys. The control archive retains every control capture/reference,
midpoint and pilot. Full surfaces, words, exact null calculations and failure
statuses remain in `results.json`; no best-row selection was performed.

Handoff status: **DONE_WITH_CONCERNS** — fixed synthetic gates pass; positive
source-only peaks and the limits above must remain visible in interpretation.
