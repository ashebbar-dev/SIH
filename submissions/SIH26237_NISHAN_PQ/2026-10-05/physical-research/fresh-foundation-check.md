# Fresh foundation verification — 28 September 2026

Main commit: `f37e861dc02815adf1bebb3e1b45ff222dccf821`.

Coordinator executed:

```sh
taskset -c 4 nice -n 19 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq .venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
```

Result: exit0, **59 tests passed in63.148seconds**. One Mesa Rusticl warning
appeared; there were no test failures. Unified-exec session79186 completed.
This records the observed tool result; it is not a claimed raw stdout archive.

`nishan doctor` was checked again during consolidation:

```json
{"ml_dsa_65": true, "ml_kem_768": true, "openssl_version": "OpenSSL 3.6.4 25 Aug 2026 (Library: OpenSSL 3.6.4 25 Aug 2026)", "ready": true}
```

No tracked main-worktree modifications were present after these checks. User
photographs/Test directories remain untracked and were not modified or removed.
The19source hashes in the historical12-scenario safeguards demo were also
checked against the current files using `sha256sum --check --strict`: all19
matched. This establishes source correspondence, not a new execution of those
12scenarios.
These tests do not establish independent key custody, malicious-quorum
resistance, physical robustness, or completion of experimental branches.

## Fresh safeguard replay — supersedes historical-only execution status

The coordinator subsequently ran the unchanged main scenario runner against a
new exclusive synthetic output directory. Unified-exec session8008 exited0:
`pqc_ready=true`, `cases=12`, `all_passed=true`.

```sh
taskset -c 4 nice -n 19 env OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq .venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py --output physical_captures/stroke-v3-20260918/test3-20260928/fresh-stable-safeguards-v1
```

Machine-readable evidence: `fresh-stable-safeguards-v1/results.json`, with
all12case outcomes, realPQC profile, source commitments and limitations.
Result SHA256: `1f5a7a1961faf89fa399dc104d6e9ad66181d1b00e99bacbf46fc59d7ecc45e7`.
All19recorded source hashes were subsequently rechecked against main and match.
This is fresh protocol-scenario evidence, not12independent population trials
or any increase in physical recovery. Synthetic private keys under that
fixture directory are local demo-only and must not be uploaded or reused.

Exact observed non-failing environment warning:

```text
=== Rusticl warning: Patched Mesa libclc not detected. Upstream libclc may contain known bugs or breaking changes and isn't guaranteed to work reliably. Please visit https://gitlab.freedesktop.org/karolherbst/mesa-libclc for more information. ===
```
