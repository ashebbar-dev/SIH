# Laptop handoff — 15 September 2026

Start here. Older plans and the historical sections of README.md are not the
current execution order. This handoff preserves source, tests, presentations,
research reviews and shareable measured evidence. It does not resume research.

## Immediate objective and current state

The user has a six-person team and a 15 September evaluation. The immediate
priority is a dependable NISHAN digital demonstration and presentation, not a
new research direction. DHRUVA remains a separate research prototype.

- NISHAN's supported demonstration is a terminal-driven synthetic one-page PDF
  workflow: encrypted package, per-recipient/session fingerprint, recipient
  ML-DSA signature, local ledger and configured witness checks, clean-file
  attribution and manipulated-copy abstention.
- The saved 12 September safeguard run passed 12/12 scenarios. Its 19 source
  hashes matched the current code at the 14 September readiness inspection.
  These are historical scenario results, not a fresh run on the new laptop.
- The six-slide PPTX/PDF and speaker notes are under
  `submissions/SIH26237_NISHAN_PQ/`. Team name, team ID and repository-link
  placeholders remained at the last strict check. A private handoff repository
  does not automatically satisfy a public submission-link requirement.
- Original physical recovery was 0/4 captures at the shipped threshold.
  Exploratory receivers recovered the same one capture. No reliable phone-photo
  attribution has been established. PDF-source raster evidence remains a
  research lead, not the strict corroborated verdict.
- Validator, witness and recipient demo keys are co-located. Do not claim
  independent administrative control, authority non-framing, human guilt,
  delivery/reading proof or certified security.
- DHRUVA's corrected four-development-drive median drift was approximately
  16.110%, 21.855%, 45.412%, 20.347%; it is not a demonstrated sub-10% mobile
  navigation engine. See its README and dated aligned-ablation findings.

## Clone and recreate the runtime

Handoff verification on 15 September: a clean export of the staged files passed
all 12 fresh safeguard scenarios and the presentation verifier with placeholders
allowed. This used the source machine's existing interpreter and OpenSSL, not a
fresh dependency install or another laptop. The safe summary is
`research/evidence/github-handoff-2026-09-15.json`; no generated private demo
state is included.

Repository: https://github.com/ashebbar-dev/SIH (private handoff).
Authenticate with an account that has access. Do not put tokens in commands or
remote URLs.

```bash
gh repo clone ashebbar-dev/SIH
cd SIH
python3 --version
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-handoff.txt
export PYTHONPATH="$PWD/prototypes/nishan_pq"
export PYTHONDONTWRITEBYTECODE=1
.venv/bin/python -m nishan doctor
```

The source machine ran Python 3.14.7. `requirements-handoff.txt` records its
installed packages; it has not been certified on every OS or Python version.
The package declares Python >=3.11, but the pinned scientific packages may have
stricter requirements. If installation fails, record the actual error rather
than silently substituting dependencies immediately before the demo.

The commands above avoid a machine-specific editable-install path by setting
PYTHONPATH. Repeat that export when opening another terminal. An editable
installation is optional once build dependencies are available.

Use Linux, macOS, or a suitable Linux environment on Windows; the current ledger
uses `fcntl.flock`, so native Windows Python is not the supported runtime. The
source machine is the tested environment; macOS/WSL portability is not a measured
claim. PDF opening commands may differ by OS.

NISHAN invokes the **system OpenSSL executable**, not merely Python's
`cryptography` library. The source runtime reported OpenSSL 3.6.4 with ML-KEM-768
and ML-DSA-65. The new machine must expose both algorithms:

```bash
openssl version
openssl list -kem-algorithms
openssl list -signature-algorithms
.venv/bin/python -m nishan doctor
```

`ready` must be true. Installing Python dependencies alone does not solve a
missing OpenSSL algorithm/provider. Never introduce a classical fallback to make
the demonstration look successful. Complete downloads/setup before disconnecting
the network; the prepared demonstration itself needs no Internet, GPU, ESP32 or
microphone. `jq` is optional for displaying JSON; a text editor also works.

## Rehearse the current demo

Run from the repository root in the prepared terminal:

```bash
NISHAN_DEMO_DIR="$(mktemp -d /tmp/nishan-demo-XXXXXX)"
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py \
  --output "$NISHAN_DEMO_DIR"
jq '{pqc_ready, all_passed, cases: [.cases[] | {name, passed}]}' \
  "$NISHAN_DEMO_DIR/results.json"
```

Require `pqc_ready: true`, exactly 12 cases and `all_passed: true`. Stop and
investigate any failure. The runner creates fresh demo keys and must use a new
output directory for each run. Do not upload that entire directory.

Open `fixture/source.pdf`, `fixture/alice.pdf`, `fixture/bob.pdf` and optionally
`fixture/third.pdf` inside the printed output directory. Then inspect:

