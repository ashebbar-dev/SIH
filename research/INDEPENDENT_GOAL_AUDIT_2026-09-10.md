# SIH 2026: independent goal audit — 10 September 2026

**Subsequent user decision:** improvement work now concentrates on NISHAN and
Dhruva before considering alternatives. Its later candidate-priority recommendations are superseded by
[the original-ideas-first decision](ORIGINAL_IDEAS_FIRST_2026-09-10.md).

**Subsequent data finding:** the numerical transfer outputs below were
reproduced, but their interpretation is confounded. Independent raw-CSV
inspection verified a 312.142-second phone recording gap in S4 while the
paired VBOX rows remain 0.1 seconds apart. The loader discarded timestamps and
paired rows by index. Per-journey offsets also need correction. These numbers
are not clean measures of model transfer, and the benchmark must be repaired
before using them to reject Dhruva. [Verified gap](evidence/dhruva-s4-timestamp-gap-2026-09-10.json)

## Verdict

The current workspace does **not** meet the requested goal of a novel solution with results significantly better than the strongest existing systems. NISHAN is a useful integrated demonstration with real cryptographic operations; Dhruva is a preliminary estimator. Neither has a fair comparison against current leading methods, an independently established novel contribution, or evidence of winning SIH.

The earlier strategy optimizes submission readiness and apparent competition. Those are relevant to a hackathon but do not establish the scientific advantage the user asked for. This audit keeps the original ambition open. A working demo, a repaired bug, a green test suite, or a promising new idea does not complete it.

User-confirmed constraints: six people; internal submission on **15 September**; an ordinary ESP32 kit board, with exact module unverified; access to a microphone, printer/scanner, and an RTX 3060 laptop; free online GPU sessions may also be used. The current execution machine is an i5-8350U with about 23 GiB RAM; no NVIDIA runtime or attached ESP32 serial port was detected. Access to the other laptop or a cloud training session has not been established in this environment.

## What was inspected and reproduced

Reviewed project strategy, novelty audit, submission verifier, both prototype implementations and tests, experiment scripts and JSON/CSV evidence, physical-capture instructions, and relevant earlier scratch carrier experiments. Independent agents examined current literature, alternatives and comparator reproducibility. Git history was unavailable, so this is a snapshot audit rather than a commit-diff review.

The cached JSON contains **233** statements. The newer cached official HTML contains the added SIH26234–SIH26237 entries. The live official portal and guidelines returned HTTP 403 during this review; counts and wording from those caches are historical evidence, not a refreshed official verification. The user supplied the operative internal deadline.

Reproduced:

- Original NISHAN suite: **19 tests passed**.
- New PDF-policy regression: **three failed assertions and three format errors before repair**.
- Final NISHAN suite: **22 tests passed**, including the new parser-policy and raster compatibility checks.
- Dhruva S1: recovered the stored **71.753 m / 18.342%** median 60-second result.
- Frozen Dhruva model transferred to **S2, S3a and S4**, with full per-window output and a manifest written before fitting.

The submission verifier checks formatting, expected strings and stored artifact consistency. It does not compare competitors, establish novelty, certify the endpoint threat model, or independently prove every number. Passing it cannot establish this goal.

## NISHAN: strongest findings

### A real decision-policy defect was reproduced and repaired

Before repair, the evidence policy recognized a PDF only when its first five bytes were `%PDF-`. The renderer accepted a PDF with a leading newline. The same editable document therefore passed through different evidence rules depending on its preamble.

In the local synthetic fixture, a conflicting visual/layout document ordinarily caused abstention. With the newline added, the software skipped the layout observation and returned Alice from the visual channel. A one-channel document likewise changed from abstention to attribution. This proves a policy bypass, not that an arbitrary innocent person's fingerprint can be forged.

The implementation now obtains PDF identity from the renderer's parser, and the image loader uses the same classification. Valid Pillow raster formats remain supported; unrecognized input fails. Regression tests cover matching channels, conflicting channels and one missing channel under ordinary, prefixed and renamed PDF inputs.

