# NISHAN interactive judge demonstration

Date: 15 September 2026. User requests a browser-based photo/PDF upload demo,
phone-to-laptop transfer over USB if supported, and a GitHub push when verified.

## Binding requirements

- Add an offline, dependency-light browser UI; no cloud services, CDN assets or
  model downloads. Preserve the existing NISHAN core and saved evidence hashes.
- Use actual existing watermark extraction. Never infer a watermark from a
  filename, selected recipient, button choice, page similarity or a stored
  expected answer. Do not lower the existing 2,100 visual score threshold.
- Only an exact hash match to the known unmarked source permits the label
  "Known original — no watermark". A photograph without a recovered signal is
  "Inconclusive — no reliable watermark recovered", not proof of no watermark.
- Distinguish the public fixture from a signed release. Existing printed
  `artifacts/nishan/dual-carrier-user-0000-live-text.pdf` uses the public fixture
  key/contexts in `tools/benchmark_tardos_pdf.py`, row 0 and the documented
  synthetic session `public-fixture-session-0000`. It has no recipient-signed
  ledger record. Label its row as "Demo recipient 0000" and its session as a
  fixture session, never as a real employee or verified signed session.
- Support actual signed Alice/Bob copies prepared with existing ML-KEM,
  ML-DSA, core release, ledger and pinned witness APIs. Their UUID sessions and
  identities must come from the verified trace output. If PQC or the platform
  is unavailable, disable preparation with a clear error; public-fixture
  analysis must remain usable without importing the fcntl-dependent core.
- A photo/raster can provide an explicitly labelled research lead but never the
  PDF-source strict corroborated verdict. Keep visual and layout channels,
  signature verification and exact file identity as separate visible facts.
- Do not claim physical robustness, mathematical certainty, human guilt,
  independent administrators, or actual-device USB testing that was not done.
- Preserve the current one-page scope. Accept JPEG, PNG, WebP and PDF by actual
  parsing, not suffix alone. Explain unsupported HEIC, malformed, encrypted or
  multi-page input. Apply EXIF orientation to image decoding. Never overwrite
  uploaded originals or re-encode a signed PDF before verification.
- Default server binding: 127.0.0.1:8765. Optional explicit LAN binding may be
  documented for a trusted network, with a local-demo/not-production warning.
  No public tunnels, shell execution from requests or arbitrary file serving.
- Bound request bodies to 25 MiB, decoded images to 40 million pixels, and
  preview images to a reasonable display size. Use one processing worker,
  reject overlapping long jobs with a readable busy response, and keep at most
  20 completed jobs/files. Check Content-Length before reading a body.
- Require a per-server random request token and same-origin checks for
  mutating browser requests. No permissive CORS. Bind-local Host checks protect
  against DNS rebinding. Server files/routes must be allowlisted; do not trust
  uploaded filenames as filesystem paths. Render user strings with textContent.
- Uploads, keys, run state and browser-test recordings stay in ignored local
  storage or /tmp. Publish only safe source, documentation and test evidence.
- USB workflow must send a chosen/captured photo from the phone browser directly
  to this server and make it appear automatically on the desktop, without
  requiring MTP browsing. Document Android adb reverse and authorization,
  latency limitations and fallbacks; do not automate phone permissions.
- The public repository is https://github.com/ashebbar-dev/SIH. User authorizes
  pushing the completed feature to main after review and verification. Do not
  restart old research agents, experiments or the separate Codex session.

## UI and API design

Create a polished, readable light interface with navy/teal accents, responsive
desktop/mobile layout and no decorative fake confidence. Main view contains:
mode selector (Existing print / Signed demo), upload/drop zone, incoming-photo
status, uploaded-page preview, large plain-language verdict, recipient/session
cards when evidence supports them, and expandable signal/signature details.
Always show the short limitation about photographs. Include fixture download
buttons and a clear button to prepare fresh signed copies for the digital backup.
Use a three-step story: Choose a copy / Create a leak / Inspect the evidence.
Add one-click Try original, Try marked and Try screenshot buttons. These must
fetch real allowlisted fixtures and submit their bytes through the normal
analysis API, never substitute precomputed results. Screenshot is a labelled
digital transformation, not a simulated successful physical photograph.
Show the known source and uploaded preview side by side on desktop. After signed
preparation, let the judge choose Alice or Bob's actual issued PDF as the test
copy and show the recipient/session only from analysis evidence.

Phone view `/mobile` has a prominent Take photo button using
`<input type="file" accept="image/*" capture="environment">`, a normal Choose
photo fallback, mode selection and upload/result status. This is a browser
request for camera capture; exact behavior depends on the phone/browser.
Desktop polling must discover phone submissions automatically. Show the actual
duration, not simulated progress.

Use stdlib HTTP server + existing Python libraries; vanilla HTML/CSS/JS assets.
No new npm/runtime packages are required. Separate detector/policy, HTTP job
handling, launch CLI and UI assets. Keep files focused, preferably under 450
lines each; split detector helpers into a named companion file if needed and
record the reason in the implementation report.

Routes (implementation may add only specific static/download routes):

- GET `/`, `/mobile`, `/static/app.js`, `/static/style.css`.
- GET `/api/status`: public capabilities, fixtures, latest job ID and CSRF token.
- POST `/api/analyze?mode=public|signed`: raw file bytes, X-Nishan-Token and
  X-File-Name headers; returns 202 + job ID. A mode chooses a decoding context,
  never an expected identity or output verdict.
- POST `/api/prepare`: prepares or returns the current valid signed demo,
  asynchronously through the same bounded worker.
- GET `/api/jobs/<id>`: queued/running/done/error and a JSON-safe result.
- GET `/api/jobs/<id>/preview`, `/api/jobs/<id>/report`: allowlisted per-job assets.
- GET `/api/fixtures/<id>`: only known public/current signed PDFs and the existing
  `artifacts/nishan/dual-carrier-user-0000-screenshot.png`, as attachments.

`DemoEngine(workspace: Path, state_dir: Path)` owns public material and the
optional signed fixture. `analyze(path: Path, mode: str) -> dict` returns a
stable result with `kind`, `title`, `summary`, `assurance`, `recipients`,
`channels`, `diagnostics` and `limitations`. `prepare_signed() -> dict` uses
fresh state and persists it safely; reusing the same state directory preserves
the session context needed to trace its earlier issued prints.

`kind` values: `known_original`, `fixture_match`, `verified_session`,
`research_lead`, `inconclusive`. HTTP/input errors are errors, not these verdicts.
`recipients` are empty for inconclusive/known-original. `fixture_match` must
clearly say public test fixture and signature unavailable; `verified_session`
requires actual `core.trace_leak` corroboration and signature/witness checks.
Signed traces with visual-only evidence remain `research_lead`. In public
mode, digital PDF layout corroboration uses the same public contexts as the
benchmark; raster matches remain research leads. Multiple conflicting or
unregistered row crossings must not become a single named recipient.

## Verification

Tests must include real fixture extraction, exact-source detection, renamed
files, unrelated/blank inputs, raster-only non-promotion, no-PQC behavior,
malformed/oversized uploads, path traversal, missing token/cross-origin requests,
bounded worker/history behavior and status synchronization. A full signed
integration test may skip only with an explicit no-PQC reason. Separately run
it on this source machine, where required PQC is available.

Browser validation must exercise both desktop and mobile viewport layouts,
actual upload/status/result transitions and a phone-route-to-desktop job update.
Recorded/browser tests do not constitute a real USB/phone hardware test.