```bash
jq '{decision: .channel_decision.decision,
     attribution: [.attribution[] | {recipient_id, session_id, recipient_signature_valid}],
     witness_valid: .ledger_witness.valid}' "$NISHAN_DEMO_DIR/clean-evidence.json"
jq '{decision: .channel_decision.decision, attribution}' \
  "$NISHAN_DEMO_DIR/rendered-transplant-evidence.json"
jq '.cases[] | select(.name == "rollback_trace_rejected")' \
  "$NISHAN_DEMO_DIR/results.json"
```

Expected: clean Alice copy has `corroborated_channels`; the rendered transplant
has empty attribution and `abstain_missing_layout_channel`; the rollback check
rejects. These jq commands display the newly generated results, not new traces.

Full presentation order and limitations:
`submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md`.
Use `demo_release_safeguards.py`, not the older `python -m nishan demo` workflow
as the current safeguard demonstration. Retain a screen recording as backup.
Temporary output may disappear after a reboot; keep any chosen backup securely
outside Git and never reuse the synthetic private keys for real documents.

## Verify source and presentation

```bash
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
.venv/bin/python -m unittest discover -s submissions/SIH26237_NISHAN_PQ/tests -v
.venv/bin/python submissions/SIH26237_NISHAN_PQ/verify_submission.py \
  --root . --allow-placeholders
```

Run the last command without `--allow-placeholders` before actual submission.
Do not overwrite reviewed evidence simply to silence a verifier. The current
slides are retained unchanged in the handoff. New code changes can invalidate
the saved code-hash evidence and must be tested and documented honestly.

## Fresh physical capture requested, not yet measured

The latest instruction to the user was to print
`artifacts/nishan/dual-carrier-user-0000-live-text.pdf` at A4 actual size/100%,
with toner saving disabled. Take full-resolution normal-camera photographs,
straight-on and at a modest angle, all four corners visible. Do not use a
document-enhancing scanner app for those two captures. Preserve originals and
transfer as files, without chat-image recompression.

Suggested names: `nishan_front.jpeg`, `nishan_angle.jpeg`; an optional photograph
of `artifacts/nishan/synthetic-source.pdf` is the unmarked negative control.
No new capture had been supplied in this chat when the handoff was prepared.
The scorer for this specific public fixture is
`prototypes/nishan_pq/tools/score_physical_capture.py`; its key is deliberately
public test material. Do not apply that decoder to arbitrary newly issued PDFs.
Keep new outputs in a fresh directory and do not lower thresholds after seeing
the result to manufacture a pass.

## Paused work and next research context

- Compact-carrier pilot:
  `research/evidence/nishan-compact-carrier-2026-09-12/progress.md`,
  `task-1-report.md`, `task-1-review.md`, and
  `research/NISHAN_COMPACT_CARRIER_DECISION_2026-09-12.md`.
  One fixed synthetic run exists; baseline and variants already passed its
  positive cases, so it did not establish an attribution-success improvement.
  The review requested fixes, and work was interrupted. Treat the current
  experiment code as unfinished until inspected; do not silently resume it.
- Auth-orthogonal experiment: its visual tag did not solve transplant/content
  authentication. See `research/NISHAN_AUTH_ORTHOGONAL_DECISION_2026-09-12.md`.
- GPT-6 Pro suggestions were reviewed, not established as implemented results:
  `research/GPT6_PRO_RESPONSE_DECISION_2026-09-12.md` and its two linked reviews.
- Prior separate research session identifier:
  `01a086b4-d6d8-7b21-ae43-54d8999ed130`.
  Its lab is `parallel_research/sol_ultra_01a086b4_2026-09-12/`.
  Do not send queued instructions or restart old chats/agents automatically.
  The user previously stopped all research after delayed coordination messages
  appeared to restart it. Ask directly in chat for necessary input.
- Dataset files were observed under the old lab's
  `outputs/dhruva_speed_state/input/` during packaging. They are not included in
  Git. Saved plots/reports/source are included; raw IO-VNBD data must be acquired
  separately with provenance/licensing checked. Do not claim to have trained a
  deployable model merely because benchmark code is present.

## Deliberately excluded from Git

- Local virtual environments, caches, credentials, PEM/private-key files,
  authority secrets, identities, live ledgers/witnesses and raw demo state.
- Raw third-party datasets and personal camera originals. Existing diagnostic
  buffers of public synthetic test pages and source-derived public test fixtures
  are retained; they are not real recipient secrets.
- Opaque tar/zip snapshots that could contain secret material. Source, readable
  reviews, diffs and safe measured reports are retained.
- `research/evidence/nishan-compact-carrier-2026-09-12/run-01/private/replay-state.npz`.
  It contains random keys required to score that exact pilot's old prints.
  The same private state cannot be reconstructed from public commitments.
  For that exact experiment, transfer it separately through a secure private
  channel if needed; never put it into Git. A fresh run creates different keys
  and requires its own newly printed pages. This limitation does not affect the
  public physical-test fixture recommended above.
- An accidental root file named `=4.11` remains locally, ignored rather than
  deleted. Nothing was removed from the user's original workspace for handoff.

Preserve these exclusions in later commits. Private GitHub visibility is not a
reason to commit reusable secrets. Do not make this research handoff public
without another publication and licensing review.
