# Task 2: frozen physical shared-bias registration experiment

Status: DONE_WITH_CONCERNS. The prescribed experiment date/name is 2026-09-10; execution crossed midnight into 2026-09-11 Asia/Kolkata. Implementation and the single preparation/scoring run completed; the bounded translation hypothesis did not newly recover akshay2.

## Implementation and boundaries

Created `research/tools/probe_nishan_bias_physical.py` and `prototypes/nishan_pq/tests/test_bias_physical_boundary.py`. Production modules, Task1 code, older evidence, and the Downloads images were not edited. No Git initialization or commits, downloads, installations, or external writes were used.

The CLI exposes `validate_gate`, `validate_prepared`, `prepare`, and `score`. Preparation validates the completed successful Task1 gate, manifest digest, and every recorded workspace-contained code dependency before creating its exclusive output directory. The successful gate is `research/evidence/nishan-bias-registration-synthetic-2026-09-10/`.

Bias-only preparation uses Task1's zero-row view of the unchanged keyed generator with the exact public fixture secret, contexts, config(1000,5,1e-6), strength 4, 144 DPI and 6-pixel blocks. All 52,500 symbols are retained. Only `affine_baseline` and `affine_bias_translation` are declared; H=8000 and epsilon=1e-6 are fixed.

The physical response embeds artificial all-zero and all-one words using existing `tardos_carrier.embed_pdf` on the original source PDF in a scoped temporary directory. It loads the actual rendered RGB endpoints, applies existing luma arithmetic, forms Task1 endpoint expectation using q=floor(p*2^32)/2^32, then applies the fixed Gaussian sigma 0.75 blur. The endpoint PDF files are temporary; the actual luma endpoints, q image, native and blurred midpoint/pilot remain in the NPZ.

Each capture independently recomputes ORB and the retained single-resampling runner's exact `refine` and `compose_and_render` helpers. The runner's `run` function is never called. The reviewed fixed 289-candidate search operates on original RGB8 captures; accepted transforms decode a direct original-pixel rendering. Failed initialization is represented for both profiles, and failed bias refinement has no word or accusation. Search objective surfaces, transforms, masks, mask/energy statistics, input/module hashes and settings are committed before any roster generation.

Both hard decoders cast rendered luma to float32, subtract original source luma in float32, multiply existing float32 signed block templates, sum in float32, and use strict corr>0. The objective remains float64. The content metric is explicitly recorded as the existing gradient similarity applied to rounded luma uint8; it is diagnostic only and does not choose a transform.

Preparation writes exactly `preparation.json`, `prepared.npz`, then `commitment.json` last. The final commitment hashes both preceding files. The JSON also hashes every individual stored array. Scoring validates this commitment, array digests, ordered eight-profile inventory, fixed settings, code dependencies, binary words and float32 correlations, then generates the original 1000-row roster and asserts exact bias equality. It consumes stored words only, retains all 1000 scores for each successful profile, and uses the existing conditional-null helper and strict score>threshold. Z=2100 is retained as a control. All failures are retained with no accusations.

Only the separate scoring process opens the prior physical single-resampling JSON. It compares each affine-baseline score vector and composed matrix against the retained `orb_ecc_affine` record at rtol=0, atol=1e-9, with explicit mismatch/missing/failure states. It never selects a profile or feeds results into preparation.

## Focused RED/GREEN tests

Exact command for each test run:

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -p 'test_bias_physical_boundary.py' -v
```

Initial RED, exit 1, before the CLI existed (six initial boundary cases):
```text
test_bias_physical_boundary (unittest.loader._FailedTest.test_bias_physical_boundary) ... ERROR

======================================================================
ERROR: test_bias_physical_boundary (unittest.loader._FailedTest.test_bias_physical_boundary)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_bias_physical_boundary
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 426, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 367, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/user_end4/MySpace/SIH/prototypes/nishan_pq/tests/test_bias_physical_boundary.py", line 14, in <module>
    from research.tools import probe_nishan_bias_physical as physical
ImportError: cannot import name 'probe_nishan_bias_physical' from 'research.tools' (unknown location)


----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

Initial implementation GREEN: 6 tests passed in 0.028s. The test scored tiny mocked words and printed eight tiny fixture records. Two supplementary passing tests then covered original-PDF binary endpoints/blur and the actual preparation serialization path with explicit refinement failure. The final test adjustment kept even the mocked scorer's prior-evidence path local to its temporary directory. Final GREEN before the physical run, exit 0:

