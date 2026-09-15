# NISHAN first physical capture — 10 September 2026

## Latest outcome

After all four supplied files were tested with the unchanged baseline, the
previously reviewed conditional-threshold rule recovered **only the correct
test recipient from akshay3.jpeg**, without selecting any other row. The
historical threshold failed on that same image. All other files still produce
no accusation. This is useful physical-capture progress from an established
decoder calibration, not a new watermark algorithm or a broad success rate.

Complete [conditional evidence](evidence/nishan-physical-conditional-2026-09-10.json)
retains all 1,000 scores for each file, input/helper hashes, thresholds and
finite-theta witnesses. An independent reviewer verified the stored-score
decisions, hash consistency and witness arithmetic. It did not independently
reconstruct image decoding or cumulants in that check.

## Baseline result

The user printed the test page and supplied `/home/user_end4/Downloads/akshay.jpeg`.
They confirmed it was captured with a **phone scanning app, Doc Scanner**, not
a flatbed/MFP scanner. The unchanged existing decoder recovered no recipient
and accused no other row. This is a retained failure, not a passing physical
robustness result.

| Metric | Observed |
|---|---:|
| Correct-row score | −49.933 |
| Highest other-row score | 203.301 |
| Existing threshold | 2100 |
| Accused rows | None |
| Decoded bit disagreement against expected row | 50.0038% |
| Exactly zero carrier correlations | 86.5981% |
| Content registration similarity, before → after | 0.445965 → 0.778345 |
| RANSAC inliers / accepted feature matches | 657 / 1045 |

This scan does not have the strong positive correct-row score found in the
earlier simulated white-clipping case. The earlier threshold improvement
therefore cannot be presented as a fix for this physical failure.

## Evidence and provenance

- [Baseline evidence](evidence/nishan-akshay-scan-2026-09-10.json).
- [Capture provenance and additional diagnostics](evidence/nishan-akshay-scan-provenance-2026-09-10.json).
- Aligned diagnostic preview: `artifacts/nishan/akshay-scan-2026-09-10-alignments/00-akshay-aligned.png`.
- Original capture is unchanged, 2093×2937 RGB JPEG, 197,184 bytes, no embedded
  EXIF or DPI metadata. Its SHA-256 is recorded in provenance.

The expected print was `artifacts/nishan/dual-carrier-user-0000-live-text.pdf`,
as previously requested. The visible page content matches the synthetic
fixture, but exact print settings and the physical file identity are not
independently verified. Public fixture keys are used; this is not production
secret-key security evidence. The raster test does not decode PDF content-stream
layout metadata from the photograph.

Exact run:

```sh
env PYTHONPATH=prototypes/nishan_pq .venv/bin/python \
  prototypes/nishan_pq/tools/score_physical_capture.py \
  /home/user_end4/Downloads/akshay.jpeg \
  --evidence research/evidence/nishan-akshay-scan-2026-09-10.json \
  --preview-directory artifacts/nishan/akshay-scan-2026-09-10-alignments
```

The evidence path was verified absent before running; preserve this result
instead of overwriting it with future decoder attempts. The existing runner's
wording about the marking condition is not a new soundness theorem: completeness
and soundness assumptions must be separated as in the conditional-threshold note.

## What the failure suggests, and what it does not prove

92.54% of original scan pixels are exactly white. Within source-white regions,
the digital marked PDF is 52.88% exactly white, whereas the aligned scan is
95.47% exactly white. Those regions include pixels near text and borders, so
residual registration errors can contaminate the comparison. The observation
is consistent with faint marks being removed, but does not identify whether
printing, app cleanup or both caused that removal. Registration improvement
also does not establish subpixel carrier alignment; geometry remains a
possible contributor.

The user has been asked for an ordinary-camera photograph of the **same sheet**,
outside Doc Scanner, with all four corners visible. This paired capture can
help distinguish app processing from printing/decoder failure. No reprint or
purchase has been requested. Tone-probe implementation is deferred while this
more relevant physical evidence is investigated; its saved plan remains
unexecuted.

One failed scan does not justify abandoning NISHAN. It identifies a concrete
physical-channel failure to diagnose and improve, with the current result
retained as the baseline.

## Second supplied image: camera capture shared through WhatsApp

The user then supplied `/home/user_end4/Downloads/akshay1.jpeg`, reported as
taken with the camera, and confirmed it was shared through WhatsApp. The file
is 912×1280 RGB JPEG, 51,219 bytes, with no EXIF or DPI metadata. Its original
camera dimensions and transfer settings are unknown. It is not a verified
unprocessed original.

