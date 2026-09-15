# Dhruva: vehicle inertial comparators and a bounded research gap

Research date: 11 September 2026. This is a primary-source comparison, not an experiment or a claim that Dhruva beats published methods. Five comparator papers and three associated repositories were examined in detail; a final currency check also found a 2026 manuscript listed by its author as under review. No datasets, repositories, weights or packages were downloaded; no fitting, inference or existing-artifact changes were performed.

The strongest practical conclusion is that Dhruva needs a matched speed baseline before an elaborate new fusion system. Its current error is especially sensitive to speed estimation, while learned covariance, learned attitude/velocity, phone-frame alignment and timing-aware training already have vehicle-specific prior art. None of the audited published numbers measures the same quantity on our four journeys.

## Local comparison contract

The [aligned ablation](DHRUVA_ALIGNED_ABLATION_FINDINGS_2026-09-10.md) freezes 400 candidate 60-second outages, with 370 time/history-valid windows and 355 drift-eligible windows traveling at least 50 m. S1 training uses 20,495 samples; S1/S2/S3a/S4 are all previously inspected development journeys. Learned speed plus phone gyro gives median drift 16.110%, 21.855%, 45.412%, 20.347%. Giving the system reference heading still leaves 11.695%, 17.947%, 41.665%, 16.587%; reference speed plus phone gyro is much better. These oracle substitutions diagnose limitations; their differences are not additive causal error contributions.

The [reference audit](DHRUVA_REFERENCE_QUALITY_AUDIT_2026-09-10.md) found all 71 zero-satellite S1 rows in training, plus substantial neighboring reference disagreement. Literal satellite values have unresolved flag encoding. Coordinate/GPS-speed agreement is not independent truth; indicated vehicle speed has unverified calibration. Consequently neither a quality threshold nor a claim that those 71 rows explain the speed error is justified yet.

For any new comparison, use the same physical windows, permitted pre-outage history, timing treatment and initial-state information for every method. Preserve separate tables for ideal initialization and deployable pre-outage initialization. Report endpoint error for short journeys too; report percentage drift only under the existing distance rule. Keep all four journeys labeled development data until new journeys are held out before further model choices.

## Five concrete comparators

### 1. AI-IMU Dead-Reckoning — Brossard, Barrau and Bonnabel, 2020

**Inputs and assumptions:** vehicle-mounted OxTS RT3003 accelerometer/gyro at 100 Hz, deliberately using KITTI raw rather than 10 Hz synchronized data. The invariant EKF learns IMU biases and a small IMU/car misalignment; a neural adapter controls motion-constraint covariance. Evaluation starts from reference position, velocity and attitude, with zero initial biases/lever arm and identity extrinsic rotation.

