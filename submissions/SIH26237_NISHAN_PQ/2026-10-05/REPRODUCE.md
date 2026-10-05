# Reproducing the stable digital results

Run from the repository root. The measured stable application source is baseline
`f37e861dc02815adf1bebb3e1b45ff222dccf821`; this publication changes documentation
and evidence, not that application source. Research variants require their indexed
branch/version and are not installed by these commands.

## Prepare the environment before going offline

Linux is the tested environment. The ledger uses `fcntl.flock`; native Windows
Python is not supported. See the root `requirements-handoff.txt` for recorded
Python packages, and the application README for assumptions.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-handoff.txt
export PYTHONPATH="$PWD/prototypes/nishan_pq"
export PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1
export OMP_NUM_THREADS=1
.venv/bin/python -m nishan doctor
```

The system OpenSSL executable must provide **ML-KEM-768 and ML-DSA-65**. Installing
Python packages alone does not provide this. `doctor` must report `ready: true`;
do not add a classical fallback. The September measurements used OpenSSL 3.6.4.
The 5 October publication check used 3.6.5; timings are environment-dependent.
Package pins record the original machine, not universal portability certification.

## Tests and benchmarks

Use a fresh scratch directory outside the checkout; never publish its keys or
fixture folders. These output flags avoid overwriting checked-in benchmark evidence.

```bash
task_scratch=$(mktemp -d /tmp/nishan-reproduction-XXXXXX)
export MPLCONFIGDIR="$task_scratch/matplotlib"
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py \
  --output "$task_scratch/safeguards"
.venv/bin/python prototypes/nishan_pq/tools/benchmark_tardos_pdf.py \
  --source artifacts/nishan/synthetic-source.pdf \
  --output-directory "$task_scratch/carrier" --evidence "$task_scratch/carrier.json"
.venv/bin/python prototypes/nishan_pq/tools/benchmark_tardos_trials.py \
  --output "$task_scratch/codebooks.json"
.venv/bin/python prototypes/nishan_pq/tools/benchmark_end_to_end_trials.py \
  --trials 30 --output "$task_scratch/jpeg.json"
```

Expectations and definitions:

- Core suite: **59 passing tests** on the unchanged source.
- Safeguards: **12/12** named scenarios, including clean-PDF agreement, concurrency,
  retained-witness rollback, wrong pin and publication failure handling.
- Carrier benchmark: **25/25 expected outcomes**, including intentional abstentions.
- Code-level study: **120 cases = 30 codebooks × four strategies**; no PDF/photo channel.
- JPEG study: **30 expected visual rows** without extra rows crossing threshold.
  Under the strict policy, raster-only attribution may remain empty/false; do not
  reinterpret `exact_session_attribution: false` as an authenticated PDF verdict.

Random keys/session IDs and runtime measurements are not byte-identical between
runs. Compare the declared case outcomes and boundaries, not timing or signature bytes.
The 175 mixed cases cannot estimate the theoretical rare error budget empirically.

## Physical research and exclusions

Physical-research reports and indexed source expose methods, failures, hashes and
development-corpus measurements. Original phone photographs and personal transport
records remain private. Therefore **the public package is insufficient for an
independent physical rerun without separately obtaining the capture inputs**.
Path references inside archived reports describe the original experiment layout;
they are provenance, not portable commands. Later source/clean-render probes are
not substitute photographs. Do not silently tune thresholds or replace real tilted
captures with digital warps when recreating a study.

## Package integrity

From this dated package directory:

```bash
sha256sum -c SHA256SUMS
```

This checks file integrity against the published manifest. It is not a third-party
attestation of scientific results, a signed release certificate, or a privacy guarantee.
