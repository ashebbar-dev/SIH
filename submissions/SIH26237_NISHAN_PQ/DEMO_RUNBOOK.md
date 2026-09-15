# NISHAN-PQ five-minute offline judge demonstration

Status: 12 September 2026. This runbook demonstrates the tested research
prototype on public synthetic fixtures. It does not demonstrate production
certification, human guilt, delivery/reading proof or robust physical recovery.

## Before the session

- Fill in: team ID **[TEAM ID]**, registered team name **[TEAM NAME]** and public
  repository **[PUBLIC REPOSITORY URL]**.
- Use the project `.venv` with the checked-in dependencies and an OpenSSL provider
  exposing ML-KEM-768 and ML-DSA-65. The runner checks both and fails if unavailable.
- Disconnect networking if the judges request an air-gapped demonstration. The
  measured workflow needs neither a GPU nor an ESP32.
- Keep the reviewed evidence directory unchanged. Each run must use a new, empty
  output root. Do not publish, copy into the repository or reuse any generated
  private keys or secrets; they are synthetic demo-only material.
- Open slide 5 and a terminal at the project root.

## Invocation

Choose a new literal run name every time. For example, use `run-01` only once;
increment the suffix for later rehearsals instead of deleting or overwriting it.

```bash
.venv/bin/python prototypes/nishan_pq/tools/demo_release_safeguards.py \
  --output /tmp/nishan-judges-run-01
```

Expected summary shape:

```json
{
  "results": ".../results.json",
  "pqc_ready": true,
  "cases": 12,
  "all_passed": true
}
```

If the root already contains output, the runner refuses it. Pick a new suffix;
do not remove or overwrite the earlier evidence. A skipped or unavailable PQC
check is not a pass.

## Five-minute judge flow

### 0:00–0:35 — Frame the decision

Say: “NISHAN-PQ connects a leaked artifact to a signed release session when the
available evidence corroborates. When it does not, the system returns
inconclusive rather than naming a person.”

Point out that the runner is offline, uses public synthetic one-page PDFs, and
reports security scenarios—not population trials.

### 0:35–1:25 — Two recipients and a repeated session

Show these cases in the new `results.json`:

- `concurrent_distinct_sessions_rows`: two processes issue the same source to
  two recipients; their rows and session IDs differ. Process ordering may swap
  row 0 and row 1.
- `third_release_row`: the next release succeeds on row 2.
- `signed_copy_hash_match`: all three published files match the hashes in their
  signed release receipts.

Explain: serialization spans validation, row allocation, signing, append,
checkpoint and publication. A signed record means release authorization, not
successful delivery or reading.

### 1:25–2:05 — Clean PDF source association

Show `clean_pdf_trace`:

- decision: `corroborated_channels`;
- visual and layout evidence select the same Alice release session;
- the recipient signature is valid;
- configured witness status is valid for the checked snapshot.

Explain: tracing is non-blind and uses the retained original. The witness result
is a checked snapshot, not an eternal freshness guarantee.

### 2:05–2:45 — Raster transplant stays inconclusive

Show `rendered_transplant_abstains`:

- high-assurance `attribution` is empty;
- decision: `abstain_missing_layout_channel`;
- the visual score remains only under `visual_only_research_leads`.

Optionally show `low_capacity_pdf_abstains`, which records a signed capacity
limitation and also leaves attribution empty. Say: “Digital PDF corroboration;
raster-only matches are research leads.” Genuine image screening remains a
separate research mode.

### 2:45–3:40 — Pin and rollback gates

Show:

- `wrong_pin_rejected`: configured release rejects the wrong actual witness-key
  pin and creates no output;
- `rollback_release_rejected`: all ledger replicas are truncated to the same
  apparently quorum-valid prefix, but configured release rejects it;
- `rollback_trace_rejected`: configured trace rejects the same rollback;
- `trace_read_only`: witness checkpoint bytes are unchanged by trace.

Explain: this guarantee requires a caller-provisioned pin and trustworthy
retained witness state. All demo validator and witness keys remain co-located;
R8 is therefore not met against one administrator controlling everything.

### 3:40–4:25 — Witness/checkpoint failure publishes nothing

Show both:

- `checkpoint_failure_no_publication`: no destination is created;
- `checkpoint_failure_preserves_existing_output`: an existing destination is
  unchanged.

Explain the precise boundary: the signed release-authorization record remains
committed after the injected checkpoint failure. The ledger then exposes an
`unwitnessed_extension`; deliberate review and checkpoint recovery are required.
Do not call this a rollback of the committed record.

### 4:25–5:00 — Close with evidence and next gate

Show `pqc_ready: true`, `all_passed: true`, the exact 12 unique case names and the
19-entry `code_sha256` map. The deck build independently checks those hashes
against current files before presenting the fresh claims.

Close with three boundaries and the next-round plan:

1. Source-copy/session evidence does not establish human guilt and can be framed
   by a trusted authority able to reproduce an issued copy.
2. Physical recovery remains experimental: 0/4 at the shipped threshold;
   exploratory profiles recover the same 1/4 capture.
3. Next round: independent administrative/key custody, a larger multi-recipient
   and multi-page corpus, representative held-out print/camera tests, and a
   portable independent evidence verifier.

## Quick result inspection

Replace the path with the new run root used above.

```bash
jq '{version, pqc_ready, all_passed, cases: [.cases[] | {name, passed}]}' \
  /tmp/nishan-judges-run-01/results.json
```

Optional current-file hash check:

```bash
jq -r '.code_sha256 | to_entries[] | "\(.value)  \(.key)"' \
  /tmp/nishan-judges-run-01/results.json \
  | sha256sum -c -
```

Stop if any case is missing, duplicated or false; if `pqc_ready` is not exactly
true; or if any code hash differs. Do not describe a partial run as the reviewed
12/12 demonstration.
