# KWS Streaming Diagnostic Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Obtain auditable chronological predictions from a released baseline before designing or claiming an improved custom-word system.

**Architecture:** A desktop runner feeds mono PCM16 audio through a persistent native microfrontend and LiteRT interpreter. It records raw predictions and explicitly specified ESPHome-style continuous-listening triggers; the existing independent evaluator scores labeled streams.

**Tech Stack:** Python 3.12, NumPy 2.5.3, ai-edge-litert 2.2.0, pymicro-features 2.0.2, standard-library unittest and wave.

**Spec:** `research/KWS_RESEARCH_PROTOCOL_2026-09-10.md`; pinned runtime details in `research/KWS_BASELINE_INPUTS_2026-09-10.md`, sections Feature and training settings and First clean streaming diagnostic.

## Global Constraints

- Public assistant-word models are diagnostics only; never describe them as the custom SIH solution.
- Desktop timings are not ESP32 listening CPU, latency or full RAM measurements.
- Start each independent recording with a fresh model and frontend; preserve states throughout each recording.
- Store raw uint8 outputs, both probability conventions, input/model hashes and timing rules.
- Never remove duplicates from the evaluator or discard inconvenient recordings.
- Do not initialize Git, create commits, flash the board, or change the main `.venv`.
- Use `apply_patch` for source edits. No external downloads or dependency installs by the implementation worker.

---

### Task 1: Streaming runtime with exact diagnostic policy

**Files:**
- Create: `prototypes/kws/run_stream.py`
- Create: `prototypes/kws/tests/test_run_stream.py`
- Create: `prototypes/kws/README.md`
- Keep unchanged: `prototypes/kws/evaluate_stream.py` and its tests.

**Interfaces:**
- Consumes: `--model-manifest PATH --audio PATH --output PATH` and optional positive integer `--chunk-samples` default 160. Manifest resolves its `model` relative to its own parent; require version 2, feature step 10 ms, valid cutoff [0,1], positive integer probability window. Audio must be uncompressed mono 16-bit 16000 Hz WAV; reject other formats explicitly.
- Produces: JSON schema version 1 with model/audio SHA256, model tensor shapes/dtypes/scales/zero points, dependency versions, audio duration, total read samples, consumed native samples, unprocessed tail samples, feature/invocation counts, incomplete final stride count, separate frontend/invoke desktop elapsed times, raw chronological predictions and `triggers_s`.
- Functions for tests: `quantize_features(features) -> np.ndarray`, `StreamingDetector(cutoff: int, window: int)`, `StreamingDetector.advance(probability: int | None) -> bool`, and `run_stream(manifest_path: Path, audio_path: Path, chunk_samples: int = 160) -> dict`.
- Each prediction contains `time_s`, `raw_uint8`, `tensor_probability`, `device_probability`. `tensor_probability = (raw - output_zero_point) * output_scale`; `device_probability = raw / 255.0`. Trigger times equal the triggering prediction's consumed-sample timestamp.

- [ ] **Step 1: Write failing tests for feature conversion and detection boundaries.**

```python
def test_feature_conversion(self):
    raw = np.array([0, 1, 333, 666, 1000], dtype=np.int64)
    expected = np.array([-128, -128, 0, 127, 127], dtype=np.int8)
    np.testing.assert_array_equal(quantize_features(raw / 25.6), expected)

def test_strict_cutoff_and_reset(self):
    detector = StreamingDetector(cutoff=247, window=5)
    for _ in range(100):
        self.assertFalse(detector.advance(0))
    for _ in range(5):
        self.assertFalse(detector.advance(247))
    self.assertTrue(detector.advance(248))
    self.assertFalse(detector.advance(255))
```

Also assert high outputs do not advance cooldown, `None` advances one feature slice using the latest raw output but cannot itself trigger, invalid configuration/audio rejection, consumed timestamps and chunk-size-independent real inference. Use temporary generated PCM WAVs for tests; runtime-dependent model test reads environment variable `KWS_TEST_MODEL_MANIFEST` and explicitly skips only when absent.

- [ ] **Step 2: Run `.venv-kws/bin/python -m unittest discover -s prototypes/kws/tests -p 'test_run_stream.py' -v`; retain expected missing-module failure.**