Evidence: [before repair](evidence/nishan-format-policy-before.json), [regression tests](../prototypes/nishan_pq/tests/test_pdf_format_policy.py). This repair protects the existing engineering claim; it is not a research breakthrough.

### The robustness evidence is too narrow for superiority

The main carrier study uses one synthetic page and named digital transformations. Thirty release sessions vary recipient/session assignments, and thirty codebooks vary the code construction; neither substitutes for independent documents, printers, phones or capture conditions. No direct leading-method comparison exists.

Exact extracted text, working signatures, all-row scoring and the named collusion results are valuable. They do not establish robust physical attribution, non-framing, protection from an untrusted endpoint, or a general false-accusation rate.

Both PDF carriers remain removable. Canonical extraction and regeneration of identical text removes recipient-specific layout/rendering information. Preserving exact text while claiming universal recovery through arbitrary retyping would contradict that information-loss boundary.

### Key custody and client enforcement remain architectural gates

The demonstration controls recipient, validator and witness keys locally. A signed event identifies a key/session; it does not prove that a particular human leaked a file. The sender can reconstruct the existing fingerprints. A malicious recipient can access plaintext before the prototype finishes marking. Separate custody, enforced release and adjudication are substantive requirements.

Earlier scratch experiments add a recipient-secret visual authentication channel orthogonal to the Tardos patterns. They may support a useful carrier experiment, but do not implement an asymmetric fingerprinting protocol: the scripts hold all secrets, use a literal document context, add a separately removable image, and lack independent enrollment/adjudication. Mandatory authentication on every accusation would make that channel's physical reliability essential. Secret keys also do not prevent copying an already observed physical pattern. [Asymmetric Tardos prior art](https://arxiv.org/html/1010.2621)

### The Tardos explanation needs a distinction

