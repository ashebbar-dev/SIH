# NISHAN Interactive Demo Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver and push an honest, interactive NISHAN photo/PDF demonstration with direct phone-browser uploads and a verified signed-PDF backup.

**Architecture:** A local stdlib HTTP server wraps existing immutable detector APIs. Separate public-fixture and signed-session modes retain their distinct assurance, while a responsive browser UI presents actual asynchronous results and a mobile capture page.

**Tech Stack:** Python stdlib, existing NumPy/Pillow/PyMuPDF/OpenCV/NISHAN, vanilla HTML/CSS/JS, optional Android platform-tools for USB forwarding.

**Spec:** `docs/NISHAN_INTERACTIVE_DEMO_SPEC.md`

## Global Constraints

- No existing core or saved evidence changes; keep all 19 saved code hashes valid.
- Preserve n=1000, c=5, m=52500 and threshold 2100; do not tune on uploaded photos.
- Only exact known source bytes permit a definite unmarked-original result.
- Public fixture sessions are unsigned synthetic labels, not verified employees.
- Photos never receive strict PDF-source corroborated attribution.
- Default server 127.0.0.1:8765; 25 MiB upload, 40 million image pixels, one worker, 20 completed jobs.
- No secrets/uploads in Git, no CDN/cloud dependencies, no arbitrary file serving.
- No old research continuation. User authorizes the final reviewed push to main.

---

### Task 1: Implement and test the complete interactive demonstration

**Files:**
- Create: `prototypes/nishan_pq/demo_app/__init__.py`
- Create: `prototypes/nishan_pq/demo_app/engine.py`
- Create: `prototypes/nishan_pq/demo_app/public_fixture.py`
- Create: `prototypes/nishan_pq/demo_app/server.py`
- Create: `prototypes/nishan_pq/demo_app/static/index.html`
- Create: `prototypes/nishan_pq/demo_app/static/mobile.html`
- Create: `prototypes/nishan_pq/demo_app/static/style.css`
- Create: `prototypes/nishan_pq/demo_app/static/app.js`
- Create: `prototypes/nishan_pq/demo_app/tests/test_engine.py`
- Create: `prototypes/nishan_pq/demo_app/tests/test_server.py`
- Create: `prototypes/nishan_pq/tools/run_interactive_demo.py`
- Create: `prototypes/nishan_pq/INTERACTIVE_DEMO.md`
- Modify: `.gitignore`, `README.md`, `CONTINUE_HERE.md` (new entry point/current public visibility only).

**Interfaces:**
- Read the binding spec `docs/NISHAN_INTERACTIVE_DEMO_SPEC.md` in full first.
- Consume existing `tardos.parameters/generate_keyed/accusation_scores/accuse`,
  `tardos_carrier.decode_word_with_diagnostics`, `live_pdf.read_carrier/decode_carrier`
  and `layout_tag` APIs without changing them.
- Public secret is SHA3-256 of the literal bytes
  `NISHAN Tardos carrier public fixture v1`; codebook context
  `public-benchmark-codebook/v1`, carrier context
  `synthetic-source/full-tardos-profile-v1`, fixture row 0,
  session `public-fixture-session-0000`. See the existing benchmark for the
  layout context and magnitude, never invent a new fixture binding.
- Consume existing real `core.encrypt_once`, `core.decrypt_and_attribute`,
  `core.trace_leak`, `identity.create_identity`, `ledger.initialize/audit`,
  `witness.initialize/checkpoint` only inside optional signed mode.
- Produce `DemoEngine(workspace, state_dir).analyze(path, mode)` and
  `.prepare_signed()` and the exact HTTP route/result contract from the spec.

- [x] **Step 1: Write focused failing tests for the detector and result policy.**

Start with real public source and marked fixtures, not mocked success scores:

```python
def test_source_is_exact_known_original(self):
    result = self.engine.analyze(self.root / 'artifacts/nishan/synthetic-source.pdf', 'public')
    self.assertEqual(result['kind'], 'known_original')
    self.assertEqual(result['recipients'], [])

def test_public_fixture_is_not_a_signed_identity(self):
    result = self.engine.analyze(self.root / 'artifacts/nishan/dual-carrier-user-0000-live-text.pdf', 'public')
    self.assertEqual(result['kind'], 'fixture_match')
    self.assertNotEqual(result['assurance'], 'verified_signed_session')
    self.assertEqual(result['recipients'][0]['session_id'], 'public-fixture-session-0000')
```

Also create an actual raster from the marked PDF and require a research lead
or inconclusive, never `verified_session` or a signed identity. A blank/unrelated
image must not produce a named match. Renaming a marked PDF to a JPEG suffix
must not alter its content-based evidence decision. Add explicit no-PQC and
multi-page/oversize/malformed-input cases. For signed mode, prepare actual
Alice/Bob copies and trace them; validate persistent state reuse on restart.