```text
test_decoder_preserves_float32_cancellation_and_strict_sign (test_bias_physical_boundary.PhysicalBoundaryTests.test_decoder_preserves_float32_cancellation_and_strict_sign) ... ok
test_exclusive_outputs_preserve_existing_evidence (test_bias_physical_boundary.PhysicalBoundaryTests.test_exclusive_outputs_preserve_existing_evidence) ... ok
test_gate_rejects_manifest_hash_module_hash_and_escape (test_bias_physical_boundary.PhysicalBoundaryTests.test_gate_rejects_manifest_hash_module_hash_and_escape) ... ok
test_prepare_commits_both_profiles_and_failures_without_roster_or_prior (test_bias_physical_boundary.PhysicalBoundaryTests.test_prepare_commits_both_profiles_and_failures_without_roster_or_prior) ... ok
test_prepare_rejects_failed_gate_before_loading_images (test_bias_physical_boundary.PhysicalBoundaryTests.test_prepare_rejects_failed_gate_before_loading_images) ... ok
test_score_uses_frozen_words_profiles_and_8000_without_registration (test_bias_physical_boundary.PhysicalBoundaryTests.test_score_uses_frozen_words_profiles_and_8000_without_registration) ... ok
test_scoring_rejects_changed_file_and_changed_word (test_bias_physical_boundary.PhysicalBoundaryTests.test_scoring_rejects_changed_file_and_changed_word) ... ok
test_source_response_uses_original_pdf_binary_endpoints_and_blur (test_bias_physical_boundary.PhysicalBoundaryTests.test_source_response_uses_original_pdf_binary_endpoints_and_blur) ... ok

----------------------------------------------------------------------
Ran 8 tests in 0.038s

OK
```

Tests use temporary directories, tiny arrays and mocked image/roster boundaries. The endpoint test rejects the raster replacement helper. The preparation fixture forbids roster generation and prior-baseline loading; the scorer fixture forbids image loading and both registration entry points. Tamper tests separately change a committed file and alter a word while renewing only the outer commitment, exercising the inner array digest check.

## Real commands and output

Preparation command, one process, one attempt:

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python research/tools/probe_nishan_bias_physical.py prepare --gate research/evidence/nishan-bias-registration-synthetic-2026-09-10 --output research/evidence/nishan-bias-physical-2026-09-10
```

Preparation exited 0. Exact standard output:

```text
{"capture": "akshay.jpeg", "baseline": "prepared", "bias_translation": "boundary_failure", "dx": 1.75, "dy": 2.0, "objective": 0.001197773522248073, "statistics": {"blocks": 41539, "masked_pixels": 1495404, "active_blocks": 52500, "rank_discarded_blocks": 0, "full_pilot_energy": 1114617.5064160274, "masked_pilot_energy": 866305.264654841, "pilot_energy_fraction": 0.7772220153264804}}
{"capture": "akshay1.jpeg", "baseline": "prepared", "bias_translation": "boundary_failure", "dx": -2.0, "dy": 2.0, "objective": 0.0023249855859585594, "statistics": {"blocks": 41403, "masked_pixels": 1490508, "active_blocks": 52500, "rank_discarded_blocks": 0, "full_pilot_energy": 1114617.5064160274, "masked_pilot_energy": 863747.1569937664, "pilot_energy_fraction": 0.7749269610622602}}
{"capture": "akshay2.jpeg", "baseline": "prepared", "bias_translation": "accepted", "dx": -0.5, "dy": -0.25, "objective": 0.008898724754172988, "statistics": {"blocks": 42450, "masked_pixels": 1528200, "active_blocks": 52500, "rank_discarded_blocks": 0, "full_pilot_energy": 1114617.5064160274, "masked_pilot_energy": 885561.4433858276, "pilot_energy_fraction": 0.7944980572154181}}
{"capture": "akshay3.jpeg", "baseline": "prepared", "bias_translation": "accepted", "dx": 0.0, "dy": 0.5, "objective": 0.01466169522074399, "statistics": {"blocks": 42405, "masked_pixels": 1526580, "active_blocks": 52500, "rank_discarded_blocks": 0, "full_pilot_energy": 1114617.5064160274, "masked_pilot_energy": 885103.477623903, "pilot_energy_fraction": 0.7940871846431783}}
{"completed": true, "output": "research/evidence/nishan-bias-physical-2026-09-10", "commitment_sha256": "956678e16fac26228029f6ab34e7bb5e4ef76264b00d4a98898907dc6463c76c"}
```

Scoring command, one separate fresh process, one attempt:

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python research/tools/probe_nishan_bias_physical.py score --prepared research/evidence/nishan-bias-physical-2026-09-10 --output research/evidence/nishan-bias-physical-2026-09-10/scores.json
```

