# Dhruva reference-quality audit — 10 September 2026

S1 contains reference-speed/coordinate disagreement around zero-satellite records and also in adjacent intervals whose minimum raw satellite value is four. All 71 zero-satellite S1 rows entered the manifested speed-training set, but this audit cannot determine their contribution to the model's total error. The existing numerical ablation remains an exploratory result with reference-quality limitations.

This is a separate no-fit audit. It performed no regression, model training or model inference and did not rerun existing tests. Benchmark exclusions, source files and previous results were preserved. Exact measurements, overlap indices, rejected time intervals and neighborhoods are retained in [the machine-readable audit](evidence/dhruva-reference-quality-2026-09-10.json).

## Fixed definitions and accounting

For every raw endpoint i from 10 to the final row, use the eleven coordinate samples i−10 through i and their actual VBOX time differences. The coordinate endpoint speed is the great-circle distance between the two endpoints divided by elapsed time, converted to km/h. Distances use the haversine formula with Earth radius 6,371,000 m. GPS and indicated-vehicle speed means use the same ten intervals: sum(v[j] × (t[j+1]−t[j])) / (t[i]−t[i−10]), for j=i−10,…,i−1.

Before numerical inspection, strata were fixed as minimum satellite value across all eleven endpoints: 0, 1–3, 4, 5–7, and >=8. No speed discrepancy or model error selects intervals. The nominal cadence is 0.1 s, nominal duration 1 s, with inclusive 0.001 s tolerances applied using floating-point subtraction. Nonfinite, nonpositive, cadence and duration failures are recorded separately; they are never silently coerced into a 1 s interval.

| Sequence | Raw rows | One-second candidates | Accepted by strict time check | Separately retained time flags | Neighborhood rows |
|---|---:|---:|---:|---:|---:|
| S1 | 51746 | 51736 | 51725 | 11 | 565 |
| S2 | 93876 | 93866 | 93855 | 11 | 0 |
| S3a | 24621 | 24611 | 24611 | 0 | 202 |
| S4 | 94600 | 94590 | 94590 | 0 | 603 |

Totals: 264,843 raw rows, 264,803 one-second candidates, 264,781 accepted intervals, 22 time flags and 40 initial rows without ten-row history. No nonpositive or nonfinite time interval was found. All 22 flags surround just two raw timestamps: S1 row 31881 (36057.101 s) and S2 row 18691 (41693.501000000004 s). The neighboring spacings are nominally 0.101/0.099 s. Binary subtraction exceeds the 0.001 s boundary by less than 1e-11 s; these are strict-float tolerance flags, not evidence of substantial timing gaps. Their exact endpoints, duration, ten dt values and all triggered reasons remain in JSON. The existing benchmark's exclusions were not changed.

Adjacent one-second intervals share nine of ten integration intervals and ten of eleven coordinate endpoints. Counts describe coverage, not independent statistical observations. No confidence interval or significance claim is made.

## Satellite-field encoding uncertainty

The header calls column 0 the number of GPS satellites, but the raw files also contain values 132–140. For example, S1 row 5982 has 140; S2 row 1228 has 139. Each complete raw-value histogram is retained in JSON.

Racelogic's general .VBO documentation describes adding 128 for DGPS use and 64 for an active brake trigger. Thus 132–140 is consistent with a status flag plus a smaller satellite count. This is a documented possible explanation, not a verified decoding of this export. [Racelogic .VBO file format](https://racelogic.support/knowledge-bases/general-kb/vbo-files/).

