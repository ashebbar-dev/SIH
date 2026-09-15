# Task 1 report — empirical compact carrier pilot

Date: 2026-09-12  
Status: **DONE_WITH_CONCERNS**

## Scope and outcome

The isolated fixed pilot completed successfully. It is empirical, uses one source document and two issued copies per profile, and contains no physical print/camera result. All 57 declared observation identities were present: 30 positive, 15 unmarked, 6 wrong-key, and 6 wrong-context. All 30 positive cases selected only their intended issued row; all 27 negative cases selected no rows.

Both compact profiles satisfy the frozen prioritization rule for a fresh physical test. `symmetric-6-r4` won on both issued rows for blur1 and half-resize, but not blur2. `symmetric-12-r1` won on both issued rows for blur1, blur2, and half-resize. This is not statistical significance or a superiority result.

## RED

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python -m unittest discover -s research/experiments/compact_carrier_v1 -p 'test_*.py' -v
```

Exit code: 1. Actual output:

```text
test_profiles (unittest.loader._FailedTest.test_profiles) ... ERROR

======================================================================
ERROR: test_profiles (unittest.loader._FailedTest.test_profiles)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_profiles
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 433, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 374, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/user_end4/MySpace/SIH/research/experiments/compact_carrier_v1/test_profiles.py", line 10, in <module>
    from profiles import (
    ...<4 lines>...
    )
ModuleNotFoundError: No module named 'profiles'


----------------------------------------------------------------------
Ran 1 test in 0.002s

FAILED (errors=1)
```

The retained output is `research/evidence/nishan-compact-carrier-2026-09-12/task-1-red.txt`.

## GREEN

Command:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python -m unittest discover -s research/experiments/compact_carrier_v1 -p 'test_*.py' -v
```

Exit code: 0. Actual output:

```text
test_fixed_matrix_count_and_identity (test_profiles.FrozenProfileTests.test_fixed_matrix_count_and_identity) ... ok
test_profile_constants_and_matched_area (test_profiles.FrozenProfileTests.test_profile_constants_and_matched_area) ... ok
test_profiles_mapping_is_immutable (test_profiles.FrozenProfileTests.test_profiles_mapping_is_immutable) ... ok
test_no_overwrite_output_guard (test_profiles.ReplayAndGuardTests.test_no_overwrite_output_guard) ... ok
test_replay_state_hash_rejection_happens_before_npz_load (test_profiles.ReplayAndGuardTests.test_replay_state_hash_rejection_happens_before_npz_load) ... ok
test_collapse_validates_shape_and_finiteness (test_profiles.SymmetricScoreTests.test_collapse_validates_shape_and_finiteness) ... ok
test_repetition_sums_analog_correlations_before_threshold (test_profiles.SymmetricScoreTests.test_repetition_sums_analog_correlations_before_threshold) ... ok
test_symmetric_uses_both_output_symbols (test_profiles.SymmetricScoreTests.test_symmetric_uses_both_output_symbols) ... ok
test_symmetric_validates_shape_binary_and_finiteness (test_profiles.SymmetricScoreTests.test_symmetric_validates_shape_binary_and_finiteness) ... ok
test_zero_correlation_tie_is_zero (test_profiles.SymmetricScoreTests.test_zero_correlation_tie_is_zero) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.138s

OK
```

The retained output is `research/evidence/nishan-compact-carrier-2026-09-12/task-1-green.txt`. No prototype or deck regression suite was run, as required for this isolated read-only integration.

## Full pilot execution