The same unchanged decoder and settings again accuse nobody. Correct-row score
is −22.477, highest other-row score 168.563, threshold 2100, and decoded bit
disagreement 49.9676%. Registration similarity improves from 0.453086 to
0.729354, with 555/996 RANSAC inliers/matches. The median absolute carrier
correlation is zero. See [second baseline evidence](evidence/nishan-akshay1-camera-2026-09-10.json)
and [second provenance](evidence/nishan-akshay1-camera-provenance-2026-09-10.json).

Both supplied files fail the existing decoder. Neither failure proves that
Doc Scanner alone is responsible. WhatsApp transfer adds a possible resize/
compression stage, while print quality and finer alignment remain uncontrolled.
The user has been asked to transfer the existing original camera file as a
Document/file or by USB; no new photo or reprint is needed if it remains on
the phone. A failure after a verified unprocessed transfer must still be
retained, not explained away by capture quality.

## Third and fourth supplied images

The user supplied `akshay2.jpeg` and `akshay3.jpeg` after the request for an
original camera file. Both retain gray-paper variation rather than the nearly
pure-white background of the first two images. The third file is 898×1280,
61,129 bytes, no EXIF. The fourth is 1966×2784, 2,257,466 bytes, with Xiaomi
2311DRK48I and MediaTek Camera Application EXIF, orientation 1. It is still a
JPEG; metadata does not certify sensor-RAW or an untouched transfer history.
Neither file has any exactly white RGB pixel. No further photograph is needed
for this first diagnostic.

Their unchanged baseline results are retained together in
[akshay2/akshay3 baseline evidence](evidence/nishan-akshay2-akshay3-2026-09-10.json).
Both initially fall below the old threshold, with no accusations. Existing
decoder geometry, bits and scores were then reproduced for **all four files**
before the already reviewed conditional threshold was applied. This did not
optimize a cutoff against the known recipient or choose only the best image.

| File | Expected-row score | Highest other score | Old threshold | Conditional threshold | Conditional accused rows |
|---|---:|---:|---:|---:|---|
| akshay.jpeg | −49.933 | 203.301 | 2100 | 404.398 | None |
| akshay1.jpeg | −22.477 | 168.563 | 2100 | 437.549 | None |
| akshay2.jpeg | 683.938 | 604.472 | 2100 | 1006.056 | None |
| akshay3.jpeg | 1357.130 | 588.274 | 2100 | 1077.189 | Only row 0 |

The new run predeclared epsilon=10^-6 and H=4×1000=4000 for its four capture/
decoder tests. Each threshold depends only on the biases, decoded word and
fixed budget, not recipient scores. Its modeled bound is conditional on
independent innocent-row sampling; it is not a measured probability of wrongful
attribution, a certified bound for public deterministic keys, or a budget for
all earlier/future research. Repeated captures of one sheet are not independent
documents or independent codebooks. Production decision code remains unchanged.

For akshay3 the expected row is ranked first, 46.1067% of decoded bits disagree,
only 0.5295% of correlations are exactly zero, and median absolute correlation
is 21.9945. The mark therefore retains usable recipient information despite
substantial bit errors. This narrows the earlier suspicion: complete erasure
is not a valid explanation for this camera image. Finer registration, tone
modeling and more robust printed carriers remain candidate improvements.

Reproduce the conditional calculation with existing functions, fixing the four
filenames above and H=4000 before any scoring:

```python
from research.tools.probe_nishan_capture_channel import conditional_null_threshold
from nishan import tardos, tardos_carrier

# Use the public fixture secret and both contexts from score_physical_capture.py.
# Generate the same 1000-row, c=5, epsilon=1e-6 codebook once.
word, correlations, diagnostics = tardos_carrier.decode_word_with_diagnostics(
    source_path, capture_path, config.code_length, secret, carrier_context)
scores = tardos.accusation_scores(biases, codebook, word)
null = conditional_null_threshold(biases, word, 1e-6, 4000)
accused = [] if null['threshold'] is None else np.flatnonzero(
    scores > null['threshold']).tolist()
```

The run asserted that every expected-row score and maximum-other score matched
its earlier immutable baseline within 10^-9. The independent reviewer also
checked baseline bit-error fields and decisions. Next validation needs other
recipients, independent documents/codebooks, unmarked controls and repeat
physical captures, preserving failures rather than tuning on this one sheet.