**Training and result:** each evaluated sequence is omitted from its adapter training; supervision optimizes relative translation error. The reported 1.10% is a mean translation increment error over KITTI distance segments of 100–800 m, not median 60-second horizontal endpoint drift. Sequence 03 lacks raw data; sequences 00/02/05 with logging problems are discussed separately from the principal summary. [Paper, Sections IV–V and Table 1](https://arxiv.org/pdf/1904.06064).

**Code and compatibility:** public Python/PyTorch code, MIT license. Crucially, the supplied checkpoint is trained on sequences 00/01/04–11, leaving only 02 as its test sequence. It is not a universal held-out checkpoint. [Author repository](https://github.com/mbrossar/ai-imu-dr). S1/S2/S3a/S4 provide compatible sensor types, but their 10 Hz phone data require a documented adaptation and retraining; the published 100 Hz result cannot be imported.

### 2. AVNet / DMDVDR — Qian et al., 2025

**Inputs and assumptions:** Huawei Mate 30 accelerometer/gyro, resampled to 200 Hz; 200-sample windows produce 1 Hz learned attitude increments and forward velocity. The phone is rigidly fixed at one mounting angle. Initial attitude must be supplied; precise initial position/velocity provenance remains unresolved in this bounded inspection.

**Training and result:** NovAtel SPAN/ISA-100C provides reference pose/velocity; 11 custom parking sequences use leave-one-sequence-out training of both learned measurements and filter adapter. The 0.4% average horizontal translation error uses relative pose increments over 100–900 m segments. It is not Dhruva's outage metric. Data are available by author request. [Paper, implementation, experimental setup, evaluation metrics and results](https://link.springer.com/article/10.1186/s43020-025-00168-7).

**Code and compatibility:** the paper links [QDeepOdo](https://github.com/DragonEmperorG/QDeepOdo) and [QAIIMUDeadReckoning](https://github.com/DragonEmperorG/QAIIMUDeadReckoning). Both repositories exist with training/testing source; documentation is sparse, and complete reproduction assets were not verified. Our 10 Hz streams cannot recreate the 200 Hz input information. Architecture adaptation is possible, but reference attitude supervision and causal initialization need additional validation.

### 3. DVSE, “An Inertial Sequence Learning Framework for Vehicle Speed Estimation via Smartphone IMU” — Xiao, Ren and Li, 2025 preprint

**Inputs and assumptions:** smartphone IMU; learned noise compensation and phone/vehicle orientation, one-second integrated inputs, and a 10-second temporal window. The text's 50 Hz example does not establish the raw acquisition rate. It predicts velocity changes; despite its initialization-free claim, the absolute initial-speed integration convention is not clearly specified.

**Training and result:** GNSS supervision from approximately 200 hours and over 300 drivers; 20% of trajectories are test data, with remaining data divided 80/20 for training/validation. A separate random-batch split is also studied. Table I reports 60-second velocity MAE 2.35 m/s and integrated scalar-distance MAE 50.84 m, with 80th-percentile values 3.62 m/s and 83.65 m. These are not 2D endpoint errors. Timing-aware loss selects between zero and one-second GNSS lag. [Paper, Sections V–VII and Table I](https://arxiv.org/pdf/2505.18490).

**Code and compatibility:** no author code/data release was located in the paper. Local sensor types and one-second integrations are suitable for an adaptation, but exact reproduction lacks acquisition details, data and initialization semantics. Publication status verified as an [arXiv preprint](https://arxiv.org/abs/2505.18490), not assumed peer reviewed.

### 4. Smartphone speed estimation with LSTM and attention — Shin, Li and Kim, 2025

**Inputs and assumptions:** 50 Hz accelerometer/gyro, acceleration magnitude and window statistics; a 4-second window, two LSTM layers (64/32 units) and attention. It predicts speed directly in the phone frame, so trajectory initialization is outside its evaluation.

**Training and result:** OBD2 speed supervision; four Galaxy S20/S22 Ultra phones in different mounted orientations, reported 41.8 km training collection and three additional test scenarios in one underground parking facility. The validation partition and unseen-device independence are not established. Reported mean speed RMSE is 0.38 m/s; it is not navigation drift. Data are private/on request; no code link was located. [Paper, Sections 3–4 and data availability](https://www.mdpi.com/2076-3417/15/16/8824).

**Compatibility:** all required input types exist locally; replacing the window with 40 samples preserves four seconds at 10 Hz. Changed rate, reference channel and driving distribution make this a reimplementation/adaptation, not replication of the published accuracy.

### 5. Learning to Localise Automated Vehicles in Challenging Environments Using INS — Onyekpe et al., 2021

**Inputs and assumptions:** IO-VNBD vehicle/ECU longitudinal acceleration and yaw rate at 10 Hz, not the smartphone channels. A small input-delay neural network predicts displacement using acceleration and the previous displacement estimate; another predicts yaw rate. Training substitutes noisy GNSS displacement for previous predictions. Initial heading is required; acceleration calibration includes a 20-minute stationary bias measurement.

**Training and result:** 800 minutes/760 km of named vehicle subsets; different named subsets cover motorway and four challenging scenarios. Evaluation uses 10-second simulated outages with 1-second predictions. Roundabout Table 9 reports mean displacement CRSE 8.63 m versus 78.32 m for INS DR across 11 sequences. CRSE sums per-step error magnitudes; the separately named CAE retains signed errors. Neither is Dhruva's final 2D endpoint metric. [Author-hosted paper, Sections 2–4, Tables 1–3, 7 and 9](https://pure.coventry.ac.uk/ws/files/40409393/Binder2.pdf).

**Code and compatibility:** no author implementation link was located. Our paired vehicle channels enable a sensor-privileged diagnostic, but smartphone-only adaptation must replace those inputs and define causal mounting/bias calibration. Matching the dataset name or 10 Hz rate alone does not match the published experiment.

## Recommended first baseline

Reimplement comparator 4 as a four-second, 10 Hz speed model and substitute its output into the existing frozen phone-gyro branch. Preserve its documented architecture, fit normalization on training data only, and predict at each window's final timestamp using only past samples. This targets the limitation identified by our own ablation and has fewer reproduction dependencies than the complete AVNet system. It is an established-method baseline, not Dhruva's novelty.

Run one preregistered comparison with the unchanged gradient-boosting estimator and an anchored physical speed-increment baseline, all using identical starts/history. The latter is an implementation recommendation, not a published result. Any quality-sensitive training branch must use a policy fixed without inspecting test prediction errors, retain original candidates, and separately report how results change on the same windows. First resolve the reference policy from the existing audit; do not silently replace GPS labels with indicated speed.

A future claim of strong full-navigation performance should additionally survive a matched AI-IMU adaptation. Its public code makes it the clearest reusable full-navigation comparator, but its original checkpoint and published percentage do not answer the low-rate smartphone question.

## One precise research hypothesis, with novelty still uncertain

Investigate **identifiability-aware pre-outage calibration with explicit uncertainty carried into the outage**: jointly estimate clock offset, phone/vehicle rotation and IMU bias only in motion directions that the pre-outage history can constrain, then preserve the unresolved directions as uncertainty during speed-increment integration. The target failure is a confident but incorrect velocity estimate after transferring to a different journey or mounting condition.

This is a proposed hypothesis, not an existing Dhruva implementation. Under an ideal constant-velocity, straight-motion model, two different absolute speeds can generate the same accelerometer/gyro measurements. A learned road-vibration correlation does not remove that basic ambiguity across arbitrary vehicles, roads and devices. Therefore an honest algorithm needs a stated initial-speed source and must not convert missing information into unjustified confidence. For deployment that source can be pre-outage GNSS; uncertainty in that source must also be retained.

The potential contribution would be a derivation of the jointly identifiable calibration subspace at 10 Hz, plus a causal estimator that demonstrably improves drift and uncertainty coverage on unseen journeys without using reference labels during outages. Neither a network predicting speed increments nor GNSS-lag matching is itself novel: DVSE already addresses both. Adaptive covariance and motion-constraint weighting are also established by AI-IMU/AVNet. The bounded review has not established whether the proposed joint identifiability treatment is new; broader targeted prior-art checking would be necessary before claiming it.

Use future held-out journeys to compare calibrated error coverage, median/p95 endpoint drift and low-excitation failure rates against the same method with identifiability gating disabled. Report failures at 60 seconds before extending to longer outages. Improvement over our current development model alone would not establish improvement over the field.

## Currency and unresolved comparability

Searches included 2026 smartphone vehicle dead-reckoning and IO-VNBD terms, but this was not an exhaustive September 2026 literature review. A relevant 2026 orientation-robust vehicle DR manuscript is listed as under review on an [author's publication page](https://gitboseong.github.io/); no public paper/results were verified, so it is not assigned a numerical rank. Do not interpret the absence of a newer fully audited comparator here as proof that none exists.

The immediate unknowns are specific: DVSE raw rate/absolute-speed anchoring/code; AVNet exact filter initialization and complete reproduction assets; smartphone LSTM validation partition/code; IO-VNBD export semantics/reference validity; and performance after all methods receive the same 10 Hz smartphone inputs and outage initialization. These unresolved comparisons prevent any defensible global “current best” or “significantly better” claim at present.
