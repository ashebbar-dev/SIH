# Orthogonal authenticator carrier falsification study

This directory contains an isolated, prospective carrier experiment. It is not
production security integration and must not be used to authenticate releases
or accuse a recipient.

Run the focused suite:

```bash
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python -m unittest discover -s research/experiments/auth_orthogonal_v1 -p 'test_*.py' -v
```

Run the preregistered study exactly once into a new directory:

```bash
PYTHONPATH=prototypes/nishan_pq:research/experiments/auth_orthogonal_v1 .venv/bin/python research/experiments/auth_orthogonal_v1/run_study.py --output research/evidence/nishan-auth-orthogonal-2026-09-12/run-01
```

The destination must not already exist. The runner writes `manifest.json`
before measurement, retains all artifacts, then writes `results.json`. A crash
leaves partial evidence plus `failure.json`; do not overwrite it or select a
more favorable rerun.

## Sensitive local material

Every run retains authority secrets, authenticator secrets, wrong-key controls,
and ML-DSA-65 private keys under `material/` for reproducibility. Secret and
private manifest files are mode 0600. The material is non-production research
data: do not submit, publish, upload, or treat it as independently held key
material.

## Security and interpretation boundaries

- The harness owns every key. There is no recipient enrollment, independent
  custody, escrow, ledger, signature protocol, adjudicator, or public
  verification.
- This carrier is a full-page PDF image object and is separately removable and
  copyable. A changed-context rejection does not show that edited content will
  reject when tested under the genuine donor context. The observed-object copy
  attack directly measures that gap without receiving a key or plan.
- Exact 72-bit recovery is a fixed experimental decision rule, not proof of a
  false-attribution rate. The wrong-key candidates are correlated convenience
  controls, not a population estimate.
- Tardos accusation bounds require their theorem assumptions, including the
  marking condition. The runner records observed marking-condition violations
  and does not extend the theorem to this visual channel.
- PSNR and extracted-text equality do not establish human invisibility,
  accessibility, document semantics, or preservation of digital signatures.
- Two synthetic one-page fixtures, digital averaging, and JPEG Q55 do not
  establish physical print/scan recovery or deployment generalization.
- Gate A only measures limited digital replication. Gate B only tests the
  specified overlay transplantation hypothesis. Even both passing would not
  establish asymmetric security, malicious-distributor resistance, novelty,
  superiority, or readiness for the product or presentation.
- A scientific gate failure is a valid result. The fixed strength, profile,
  cases, exact threshold, and randomness must not be retuned or rerun to select
  favorable outcomes.