Scoring exited 0. Exact standard output (full score vectors are retained in scores.json):

```text
{"capture": "akshay.jpeg", "profile": "affine_baseline", "status": "scored", "objective": -0.0027563887866063953, "content_similarity": 0.8061620593070984, "expected_row": 0, "expected_score": 66.06978081765759, "highest_other_score": 192.47211335862684, "conditional_null": {"threshold": 413.81226172851143, "theta": 0.10523400589455889, "cumulant": 20.744414611247443, "active_symbols": 3603, "hypotheses": 8000, "family_epsilon": 1e-06, "modeled_per_hypothesis_upper": 1.2499999998684636e-10, "sample_probability": "floor(p * 2^32) / 2^32"}, "conditional_accused": [], "row0_accused": false, "historical_threshold": 2100, "historical_accused": [], "bit_error_fraction": 0.4983238095238095, "zero_correlation_fraction": 0.8656380952380952, "word_sha256": "c5aaf371fdd8df4e574651b0e55299603ceaf01997f4ad1ec5caefc926e3a597", "correlations_sha256": "32e3b3f7eca69ab202dcc4f829e6986ba84410d4ce900bf41b47ec6758a609c3", "baseline_comparison": {"status": "compared", "rtol": 0, "atol": 1e-09, "scores_match": true, "matrices_match": true, "maximum_score_difference": 0.0, "maximum_matrix_difference": 0.0}}
{"capture": "akshay.jpeg", "profile": "affine_bias_translation", "status": "boundary_failure", "reason": "maximum_on_search_boundary", "objective": 0.001197773522248073, "content_similarity": null, "conditional_accused": [], "historical_accused": [], "row0_accused": false, "conditional_null": null}
{"capture": "akshay1.jpeg", "profile": "affine_baseline", "status": "scored", "objective": 0.0013215899889516241, "content_similarity": 0.7451120615005493, "expected_row": 0, "expected_score": -11.626798556863235, "highest_other_score": 209.1849144700953, "conditional_null": {"threshold": 441.88473123789174, "theta": 0.09897831162865278, "cumulant": 20.934297253682306, "active_symbols": 4125, "hypotheses": 8000, "family_epsilon": 1e-06, "modeled_per_hypothesis_upper": 1.2499999998762838e-10, "sample_probability": "floor(p * 2^32) / 2^32"}, "conditional_accused": [], "row0_accused": false, "historical_threshold": 2100, "historical_accused": [], "bit_error_fraction": 0.4998095238095238, "zero_correlation_fraction": 0.8441904761904762, "word_sha256": "005e7be6dec51ef4d5ac40d64c7ed5547607f8bd1ec38b685565828fabf94867", "correlations_sha256": "909f53c55c11fe3240bd855bb0e7efa2579920a2b5e414981e07ef7845287570", "baseline_comparison": {"status": "compared", "rtol": 0, "atol": 1e-09, "scores_match": true, "matrices_match": true, "maximum_score_difference": 0.0, "maximum_matrix_difference": 0.0}}
{"capture": "akshay1.jpeg", "profile": "affine_bias_translation", "status": "boundary_failure", "reason": "maximum_on_search_boundary", "objective": 0.0023249855859585594, "content_similarity": null, "conditional_accused": [], "historical_accused": [], "row0_accused": false, "conditional_null": null}
{"capture": "akshay2.jpeg", "profile": "affine_baseline", "status": "scored", "objective": 0.008447212689683457, "content_similarity": 0.6894306540489197, "expected_row": 0, "expected_score": 788.3151811509675, "highest_other_score": 534.0778020922854, "conditional_null": {"threshold": 1021.0715249035352, "theta": 0.04439422751488697, "cumulant": 22.526974206869472, "active_symbols": 22764, "hypotheses": 8000, "family_epsilon": 1e-06, "modeled_per_hypothesis_upper": 1.249999999944505e-10, "sample_probability": "floor(p * 2^32) / 2^32"}, "conditional_accused": [], "row0_accused": false, "historical_threshold": 2100, "historical_accused": [], "bit_error_fraction": 0.477847619047619, "zero_correlation_fraction": 0.13651428571428573, "word_sha256": "c48f0a81e50ccff92dc321159677b022a3390a12932406231b2207504a847a4e", "correlations_sha256": "726122618ca99f6a8d71992e7ea05cd90c91bfa78bd741452ffc724ce27b6b28", "baseline_comparison": {"status": "compared", "rtol": 0, "atol": 1e-09, "scores_match": true, "matrices_match": true, "maximum_score_difference": 0.0, "maximum_matrix_difference": 0.0}}
{"capture": "akshay2.jpeg", "profile": "affine_bias_translation", "status": "scored", "objective": 0.008898724754172988, "content_similarity": 0.6801992058753967, "expected_row": 0, "expected_score": 835.1906332812098, "highest_other_score": 540.9860904492333, "conditional_null": {"threshold": 1021.6319256885182, "theta": 0.04437901686067527, "cumulant": 22.536313076864268, "active_symbols": 22798, "hypotheses": 8000, "family_epsilon": 1e-06, "modeled_per_hypothesis_upper": 1.2499999999445273e-10, "sample_probability": "floor(p * 2^32) / 2^32"}, "conditional_accused": [], "row0_accused": false, "historical_threshold": 2100, "historical_accused": [], "bit_error_fraction": 0.4765142857142857, "zero_correlation_fraction": 0.1368, "word_sha256": "6b0d29c2175b1eba552cd3dc18169a6d4bd28c2b192e8bf85080239f3cfd9382", "correlations_sha256": "8ebc93ec888fa612293fce93cdc7bebd4ad33cf7b5a3f0c8620b70ca544b8d21"}
{"capture": "akshay3.jpeg", "profile": "affine_baseline", "status": "scored", "objective": 0.014285065754319828, "content_similarity": 0.6977550387382507, "expected_row": 0, "expected_score": 1709.9414108908845, "highest_other_score": 549.3936166235932, "conditional_null": {"threshold": 1097.4819628918053, "theta": 0.041409126033530856, "cumulant": 22.643061542245942, "active_symbols": 26404, "hypotheses": 8000, "family_epsilon": 1e-06, "modeled_per_hypothesis_upper": 1.2499999999482354e-10, "sample_probability": "floor(p * 2^32) / 2^32"}, "conditional_accused": [0], "row0_accused": true, "historical_threshold": 2100, "historical_accused": [], "bit_error_fraction": 0.4461904761904762, "zero_correlation_fraction": 0.006076190476190476, "word_sha256": "4c072fa345e3aa98d50ec05144deac31bfeb23a06393d7b98f1882e16cfbb756", "correlations_sha256": "b082ef42fdcb49a426614034bef8a6ec3e05df0be39a0abbf0a9e2e2db38d52f", "baseline_comparison": {"status": "compared", "rtol": 0, "atol": 1e-09, "scores_match": true, "matrices_match": true, "maximum_score_difference": 0.0, "maximum_matrix_difference": 0.0}}
{"capture": "akshay3.jpeg", "profile": "affine_bias_translation", "status": "scored", "objective": 0.01466169522074399, "content_similarity": 0.6907787322998047, "expected_row": 0, "expected_score": 1827.3338156626833, "highest_other_score": 518.086474867613, "conditional_null": {"threshold": 1096.2895022695366, "theta": 0.04146167884621422, "cumulant": 22.651295886907846, "active_symbols": 26356, "hypotheses": 8000, "family_epsilon": 1e-06, "modeled_per_hypothesis_upper": 1.2499999999481687e-10, "sample_probability": "floor(p * 2^32) / 2^32"}, "conditional_accused": [0], "row0_accused": true, "historical_threshold": 2100, "historical_accused": [], "bit_error_fraction": 0.4431428571428571, "zero_correlation_fraction": 0.0064, "word_sha256": "51d8fe8831af896e9f0a198369da97c739dc0e91e632e86506898eb32f0a2709", "correlations_sha256": "4dba5bfe530ac86156a6986aae9560d8c6f60acfc889c48169330176b6c32075"}
{"completed": true, "output": "research/evidence/nishan-bias-physical-2026-09-10/scores.json", "sha256": "38ba1ddf81519415d56d70fa7c37fbee940eb1341a796d8cb9fc2ca5c3ad0b9b", "all_baseline_controls_match": true}
```

