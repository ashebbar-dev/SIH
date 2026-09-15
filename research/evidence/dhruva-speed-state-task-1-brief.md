### Task 1: Pure interval targets, speed state and metrics

**Files:**
- Create `research/tools/dhruva_speed_state.py`.
- Create `prototypes/dhruva/tests/test_speed_state.py`.
- Create `research/evidence/dhruva-speed-state-task-1-report.md`.

**Interfaces:**

```python
def backward_targets(times: np.ndarray, speed_mps: np.ndarray,
                     raw_rows: np.ndarray, satellite_field: np.ndarray
                     ) -> tuple[np.ndarray, np.ndarray, np.ndarray]: ...
# Returns n acceleration targets, n×2 raw supports, n NZ2 flags.
def integrate_speed(times: np.ndarray, acceleration_at_rows: np.ndarray,
                    initial_speed: float) -> tuple[np.ndarray, np.ndarray]: ...
# Both inputs have n=L+1 elements. Returns signed states and output-clipped states.
def absolute_speed(raw_prediction: np.ndarray, initial_speed: float | None = None
                   ) -> tuple[np.ndarray, np.ndarray]: ...
# Returns pre-final-clip candidate and nonnegative output, preserving old ordering.
def speed_metrics(*, times: np.ndarray, signed_speed: np.ndarray,
                  output_speed: np.ndarray, gps_speed: np.ndarray,
                  indicated_speed: np.ndarray, headings: np.ndarray,
                  truth_displacement: tuple[float, float],
                  acceleration: np.ndarray | None = None) -> dict: ...
```

All vectors must be one-dimensional with matching lengths and finite elements,
except backward_targets returns NaN at its first target. Times strictly
increase. Metrics require at least two timestamps. Raw rows are nonnegative
integers, consecutive, and within satellite_field bounds. Satellites must be
finite; arbitrary nonzero values are not decoded as quality flags. Initial
speed must be finite and nonnegative. Raise ValueError on invalid inputs;
do not silently shorten, mask or coerce them.

- [ ] **Step 1: Write focused tests and run RED.**

Include these numerical assertions, plus invalid-shape/nonfinite/duplicate-time,
nonconsecutive/out-of-bounds raw-row and negative-initial-speed rejection cases:

```python
t = np.array([0., .1, .4, .6])
v = np.array([2., 2., 8., 5.])
sat = np.ones(20); sat[11] = 0
a, supports, keep = backward_targets(t, v, np.arange(10,14), sat)
assert np.isnan(a[0])
np.testing.assert_allclose(a[1:], [0.,20.,-15.], atol=1e-12)
np.testing.assert_array_equal(supports, [[-1,10],[10,11],[11,12],[12,13]])
np.testing.assert_array_equal(keep, [False,False,False,True])

v = np.array([0.,0.,1.,1.,0.,2.]); t = np.arange(6)*.1
a = np.r_[999., np.diff(v)/np.diff(t)]
signed, out = integrate_speed(t,a,v[0])
np.testing.assert_allclose(signed,v,atol=1e-12)
np.testing.assert_allclose(out,v,atol=1e-12)

signed, out = integrate_speed(np.array([0.,1.,2.]),np.array([999.,-2.,1.]),1.)
np.testing.assert_array_equal(signed,[1.,-1.,0.])
np.testing.assert_array_equal(out,[1.,0.,0.])  # No clipped-state feedback.
_, out = absolute_speed(np.array([-5.,2.,4.]),10.)
np.testing.assert_array_equal(out,[10.,12.,14.])

t = np.arange(601)*.1; gps = np.full(601,10.); a = np.full(601,.1)
signed,out = integrate_speed(t,a,10.)
r = speed_metrics(times=t,signed_speed=signed,output_speed=out,gps_speed=gps,
    indicated_speed=gps,headings=np.zeros(601),truth_displacement=(0.,600.),
    acceleration=a)
assert abs(r['endpoint_error_m']-179.7)<1e-8
assert abs(r['terminal_speed_error_mps']-6.)<1e-10
assert abs(r['mean_acceleration_error_mps2']-.1)<1e-12
```

Also test zero acceleration on times[0,.1,.3], v0=10, zero headings and truth
(0,3): exact constant speeds, MAE0, endpoint error0, distance3 and null drift.
Perturb a[0] without changing any integrated output. Test a nonconstant speed
onset/braking sequence (above), not only constant acceleration.

```sh
env MPLCONFIGDIR=/tmp/sih-matplotlib .venv/bin/python -m unittest discover -s prototypes/dhruva/tests -p 'test_speed_state.py' -v
```

- [ ] **Step 2: Implement the exact arithmetic.**

After the declared checks, use these relationships:

```python
targets = np.r_[np.nan, np.diff(speed_mps)/np.diff(times)]
supports = np.column_stack((np.r_[-1,raw_rows[:-1]],raw_rows))
keep = np.r_[False, (satellite_field[raw_rows[:-1]] != 0) &
                    (satellite_field[raw_rows[1:]] != 0)]

signed = np.r_[initial_speed, initial_speed +
               np.cumsum(acceleration_at_rows[1:] * np.diff(times))]
output = np.maximum(0.,signed)

p = np.maximum(0.,raw_prediction)
candidate = raw_prediction.copy() if initial_speed is None else p+initial_speed-p[0]
output = np.maximum(0.,candidate)
```

For metrics reuse existing `audit_dhruva_aligned.integrate_displacement`;
do not copy its integration. All stored states/reference arrays include both
endpoints; position and time-weighted speed metrics use left samples[:-1].
Return exact keys `predicted_east_m`, `predicted_north_m`, `truth_east_m`,
`truth_north_m`, `distance_m`, `distance_eligible_for_drift_ratio`,
`endpoint_error_m`, `drift_ratio`, `speed_mae_gps_mps`,
`speed_mae_indicated_mps`, `mean_speed_error_mps`,
`mean_unclipped_speed_error_mps`, `clipped_fraction`,
`terminal_speed_error_mps`, `mean_acceleration_error_mps2`.

```python
dt = np.diff(times); duration = float(dt.sum())
gps_error = output_speed[:-1]-gps_speed[:-1]
speed_mae_gps_mps = float(np.sum(abs(gps_error)*dt)/duration)
mean_speed_error_mps = float(np.sum(gps_error*dt)/duration)
mean_unclipped_speed_error_mps = float(np.sum((signed_speed[:-1]-gps_speed[:-1])*dt)/duration)
clipped_fraction = float(np.mean(signed_speed[:-1] < 0))
terminal_speed_error_mps = float(output_speed[-1]-gps_speed[-1])
mean_acceleration_error_mps2 = None if acceleration is None else float(
    np.sum((acceleration[1:]-np.diff(gps_speed)/dt)*dt)/duration)
```

Indicated MAE uses the identical weighted formula against indicated_speed.
Distance is sum(gps_speed[:-1]*dt). Endpoint error is hypot of estimated-minus-
truth east/north. Drift is error/distance only if distance>=50m, else None.

- [ ] **Step 3: Run GREEN, self-review and report.**

Run only the focused command above, retain exact RED/GREEN output, changed
files, arithmetic decisions, and limitations in the Task1 report. Do not load
real data, fit models, create Task2 code or modify old helpers. Root performs
independent review before the physical-data experiment.

