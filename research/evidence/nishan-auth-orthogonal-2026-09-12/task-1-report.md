# Task 1 report — isolated prospective carrier falsification study

Date: 2026-09-12  
Status: **DONE_WITH_CONCERNS**  
Scope: isolated research experiment only; no production security integration.

## Outcome

The fixed implementation and the sole prospective run completed without a
crash or profile change.

- **Gate A: PASS.** All 44/44 participating-tag decisions matched exactly over
  the 16 positive authenticator artifacts. All 36/36 other-issued decisions,
  60/60 direct negatives, 6/6 changed-context controls, and 200/200 wrong-key
  controls rejected.
- **Gate B: FAIL.** Both 0/2 copied-overlay artifacts rejected the donor tag;
  equivalently, the genuine row-0 donor tag survived exactly in both the
  content-modified PDF and its JPEG-Q55 raster.
- The correct research decision is therefore **no-go for a
  transplant-resistant content-authentication claim**. Gate B's scientific
  failure is not an implementation failure.
- The narrower observation is that the copied donor pattern remained
  associated with the donor's genuine context. That is distinct from
  authenticating the edited content: rejection when a verifier substitutes a
  changed candidate context did not cause rejection when the edited document
  was evaluated under the genuine donor context.

The completed run is at `run-01/`; its machine-readable records are
`run-01/manifest.json` and `run-01/results.json`.

## Implementation

Only the requested research implementation sources were added:

- `research/experiments/auth_orthogonal_v1/carrier.py`
  - canonical sorted compact ASCII JSON context with all six fixed fields;
  - 72-bit HMAC-SHA3-256 tag, Hamming(7,4) encoding, 25,200 unique PRF-selected
    placements, orthogonal template orientation, and recipient PRF polarity;
  - fixed-strength PDF embedding, registered luma residual extraction, exact
    decoding with all 126 raw sums retained;
  - observed PDF image-object copying with PyMuPDF soft-mask reconstruction;
    the function accepts donor, target, and destination paths only;
  - explicit type, profile, page-count, geometry, capacity, and finite-number
    validation.
- `research/experiments/auth_orthogonal_v1/run_study.py`
  - fresh material generation once, actual ML-DSA-65 keys, two fixed sources,
    premeasurement manifest, matched Tardos/auth matrix, all negatives, the
    copied-overlay attack, finite JSON, artifact hashes, timings, and gates;
  - refusal to overwrite existing output and preservation of `failure.json` if
    a new run crashes.
- `research/experiments/auth_orthogonal_v1/test_carrier.py`
  - eight real array/PDF tests, without mocks.
- `research/experiments/auth_orthogonal_v1/README.md`
  - exact commands, local-key warning, fixed-result policy, and security
    boundaries.

No dependency was added. No prototype, production, artifact source,
presentation, or submission file was edited. The workspace has no Git
repository; Git was not initialized and no commit was made.

## TDD and execution evidence

### RED

Command:

```bash
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python -m unittest discover -s research/experiments/auth_orthogonal_v1 -p 'test_*.py' -v
```

Full relevant output before implementation (exit 1):

```text
test_carrier (unittest.loader._FailedTest.test_carrier) ... ERROR

======================================================================
ERROR: test_carrier (unittest.loader._FailedTest.test_carrier)
----------------------------------------------------------------------
ImportError: Failed to import test module: test_carrier
Traceback (most recent call last):
  File "/usr/lib/python3.14/unittest/loader.py", line 433, in _find_test_path
    module = self._get_module_from_name(name)
  File "/usr/lib/python3.14/unittest/loader.py", line 374, in _get_module_from_name
    __import__(name)
    ~~~~~~~~~~^^^^^^
  File "/home/user_end4/MySpace/SIH/research/experiments/auth_orthogonal_v1/test_carrier.py", line 14, in <module>
    from carrier import (
    ...<9 lines>...
    )
ModuleNotFoundError: No module named 'carrier'

----------------------------------------------------------------------
Ran 1 test in 0.000s

FAILED (errors=1)
```

This is the intended RED: the test module existed and the carrier did not.

