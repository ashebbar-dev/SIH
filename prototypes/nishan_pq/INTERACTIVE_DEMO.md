# NISHAN interactive judge demonstration

This is the primary, offline browser demonstration for NISHAN. It accepts an
actual one-page PDF or JPEG/PNG/WebP image, extracts the existing watermark
channels, and presents only the verdict those channels support. It uses no
cloud service, CDN, model download or mocked answer.

## Launch on the prepared Linux laptop

From the repository root:

```bash
git pull --ff-only
.venv/bin/python prototypes/nishan_pq/tools/run_interactive_demo.py
```

Open <http://127.0.0.1:8765/>. Press `Ctrl+C` in the terminal to stop the
server. The default binding is loopback-only, request bodies are limited to
25 MiB, and private signed-demo state is stored under ignored `.nishan-demo/`.
Analysis can take a few seconds; the interface reports the measured duration
and does not simulate progress or promise zero delay.

Uploaded bytes and generated preview/report files are temporary job artifacts.
Only the newest 20 completed jobs are retained while the server runs, and
owned orphan job files are removed when it next starts. Signed identities,
ledger, witness and issued PDFs are a separate persistent run and are not
removed by that cleanup.

The fastest judge flow is:

1. Click **Try original**. The real published source is uploaded and can be
   called known-original only because its SHA3-256 bytes match exactly.
2. Click **Try marked**. The real public fixture PDF is uploaded; the result
   requires agreement between its visual row and editable-PDF layout tag.
3. Click **Try screenshot**. This is the existing public PNG, explicitly a
   digital transformation. Even a recovered visual signal remains a research
   lead because a raster has no PDF layout channel.
4. Select **Signed demo**, click **Prepare Alice + Bob**, then inspect either
   actual issued PDF. Preparation uses the existing ML-KEM-768, ML-DSA-65,
   signed receipt, quorum-ledger and pinned-witness code.

You can also drag or choose a file. Unsupported HEIC, malformed/encrypted PDFs,
multi-page documents, files over 25 MiB and images over 40 million decoded
pixels are rejected as input errors rather than displayed as evidence verdicts.

## Send a phone photo directly over USB

This workflow avoids waiting for a camera file to appear through MTP. On the
laptop, launch the server as above. Connect an Android phone with USB debugging
enabled, accept its trusted-computer/RSA authorization prompt, then run:

```bash
adb devices
adb reverse tcp:8765 tcp:8765
```

The device must appear as `device`, not `unauthorized`, in the first command.
In the phone browser open:

```text
http://127.0.0.1:8765/mobile
```

Use **Take photo** (a browser request for `capture=environment`) or **Choose
existing photo**, select the mode, and submit. The browser sends the selected
bytes directly to the laptop server, and desktop status polling discovers the
same job automatically. Exact camera-picker behavior, permission prompts and
latency vary by Android version and browser. This code has not been claimed as
an actual-device USB test and it does not automate phone permissions.

Disconnect the reverse mapping after the demonstration:

```bash
adb reverse --remove tcp:8765
```

The Android platform documentation explains [accessing a local development
server through `adb reverse`](https://developer.android.com/develop/ui/views/layout/webapps/access-local-server)
and the [`adb` device/authorization workflow](https://developer.android.com/tools/adb).

## Existing print versus fresh signed copies

The already printed
`artifacts/nishan/dual-carrier-user-0000-live-text.pdf` is deliberately public
fixture row 0, using session `public-fixture-session-0000`. Its UI label is
**Demo recipient 0000**. It has no recipient-signed ledger record and must not
be described as Alice, Bob, a real employee, or a verified signed session.

The optional Alice/Bob button creates fresh identities, session UUIDs, released
PDFs and witnessed ledger state locally. Reusing `.nishan-demo/` preserves the
same current run so an earlier issued copy remains traceable after a restart.
Deleting that private state loses its trace context. Freshly prepared copies
contain different session identities, so physical use requires printing those
new PDFs; an old public print cannot become Alice or Bob by selecting a UI mode.

Signed mode needs a compatible system OpenSSL with ML-KEM-768 and ML-DSA-65.
When unavailable, preparation is disabled with an explanation and the public
fixture remains usable. There is no classical or insecure fallback.

## Physical-result boundary

A photograph can provide an explicitly labelled visual **research lead**, but
never the strict signed-PDF corroborated verdict. A score below threshold is
**Inconclusive — no reliable watermark recovered**, never “proven unmarked.”
Only an exact source-file hash permits **Known original — no watermark**.

The demonstration does not claim robust recovery from every print/photo,
mathematical certainty, guilt or intent, proof that a recipient read a file, or
independent administration of keys stored on this laptop. Preserve the camera's
original file; messaging apps and document scanners may resize, enhance or
recompress it.

## Fallbacks and non-loopback use

If USB debugging or `adb reverse` is unavailable, choose the original photo on
the laptop after a normal cable/manual transfer. A trusted-LAN fallback is:

```bash
.venv/bin/python prototypes/nishan_pq/tools/run_interactive_demo.py --host 0.0.0.0
```

Then open the laptop's LAN IP and port 8765 from the phone. This local demo
server is not production-hardened: use that option only on a trusted network,
never expose it through a public tunnel, and return to loopback afterward.
Firewall setup and the laptop IP differ by network.

The supported build target is the prepared Linux system. WSL USB/port routing
depends on the Windows/WSL version and is not verified here; native Windows
Python is not supported because the existing ledger uses `fcntl`. On another
laptop, recreate the pinned Python environment and compatible OpenSSL before
the event rather than changing dependencies during the demonstration.
