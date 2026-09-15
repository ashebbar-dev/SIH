# Dhruva final fix-wave review package

Original finding: backward restarts could replace the initial healthy calibration span with later raw data because overlap selection sorted timestamps.

Ruling: use only each stream's initial contiguous raw span intersected with its fixed physical prefix; no later calibration episode fallback. Insufficient initial overlap fails explicitly. Final align_pair remains unchanged.

Requirements: docs/superpowers/plans/2026-09-10-dhruva-time-alignment.md.
Report with covering13-test red/green evidence: research/evidence/dhruva-time-alignment-implementation.md, final fix section.
Ledger: research/evidence/dhruva-time-alignment-progress.md.

Review only the one finding and new breakage in these fix diffs. Do not rerun reported tests or unchanged real-data audits.

```diff
--- before/time_alignment.py
+++ after/time_alignment.py
@@ -200,36 +200,15 @@
     return [(int(start), int(end)) for start, end in zip(starts, ends)]
 
 
-def _prefix_length(times: np.ndarray, prefix_s: float) -> int:
-    outside = np.flatnonzero(times > times[0] + prefix_s)
-    return int(outside[0]) if len(outside) else len(times)
-
-
-def _first_overlap(
-    phone_times: np.ndarray,
-    phone_spans: list[tuple[int, int]],
-    reference_times: np.ndarray,
-    reference_spans: list[tuple[int, int]],
-) -> tuple[tuple[int, int], tuple[int, int], float, float] | None:
-    overlaps: list[tuple[float, int, int, tuple[int, int], tuple[int, int], float]] = []
-    for phone_span in phone_spans:
-        if phone_span[1] - phone_span[0] < 2:
-            continue
-        phone_start = float(phone_times[phone_span[0]])
-        phone_end = float(phone_times[phone_span[1] - 1])
-        for reference_span in reference_spans:
-            reference_start = float(reference_times[reference_span[0]])
-            reference_end = float(reference_times[reference_span[1] - 1])
-            start = max(phone_start, reference_start)
-            end = min(phone_end, reference_end)
-            if start <= end:
-                overlaps.append(
-                    (start, phone_span[0], reference_span[0], phone_span, reference_span, end)
-                )
-    if not overlaps:
-        return None
-    start, _, _, phone_span, reference_span, end = min(overlaps)
-    return phone_span, reference_span, start, end
+def _initial_prefix_length(
+    times: np.ndarray, elapsed_ms: np.ndarray | None, prefix_s: float
+) -> int:
+    """Return the prefix end inside the initial contiguous acquisition span."""
+
+    initial_span_end = contiguous_spans(times, elapsed_ms)[0][1]
+    initial_times = times[:initial_span_end]
+    outside = np.flatnonzero(initial_times > initial_times[0] + prefix_s)
+    return int(outside[0]) if len(outside) else initial_span_end
 
 
 def _offset_grid(max_residual_s: float, step_s: float) -> list[float]:
@@ -259,41 +238,38 @@
     if pair.reference.ndim != 2 or pair.reference.shape[1] < 5:
         raise ValueError("reference measurements must contain five columns")
 
-    phone_count = _prefix_length(pair.phone_time_s, prefix_s)
-    reference_count = _prefix_length(pair.reference_time_s, prefix_s)
+    phone_count = _initial_prefix_length(
+        pair.phone_time_s, pair.phone_elapsed_ms, prefix_s
+    )
+    reference_count = _initial_prefix_length(pair.reference_time_s, None, prefix_s)
     phone_times_raw = pair.phone_time_s[:phone_count]
     reference_times = pair.reference_time_s[:reference_count]
     phone_values = pair.phone[:phone_count]
     reference_values = pair.reference[:reference_count]
-    phone_spans = contiguous_spans(phone_times_raw, pair.phone_elapsed_ms[:phone_count])
-    reference_spans = contiguous_spans(reference_times)
 
     best: tuple[float, float, int, int, float, float] | None = None
     for offset in _offset_grid(max_residual_s, step_s):
         shifted_phone_times = phone_times_raw + offset
-        overlap = _first_overlap(
-            shifted_phone_times, phone_spans, reference_times, reference_spans
-        )
-        if overlap is None:
+        if len(shifted_phone_times) < 2:
+            continue
+        start = max(float(shifted_phone_times[0]), float(reference_times[0]))
+        end = min(float(shifted_phone_times[-1]), float(reference_times[-1]))
+        if start > end:
             continue
-        phone_span, reference_span, start, end = overlap
-        reference_start, reference_end = reference_span
-        rows = np.arange(reference_start, reference_end)
+        rows = np.arange(reference_count)
         rows = rows[
             (reference_times[rows] >= start) & (reference_times[rows] <= end)
         ]
         if len(rows) < 50:
             continue
-        phone_start, phone_end = phone_span
-        interpolation_times = shifted_phone_times[phone_start:phone_end]
         reference_signal = reference_values[rows, 4]
         if np.ptp(reference_signal) == 0.0:
             continue
         for axis in range(3):
             phone_signal = np.interp(
                 reference_times[rows],
-                interpolation_times,
-                phone_values[phone_start:phone_end, 7 + axis],
+                shifted_phone_times,
+                phone_values[:, 7 + axis],
             )
             if np.ptp(phone_signal) == 0.0:
                 continue
@@ -323,7 +299,7 @@
     if best is None:
         raise ValueError(
             "clock calibration requires at least 50 paired, varying observations "
-            "inside the first contiguous prefix overlap"
+            "inside the initial contiguous prefix overlap"
         )
 
     correlation, offset, axis, count, start, end = best
--- before/test_time_alignment.py
+++ after/test_time_alignment.py
@@ -215,6 +215,57 @@
         self.assertGreaterEqual(before["paired_sample_count"], 50)
         self.assertLessEqual(before["calibration_time_bounds_s"][1], 140.0)
 
+    def test_clock_calibration_ignores_later_backward_restart(self):
+        initial_time = np.arange(10.0, 20.0, 0.1)
+        restarted_time = np.arange(0.0, 10.0, 0.1)
+        phone_time = np.concatenate((initial_time, restarted_time))
+        reference_time = np.arange(0.0, 20.0, 0.1)
+        phone = np.zeros((len(phone_time), 16))
+        reference = np.zeros((len(reference_time), 5))
+        phone[:, 7] = np.sin(0.37 * phone_time) + 0.2 * np.cos(1.13 * phone_time)
+        reference[:, 4] = (
+            np.sin(0.37 * reference_time) + 0.2 * np.cos(1.13 * reference_time)
+        )
+        pair = self._pair(phone_time, phone, reference_time, reference)
+
+        before = estimate_clock_offset(pair, max_residual_s=0.0)
+        phone[len(initial_time) :, 7] = np.linspace(-20.0, 30.0, len(restarted_time))
+        after = estimate_clock_offset(pair, max_residual_s=0.0)
+
+        self.assertEqual(before, after)
+        self.assertGreaterEqual(before["calibration_time_bounds_s"][0], 10.0)
+        self.assertEqual(before["phone_prefix_time_bounds_s"], [10.0, initial_time[-1]])
+
+    def test_clock_calibration_ignores_smooth_wall_clock_after_elapsed_reset(self):
+        time = np.arange(0.0, 20.0, 0.1)
+        elapsed = np.concatenate((np.arange(100) * 100.0, np.arange(100) * 100.0))
+        signal = np.sin(0.019 * time**2) + 0.3 * np.cos(0.83 * time)
+        phone = np.zeros((len(time), 16))
+        reference = np.zeros((len(time), 5))
+        phone[:, 7] = signal
+        reference[:, 4] = signal
+        pair = self._pair(time, phone, time, reference, elapsed=elapsed)
+
+        before = estimate_clock_offset(pair, max_residual_s=0.0)
+        phone[100:, 7] = np.linspace(100.0, -100.0, 100)
+        after = estimate_clock_offset(pair, max_residual_s=0.0)
+
+        self.assertEqual(before, after)
+        self.assertEqual(before["paired_sample_count"], 100)
+        self.assertEqual(before["phone_prefix_time_bounds_s"], [0.0, time[99]])
+
+    def test_clock_calibration_does_not_fallback_after_inadequate_initial_overlap(self):
+        later_time = np.arange(0.0, 10.0, 0.1)
+        phone_time = np.concatenate(([100.0, 100.1], later_time))
+        phone = np.zeros((len(phone_time), 16))
+        reference = np.zeros((len(later_time), 5))
+        phone[2:, 7] = np.sin(0.7 * later_time)
+        reference[:, 4] = np.sin(0.7 * later_time)
+        pair = self._pair(phone_time, phone, later_time, reference)
+
+        with self.assertRaisesRegex(ValueError, "initial contiguous"):
+            estimate_clock_offset(pair)
+
     def test_zero_motion_clock_calibration_fails_explicitly(self):
         time = np.arange(0.0, 20.0, 0.1)
         pair = self._pair(time, np.zeros((len(time), 16)), time, np.zeros((len(time), 5)))
```