### GREEN / complete new suite

The same prescribed command was run once at stable code. Full output (exit 0):

```text
test_cli_refuses_existing_output_directory (test_carrier.CarrierTests.test_cli_refuses_existing_output_directory) ... ok
test_context_and_secret_validation (test_carrier.CarrierTests.test_context_and_secret_validation) ... ok
test_context_is_canonical_and_each_field_binds (test_carrier.CarrierTests.test_context_is_canonical_and_each_field_binds) ... ok
test_copy_observed_overlays_preserves_changed_target_text_and_masks (test_carrier.CarrierTests.test_copy_observed_overlays_preserves_changed_target_text_and_masks) ... ok
test_copy_rejects_page_geometry_mismatch (test_carrier.CarrierTests.test_copy_rejects_page_geometry_mismatch) ... ok
test_exact_decode_and_intentional_expected_tag_mismatch (test_carrier.CarrierTests.test_exact_decode_and_intentional_expected_tag_mismatch) ... ok
test_plan_has_unique_placements_and_orthogonal_orientations (test_carrier.CarrierTests.test_plan_has_unique_placements_and_orthogonal_orientations) ... ok
test_plan_rejects_wrong_profile_capacity (test_carrier.CarrierTests.test_plan_rejects_wrong_profile_capacity) ... ok

----------------------------------------------------------------------
Ran 8 tests in 2.349s

OK
```

Before that single stable suite, an AST-only syntax check produced:

```text
AST OK: research/experiments/auth_orthogonal_v1/carrier.py
AST OK: research/experiments/auth_orthogonal_v1/run_study.py
AST OK: research/experiments/auth_orthogonal_v1/test_carrier.py
```

### Sole prescribed study run

Command:

```bash
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python research/experiments/auth_orthogonal_v1/run_study.py --output research/evidence/nishan-auth-orthogonal-2026-09-12/run-01
```

Full progress/output (exit 0):

```text
[source-a] generating fixed inputs and fresh material
[source-b] generating fixed inputs and fresh material
[study] premeasurement manifest written
[source-a] embedding ten matched copies
[source-a] tardos-only coalition=1 average-png
[source-a] tardos-only coalition=1 average-jpeg-q55
[source-a] tardos-plus-auth coalition=1 average-png
[source-a] tardos-plus-auth coalition=1 average-jpeg-q55
[source-a] tardos-only coalition=2 average-png
[source-a] tardos-only coalition=2 average-jpeg-q55
[source-a] tardos-plus-auth coalition=2 average-png
[source-a] tardos-plus-auth coalition=2 average-jpeg-q55
[source-a] tardos-only coalition=3 average-png
[source-a] tardos-only coalition=3 average-jpeg-q55
[source-a] tardos-plus-auth coalition=3 average-png
[source-a] tardos-plus-auth coalition=3 average-jpeg-q55
[source-a] tardos-only coalition=5 average-png
[source-a] tardos-only coalition=5 average-jpeg-q55
[source-a] tardos-plus-auth coalition=5 average-png
[source-a] tardos-plus-auth coalition=5 average-jpeg-q55
[source-a] direct, changed-context and 100 wrong-key controls
[source-b] embedding ten matched copies
[source-b] tardos-only coalition=1 average-png
[source-b] tardos-only coalition=1 average-jpeg-q55
[source-b] tardos-plus-auth coalition=1 average-png
[source-b] tardos-plus-auth coalition=1 average-jpeg-q55
[source-b] tardos-only coalition=2 average-png
[source-b] tardos-only coalition=2 average-jpeg-q55
[source-b] tardos-plus-auth coalition=2 average-png
[source-b] tardos-plus-auth coalition=2 average-jpeg-q55
[source-b] tardos-only coalition=3 average-png
[source-b] tardos-only coalition=3 average-jpeg-q55
[source-b] tardos-plus-auth coalition=3 average-png
[source-b] tardos-plus-auth coalition=3 average-jpeg-q55
[source-b] tardos-only coalition=5 average-png
[source-b] tardos-only coalition=5 average-jpeg-q55
[source-b] tardos-plus-auth coalition=5 average-png
[source-b] tardos-plus-auth coalition=5 average-jpeg-q55
[source-b] direct, changed-context and 100 wrong-key controls
[source-b] copied-overlay falsification attack
[source-b] copied-overlay copied-pdf
[source-b] copied-overlay copied-jpeg-q55
[study] complete Gate A=True Gate B=False runtime=114.054313s
```

