# Dhruva reference-quality findings — 10 September 2026

## New finding and its scope

The timestamp-corrected evaluator is numerically consistent, but its GPS
reference-speed labels are not uniformly trustworthy. In S1, raw reference
row1379 reports zero GPS satellites and zero GPS speed while the separately
recorded indicated vehicle speed remains64.01km/h. All71 S1 zero-satellite
rows enter the manifested speed-training set. This was found during a
read-only acceleration/calibration feasibility probe, not by choosing windows
to improve navigation results.

This does **not** establish that bad reference labels explain the large
remaining transfer error. No S1 valid evaluation outage contains a
zero-satellite row, and71 rows are only a small part of the20,495 training
samples. Other reference-quality problems are possible, but must be measured.
Do not erase or relabel prior benchmark results, silently drop test windows,
or replace GPS coordinates with vehicle speed and call it position truth.

The [dataset paper](https://arxiv.org/pdf/2005.01701), PDF page3 (zero-based2), explicitly reports
GPS reception outages and refers to a separate “GPS outages” file. Its Table3
distinguishes satellite count, GPS velocity and indicated vehicle speed. No
matching outage annotation was found in the locally extracted subset; an
independent check verified the numerical witnesses and counts. The current
repository tree has916 entries, `truncated=false`, at treeSHA
`118939602e3422d47b8ab0807b623751c3ac135b`; no separately tracked path matches
outage/GPS/index/annotation. ZIP contents and historical versions were not
inspected, so archive-only or historical availability remains unresolved.

## Exact witness

Zero-based CSV data rows exclude the header. Source is the unchanged
`S1/V-S1.csv` under the data root recorded in the current aligned manifest.

| Raw row | Time of day, s | Satellites | GPS speed, km/h | Indicated vehicle speed, km/h |
|---|---:|---:|---:|---:|
| 1371 | 33006.1 | 0 | 0 | 63.89 |
| 1372 | 33006.2 | 4 | 4.226 | 63.88 |
| 1379 | 33006.9 | 0 | 0 | 64.01 |
| 1380 | 33007.0 | 4 | 11.894 | 64.11 |
| 1389 | 33007.9 | 10 | 63.385 | 64.01 |

At row1379, differencing the GPS speed over the preceding1s yields
−25.54m/s². This is not a credible ordinary longitudinal acceleration label
given the simultaneous near-constant indicated vehicle speed. The neighboring
four-satellite samples are also substantially inconsistent, so excluding only
exact-zero satellite rows is not a complete reference-quality solution.

Reproduce the witness without changing any input:

```sh
sed -n '1373,1382p' '/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/V-S1.csv' | cut -d, -f1,2,5,16
```

## Scope in the existing frozen manifest

These counts use the already frozen `dhruva-aligned-2026-09-10-2/manifest.json`.
They do not define new exclusions. An outage includes both raw endpoints when
checking reference quality.

| Sequence | Raw reference rows | Zero-satellite rows | Valid outages | Valid outages containing zero-satellite rows | Outages with zero-satellite initial/endpoint |
|---|---:|---:|---:|---:|---:|
| S1 | 51746 | 71 | 48 | 0 | 0 |
| S2 | 93876 | 0 | 144 | 0 | 0 |
| S3a | 24621 | 2 | 37 | 1 | 0 |
| S4 | 94600 | 3 | 141 | 2 | 0 |

There are no1–3-satellite rows in these four raw files, so the zero and
under-four counts coincide. Every zero-satellite row has indicated vehicle
speed above5km/h; that does not mean its GPS speed is always zero. In S1 all71
such rows are among the20,495 manifested training rows.

The independent check localizes the affected evaluation samples to S3a
rows14660–14661 in window`S3a:raw-14400-15000`, S4 row57034 in
`S4:raw-57000-57600`, and S4 row65225 in`S4:raw-64800-65400`. S4's third
zero-satellite row93950 is in an already gap-excluded candidate. Checking
half-open outage intervals instead of including endpoints gives the same
counts here because no endpoints are flagged. In S1,55 of the71 flagged
rows have zero GPS speed and16 retain nonzero GPS speed.

Additional descriptive comparison, absolute GPS-vs-indicated speed difference:

| Sequence / satellite bin | Rows | Median difference, km/h | P95 difference, km/h | Maximum difference, km/h |
|---|---:|---:|---:|---:|
| S1 / zero | 71 | 25.000 | 32.545 | 64.010 |
| S1 / four | 31 | 20.256 | 51.473 | 59.654 |
| S1 / five–seven | 163 | 0.341 | 18.180 | 27.723 |
| S1 / eight or more | 51481 | 0.271 | 1.043 | 19.763 |
| S2 / eight or more | 93831 | 0.253 | 0.987 | 10.890 |
| S3a / eight or more | 23956 | 0.290 | 0.994 | 5.491 |
| S4 / eight or more | 84621 | 0.248 | 1.060 | 11.185 |

These are literal raw-field bins, not a chosen quality threshold. Values132–140
also occur; their encoding in this CSV export is unresolved, so the eight-or-more
bin is not a certified satellite-count or high-quality category. The independent
[full audit](DHRUVA_REFERENCE_QUALITY_AUDIT_2026-09-10.md) records that limitation.
CAN/indicated
speed has its own calibration, quantization, slip and timing limitations; it
is a corroborating channel, not certified ground truth. High satellite count
alone also does not prove reference accuracy.

## Probe that exposed the issue

The root used the reviewed timestamp loader and stored clock offsets, only
the initial aligned segment, and rows after the200-row warmup within both
recorded raw140s clock prefixes. One-second time-weighted means of the three
phone accelerometer channels plus an intercept were fitted by least squares
to one-second GPS-speed differences. The first half of eligible prefix rows
was used for fitting, the second half for this diagnostic check. No navigation
outage was evaluated and no production model or evidence file was modified.

| Sequence | Fit/check samples | Check correlation | Check RMSE, m/s² | Zero-acceleration RMSE, m/s² |
|---|---|---:|---:|---:|
| S1 | 599 / 599 | 0.126 | 3.167 | 3.191 |
| S2 | 562 / 563 | 0.462 | 0.652 | 0.737 |
| S3a | 566 / 566 | 0.412 | 0.717 | 0.660 |
| S4 | 591 / 591 | 0.822 | 0.346 | 0.522 |

The S1 anomaly prompted inspection of raw reference metadata rather than a
conclusion that its accelerometer was unusable. These overlaps are not
independent validation samples; clock estimation used the whole140s prefix,
and these journeys are already development data. Neither fitting nor this
check supports a field-performance claim.

### Same-row comparison with indicated vehicle speed

After the GPS anomaly was identified, the identical fitting/check rows and
unchanged regression were compared using the indicated-speed derivative as
the target. All exact raw row lists and coefficients are retained in
[label-comparison evidence](evidence/dhruva-prefix-acceleration-labels-2026-09-10.json).
The GPS control reproduces the first probe numerically.

| Sequence | Indicated-label check correlation | Check RMSE, m/s² | Zero-acceleration RMSE, m/s² |
|---|---:|---:|---:|
| S1 | 0.506 | 0.646 | 0.694 |
| S2 | 0.561 | 0.606 | 0.735 |
| S3a | 0.391 | 0.727 | 0.656 |
| S4 | 0.842 | 0.337 | 0.525 |

S1's extreme GPS-target residual is much smaller with this corroborating
channel, but the simple regression is still only modestly better than zero
acceleration there and is worse than zero acceleration on S3a. This is not
evidence for deploying constant-axis acceleration integration or for replacing
the reference trajectory. Different targets are not a matched navigation
performance improvement.

## Next action

Independent verification of the raw witnesses, metadata coverage and current
repository annotation search is complete in the
[full audit](DHRUVA_REFERENCE_QUALITY_AUDIT_2026-09-10.md). The same-row
indicated-speed comparison above is also complete. Next predeclare a
reference-quality sensitivity analysis
that leaves the current evidence untouched. It should distinguish corrupted
training targets, invalid initialization/endpoint references and invalid
distance denominators. Keep indicated speed a corroborating channel, not
replacement position truth. Do not train a new large
model or claim a score improvement before this distinction is understood.

The successful final code review of the existing aligned experiment remains
valid for its stated arithmetic/spec scope. Data-source validity is an
additional requirement, not something passing unit tests can establish.

### Independent next-study recommendation, not executed

A bounded design review recommends a speed-only comparison on all370 existing
valid window IDs: unchanged absolute-speed estimation, its outage-start offset
control, and acceleration-based propagation from the same privileged initial
speed. Compare the full frozen S1 training set with a literal-zero-flag
sensitivity arm; for an acceleration target, flag its entire differencing
support. This is not a clean-label certificate. Preserve all evaluation
windows, constant-speed and reference-speed controls, and use reference heading
only to isolate speed. Indicated-speed agreement remains corroboration, not
truth. No such model has been fitted or evaluated; the exact target/integration
alignment and decision criteria require a separate fixed implementation plan.