## All eight outcomes

| Capture | Profile | Status | Row0 score | Highest other | Conditional threshold | Accused rows | BER | Zero-correlation fraction |
|---|---|---|---:|---:|---:|---|---:|---:|
| akshay.jpeg | affine_baseline | scored | 66.069781 | 192.472113 | 413.812262 | [] | 0.498324 | 0.865638 |
| akshay.jpeg | affine_bias_translation | boundary_failure at (1.75,2.0) | — | — | — | [] | — | — |
| akshay1.jpeg | affine_baseline | scored | -11.626799 | 209.184914 | 441.884731 | [] | 0.499810 | 0.844190 |
| akshay1.jpeg | affine_bias_translation | boundary_failure at (-2.0,2.0) | — | — | — | [] | — | — |
| akshay2.jpeg | affine_baseline | scored | 788.315181 | 534.077802 | 1021.071525 | [] | 0.477848 | 0.136514 |
| akshay2.jpeg | affine_bias_translation | scored; (-0.5,-0.25) | 835.190633 | 540.986090 | 1021.631926 | [] | 0.476514 | 0.136800 |
| akshay3.jpeg | affine_baseline | scored | 1709.941411 | 549.393617 | 1097.481963 | [0] | 0.446190 | 0.006076 |
| akshay3.jpeg | affine_bias_translation | scored; (0.0,0.5) | 1827.333816 | 518.086475 | 1096.289502 | [0] | 0.443143 | 0.006400 |