There was no repaired or outcome-selected second run.

## Fixed inputs and fidelity

Both PDFs were one A4-sized rendered page at 144 DPI with 55,440 available
6-by-6 blocks, exceeding the 52,500-symbol requirement.

| Source | SHA-256 | SHA3-256 | extracted-text SHA3-256 |
|---|---|---|---|
| A | `5b347ce904b224a0b33602b12b905d0534d7f626c7319cec960f8bf2e7ed5b06` | `1f1efd3373e76da4b0a01a3ada653bd5edb3849762c6a18adaf14be2310f0adb` | `7e826adac335ded60bda03c2c650d597e326a2c380ec2d8dbe510ac5d10e8cce` |
| B | `1a9e26018a05655dd4c47e25ce20990f0f250c9ccb7d21d1f239e995fc842f56` | `8d358a4158f21cce09781173fd04688f661bb2f155ab580bbd301389b571b1b5` | `f2eba13e4b3030a7cc61499a9c5c74b6dbf50e57d451817658949cc51d14ec15` |

All 20 marked PDFs retained exact extracted text. Source-to-output PSNR in row
order 0–4 was:

| Source/channel | PSNR dB |
|---|---|
| A, Tardos only | 41.866, 41.866, 41.865, 41.866, 41.863 |
| A, Tardos + auth | 38.577, 38.580, 38.577, 38.579, 38.577 |
| B, Tardos only | 41.927, 41.924, 41.924, 41.927, 41.927 |
| B, Tardos + auth | 38.637, 38.638, 38.638, 38.640, 38.640 |

These measurements do not imply invisibility or signature preservation.

## Authenticator positive observations

Each row below gives `[decoded distance for candidate rows 0,1,2,3,4]`. The
exact-match set equalled the expected coalition prefix in every artifact.

| Source | Coalition | Transform | Expected = exact rows | Distances 0–4 |
|---|---:|---|---|---|
| A | 1 | PNG average | `[0]` | `[0,40,37,34,29]` |
| A | 1 | JPEG Q55 | `[0]` | `[0,38,36,36,44]` |
| A | 2 | PNG average | `[0,1]` | `[0,0,39,37,35]` |
| A | 2 | JPEG Q55 | `[0,1]` | `[0,0,36,40,43]` |
| A | 3 | PNG average | `[0,1,2]` | `[0,0,0,35,34]` |
| A | 3 | JPEG Q55 | `[0,1,2]` | `[0,0,0,33,42]` |
| A | 5 | PNG average | `[0,1,2,3,4]` | `[0,0,0,0,0]` |
| A | 5 | JPEG Q55 | `[0,1,2,3,4]` | `[0,0,0,0,0]` |
| B | 1 | PNG average | `[0]` | `[0,32,35,38,36]` |
| B | 1 | JPEG Q55 | `[0]` | `[0,35,40,37,35]` |
| B | 2 | PNG average | `[0,1]` | `[0,0,34,37,35]` |
| B | 2 | JPEG Q55 | `[0,1]` | `[0,0,32,39,37]` |
| B | 3 | PNG average | `[0,1,2]` | `[0,0,0,38,41]` |
| B | 3 | JPEG Q55 | `[0,1,2]` | `[0,0,0,40,37]` |
| B | 5 | PNG average | `[0,1,2,3,4]` | `[0,0,0,0,0]` |
| B | 5 | JPEG Q55 | `[0,1,2,3,4]` | `[0,0,0,0,0]` |

The machine result retains encoded-bit distances, corrected-block counts,
decoded/encoded bits, and all 126 summed correlations for every candidate.

## Negative observations

