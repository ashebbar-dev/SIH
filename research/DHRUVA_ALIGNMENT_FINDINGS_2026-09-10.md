# Dhruva timing diagnosis — 10 September 2026

The existing 18.34% S1 result is not a lower bound on attainable drift. More seriously, the frozen-model transfer audit also inherits substantial timing errors: each journey has a different initial phone/VBOX offset, and S4 contains a five-minute phone logging gap that row-by-row pairing silently ignores. Those transfer numbers do not isolate learned-model generalization.

This note records read-only, in-memory calculations. No estimator, dataset, or existing result artifact was changed. The numbers below are exploratory diagnostics, not new navigation performance or evidence of novelty.

## Verified timestamp discontinuities

The smartphone CSV has these zero-based columns:

- Column 7: `TIME SINCE START (ms)`.
- Column 8: `DATE (YYYY-MO-DD HH-MI-SS_SSS)`; actual values use a colon before milliseconds.
- Columns 15–17: gyroscope Yaw/Pitch/Roll, in rad/s. These are the exact three columns selected by the original benchmark's `phone[:, 7:10]` after its initial column selection.

VBOX column 1 is time since start of day in seconds; column 8 is sample period in seconds. Its reference stream remains continuous at approximately 0.1 seconds at the boundaries below.

| Journey | Consecutive zero-based phone data rows | Earlier wall-clock time | Later wall-clock time | Wall-clock interval |
|---|---|---|---|---:|
| S2 | 1863 → 1864 | 2019-09-08 12:06:58:041 | 2019-09-08 12:06:59:249 | 1.208 s |
| S4 | 35185 → 35186 | 2019-09-06 19:14:53:611 | 2019-09-06 19:20:05:753 | 312.142 s |
| S4 | 90966 → 90967 | 2019-09-06 20:53:03:752 | 2019-09-06 20:53:05:016 | 1.264 s |

The elapsed-millisecond field resets at these boundaries. For example, S4 goes from 3,526,929 ms to 10 ms across the long gap. It cannot be treated as a single continuous clock. S1 and S3a have no elapsed-time discontinuities exceeding 25 ms from their expected 100 ms sample interval.

The exact S4 phone file is:

```text
/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4/S-S4.csv
```

Direct shell reproduction, accounting for the header and one-based line numbering:

```bash
sed -n '35186,35189p' '/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4/S-S4.csv' | cut -d, -f8,9
sed -n '35186,35189p' '/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4/V-S4.csv' | cut -d, -f2,9
sed -n '1864,1867p' '/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S2/S-S2.csv' | cut -d, -f8,9
sed -n '90967,90970p' '/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)/S4/S-S4.csv' | cut -d, -f8,9
```

The existing loader truncates paired CSVs to their shorter length and pairs rows. The integrator then advances every row by 0.1 seconds. Even equal CSV lengths do not establish synchronized samples. A single initial lag cannot account for the S4 discontinuity.

## Initial offsets independently supported by clocks and gyro signals

A gyro/reference correlation search restricted to the first 1,400 rows of each journey, with candidate offsets from −300 to +300 rows, gives the following. Positive lag means phone row `i` corresponds to reference row `i + lag`.

| Journey | Best prefix lag | Absolute correlation | Selected raw gyro column | Initial clock offset after subtracting one hour from phone time |
|---|---:|---:|---:|---:|
| S1 | +3 rows / +0.3 s | 0.94315 | 16 | +0.546 s |
| S2 | +76 rows / +7.6 s | 0.97376 | 16 | +7.341 s |
| S3a | −67 rows / −6.7 s | 0.96810 | 16 | −6.506 s |
| S4 | +18 rows / +1.8 s | 0.96131 | 16 | +1.711 s |

The one-hour adjustment is an inferred clock/timezone relationship, supported by all four initial timestamps; it has not been independently verified against acquisition documentation. Sub-second sensor/clock residuals remain. The original S1 training-only estimate is +2 rows. Its ±20-row search cannot discover S2's or S3a's true initial offset range.