The existing akshay3 attribution is retained in both profiles. Akshay2 is **not newly recovered**: its accepted translation modestly increases row0 score, but the score remains below the fixed conditional threshold. Neither of the other two captures produces an accusation; their bias-profile maxima hit the frozen search boundary and remain explicit failures without decoded words. No other roster row is accused. The retained historical Z=2100 control accuses no rows in any profile.

All four baseline composed matrices and every element of all four 1000-score baseline vectors match the prior single-resampling `orb_ecc_affine` evidence exactly: maximum matrix difference 0 and maximum score difference 0, with the required rtol=0/atol=1e-9 checks all true. Baseline matching is a post-commitment control, not a selection mechanism.

Both accepted translations increase their shared-bias objective and slightly improve row0 BER; their content-similarity diagnostics decrease. These observations do not warrant selecting a profile or claiming new physical recovery. There was one physical preparation invocation and one physical scoring invocation, no code failures, no numbered retry directory, and no score-based retuning.

## Artifact and hash inventory

Fresh artifacts are exclusively in `research/evidence/nishan-bias-physical-2026-09-10/`. The NPZ contains 30 arrays, including six complete 52,500-element uint8 words and six float32 correlation vectors. Its 20,157,130-byte compressed payload includes the native original-PDF endpoints, native and blurred response arrays, p/q/q image, geometry and four masks. The preparation JSON retains every candidate surface and the successful or diagnostic selected transforms. The scores JSON retains six full 1000-element score vectors and both failure records.

Input and implementation hashes (the post-run validation independently confirms all original input hashes and source hash are unchanged):

```text
572a54f4c791ad84fc20c902e1e723f0455abdfe13b7616d1b8860fbc9dff5c8  research/tools/probe_nishan_bias_physical.py
e1e09da289a3776a06aa9037933a10c09cd333994aef1cfcafe510f2f0602dc6  prototypes/nishan_pq/tests/test_bias_physical_boundary.py
5b347ce904b224a0b33602b12b905d0534d7f626c7319cec960f8bf2e7ed5b06  artifacts/nishan/synthetic-source.pdf
858871144523664edd1cb2a03c89f0863a2249d9984757f7b3e13852c52b6f3c  /home/user_end4/Downloads/akshay.jpeg
0768a686fcfff4c220f7d2057ab491ea31c02cbb004fb1f503f3013e8f311a0e  /home/user_end4/Downloads/akshay1.jpeg
c6d278e66d35dc17903350a53dc76e4a59537e036689d31f4f0bbdce8687031c  /home/user_end4/Downloads/akshay2.jpeg
2869328b6c797ff095b23cf1a286255275dc1172b48d537bb1dedc97b6bd9203  /home/user_end4/Downloads/akshay3.jpeg
```

