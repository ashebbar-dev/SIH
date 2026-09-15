# SIH 2026 campaign workspace

## Start here on another laptop — 15 September 2026

Read [CONTINUE_HERE.md](CONTINUE_HERE.md) for the current status, exact demo
commands, environment recreation, excluded private state and paused research.
The public repository is https://github.com/ashebbar-dev/SIH.
The tested Python package versions are in
[requirements-handoff.txt](requirements-handoff.txt); OpenSSL must be installed
separately with both required PQ algorithms available.

Use [`prototypes/nishan_pq/INTERACTIVE_DEMO.md`](prototypes/nishan_pq/INTERACTIVE_DEMO.md)
for the current browser demonstration, including the Android USB workflow and
truthful physical-result boundaries. The 12-scenario safeguard runner, older
assessment, demo commands and publication
checklist below are historical context, not instructions to restart research or
regenerate the presentation. Team/submission placeholders still need review.

## Current assessment — 10 September evening

The [independent goal audit](research/INDEPENDENT_GOAL_AUDIT_2026-09-10.md)
supersedes the earlier unconditional project recommendation. Neither prototype
has demonstrated a novel advantage over the strongest current systems.
At the user's explicit direction, **NISHAN and Dhruva are the two active
improvement tracks**. NISHAN remains the prepared submission. Alternative
problem-statement work, including custom wake-word detection, is paused until
serious improvement attempts on these two fail to produce useful results.
Dhruva's earlier transfer figures are now **confounded by verified timestamp
alignment defects**, including a 312-second phone-recording gap in S4. They
must not be treated as clean generalization evidence. Repairing and rerunning
the benchmark is the first step. See the [current focus decision](research/ORIGINAL_IDEAS_FIRST_2026-09-10.md).

The audit also repaired a PDF-format inconsistency in NISHAN's corroboration
policy. All 22 tests pass, including the new end-to-end regression. The user has
confirmed six teammates and a **15 September internal submission deadline**.

## Reproducible environment

Use one project virtual environment for both prototypes and the submission tools:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/pip install --no-build-isolation -e prototypes/nishan_pq
```

The checked workspace has been verified with this single interpreter. Set
`MPLCONFIGDIR=/tmp/sih-matplotlib` when plotting on a machine whose home
configuration directory is read-only.

## Prepared internal-hackathon entry

**SIH26237 — NISHAN-PQ: Every decrypted copy leaves a verifiable mark**  
Ministry of Defence · Indian Navy (WESEE) · Software · Blockchain & Cybersecurity


1. Copy the portal text from [`paste_ready_submission.md`](submissions/SIH26237_NISHAN_PQ/paste_ready_submission.md).
2. Replace the red team ID/name placeholders and repository link in [`NISHAN-PQ_SIH26237.pptx`](submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx).
3. Rebuild and export the PDF, then run the verifier without `--allow-placeholders`.
4. Give the SPOC the completed six-page PDF. The ready preview is [`NISHAN-PQ_SIH26237.pdf`](submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pdf).

The current preview intentionally retains placeholders because the exact registered team name and team ID have not been provided.

## Why this entry

The evidence-backed decision, competitor screening, risk analysis, five-day plan, six-person role split and hostile-jury answers are in [`SIH_2026_WINNING_STRATEGY.md`](research/SIH_2026_WINNING_STRATEGY.md).

At 01:57 IST on 10 September 2026, the official portal showed SIH26237 at **0/500** ideas. The working PDF path now integrates real ML-KEM-768 and ML-DSA-65 with a 52,500-symbol Tardos rendering carrier, a domain-separated 72-bit HMAC text-layout tag, all-row scoring over a declared 1,000-session roster, enrollment-bound receipts, and offline quorum evidence. Thirty successive JPEG-Q55 releases select the exact signed session 30/30 times with zero extra rows. The 25-case deterministic attack fixture recovers 2/2, 3/3 and 5/5 rows after aligned averaging, registers a synthetic perspective photograph, and fails closed under carrier removal and disjoint or partially overlapping cross-recipient transplantation. Editable PDFs require exact channel-set agreement; one surviving channel is recorded only as an investigative lead.

## Run the primary proof

```bash
.venv/bin/python -m nishan doctor
.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
.venv/bin/python -m nishan demo --work-dir /tmp/nishan-demo
.venv/bin/python prototypes/nishan_pq/tools/benchmark_tardos_pdf.py
```

The real print/scan and phone-photo protocol is in [`physical_captures/README.md`](physical_captures/README.md). The scoped novelty audit is [`NISHAN_NOVELTY_AND_PRIOR_ART.md`](research/NISHAN_NOVELTY_AND_PRIOR_ART.md); it explicitly separates established ingredients from the implemented contribution.

Submission-safe evidence is in [`artifacts/nishan`](artifacts/nishan). The demo directory contains private keys and the watermark authority secret; do not publish it.

Git initialization and the public push are deliberately reserved for the internal-hackathon day. Follow [`GITHUB_DAY_CHECKLIST.md`](GITHUB_DAY_CHECKLIST.md) then; `.gitignore` is already prepared to keep local identities, keys, demo ledgers, and raw data out of the public repository.

## Rebuild and verify the deck

```bash
.venv/bin/python submissions/SIH26237_NISHAN_PQ/build_deck.py \
  --team-id "YOUR EXACT TEAM ID" \
  --team-name "YOUR EXACT REGISTERED TEAM NAME"

# Export the PPTX to PDF with LibreOffice/PowerPoint, then:
.venv/bin/python submissions/SIH26237_NISHAN_PQ/verify_submission.py --root .
```

## Earlier secondary prototype

**SIH26168 — Dhruva** was the earlier second-entry recommendation. Its reproducible
IO-VNBD benchmark is in [`prototypes/dhruva`](prototypes/dhruva). The new transfer
results require cause-aware improvement before submission claims. The
[SIH26172 research protocol](research/KWS_RESEARCH_PROTOCOL_2026-09-10.md) is
retained but paused; no replacement entry has earned a submission switch.