- [ ] **Step 3: Implement feature conversion and a streaming runner.**

```python
raw = np.rint(np.asarray(features, dtype=np.float64) * 25.6).astype(np.int64)
quantized = np.clip((raw * 256 + 333) // 666 - 128, -128, 127).astype(np.int8)
```

Require finite nonnegative frontend features before conversion. Validate input `int8[1,stride,40]`, output `uint8[1,1]`, stride positive. This diagnostic's fixed feature mapping targets input scale approximately `26/255` and zero point -128; reject incompatible models. Require output zero point 0 for device-probability convention. Construct interpreter with `num_threads=1` and allocate tensors once per stream. Read all WAV samples and respect `samples_read`; reject impossible/no-progress native returns. Buffer transport input into fixed 160-sample native calls so returned feature timestamps are independent of `--chunk-samples`. The installed native API rejects calls shorter than 160 samples: retain the final shorter tail as explicitly unprocessed, without zero-padding or silently counting it as consumed. Report both that tail and any leftover complete feature stride. A complete first feature requires 480 samples, so the first three-row model invocation completes at 800 samples (0.05 s). Build nonoverlapping groups of `stride` newly generated feature rows, invoke once per complete group, never recreate model state within a recording.

- [ ] **Step 4: Implement the explicitly declared continuous-listening detection policy.**

Initialize a zero-filled ring of `window` raw predictions, index 0, suppression -100. Quantize manifest cutoff with `int(cutoff * 255)` and report that integer. On each feature row, optionally update the ring if a model invocation completed (increment/wrap index before writing). If the most recent ring value is below cutoff, increment suppression toward zero by one. Only a new prediction may trigger, only when suppression is zero and `sum(ring) > cutoff * window`. On a trigger clear the ring and reset suppression to -100, keeping the network/frontend and ring index. This is an explicit synchronous continuous-listening diagnostic without VAD; do not claim parity with asynchronous firmware scheduling or stop-after-detection behavior before device verification.

- [ ] **Step 5: Run focused and real-model tests.**

```sh
KWS_TEST_MODEL_MANIFEST=/tmp/sih-kws-models-20260910/models/v2/okay_nabu.json .venv-kws/bin/python -m unittest discover -s prototypes/kws/tests -p 'test_run_stream.py' -v
```

In the real-model test compare raw outputs, trigger times and feature counts on the same nonconstant generated PCM stream across fresh runs with chunk sizes 73, 160 and 997. Assert three-row model's first invocation timestamp 0.05 s and 30 ms subsequent cadence. Separate actual output assertions from mocked shape/format validation. Record skipped tests honestly.

- [ ] **Step 6: Document/run the CLI and hand off for independent review.**

```sh
.venv-kws/bin/python prototypes/kws/run_stream.py --model-manifest /tmp/sih-kws-models-20260910/models/v2/okay_nabu.json --audio data/kws/diagnostic/positive-stream.wav --output artifacts/kws/positive-stream.json
```

README must include dependencies, command, quantization/state/timestamp semantics, how to copy `triggers_s` into the evaluator's recording manifest, diagnostics-only limitation, and lack of board microphone/device measurements. External model paths are runtime inputs, not vendored dependencies. Do not claim a passing synthetic positive means real-person recall.

## Review and execution record

This plan implements the baseline diagnostic portion of the research protocol only. Training custom phrases, recording independent human speakers, board runtime measurement and a strong-method comparison remain required research work, not completed by this plan.

Ruling: use file snapshots and retained review reports, not Git worktrees/commits — repository initialization is deliberately reserved for submission day; the cost is losing automatic commit-diff recovery.

Ruling: retain/report a final sub-160-sample WAV tail without native processing or padding — pymicro-features 2.0.2 rejects shorter calls; no complete 10 ms feature step is fabricated. The cost is up to 159 final audio samples not processed, explicitly disclosed rather than hidden in the consumed count.

Preflight: Task 1's runner and tests share the four named interfaces above. The existing evaluator consumes only schema-compatible recording metadata/events/triggers, not this runner's extra metadata; integration must construct that explicit manifest. No other task edits these files.