Prepared artifacts and successful gate hashes:

```text
cb32f3941581f20e1b49bc253b50a11b122a9dad3c823a97ed21fb61c114a7b2  research/evidence/nishan-bias-physical-2026-09-10/preparation.json
bc41f6e32739b1fb4e454a19c47d0aae3877999f37f20f5b28bcd69f245b5f9d  research/evidence/nishan-bias-physical-2026-09-10/prepared.npz
956678e16fac26228029f6ab34e7bb5e4ef76264b00d4a98898907dc6463c76c  research/evidence/nishan-bias-physical-2026-09-10/commitment.json
703c640df2379a2f0096f70cd1a240237e946534eb137ec8757a16176b23fd48  research/evidence/nishan-bias-registration-synthetic-2026-09-10/manifest.json
9941ec6b312e5bbd6481bcf0ad460191c681a60a7b1407387f5bc5402dd34aee  research/evidence/nishan-bias-registration-synthetic-2026-09-10/results.json
4.0K	research/evidence/nishan-bias-physical-2026-09-10/commitment.json
296K	research/evidence/nishan-bias-physical-2026-09-10/preparation.json
20M	research/evidence/nishan-bias-physical-2026-09-10/prepared.npz
180K	research/evidence/nishan-bias-physical-2026-09-10/scores.json
```

Final read-only verification called `validate_prepared` again, recomputed source/capture hashes and enumerated file sizes and all per-array shapes/dtypes/digests. It did not run preparation, registration, roster generation or scoring again. Exact inventory output:

```json
{
  "code_sha256": {
    "prototypes/nishan_pq/nishan/registration.py": "604c380475bd604f32a16ace55463b28f29d52f61b23b103149bc74fa0b7f92f",
    "prototypes/nishan_pq/nishan/tardos.py": "cf0fe3bb08bbb6aa4daaa56cbd6f356c86a98cfddaba5c64297668adf2623bd0",
    "prototypes/nishan_pq/nishan/tardos_carrier.py": "ea818369f5fd73975fdd66380352d3d3afb75e42cd0de3dc841e4243a8a2a0f9",
    "prototypes/nishan_pq/nishan/watermark.py": "f52b1aa480393ff8baae407b31f2400a1476571bb38eaeb9248c6761bdca006c",
    "prototypes/nishan_pq/tests/test_bias_physical_boundary.py": "e1e09da289a3776a06aa9037933a10c09cd333994aef1cfcafe510f2f0602dc6",
    "research/tools/nishan_bias_registration.py": "2991323b8fbe9c8fc7e8a435dae9b777e2f739eda8d9353be8be574c6f6446eb",
    "research/tools/probe_nishan_bias_physical.py": "572a54f4c791ad84fc20c902e1e723f0455abdfe13b7616d1b8860fbc9dff5c8",
    "research/tools/probe_nishan_capture_channel.py": "c8cdb2e3cdf1302db465cf100fc05da7302df40d5e4ac16f1fda4c29b3c4bcd2",
    "research/tools/probe_nishan_physical_registration_single.py": "d5c9ed1f967e648ab84894067f9bc835213eb077657c93e04aa1ea1a9704d5ee"
  },
  "original_inputs_unchanged": true,
  "source_unchanged": true,
  "files": [
    {
      "name": "commitment.json",
      "bytes": 272,
      "sha256": "956678e16fac26228029f6ab34e7bb5e4ef76264b00d4a98898907dc6463c76c"
    },
    {
      "name": "preparation.json",
      "bytes": 302445,
      "sha256": "cb32f3941581f20e1b49bc253b50a11b122a9dad3c823a97ed21fb61c114a7b2"
    },
    {
      "name": "prepared.npz",
      "bytes": 20157130,
      "sha256": "bc41f6e32739b1fb4e454a19c47d0aae3877999f37f20f5b28bcd69f245b5f9d"
    },
    {
      "name": "scores.json",
      "bytes": 182477,
      "sha256": "38ba1ddf81519415d56d70fa7c37fbee940eb1341a796d8cb9fc2ca5c3ad0b9b"
    }
  ]
}
{
  "p": {
    "shape": [
      52500
    ],
    "dtype": "float64",
    "sha256": "ced73e739e79efa0ecdf37a5354d27f57fa350f8da56e226c59da2e99b7ee33c"
  },
  "source_luma": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float32",
    "sha256": "f9a280fb00a8c39a8f8485ed8dfa66915505ff4be01708d7e754f5c4394d0319"
  },
  "order": {
    "shape": [
      52500
    ],
    "dtype": "int64",
    "sha256": "7a4bca54fd4caa3e417bde6a58f3c381e4e49983575625250fc13f0abf79e796"
  },
  "orientation": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "8c9f2a77e91c238f9c774396363ddf587daccb6a0cafbf2146a8356227db7061"
  },
  "polarity": {
    "shape": [
      52500
    ],
    "dtype": "int8",
    "sha256": "5a2c94195e55258b900d4edb1efb16dc0d79e3deb13203ade1af382ec9c4b7e3"
  },
  "active_blocks": {
    "shape": [
      280,
      198
    ],
    "dtype": "bool",
    "sha256": "6983c977c2fd74f96d7e1da4bb8c9d6810ef81b9f7d7c3a4cc6cd7bea425c8e5"
  },
  "r0": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "7096236ee81814677e83a3c629b93b6d200c85174bebedff7557c621ac728478"
  },
  "r1": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "aab163318ac6e596be9441023f224a8e0ad2d1aed3762acb3889eb14b99303ca"
  },
  "q": {
    "shape": [
      52500
    ],
    "dtype": "float64",
    "sha256": "7caaacd1f8f24ec7624f6267e233adf7ff8fa3bb5ba6a2dc98369230b9f41074"
  },
  "q_image": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "d941e11ba19b072f250c7a19c97db99102d6a1403fa88d9b0dc0219a3848c3e4"
  },
  "native_midpoint": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "3055951c15ee8246d05c319a3458c37091d6b081733016f32af729fe5fd56fa8"
  },
  "native_pilot": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "05fd9317a89992332f4a2667d118b66eb806dd1a9c53a6cd8d36e435ae5d207b"
  },
  "midpoint": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "aaccf9d32f87d36b2aff5d50515f1106302866ffb1cc6f0b4ed6051263a71146"
  },
  "pilot": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "float64",
    "sha256": "a6e871a63115a6523bca44c867dc73184412b09b6dbcd3f947daf40ea9791078"
  },
  "capture_0_mask": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "bool",
    "sha256": "6c264d88c62f29612f93cba90a39483b9c2a1b9455b3ce290c881f474e8e36b2"
  },
  "record_0_word": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "c5aaf371fdd8df4e574651b0e55299603ceaf01997f4ad1ec5caefc926e3a597"
  },
  "record_0_correlations": {
    "shape": [
      52500
    ],
    "dtype": "float32",
    "sha256": "32e3b3f7eca69ab202dcc4f829e6986ba84410d4ce900bf41b47ec6758a609c3"
  },
  "capture_1_mask": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "bool",
    "sha256": "46d12e9b45cb59b3ffecc0437fad81aaee34feac10c7847abf0858c2615d3630"
  },
  "record_2_word": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "005e7be6dec51ef4d5ac40d64c7ed5547607f8bd1ec38b685565828fabf94867"
  },
  "record_2_correlations": {
    "shape": [
      52500
    ],
    "dtype": "float32",
    "sha256": "909f53c55c11fe3240bd855bb0e7efa2579920a2b5e414981e07ef7845287570"
  },
  "capture_2_mask": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "bool",
    "sha256": "c703ed17d079855d0d42f595fbd2864ff0c12ae8d8dabde23df2856f857794b2"
  },
  "record_4_word": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "c48f0a81e50ccff92dc321159677b022a3390a12932406231b2207504a847a4e"
  },
  "record_4_correlations": {
    "shape": [
      52500
    ],
    "dtype": "float32",
    "sha256": "726122618ca99f6a8d71992e7ea05cd90c91bfa78bd741452ffc724ce27b6b28"
  },
  "record_5_word": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "6b0d29c2175b1eba552cd3dc18169a6d4bd28c2b192e8bf85080239f3cfd9382"
  },
  "record_5_correlations": {
    "shape": [
      52500
    ],
    "dtype": "float32",
    "sha256": "8ebc93ec888fa612293fce93cdc7bebd4ad33cf7b5a3f0c8620b70ca544b8d21"
  },
  "capture_3_mask": {
    "shape": [
      1684,
      1190
    ],
    "dtype": "bool",
    "sha256": "6c6fb18890a93371b3bdd51eec23fbc6f0b21f71efc0b2572dc6d58f2fd3e8db"
  },
  "record_6_word": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "4c072fa345e3aa98d50ec05144deac31bfeb23a06393d7b98f1882e16cfbb756"
  },
  "record_6_correlations": {
    "shape": [
      52500
    ],
    "dtype": "float32",
    "sha256": "b082ef42fdcb49a426614034bef8a6ec3e05df0be39a0abbf0a9e2e2db38d52f"
  },
  "record_7_word": {
    "shape": [
      52500
    ],
    "dtype": "uint8",
    "sha256": "51d8fe8831af896e9f0a198369da97c739dc0e91e632e86506898eb32f0a2709"
  },
  "record_7_correlations": {
    "shape": [
      52500
    ],
    "dtype": "float32",
    "sha256": "4dba5bfe530ac86156a6986aae9560d8c6f60acfc889c48169330176b6c32075"
  }
}
```