Run (use the source machine's interpreter through the absolute path):

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq /home/user_end4/MySpace/SIH/.venv/bin/python -m unittest discover -s prototypes/nishan_pq/demo_app/tests -p 'test_engine.py' -v
```

Expected RED: missing application modules before implementation. Record the
actual failing output in the implementation report.

- [x] **Step 2: Implement the engine, public decoder and lazy signed mode.**

Keep public material cached once per engine, scored across all 1,000 rows.
Only layout-and-visual set agreement produces a digital public fixture match;
the label explicitly remains unsigned. Exact known-source hashing is a separate
branch. No remembered expected scores are substituted for extraction. Use actual
registration diagnostics to reject unrelated/weakly aligned content; page
similarity alone never identifies a watermark. Unknown crossings/conflicts
return inconclusive rather than the nearest expected identity.

For signed mode, create a local run under ignored `.nishan-demo/`, copy the
synthetic reference, issue Alice/Bob with fresh identities and witness state,
and expose only PDF outputs. Keep original core APIs unchanged and persist the
current run pointer with a validated local basename. Do not rename an initialized
ledger directory if its config embeds absolute key paths. Protect private state
with filesystem permissions; avoid insecure fallback identities/PQC.

Use parsed input type and EXIF-corrected temporary image copies, retaining the
uploaded original. The signed PDF itself must remain byte-identical during
verification. Include evidence score/threshold, channel outcomes, file hash,
real elapsed time and limitations in results, not a decorative confidence %.

- [x] **Step 3: Write RED HTTP/security tests, then implement the bounded server and CLI.**

Create a test server on a dynamically selected loopback port, exercising real
HTTP requests. Assert status 403 for missing request token/cross-origin writes,
413 for advertised oversize bodies, and rejection of unknown fixture IDs and
traversal paths. Verify no request can download state/keys. Submit a real source
PDF as raw bytes, wait for its actual job, and assert the latest-job status
links to its `known_original` result. Exercise busy behavior and retained-job
limits with controllable engine timing, not arbitrary sleeps.

`run_interactive_demo.py` inserts its own project module directory into sys.path,
accepts `--host`, `--port`, `--state-dir`, defaults to loopback and ignored local
state, and prints the desktop/mobile URLs and shutdown instruction. `--help`
must work without importing fcntl-dependent core. Server serves only explicit
UI, job and fixture routes, applies request limits before allocating bodies,
has no permissive CORS, and uses one worker for preparation/analysis.

- [x] **Step 4: Implement the responsive desktop and phone views.**

Use the exact route contract in the spec. Status polling shares completed phone
uploads with the desktop. Display errors/unsupported input without clearing a
result into a false success. Keep file names HTML-safe. Include mode-specific
help and no-PQC feedback. Buttons download the existing original/dual fixtures
or prepare/download signed Alice/Bob copies. Prevent ambiguous overlapping jobs;
re-enable controls on completion/error and revoke preview object URLs.

Use a light canvas, navy typography, teal accents, accessible contrast and large
verdict cards. Make camera capture a separate simple `/mobile` workflow with
both camera-request and existing-file options. Do not rely on auto-saving phone
photos appearing immediately via USB/MTP.
Use the three-step Choose copy / Create leak / Inspect evidence story and
side-by-side reference/upload previews from the spec. Provide one-click Try
original, Try marked and Try screenshot actions by fetching actual allowlisted
fixture bytes and submitting them through the normal upload endpoint. The
screenshot is the existing public screenshot PNG, explicitly labelled a digital
transformation. In signed mode, allow Alice/Bob copy selection from the real
prepared fixture list; do not expose a UI control that selects the detector's
expected answer.

- [x] **Step 5: Document exact launch/phone commands and update entry points.**

Document:

```bash
git pull --ff-only
.venv/bin/python prototypes/nishan_pq/tools/run_interactive_demo.py
adb devices
adb reverse tcp:8765 tcp:8765
# Android phone browser: http://127.0.0.1:8765/mobile
# Disconnect after use:
adb reverse --remove tcp:8765
```

Explain USB debugging/trusted-computer authorization, phone/browser variation,
Windows/WSL limitations, optional trusted-LAN/manual-file fallback, and the need
for compatible OpenSSL for the signed demo. No promises of physical success or
zero upload/processing delay. Explain existing prints vs fresh signed copies
and why the latter need reprinting for their own session identity. Add ignored
local state to `.gitignore`; update README/CONTINUE_HERE to point to this guide
and correct their current repository visibility to public without rewriting
historical evidence JSON.

- [x] **Step 6: Run focused suite, existing regressions and self-review; commit.**

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq /home/user_end4/MySpace/SIH/.venv/bin/python -m unittest discover -s prototypes/nishan_pq/demo_app/tests -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq /home/user_end4/MySpace/SIH/.venv/bin/python -m unittest discover -s prototypes/nishan_pq/tests -v
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=prototypes/nishan_pq /home/user_end4/MySpace/SIH/.venv/bin/python submissions/SIH26237_NISHAN_PQ/verify_submission.py --root . --allow-placeholders
git diff --check
```

The controller performs browser validation and task/final reviews, then merges
and pushes only after they pass. Implementer commits only the named feature
files, does not merge/push, and does not spawn agents. Report exact tests run,
actual RED/GREEN results, any warning/error and private-state exclusions.