The destination did not exist before this one execution. No seed, threshold, transform, strength, or profile was tuned, and the pilot was not rerun.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python research/experiments/compact_carrier_v1/run_study.py --output research/evidence/nishan-compact-carrier-2026-09-12/run-01
```

- Exit code: 0
- Runner duration: 127.54282832099852 seconds
- Original codebook generation: 1.6630934679997154 seconds
- Symmetric shared codebook generation: 0.2875995319991489 seconds
- Observation counts: total 57; positive 30; unmarked 15; wrong-key 6; wrong-context 6
- `results.json` SHA3-256: `6551658be185470954dc3a14238a5e72c6f14496de7abace9194e3f75ec7583b`

## Positive observations

Each cell lists rows 0 and 7 in that order. Ratios are intended-row score divided by the frozen profile threshold; BER is logical decoded-bit error rate; selected values are the complete selected-row lists. Intended rank was 1 in every case.

| Profile | Transform | Intended ratios (row 0, row 7) | Logical BER (row 0, row 7) | Selected rows |
|---|---|---:|---:|---|
| original-6-r1 | clean | 8.322667650573344, 8.21208202308448 | 0, 0 | [0], [7] |
| original-6-r1 | jpeg55 | 6.64719926641654, 6.564432436236387 | 0.1002095238095238, 0.10234285714285714 | [0], [7] |
| original-6-r1 | blur1 | 7.648351393422027, 7.5497091554368945 | 0.04068571428571428, 0.04097142857142857 | [0], [7] |
| original-6-r1 | blur2 | 7.4586164845774015, 7.370299469234854 | 0.05198095238095238, 0.05228571428571428 | [0], [7] |
| original-6-r1 | half-resize | 7.6301201054257834, 7.558851505964583 | 0.04133333333333333, 0.04125714285714286 | [0], [7] |
| symmetric-6-r4 | clean | 10.331084602168605, 10.478426600392678 | 0, 0 | [0], [7] |
| symmetric-6-r4 | jpeg55 | 9.792979632452571, 9.960265755044853 | 0.025302084178087745, 0.025058794907144594 | [0], [7] |
| symmetric-6-r4 | blur1 | 8.380845178049533, 8.454258150900836 | 0.09626145486984024, 0.09715351552996512 | [0], [7] |
| symmetric-6-r4 | blur2 | 7.132433026469101, 7.295219677025851 | 0.1534344335414808, 0.15278566215229908 | [0], [7] |
| symmetric-6-r4 | half-resize | 9.01183847736295, 9.127423264502868 | 0.06536371746006, 0.06601248884924175 | [0], [7] |
| symmetric-12-r1 | clean | 10.331084602168605, 10.478426600392678 | 0, 0 | [0], [7] |
| symmetric-12-r1 | jpeg55 | 10.123232041813571, 10.269705103435232 | 0.010137052955964641, 0.00989376368502149 | [0], [7] |
| symmetric-12-r1 | blur1 | 9.595414170062545, 9.716601466733444 | 0.03795312626713162, 0.03868299407996107 | [0], [7] |
| symmetric-12-r1 | blur2 | 9.298895662567894, 9.360205153909751 | 0.05376692887843646, 0.055145568080447654 | [0], [7] |
| symmetric-12-r1 | half-resize | 9.481390178412783, 9.666760898358175 | 0.04038601897656313, 0.040710404671154 | [0], [7] |

## Negative observations

Negative BER is null because these observations have no participating source row and are not claimed random-bit tests. No negative observation selected a row. The table reports the maximum all-row score/threshold ratio in each kind/profile group and the case where it occurred.

| Kind | Profile | Cases | Maximum ratio | Case (row, transform, maximum-score row) |
|---|---|---:|---:|---|
| unmarked | original-6-r1 | 5 | 0.09838239282168185 | null, blur2, 981 |
| unmarked | symmetric-6-r4 | 5 | 0.5632522774510829 | null, clean, 79 |
| unmarked | symmetric-12-r1 | 5 | 0.5632522774510829 | null, clean, 79 |
| wrong-key | original-6-r1 | 2 | 0.18372840950325478 | 0, clean, 433 |
| wrong-key | symmetric-6-r4 | 2 | 0.4560499129968159 | 0, clean, 239 |
| wrong-key | symmetric-12-r1 | 2 | 0.42518026796482744 | 7, clean, 316 |
| wrong-context | original-6-r1 | 2 | 0.1916507785210156 | 0, clean, 494 |
| wrong-context | symmetric-6-r4 | 2 | 0.46472950024867216 | 7, clean, 234 |
| wrong-context | symmetric-12-r1 | 2 | 0.45396491920074616 | 7, clean, 23 |

## PDF fidelity

Actual source/marked measurements at 144 DPI are below. Extracted text equality was true for every issued PDF.

| Profile | Row | PSNR dB | Text equal | Marked bytes | Embed seconds |
|---|---:|---:|---|---:|---:|
| original-6-r1 | 0 | 41.870 | true | 248175 | 3.765171361999819 |
| original-6-r1 | 7 | 41.868 | true | 248578 | 3.3764898929948686 |
| symmetric-6-r4 | 0 | 42.137 | true | 254407 | 3.341681730998971 |
| symmetric-6-r4 | 7 | 42.137 | true | 254445 | 3.2414306869977736 |
| symmetric-12-r1 | 0 | 42.142 | true | 175249 | 2.099814304994652 |
| symmetric-12-r1 | 7 | 42.140 | true | 175138 | 1.976646309994976 |

The source PDF is 2,706 bytes. Equal nominal carrier area is not equal perceptual fidelity; these values describe only this source and renderer.

## Frozen advancement evaluation

All prerequisites passed:

- both compact profiles selected only their intended row in both clean cases;
- extracted PDF text was unchanged for both compact profiles; and
- all 27 negative observations selected no rows.

Results under the unchanged rule:

- `symmetric-6-r4`: worth a fresh physical test; winning diagnostic transforms were blur1 and half-resize. Negative result: it did **not** exceed original on blur2 for either issued row (compact 7.132433026469101 vs original 7.4586164845774015 for row 0; compact 7.295219677025851 vs original 7.370299469234854 for row 7).
- `symmetric-12-r1`: worth a fresh physical test; winning diagnostic transforms were blur1, blur2, and half-resize.

## Capture replay smoke

Command (stdout retained as a generated evidence artifact):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python research/experiments/compact_carrier_v1/score_capture.py --run research/evidence/nishan-compact-carrier-2026-09-12/run-01 --profile symmetric-12-r1 --suspect research/evidence/nishan-compact-carrier-2026-09-12/run-01/rasters/symmetric-12-r1/row-0/clean.png > research/evidence/nishan-compact-carrier-2026-09-12/run-01/capture-smoke.json
```