The original paper separates soundness (avoiding innocent accusations) from completeness (catching a guilty party). Its Theorem 1 proof does **not** require the marking condition; completeness does. Existing statements that JPEG symbol errors automatically invalidate every soundness argument are too broad. This does not certify the implementation: finite precision, the keyed generator, access to innocent codewords and adaptive observations still require analysis. [Original paper, sections 2.2 and 6](https://www.renyi.hu/~tardos/fingerprint.pdf)

## Relevant modern comparisons missing from the original selection

These native results cannot be ranked against NISHAN by comparing the numbers directly.

| Work | Relevant evidence | What a fair comparison must respect |
|---|---|---|
| [CoreMark, June 2025](https://arxiv.org/html/2506.23066v1) | At 12-point English: 95.79% print-scan and 94.59% print-camera raw bit accuracy; real devices and document variations | Rasterized characters lose selectability; raw bit accuracy is not recipient attribution; its binary-image PSNR is not the same quality metric |
| [Client-Side Embedding, TIFS 2024](https://huazhongyun.github.io/pdf/Client-Side_Embedding_of_Screen-Shooting_Resilient_Image_Watermarking.pdf) | Already combines encrypt-once distribution, personalized client decryption and screen-camera resilience; 24 information bits expanded to 63 by BCH | [Public MATLAB code](https://github.com/XIAO-Xiangli/SW) needs dependency, licensing and failure-path checks; no Tardos coalition guarantee |
| [SepWater, TCSVT 2026](https://ieeexplore.ieee.org/document/11419148/) | Separates client reconstruction from watermark processing; [author model/code and test-data link](https://github.com/CVhnu/SepWater) | Published stack uses CUDA; use its native payload and released model; rerun on the same capture process |
| [CoMSMark, July 2026 preprint](https://arxiv.org/html/2607.23553v1) | Studies screen identities and collusive residual estimation; includes trained visual robustness | Its collusion task differs from Tardos guilty-coalition attribution; a successful comparison must state which properties overlap |

A selectable, content-bound physical fingerprint or more efficient asymmetric release could still be research directions. Neither vectorization, dual channels, client-side marking nor recipient signatures alone would be new. First reproduce strong comparison methods, then test a specific additional mechanism.

Comparator code inspection adds practical cautions: SW requires MATLAB image
processing and communications functionality, has no declared environment or
root license, and can fail on sparse pages. Its clean RGB round trip must be
reproduced before any capture study. SepWater's dependency file is a package
listing rather than an installable lock; its released extraction script reports
bit accuracy against an expected secret, not independently decoded recipient
identity. Weights/configuration compatibility and the complete decoding path
need a smoke test on the available GPU. Neither comparator was installed or run
during this audit. [SW implementation](https://github.com/XIAO-Xiangli/SW)
· [SepWater extraction](https://github.com/CVhnu/sepwater/blob/main/extract.py)

## Dhruva: fresh evidence changes the recommendation

Training parameters, features, timing lag and gyro map were frozen from the original S1 training prefix. Additional journeys were not used for fitting. The audit also evaluated three simple speed baselines; none brought all journeys near the target.

| Journey | 60-second windows, all / ratio eligible | Median endpoint error, all windows | Median drift, eligible windows | Eligible windows below 10% |
|---|---:|---:|---:|---:|
| S1 holdout | 51 / 51 | 71.75 m | 18.34% | 17.65% |
| S2 | 154 / 147 | 183.87 m | 47.49% | 6.12% |
| S3a | 38 / 38 | 383.46 m | 63.67% | 0% |
| S4 | 155 / 137 | 280.29 m | 56.34% | 6.57% |

Percentage metrics exclude journeys' outage windows traveling under 50 m, as in the original policy. The absolute-error and percentage columns therefore have different denominators where shown. Outages from one journey are not independent journeys.

This is an exploratory transfer diagnostic, **not** a new algorithm's untouched confirmation set. It retains ideal reference initial state and pre-outage VBOX yaw calibration. Fixed synchronization and mount mapping may contribute to transfer failure; the experiment does not isolate their causes. Original and audit integrators agree numerically. [Manifest](evidence/dhruva-transfer-2026-09-10/experiment-manifest.json) · [Results](evidence/dhruva-transfer-2026-09-10/results.json) · [All windows](evidence/dhruva-transfer-2026-09-10/windows.csv) · [Runnable audit](tools/audit_dhruva_transfer.py)

The cached official statement requires less than 10% drift; it does not grant compliance merely because a median passes. Its map matching, automatic alignment, GNSS fusion, mobile runtime and transition behavior are also absent from this prototype.

AVNet/DMDVDR already combines learned attitude/velocity with an invariant Kalman filter and reports 0.4% average relative horizontal translation error on its own parking-lot data. That is **not** a valid numerical comparison with the S1 result: data, sensors, scenarios and metrics differ. It does show that adding those familiar ingredients would not establish novelty. Its data are available on request, while code is linked by the authors. [AVNet, June 2025](https://link.springer.com/article/10.1186/s43020-025-00168-7)

Decision: pause Dhruva as a breakthrough candidate under this deadline. Its data audit is useful; the present estimator has not demonstrated transferable performance.

## Alternative research bets

The following are opportunities to test, not proven winners. Submission counts did not determine this shortlist.

| Candidate | Potential advance to investigate | Required strong comparison | First reason to reject it |
|---|---|---|---|
| SIH26172 — custom voice activator | Improve the real-device false-trigger/recall/compute frontier for custom phrases | Current micro-wake-word and relevant recent streaming methods, trained on the same phrases/data | Failure to fit complete runtime below the stated RAM/CPU limits, or gains explained only by threshold/data changes |
| SIH26164 — cryptographic discovery | More accurate usage/configuration reasoning with auditable unresolved cases | Current CBOMkit with correct build context, cdxgen and reproducible recent research | Comparing only to regex, suppressing unknowns, or counting conventions masquerading as better discovery |
| SIH26156 — perimeter log normalization | Reduce silent field-semantics errors and onboarding work after vendor/version changes | Maintained vendor adapters plus strong automatic parsing | Winning template clustering while failing event semantics, or obtaining accuracy by rejecting difficult events |

For voice activation, the cached PS requires a custom keyword, open frameworks, under 256 KB RAM and under 10% listening CPU. Official micro-wake-word releases demonstrate regular ESP32 operation, but this is not proof of those stricter limits. GPU access and a microphone make the experiment practical. Training custom words, cascades, augmentation and threshold tuning are already established. [Training framework](https://github.com/OHF-Voice/micro-wake-word) · [Regular ESP32 release evidence](https://github.com/OHF-Voice/micro-wake-word/releases/tag/v2.1_models)

For crypto discovery, August 2026 Crypsy reports 0.75 occurrence-level F1 but 0.95 component-level F1; much of the difference is counting. Its remaining usage-analysis and actionable-alert limitations are more interesting than the headline score. Its supplementary download was not obtained in this audit. Dynamic evidence must not turn an unobserved path into proof of absence. [Crypsy/Cryben paper](https://arxiv.org/html/2608.04857v1) · [CBOMkit](https://github.com/cbomkit/sonar-cryptography) · [cdxgen plugins](https://github.com/cdxgen/cdxgen-plugins-bin)

For log normalization, OCSF already supports raw and unmapped fields, and current systems already combine small models and validation. The useful target is correct vendor/event semantics under held-out versions, not merely a high Loghub template score. [OCSF](https://github.com/ocsf/ocsf-docs/blob/main/overview/understanding-ocsf.md) · [MicLog](https://github.com/arjen-yu/MicLog) · [Elastic Syslog Router](https://www.elastic.co/docs/reference/integrations/syslog_router)

Other screened options included sensor-fault detection, monsoon post-processing, lunar image matching, satellite change search and optimization. Their current data, annotation or strong-baseline burdens did not produce a better verified opportunity. This is a resource-aware screening judgment, not an exhaustive theorem that no other PS could be better.

## Decision process for the remaining days

With the confirmed microphone and GPU access, **SIH26172 is the first research
experiment**; SIH26164 is the next software alternative. The specific adaptation
hypothesis, comparison methods, evidence rules and six-person allocation are in
the [KWS research protocol](KWS_RESEARCH_PROTOCOL_2026-09-10.md). This is an
experiment priority, not a finding that a new entry is already better.

1. **Immediately:** preserve NISHAN's working demonstration and repaired evidence policy. Run the existing five-capture physical protocol with available printer/scanner access. It is an initial feasibility test, not a leading-method comparison.
2. **By 11 September:** establish whether a strong custom-word baseline runs within the actual ESP32 constraints. Reproduce its streaming evaluation; choose a specific mechanism only after identifying a repeatable failure or cost source. In parallel, finish comparator/data access for the leading software alternative.
3. **11–12 September:** test one candidate change against matched baselines. Freeze evaluation speakers/documents/repositories and configurations before candidate selection. Record all results and failure cases.
4. **13 September:** promote a direction only if the measured improvement survives the stronger comparison and fits the whole PS. Otherwise retain the honest working submission and continue research; do not rename prototype readiness as success.
5. **14 September:** freeze reproducible evidence and prepare the correct presentation, team details and rehearsal for the 15th. Continue the research objective afterward where competition rules permit.

A prospective voice gate is a practically substantial reduction in false activations at matched recall, while meeting the full RAM/CPU and latency requirements. A prospective crypto gate is substantially fewer non-actionable findings at matched discovery recall on unseen repositories. These targets must be specified before evaluation; they are not predictions.

The final goal remains open. No novel candidate has yet beaten the strongest relevant comparisons, and no SIH outcome can be certified from this workspace.
