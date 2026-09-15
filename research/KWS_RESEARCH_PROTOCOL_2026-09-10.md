# SIH26172: first research experiment

Status: **paused by explicit user direction, 10 September**. First give NISHAN
and Dhruva serious improvement attempts; investigate other problem statements
only if those fail to produce useful results. The gates below are the earlier
prospective protocol, not an active allocation. No trained custom candidate,
device inference measurements, novelty or superiority claim exists. The full
SIH-winning research objective remains open.

## Why test this candidate first

The team now has six people, access to a microphone, an RTX3060 laptop, optional
free online GPU sessions and a standard ESP32 kit board. A small streaming model
can be trained and evaluated against public software, and its hardware costs can
be measured directly. Actual chip, microphone interface, VRAM and training
throughput still need verification.

The [cached SIH26172 statement](evidence/alternative-ps-review-snapshot-2026-09-10.json)
requires a custom wake word, open frameworks,
less than 256 KB RAM and less than 10% CPU during continuous listening, followed
by low-latency transfer of subsequent audio to an ASR server. A laptop-only
classifier does not satisfy it. Full application memory includes capture,
feature extraction, inference, buffering, operating-system tasks and networking.
Report CPU use per core and in total; do not hide one saturated core behind a
different normalization. Report both 256,000-byte and 262,144-byte comparisons
until the sponsor clarifies the KB convention.

## Hypothesis

In a stream dominated by unrelated speech and background noise, a constrained
feature-calibration update might reduce false triggers after an acoustic change
without causing the wake word to be forgotten. Freeze the keyword network;
adapt only a small calibration layer; retain a fixed bank of positive and
confusing-negative anchors; accept an update only if it preserves the anchor
margins; otherwise retain the previous calibration. Bound update cadence and
measure its complete computation and memory cost.

The update/acceptance rule is still to be specified against observed baseline
failures. Anchors and constrained adaptation are known techniques. A new name or
their combination alone is insufficient novelty. If ordinary threshold/noise
calibration or existing adaptation achieves the same result, reject this claim.

Relevant prior art includes [AdaKWS](https://arxiv.org/html/2505.14600v1), which
already studies adaptation and collapse, and
[LLM-Synth4KWS](https://arxiv.org/html/2505.22995v1), which already generates
confusable training examples. Neither generic test-time adaptation nor
AI-generated hard negatives is the proposed invention.

## Strong baseline and data

Use the current [OHF micro-wake-word framework](https://github.com/OHF-Voice/micro-wake-word)
and its supplied training notebook as the initial implementation. Record the
exact commit, package versions, feature configuration, seed and training data
hashes. Retrain for custom phrases: released generic assistant-keyword models
are only hardware diagnostics and must not be submitted as the custom solution.

The official [v2.1 release](https://github.com/OHF-Voice/micro-wake-word/releases/tag/v2.1_models)
supports regular ESP32 hardware. It does not establish the SIH resource limits.
The microphone must support a real ESP32 audio path; access to a USB laptop
microphone alone does not prove this.

The available [micro-wake-word feature dataset](https://huggingface.co/datasets/kahrendt/microwakeword)
has fixed source partitions and a CC BY-NC 4.0 label. Preserve its splits and
verify that cached features match the runtime front end. Confirm licenses for
every additional audio source and TTS model. Do not claim the resulting data
or model is unrestricted for commercial deployment.

Use checkpointed training on the RTX3060 or an available free GPU session.
No online quota, uninterrupted session or exact training duration is assumed.
The project's existing Python3.14 environment should not be modified to force
an incompatible training stack; follow the baseline's supported environment.

## Locked evaluation design

Before candidate fitting, record custom phrases, train/validation/test speakers,
audio source partitions, environment recordings, random seeds and thresholds.
Reserve test speakers and environment sessions independently; six teammates'
training utterances cannot double as evidence of general speaker robustness.

Evaluate chronological streams with sparse true wakes and transitions between
quiet, fan noise, conversation/TV, and quiet again. Use multiple transition
orders, sources and signal levels. Keep raw trigger timestamps and label
intervals. Avoid balanced isolated-clip accuracy as the main result.

Compare:

1. Strong fixed micro-wake-word with a validation-tuned threshold.
2. Simple noise-aware threshold or feature recalibration.
3. A faithful AdaKWS-style reproduction if its requirements can be met; label
   unofficial reproductions and do not silently weaken the reference method.
4. The candidate, including an ablation without anchor constraints.

Match phrases, data budgets, quantization and feature extraction. Use each
method's best validation configuration under the same compute constraints.
Keep test data out of threshold, checkpoint and architecture selection.

Primary quantities: false activations per negative hour at matched recall,
false rejections by speaker/environment, return-to-quiet degradation, trigger
latency, keyword-end-to-ASR-receipt latency, lost command-start audio, full peak
RAM and listening CPU. Separate desktop streaming measurements from physical
microphone/device measurements. Verify desktop/MCU prediction agreement.

Count duplicate triggers and exclusion windows by a rule fixed in advance.
Report uncertainty across independent recordings/speakers and seeds. Hundreds
of overlapping windows from one recording are not independent trials.
Zero false activations over 100 negative hours has an approximate one-sided
95% Poisson upper rate of 0.03/hour under that model; it is not zero risk, and
the model must not hide environmental clustering.

## Decision gates

By 11 September evening, require an exported custom-word baseline, actual ESP32
RAM/CPU measurements, a locked independent streaming evaluation, and a repeated
failure that basic threshold tuning does not resolve. Without these, do not
consume the remaining submission window on speculative adaptation.

A prospective improvement target is at least 30% fewer false triggers at matched
recall, without material return-to-quiet regression, while meeting the complete
device resource and latency constraints. Specify the allowable recall and
latency differences numerically before scoring the candidate. If the baseline
has too few errors, collect more independent negative audio; do not worsen its
threshold to manufacture headroom. The target is not a predicted result.

Passing this experiment supports only the measured operating conditions.
Claiming a leading result additionally requires a current broader comparison,
reproducibility and evidence that the contribution is not already established.

## Six-person execution split

| Owners | Work | Concrete evidence |
|---|---|---|
| 1–2 | ESP32 audio/runtime and GPU baseline training | Chip/runtime identification, trained custom model, resource logs |
| 3 | Independent audio and streaming evaluation | Fixed splits, timestamped labels, comparator results |
| 4 | Candidate mechanism and prior-art scrutiny | Exact update rule, ablations, measured cost |
| 5 | NISHAN physical captures | Original scanner/camera files following the existing protocol |
| 6 | Reproduction and submission integration | Verified artifacts, team details, cold demo and final presentation |

The NISHAN physical protocol is in [physical_captures/README.md](../physical_captures/README.md).
It protects the existing deadline option while the stronger research question
is tested. Neither lane may claim that prototype readiness satisfies the user's
requested breakthrough.