The high correlations after a wider search show that the poor narrow-search correlations are not sufficient evidence that these journeys lack usable gyro information.

## Oracle separation: heading/timing already contributes substantial error

This diagnostic substitutes reference speed during every outage while retaining the exact frozen S1 gyro fit, +2-row lag, pre-outage yaw-bias calculation, and window boundaries from the original transfer audit. Its second branch also substitutes the reference per-row heading. Both branches use privileged reference information and cannot be deployed as navigation algorithms.

The S1 gyro fit uses the aligned training slice `[200:20697]`, with the same least-squares design as the benchmark. It produces coefficients `[-0.03575119, -0.95460042, -0.36468278, -0.00534432]`, including the intercept.

| Journey | Existing learned-speed/frozen-gyro median drift | Reference speed + frozen gyro | Reference speed + reference heading | Eligible 60 s windows |
|---|---:|---:|---:|---:|
| S1 | 18.34% | 10.21% | 0.42% | 51 |
| S2 | 47.49% | 34.98% | 0.34% | 147 |
| S3a | 63.67% | 25.56% | 0.25% | 38 |
| S4 | 56.34% | 37.64% | 0.35% | 137 |

The reference-speed/frozen-gyro p95 drifts are 26.12%, 134.53%, 140.79%, and 130.11%, respectively. The corresponding fractions below 10% are 47.06%, 12.93%, 26.32%, and 18.25%. These results show that improving speed alone does not repair the existing pipeline. Error components can interact and cancel; subtracting the percentages is not a valid decomposition into independent causes.

The reference-speed/reference-heading branch checks consistency of reference velocity integration against reference coordinates. It is near 0.25–0.42% median drift and is not a smartphone performance claim.

Reproduce these oracle calculations without writing files or training a speed model:

```bash
.venv/bin/python - <<'PY'
import json
from pathlib import Path
import numpy as np

root = Path('/tmp/iovnbd/Synchronised V abd S datasets/Categorised IOVNB Dataset/S (Driver A)')
def load(name):
    p = np.loadtxt(root/name/f'S-{name}.csv', delimiter=',', skiprows=1,
                   usecols=(15, 16, 17), encoding='latin1')
    r = np.loadtxt(root/name/f'V-{name}.csv', delimiter=',', skiprows=1,
                   usecols=(2, 3, 4, 5, 14), encoding='latin1')
    n = min(len(p), len(r))
    return p[:n], r[:n]

p, r = load('S1')
p, r = p[:-2], r[2:]
train_end = int(len(p) * .4)
design = np.column_stack((p, np.ones(len(p))))
coef = np.linalg.lstsq(design[200:train_end],
                      -np.deg2rad(r[200:train_end, 4]), rcond=None)[0]
print(json.dumps({'training_end': train_end, 'gyro_coefficients': coef.tolist()}))

for name in ('S1', 'S2', 'S3a', 'S4'):
    p, r = load(name)
    p, r = p[:-2], r[2:]
    gyro = np.column_stack((p, np.ones(len(p)))) @ coef
    yaw_ref = -np.deg2rad(r[:, 4])
    speed = r[:, 2] / 3.6
    latitude, longitude = np.deg2rad(r[:, 0]), np.deg2rad(r[:, 1])
    east = (longitude - longitude[0]) * 6371000 * np.cos(np.median(latitude))
    north = (latitude - latitude[0]) * 6371000
    first = train_end if name == 'S1' else 1400
    outcomes = {'reference_speed_frozen_gyro': [], 'reference_speed_reference_heading': []}
    for start in range(first, len(r) - 600, 600):
        end = start + 600
        distance = np.sum(speed[start:end]) * .1
        if distance < 50:
            continue
        calibration = max(200, start - 1200)
        bias = np.mean(gyro[calibration:start] - yaw_ref[calibration:start])
        headings = {
            'reference_speed_frozen_gyro': np.deg2rad(r[start, 3]) + np.cumsum(gyro[start:end] - bias) * .1,
            'reference_speed_reference_heading': np.deg2rad(r[start:end, 3]),
        }
        for method, heading in headings.items():
            dx = np.sum(speed[start:end] * np.sin(heading)) * .1 - (east[end] - east[start])
            dy = np.sum(speed[start:end] * np.cos(heading)) * .1 - (north[end] - north[start])
            outcomes[method].append(float(100 * np.hypot(dx, dy) / distance))
    print(json.dumps({'sequence': name, 'results': {
        method: {'eligible_windows': len(values), 'median': float(np.median(values)),
                 'p95': float(np.percentile(values, 95)),
                 'fraction_under_10': float(np.mean(np.asarray(values) < 10))}
        for method, values in outcomes.items()
    }}))
PY
```