- Each source supplied six direct artifacts (unmarked source plus five
  Tardos-only PDFs), each tested against all five candidates: 30 decisions per
  source, 60 total, no exact matches. Decoded-distance ranges were 34–46 for A
  and 33–41 for B.
- Changed-context decoded distances for A were `[36,33,38]` for changed source
  hash, fresh session, and another actual recipient public-key fingerprint.
  For B they were `[41,37,37]`. All 6 rejected.
- The 100 fresh wrong secrets per source produced no exact matches. Distance
  ranges were 25–46 for A and 26–44 for B. All 200 individual secret hashes,
  distances, match booleans, corrected-block counts, and raw sums are retained.

## Tardos observations and theorem boundary

For all 32 matched transformed artifacts, the fixed-Z selected set exactly
equalled the participating prefix, and there were no selected nonparticipants.
The exact marking-condition violation counts are below as
`Tardos-only PNG / Tardos-only JPEG / Tardos+auth PNG / Tardos+auth JPEG`:

| Source | Coalition | Selected set in all four | Violation counts |
|---|---:|---|---|
| A | 1 | `[0]` | `0 / 5486 / 248 / 4159` |
| A | 2 | `[0,1]` | `0 / 4700 / 112 / 3262` |
| A | 3 | `[0,1,2]` | `0 / 5033 / 108 / 5319` |
| A | 5 | `[0,1,2,3,4]` | `0 / 3110 / 52 / 3230` |
| B | 1 | `[0]` | `0 / 6028 / 213 / 4971` |
| B | 2 | `[0,1]` | `0 / 5032 / 78 / 3870` |
| B | 3 | `[0,1,2]` | `0 / 5299 / 141 / 5568` |
| B | 5 | `[0,1,2,3,4]` | `0 / 3418 / 48 / 3516` |

Thus the empirical selected sets happened to be exact, but the Tardos theorem's
marking-condition premise was not observed for JPEG or combined-channel
artifacts and must not be claimed for those cases. Complete 1,000-row score
vectors and registration diagnostics are retained per case.

## Copied-overlay attack

The donor and copied PDF each contained exactly two image objects, both copied
with reconstructed soft masks. The helper call recorded exactly three paths and
received no key, secret, context, codeword, correlation, overlay array, or plan.
The target replaced one visible `quantity 120` occurrence with `quantity 920`.

| Object | File SHA-256 | Extracted-text SHA3-256 |
|---|---|---|
| genuine marked donor | `e480640b963e564a6df7ffe2ce4cb904cf603299f2431b7d253b0728ccd9d8a3` | `f2eba13e4b3030a7cc61499a9c5c74b6dbf50e57d451817658949cc51d14ec15` |
| modified target | `1a26216900d2031c7f71ddbe3801d8b277c7a45b01ca7a944e37ebda776b50dc` | `22fabef6466d830f636454eafcf047abf0d5206fcd56aa17939f0e3416bb28e3` |
| copied-overlay PDF | `15a8a5e93a609745f05cbae0f7c1628fc3e31ff879aa8f4abe6dbdabfa34cd89` | `22fabef6466d830f636454eafcf047abf0d5206fcd56aa17939f0e3416bb28e3` |
| copied-overlay JPEG Q55 | `e32a16413497de09251c26c22c927ea26f37ca4371e01f753191f1f9f949168a` | not applicable |

All three PDF file hashes differed. Donor text differed from both target and
copied output, while target and copied-output extracted text matched exactly.

| Attack artifact | Exact issued rows | Candidate decoded distances 0–4 | Donor under changed-source context | Tardos selected | Marking violations |
|---|---|---|---|---|---:|
| copied PDF | `[0]` | `[0,34,37,41,41]` | reject, distance 39 | `[0]` | 240 |
| copied JPEG Q55 | `[0]` | `[0,38,42,41,34]` | reject, distance 36 | `[0]` | 4983 |

The exact donor-tag survival on both artifacts falsifies the stronger content
binding claim for this copyable visual layer. The changed-source-context
rejections only show that a different expected plan does not match; they do not
bind the observed layer to the edited PDF's text or bytes.

