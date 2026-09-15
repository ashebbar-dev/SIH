# Review of GPT-6 Pro's NISHAN receiver proposal

12 September 2026. This reviews the response supplied by the user; it does not claim to have executed its proposed receiver or physical benchmark.

## Verdict

**Worth a staged feasibility test, not immediate adoption of the full 96-capture programme.** The good contribution is the explicit strong receiver baseline and the separation of surviving signal, extraction quality, statistical false attribution, content authenticity and human culpability. The proposed local channel estimator is still underspecified; its headline accuracy targets are acceptance choices, not predictions.

It is complementary to the separately named compact-carrier pilot, not a replacement result for it. N1 fixes the original 52,500-symbol embedding and compares receivers on identical pages. The compact pilot changes the fingerprint construction and carrier allocation, and cannot claim to have passed N1 or preserved its operating point.

## What is already in this workspace

- `research/tools/probe_nishan_capture_channel.py:29` already computes a conditional Chernoff boundary for the original hard score. It uses the actual 32-bit Bernoulli probability `floor(p*2^32)/2^32`, stable `logaddexp`, an explicit hypothesis budget and an uncertified-null warning.
- That script also compares ordinary source subtraction with an oracle channel-matched unmarked reference. The oracle is explicitly not a deployable receiver. It distinguishes source/channel mismatch from erased signal for fixed synthetic distortions.
- `research/tools/probe_nishan_physical_registration.py` and its single-profile counterpart already test global content registration/refinement without calling it novelty.
- `research/tools/probe_nishan_bias_physical.py` already commits transformations before row scoring and evaluates bounded translation refinement. Its old real-capture result remains only the same one recovered photograph under a research threshold, not an added capture or a production result.

Thus “better registration plus a Chernoff threshold” would mostly repeat work. Recipient-independent **local** warp/photometric uncertainty plus an actual soft compound-channel decoder is the substantive new proposed branch.

## Source check

Meerwald and Furon's author paper really does cover soft compound-channel fingerprint decoding, including noisy continuous extracted values and distinct averaging/interleaving models. Those ingredients are established prior art, and its AWGN experiments are not a document print-camera benchmark. See Sections V–VI of [the primary paper](https://arxiv.org/pdf/1104.5616).

CoreMark's primary paper describes changing character-stroke structures and its own physical evaluations; its limitations include image-based text output and about 0.2 seconds per character embedding. This does not establish an available, licensed implementation or a comparable 52,500-position, five-colluder system. [Primary paper](https://arxiv.org/html/2506.23066v1).

The official SIH problem-statement URL again failed retrieval here. Treat the response's transcribed requirements as provisional until the official export is available. Do not turn a desirable photograph demo into a verified mandatory quantitative PS requirement without that source.

## Corrections before implementation

1. **Define a receiver, not just a likelihood equation.** Specify the coarse warp grid, regularization and supported coverage; fitting pixels and source-tone bands; local photometric model; blur/shift candidates and mixture weights; noise floors; and exactly what causes erasure. Freeze these on calibration/validation, not on the held-out donor's score. Flat blank regions may have too little content to estimate a local warp independently.
2. **Keep all innocent-row information outside fitting.** “Do not maximize alignment separately for each row” is necessary but insufficient. A shared fit that uses all codebook rows also depends on each innocent. Separate receiver preparation from scoring, commit the prepared evidence, and use fresh codebook/key contexts for calibration versus test documents where marked calibration pages could reveal row information.
3. **Use the real sampler law.** In the proposed cumulant, replace nominal bias `p_j` as the Bernoulli probability with the implemented probability when they differ. The current generator's mismatch is already handled in the existing hard-score helper; do not regress it when adding soft weights. Name the computational-randomness and finite-arithmetic assumptions rather than claim certification.
4. **Lambda minimization is not automatically an extra multiple-testing error.** If the score weights and selected positive lambda depend only on conditioned evidence/biases, not the tested innocent row, a deterministic conditional choice can use the Chernoff argument directly. If alignment, model or threshold selection consults candidate-row scores, that argument fails. A fixed grid and toy exact enumeration help test arithmetic, but do not prove real-world independence.
5. **Define the budget's scope.** `alpha=1e-6` across 1,000 rows for one frozen receiver/artifact is not a lifetime budget across every capture, receiver variant and repeated investigation. Avoid double counting or silently claiming a familywise guarantee broader than the actual experiment. Report miss/recovery separately.
6. **Clarify coalition construction.** Average rendered copies before printing, using the same content geometry; specify spatial-interleaving masks and participant contributions. The full test has 24 held-out printed artifacts, photographed four ways, not 96 independent documents. Calibration and validation add more printing. Two phones, including a held-out phone, and those logistics are not established by an estimate of 4–6 hours of coding.
7. **Do not make the first-stage stop rule circular.** “Untraceable under manual geometry” is a practical diagnostic only for the tested receiver/model. Measure residual modulation, saturation/white clipping and signal versus unmarked controls; this can justify not spending the deadline on the branch, but cannot prove all receivers impossible.

## Recommended smallest next step

First obtain matched fresh source/marked physical captures under fixed printer settings and retain original camera files. Use the existing original-profile page as the unchanged-embedding control. Measure source-tone-specific modulation and registration residuals before investing in a full local receiver. Old photographs remain development data.

Then implement and validate the strong **global** soft baseline on synthetic known-channel controls and a small fresh calibration set. Only if usable physical evidence remains should local warp/uncertainty be added and compared on a sealed validation/test set. Do not spend the user's time collecting 96 captures before that gate.

A compact-carrier photo success would be a different, explicitly labelled outcome. Neither branch fixes operator reproduction, independently administered ledger governance, or content integrity after photographs. No production or presentation claim is changed by this review.