## Exploratory prefix-calibration check

After the wider initial-lag search, a three-axis gyro regression was fitted to aligned rows `[200:1100]` in each journey. The entire lag search and fit use only original rows before 1400. Using reference speed, the original pre-outage yaw-bias proxy, and windows beginning at row 1400 (or 40% for S1), its median drifts were S1 3.97%, S2 9.27%, S3a 4.51%, and S4 27.78%. These are oracle diagnostics; their p95 values were 16.74%, 51.76%, 17.18%, and 125.72%.

This simultaneously changes initial lag and gyro calibration, and shifts physical window boundaries. It does not establish either mechanism's isolated effect, does not handle logging gaps, and does not establish a passing median for the learned-speed estimator. The later timestamp findings explain why the S4 value still should not guide model selection. A direct gyro/gravity projection also failed in exploration: supplied gravity is nearly `[0, 0, 9.8066]` despite useful yaw mainly occupying gyro column 16. Frame semantics must be verified before assuming these fields share a device frame.

## One bounded next experiment: repair synchronization, then isolate velocity and heading

Freeze one timestamp-valid evaluation manifest before comparing estimator variants. Parse phone wall-clock dates and VBOX times, resolve the clock relationship from the healthy calibration prefix, detect logger restarts and gaps, and form contiguous intervals with actual overlapping measurements. Preserve the clocks and segment identifiers in the loaded data. Never interpolate across the five-minute missing-IMU interval or silently pair its adjacent samples with adjacent VBOX rows.

Define synthetic outages on a common physical time grid; report every gap-excluded window and the resulting coverage. Require a valid pre-outage calibration prefix. This exclusion is dictated by missing sensor data, not observed estimator error. Keep reference labels out of outage-time model inputs; VBOX speed/heading during an outage are permitted only in explicitly labelled diagnostic branches.

On those exact same valid windows, compare four branches: learned speed + phone gyro, learned speed + reference heading, reference speed + phone gyro, and reference speed + reference heading. Use the existing fixed S1 speed model initially; if correcting S1 alignment requires refitting, record that change and reproduce the old model separately. Log mounting/gyro calibration and time residuals separately. Do not tune or select a new model on the final confirmation journeys.

If timestamp repair removes most transfer error, the immediate achievement is a corrected benchmark and a usable calibration path. If reference-heading/learned-speed error remains high, then velocity transfer needs targeted work; raw axis and magnetic-field statistics currently allow route/device correlations. If reference-speed/phone-gyro error remains high, improve heading calibration and bias tracking. This experiment answers which engineering work has the strongest evidence before committing to a larger model.

The necessary phone clocks, reference clocks, gyro channels, speed, heading, and coordinates are already present locally. Useful work within five days includes time-aware loading, restart/gap handling, healthy-GNSS calibration, and a verified speed/heading ablation. These are plausible engineering improvements, not a guarantee of less than 10% drift or a new research contribution. Fresh journeys, matched strong baselines, full error distributions, and deployment-valid initialization remain necessary for broader performance claims.