## Hashes and evidence integrity

Experiment source SHA-256 values frozen in the premeasurement manifest and
rechecked unchanged after the run:

| File | SHA-256 |
|---|---|
| `carrier.py` | `17272bddebe86e14afa35d25c7eb7dc423992676aed526d47d8d8f17f13bd039` |
| `run_study.py` | `fb039545453f60e48582a26e2d22cc51dc2cbb05cc72ab6323a2d04ac00efa13` |
| `test_carrier.py` | `8fe311dd7c0e719907c751f284b3d85a372acfe3a2a77457f4ce5b1229d8b12f` |
| `README.md` | `bdc6f341ee5466733a4a64f09c9803ec2c21f0510f1624d5c6fa0a7b99a61ec4` |

Imported NISHAN module SHA-256 values, also frozen and rechecked:

| Module | SHA-256 |
|---|---|
| `tardos_carrier.py` | `ea818369f5fd73975fdd66380352d3d3afb75e42cd0de3dc841e4243a8a2a0f9` |
| `layout_tag.py` | `3994aa97c698980943ef73732a57a8c4c435c34c723b7deecc549f081ce4d8ac` |
| `watermark.py` | `f52b1aa480393ff8baae407b31f2400a1476571bb38eaeb9248c6761bdca006c` |
| `registration.py` | `604c380475bd604f32a16ace55463b28f29d52f61b23b103149bc74fa0b7f92f` |
| `pqc.py` | `a3a8b56bd9486d71addc3e2f3b5344a28a30c54eabeec4347d6373fd387cd35a` |
| `tardos.py` | `cf0fe3bb08bbb6aa4daaa56cbd6f356c86a98cfddaba5c64297668adf2623bd0` |

The results enumerate and hash 97 pre-results run files; all 97 hashes were
recomputed with zero mismatches. The run contains 98 files total because
`results.json` cannot include its own hash. External bundle hashes are:

- `manifest.json`: `a6425269f4e1f156e85775d808d9dd9de5ef0d91a0633661b1976aaa6b2a558a`
- `results.json`: `1e9d8c827bf987bf101a2107940351b5c8cf0ef5b1fd463c330ee1ecce4e2e80`

All retained secrets, private keys, wrong-secret bundles, and private material
manifests were rechecked at mode 0600; there were zero permission violations.
JSON serialization used `allow_nan=False`; unavailable non-finite values would
be explicit strings rather than bare NaN/Infinity.

## Self-review and concerns

- The fixed profile, dimensions, threshold, transforms, candidate matrix, and
  gate definitions match the frozen spec. Inputs and randomness were generated
  once, the manifest preceded measurement, and no case was filtered.
- The observed-copy helper rejects page-count/geometry mismatches and rebuilds
  each image with its soft mask. The real-PDF unit test verified two masks and
  changed-target text. The run independently recorded two donor and two copied
  image objects.
- Full outputs preserve raw evidence rather than only gate booleans. Artifact
  hash recomputation, frozen-code comparison, cardinality checks, and private
  mode checks passed.
- All JPEG and combined-layer Tardos measurements showed marking-condition
  violations. Reporting exact selected sets does not restore the theorem's
  missing premise.
- This remains a tiny, harness-controlled, synthetic convenience sample. It has
  no independent key custody, enrollment, escrow, ledger, adjudicator,
  recipient signature, public verification, malicious-provider resistance,
  physical print/scan evidence, generalization, novelty, or superiority result.
- `__pycache__/carrier.cpython-314.pyc` and
  `__pycache__/test_carrier.cpython-314.pyc` were generated by the prescribed
  interpreter runs. They are runtime caches, not added implementation sources;
  they were left in place because the task explicitly prohibited deletion.
- `results.json` is necessarily outside its own internal artifact-hash map; its
  external SHA-256 above should be used by the controller when freezing or
  moving the evidence bundle.

The read-only literature review supplied by the controller did not change the
profile or run. It informed the interpretation above: candidate-context
substitution and genuine-donor-context overlay transplantation test different
claims, so Gate B governs the stronger content-authentication claim.
