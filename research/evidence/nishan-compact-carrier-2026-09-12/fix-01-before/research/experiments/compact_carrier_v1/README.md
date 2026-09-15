# Empirical compact-carrier pilot

This isolated experiment compares the frozen `original-6-r1`, `symmetric-6-r4`, and `symmetric-12-r1` carrier profiles on one synthetic PDF. It issues rows 0 and 7, evaluates the exact 57-observation matrix, and retains replay artifacts. It is not a production attribution system.

Run the focused tests:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python -m unittest discover -s research/experiments/compact_carrier_v1 -p 'test_*.py' -v
```

Run the one fixed pilot into a destination that does not already exist:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python research/experiments/compact_carrier_v1/run_study.py --output research/evidence/nishan-compact-carrier-2026-09-12/run-01
```

Replay a capture read-only with always-on registration:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq:research/experiments/compact_carrier_v1 .venv/bin/python research/experiments/compact_carrier_v1/score_capture.py --run research/evidence/nishan-compact-carrier-2026-09-12/run-01 --profile symmetric-12-r1 --suspect research/evidence/nishan-compact-carrier-2026-09-12/run-01/rasters/symmetric-12-r1/row-0/clean.png
```

The run contains `manifest.json`, `results.json`, a copied source, six issued PDFs, controlled rasters, one NPZ per observation, physical instructions, and `private/replay-state.npz`. The private NPZ contains fresh keys and codebooks, is mode 0600, and must not be shared. Public JSON contains commitments rather than secrets. A capture replay validates both the copied source and private-state hash before loading arrays and never writes into the run.

All findings are empirical: one source document, two issued copies per profile, no physical print/camera result, no certified probabilities for the inherited finite-precision keyed sampler or noisy decoded words, no collusion guarantee, no production attribution, and no novelty or superiority claim. Equal nominal carrier area is not equal perceptual fidelity. Synthetic blur is diagnostic only, capture replay uses registration while the matrix does not, and local manifests are not independently signed provenance.