Exit code: 0. Output summary:

```json
{
  "empirical_extraction": true,
  "profile": "symmetric-12-r1",
  "registration_mode": "always",
  "selected_rows": [0],
  "selected_count": 1,
  "highest_score_row": 0,
  "highest_score": 8650.055030903923,
  "highest_score_threshold_ratio": 10.331084602168605,
  "identity_verdict": null
}
```

Full output: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/capture-smoke.json`  
SHA3-256: `4bd99d981d74ef66770a66228d345e4903d9493b9e8679e83e784346c03e3240`

The report records `registration_mode="always"`; the fixed synthetic matrix used `registration_mode="off"`. This generated clean-raster replay is a smoke validation only, not physical evidence. The CLI itself is read-only and emitted no identity verdict.

## Raw artifacts

- Public manifest: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/manifest.json`
- Complete results and exact metrics: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/results.json`
- Per-observation scores, ratios, physical correlations, logical sums and bits: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/arrays/observation-000.npz` through `observation-056.npz`
- Six issued PDFs: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/issued/`
- Controlled positive and unmarked rasters: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/rasters/`
- Private replay state: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/private/replay-state.npz` (mode 0600; do not share)
- Physical packet instructions and three row-0 PDF paths: `research/evidence/nishan-compact-carrier-2026-09-12/run-01/physical-capture-instructions.md`

`results.json` commits 102 artifacts that existed at runner completion. The later replay stdout artifact is separately committed above because `results.json` excludes post-run evidence and itself.

## Self-review and integrity checks

A read-only audit verified:

- 57 observations and 57 unique fixed identities;
- all 57 observation NPZ hashes, required array names, 1,000-score shapes, and finite score/correlation arrays;
- all 102 artifact hashes recorded by `results.json`;
- copied-source and private-replay public commitments;
- private replay mode 0600;
- finite JSON without NaN or Infinity;
- replay `registration_mode="always"`, selected row `[0]`, and null identity verdict; and
- no public-text occurrence of private key/context field names outside the private NPZ.

The runner writes the manifest before observation scoring. Replay validation checks the replay-state and copied-source hashes before loading private arrays, uses `allow_pickle=False`, and rechecks codebook/bias commitments. The run guard creates the destination with `exist_ok=False` before generating artifacts. The run contains no `failure.json`.

## Concerns and limitations

- This is empirical evidence from one source document and two issued copies per profile, not a physical result. Fresh printer/phone captures have not been supplied or scored.
- The inherited keyed sampler remains the deliberate 53-bit/float64 bias and 32-bit Bernoulli empirical baseline. The proposed precision bridge was not implemented, and no ideal theorem probability bound is claimed for this generator, the measurements, or noisy decoded words.
- There is no probability certification, collusion guarantee, production attribution, novelty claim, or superiority claim. The fixed advancement result only prioritizes profiles for a physical test.
- Synthetic JPEG, blur, and resize are controlled diagnostics, not a print/camera simulator.
- Local manifests and commitments are not independently signed provenance.
- The later capture-smoke stdout is a post-run evidence file and therefore is separately hashed in this report rather than in the runner-completion artifact map.