The report's own digest is supplied separately at handoff rather than recursively included in its inventory.


## Self-review and limitations

The source endpoint boundary and float32 sum boundary have direct focused checks. The actual preparation test preserves both profiles and H=8000 and leaves a failed refinement without a word. Gate validation rejects failed results, manifest mutation, module mutation and escaped paths. Exclusive paths preserve existing evidence. Scoring validates before roster generation and does not register images.

The commitment provides tamper detection against accidental changes; it is a local unsigned artifact, not an adversarial authenticated or externally timestamped commitment. The small scorer fixture has two mock roster rows; the actual process uses the fixed original 1000-row generator. The source fixture is explicitly constrained to one page, matching the supplied physical experiment.

This is exploratory evidence on the same source page with a public codebook, not independent confirmation or a production security guarantee. The conditional-independent innocent-bit model and finite numerical threshold arithmetic are not certified. The fixed global translation search cannot correct arbitrary local curvature, nonuniform scale or larger misalignment. No score-based retuning, rerun, image selection or profile selection is permitted.

## Final documentation fix report

This final fix wave changed documentation only. Exact edited files:

- `research/NISHAN_BIAS_PHYSICAL_FINDINGS_2026-09-11.md`
- `research/ORIGINAL_IDEAS_FIRST_2026-09-10.md`
- `research/NISHAN_PHYSICAL_ALIGNMENT_FINDINGS_2026-09-10.md`
- `research/evidence/nishan-bias-registration-task-2-report.md`

The physical status notes now record that the independent Task 2
spec/quality/implementation review is complete, with no Critical/Important
issues. The physical findings also record the frozen-run reuse caveat: the
runner aborts when prior evidence is absent, while this frozen run had matching
prior evidence and passing comparisons. A focused code fix and test are
required before future reuse without prior evidence; the runner was not
modified here.

Docs-only validation command and output:

```text
$ rg -n -i 'independent (spec/quality|implementation) review is pending|pending' research/NISHAN_BIAS_PHYSICAL_FINDINGS_2026-09-11.md research/ORIGINAL_IDEAS_FIRST_2026-09-10.md research/NISHAN_PHYSICAL_ALIGNMENT_FINDINGS_2026-09-10.md
<no output>
$ sha256sum research/tools/probe_nishan_bias_physical.py research/evidence/nishan-bias-physical-2026-09-10/commitment.json research/evidence/nishan-bias-physical-2026-09-10/scores.json
572a54f4c791ad84fc20c902e1e723f0455abdfe13b7616d1b8860fbc9dff5c8  research/tools/probe_nishan_bias_physical.py
956678e16fac26228029f6ab34e7bb5e4ef76264b00d4a98898907dc6463c76c  research/evidence/nishan-bias-physical-2026-09-10/commitment.json
38ba1ddf81519415d56d70fa7c37fbee940eb1341a796d8cb9fc2ca5c3ad0b9b  research/evidence/nishan-bias-physical-2026-09-10/scores.json
```

These hashes remain unchanged from the pre-existing report. No experiment,
test, code, artifact, or numerical claim was changed.