The HD2-specific serial and legacy CAN documents describe a satellite-number field, but neither establishes the conversion used to produce these IO-VNBD CSVs. Exact export and firmware provenance remain unresolved. Accordingly, all requested strata use literal raw values, no bits are removed, and >=8 must not be called a certified high-quality satellite group. [HD2 serial protocol](https://en.racelogic.support/motorsport/video-data-loggers/vbvdhd2/kb/vbox-video-hd2-serial-rs232-protocol/), [HD2 CAN format](https://racelogic.support/automotive/discontinued-legacy/data-loggers/vbox-video-hd2-v12-v6-v5-v1/vbox-video-hd2-v1-5/technical/can-output-format/).

## Speed consistency

Every discrepancy entry is median / p95 absolute difference in km/h. C is coordinate endpoint speed, G is the time-weighted GPS mean, and I is the time-weighted indicated-vehicle mean. Empty strata remain explicit and have no numerical statistic.

| Sequence | Minimum raw satellite value | Intervals | abs(C−G), median / p95 | abs(C−I), median / p95 | abs(G−I), median / p95 |
|---|---|---:|---:|---:|---:|
| S1 | 0 | 137 | 4.777 / 76.365 | 6.950 / 57.701 | 14.823 / 30.918 |
| S1 | 1-3 | 0 | — | — | — |
| S1 | 4 | 29 | 29.461 / 35.592 | 26.374 / 47.898 | 15.154 / 18.832 |
| S1 | 5-7 | 246 | 0.226 / 2.824 | 0.262 / 15.215 | 0.316 / 13.484 |
| S1 | >=8 | 51313 | 0.194 / 0.734 | 0.283 / 0.841 | 0.245 / 0.894 |
| S2 | 0 | 0 | — | — | — |
| S2 | 1-3 | 0 | — | — | — |
| S2 | 4 | 0 | — | — | — |
| S2 | 5-7 | 65 | 1.005 / 5.125 | 0.766 / 2.688 | 0.419 / 5.280 |
| S2 | >=8 | 93790 | 0.185 / 0.763 | 0.261 / 0.783 | 0.227 / 0.829 |
| S3a | 0 | 12 | 0.118 / 0.244 | 1.489 / 1.673 | 1.473 / 1.795 |
| S3a | 1-3 | 0 | — | — | — |
| S3a | 4 | 0 | — | — | — |
| S3a | 5-7 | 914 | 0.151 / 0.764 | 0.291 / 1.263 | 0.275 / 1.090 |
| S3a | >=8 | 23685 | 0.163 / 0.608 | 0.329 / 0.798 | 0.265 / 0.756 |
| S4 | 0 | 33 | 0.275 / 1.610 | 0.332 / 7.751 | 0.291 / 6.522 |
| S4 | 1-3 | 0 | — | — | — |
| S4 | 4 | 0 | — | — | — |
| S4 | 5-7 | 10812 | 0.223 / 0.919 | 0.385 / 1.294 | 0.287 / 1.157 |
| S4 | >=8 | 83745 | 0.174 / 0.726 | 0.276 / 0.918 | 0.225 / 0.868 |

S1's minimum-four group has only 29 overlapping intervals, with coordinate-versus-GPS discrepancy 29.461 / 35.592 km/h and coordinate-versus-indicated discrepancy 26.374 / 47.898 km/h. Its minimum-zero group has 137 intervals and much wider tails. These observations support inspecting degraded-reference neighborhoods; they do not establish a universal satellite threshold. S3a's twelve minimum-zero intervals, for example, retain close coordinate/GPS agreement (0.118 / 0.244 km/h).

GPS coordinates and GPS velocity share a receiver, so agreement between them is not independent ground truth. Indicated vehicle speed supplies a separate recorded channel, but its calibration, timing and tire-dependent scaling are not established here. None of these pairwise differences by itself identifies the correct physical speed.

## Endpoint distance versus traveled path

A one-second endpoint displacement cuts across a turn; it is not traveled path length. For each same interval, the audit also sums the ten consecutive coordinate-step distances. This sum is at least the endpoint distance up to floating precision. The difference can reflect turning, coordinate jitter or jumps, so it cannot be interpreted as pure vehicle curvature.

| Minimum raw satellite value, pooled | Intervals | Path−endpoint speed km/h, median / p95 | Path−endpoint distance m, median / p95 | Percentage deficit, median / p95 | Positive-path intervals |
|---|---:|---:|---:|---:|---:|
| 0 | 182 | 0.245 / 5.050 | 0.068 / 1.403 | 0.869 / 14.925 | 174 |
| 1-3 | 0 | — | — | — | 0 |
| 4 | 29 | 0.111 / 0.361 | 0.031 / 0.100 | 0.168 / 0.439 | 29 |
| 5-7 | 12037 | 0.006 / 0.117 | 0.002 / 0.032 | 0.014 / 1.386 | 12037 |
| >=8 | 252533 | 0.007 / 0.139 | 0.002 / 0.039 | 0.023 / 27.246 | 252159 |

The literal >=8 group has a small absolute p95 path/endpoint difference of 0.139 km/h (0.039 m over one second), while its relative p95 is 27.246%. Relative differences become unstable when the coordinate path is almost stationary; the denominator is only required to be positive, and 374 exactly zero-path intervals are separately counted. The minimum-four group's path/endpoint p95 is only 0.361 km/h, far smaller than its speed-channel disagreement, so short-chord geometry alone does not account for that group's large discrepancies. Coordinate jumps can inflate both endpoint and path speeds; this remains a consistency check rather than reference validation.

## Zero-satellite overlaps with the frozen evaluation

Flags here mean raw column 0 equals zero, not a complete GNSS-validity mask. Training and prefix columns count unique raw rows. Calibration and outage cells show unique flagged raw rows / affected valid windows. The calibration history is exactly [start−1200,start), the outage is [start,end), and initial/endpoints are checked individually.

| Sequence | All zero-satellite rows | Speed training | Journey-prefix gyro fit | Initial / endpoint flagged windows | 1200-row calibration: rows / windows | Outage: rows / windows |
|---|---:|---:|---:|---:|---:|---:|
| S1 | 71 | 71 / 20495 | 18 / 1198 | 0 / 0 | 0 / 0 | 0 / 0 |
| S2 | 0 | 0 / 0 | 0 / 1125 | 0 / 0 | 0 / 0 | 0 / 0 |
| S3a | 2 | 0 / 0 | 0 / 1132 | 0 / 0 | 2 / 2 | 2 / 1 |
| S4 | 3 | 0 / 0 | 0 / 1182 | 0 / 0 | 2 / 4 | 2 / 2 |

All 71 S1 flags also overlap the frozen-S1 gyro fit because it uses the same raw rows as speed training. Eighteen overlap the S1 journey-prefix gyro fit. GPS-quality flags do not establish invalidity of the separately recorded CAN yaw channel. They are retained as overlap information, not a reason to discard gyro calibration automatically. Of S1's 71 flagged GPS-speed labels, 55 are zero and 16 are nonzero.

S3a rows 14660–14661 occur in outage S3a:raw-14400-15000 and in calibration histories for starts 15000 and 15600. S4 row 57034 occurs in outage S4:raw-57000-57600 and histories for starts 57600 and 58200; row 65225 occurs in outage S4:raw-64800-65400 and histories for starts 65400 and 66000. S4 row 93950 is in the already excluded S4:raw-93600-94200 candidate (missing_or_gap), so only two of its three flagged rows lie in valid outage intervals. No valid initial state or endpoint is zero-satellite flagged.

## Exact witnesses and retained neighborhoods

S1 raw row 1379 (CSV line 1381), time 33006.9 s, reports zero satellites and GPS speed 0 km/h while indicated speed is 64.01 km/h. Wheel-channel values are 63.98999, 63.56999, 64.09 and 63.31; the header labels them rad/sec, and their physical conversion remains unverified. Its manifested training record is segment 0, local index 1376, phone brackets 1376–1377. Neighboring rows 1378 and 1380 report four satellites: GPS speed is 37.912 and 11.894 km/h versus indicated 63.95 and 64.11 km/h. [Raw S1 witness](</tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S1/V-S1.csv:1381>).

Each zero-satellite contiguous raw span has a requested interval from exactly ten seconds before its first timestamp through ten seconds after its last timestamp, inclusive. The JSON retains every selected index per neighborhood and one deduplicated measurement record per raw row. Each record contains time, raw satellite value, latitude/longitude, GPS and indicated speed, plus the status, stratum and speed comparisons of the one-second interval ending there. No measured column has been repaired or interpolated.

| Sequence | Flagged raw span, inclusive | Neighborhood raw bounds, inclusive | Exact time bounds s | Selected rows |
|---|---|---|---|---:|
| S1 | 1287–1296 | 1187–1396 | 32987.7–33008.6 | 210 |
| S1 | 1308–1313 | 1208–1413 | 32989.8–33010.3 | 206 |
| S1 | 1371–1371 | 1271–1471 | 32996.1–33016.1 | 201 |
| S1 | 1379–1379 | 1279–1479 | 32996.9–33016.9 | 201 |
| S1 | 19323–19334 | 19223–19434 | 34791.3–34812.4 | 212 |
| S1 | 19340–19342 | 19240–19442 | 34793–34813.2 | 203 |
| S1 | 19346–19346 | 19246–19446 | 34793.6–34813.6 | 201 |
| S1 | 19348–19357 | 19248–19457 | 34793.8–34814.7 | 210 |
| S1 | 19368–19394 | 19268–19494 | 34795.8–34818.4 | 227 |
| S3a | 14660–14661 | 14560–14761 | 67574–67594.1 | 202 |
| S4 | 57034–57034 | 56934–57134 | 67866.8–67886.8 | 201 |
| S4 | 65225–65225 | 65125–65325 | 68685.9–68705.9 | 201 |
| S4 | 93950–93950 | 93850–94050 | 71558.4–71578.4 | 201 |

Overlapping neighborhoods share records. Their union is 565 S1 rows, 202 S3a rows and 603 S4 rows: 1,370 unique rows. S2 has no zero-satellite span. Full S3a/S4 flagged-row witnesses and all S1 zero-span bounds are retained in JSON.

## Published annotation availability

The paper says GPS communication difficulties occurred and describes an index file titled “GPS outages” on physical PDF page 3 (zero-based page 2). [IO-VNBD paper](https://arxiv.org/pdf/2005.01701).

The prior read-only recursive listing of the current public repository returned 916 entries, truncated=false, tree SHA 118939602e3422d47b8ab0807b623751c3ac135b. No path matched outage, gps, index or annotation. Two root ZIP archives exist, but neither their contents nor historical revisions were inspected. Therefore no separately tracked matching annotation was found; archive-only or historical availability remains unresolved. This audit reused that lookup and downloaded no dataset/archive. [Repository tree API](https://api.github.com/repos/onyekpeu/IO-VNBD/git/trees/master?recursive=1).

## Provenance, limits and next diagnostic

All four raw reference SHA-256 values match the frozen ablation manifest. The audit records hashes for that manifest, results.json and windows.csv, along with exact raw paths and hashes. It records all 22 strict-time failures rather than dropping their existence, and retains empty strata. No new quality exclusion policy was introduced.

The smallest next step is to establish the satellite-field export semantics and a reference-quality policy from acquisition information, then preregister any quality-aware sensitivity comparison. Preserve the original result and compare changes on fixed candidate IDs. The current evidence supports a reference-quality concern; it does not measure a clean-label refit's effect, explain total model error from 71 rows, or demonstrate navigation accuracy, novelty, field readiness or threshold compliance.

Verification passed: strict JSON parsing; candidate/stratum totals and raw satellite histograms reconcile; every selected neighborhood index has one retained measurement record; all flagged overlap indices are explicit. Post-write hashes confirm all four raw reference files and the existing manifest/results/windows artifacts remain unchanged.
