# NISHAN: registering against the expected carrier from shared biases

Date: 2026-09-10. Status: design audit, not implemented or physically evaluated here.

## Recommendation

Proceed with one bounded research experiment after synthetic self-checks. Derive a registration template analytically from the shared bias vector, the source, and keyed carrier geometry; keep every recipient row outside registration. This is a plausible improvement to the current carrier, with a clean conditional false-accusation argument under an ideal secret model. It does not yet establish physical recovery, collusion completeness, or a novel synchronization method.

The most useful first experiment is a small translation refinement of the existing ORB → ECC-affine result, selected by correlation with the expected carrier. Freeze the algorithm before inspecting any new attribution scores. A successful result warrants an affine/local-warp study on new documents and keys. A failure on clipped material is evidence about signal survival, not a reason to keep changing registration until an identity scores well.

## What existing evidence actually establishes

The retained [single-resampling diagnostic](evidence/nishan-physical-registration-single-2026-09-10.json) reports the following. These numbers were read from existing JSON; this audit did not load or score the physical images.

| Capture | Registration | Content similarity | Row 0 score | Conditional threshold | Conditional accused |
|---|---|---:|---:|---:|---|
| akshay2 | ORB | 0.674 | 683.9 | 1030.9 | none |
| akshay2 | ORB + ECC affine | 0.689 | 788.3 | 1030.2 | none |
| akshay2 | ORB + ECC homography | 0.806 | 811.5 | 1031.8 | none |
| akshay3 | ORB | 0.671 | 1357.1 | 1103.8 | row 0 |
| akshay3 | ORB + ECC affine | 0.698 | 1709.9 | 1107.2 | row 0 |
| akshay3 | ORB + ECC homography | 0.803 | 975.1 | 1103.6 | none |

The associated [script](tools/probe_nishan_physical_registration_single.py) already composes transformations and makes one final resampling from original capture pixels. Thus the homography result cannot simply be dismissed as an extra final resampling. The observation motivates a carrier-sensitive alignment objective; it does not establish why the signal was lost. Around 84–87% of block correlations are exactly zero for akshay/akshay1 in these profiles, which is consistent with severe signal loss but is not by itself proof of clipping.

Implementation inspected: [carrier](../prototypes/nishan_pq/nishan/tardos_carrier.py), [code generation and scores](../prototypes/nishan_pq/nishan/tardos.py), [conditional-null helper](tools/probe_nishan_capture_channel.py), and [benchmark construction](../prototypes/nishan_pq/tools/benchmark_tardos_pdf.py). The current dual-carrier fixture uses strength **4.0**, confirmed by the benchmark construction and [benchmark artifact](../artifacts/nishan/tardos-pdf-benchmark.json). The carrier function default, 2.2, is a different setting. Its other text-layout carrier is a nuisance relative to the unchanged source and reinforces the need to exclude source edges from this first experiment.

## Conditional independence and attribution

Let the shared state be the realized biases p, source S, keyed block assignment/orientations/polarities G, and a fixed experimental protocol. In the ideal model, each innocent row has independent columns

\[
X_{ji}\sim\operatorname{Bernoulli}(q_i),\qquad
q_i=\lfloor 2^{32}p_i\rfloor/2^{32}.
\]

The q expression matches `generate_keyed`'s uniform 32-bit word comparison. Ideal bias randomness and ideal geometry randomness are independent of the row-sampling randomness. Fix a coalition excluding j. Its captures, side information, and attack randomness can depend on p, S, G and its own rows, but must be independent of row j conditional on this shared state. In particular, the attacker must not know an innocent row or receive row-dependent tracing feedback used to construct the evaluated capture.

Suppose registration, masks, nuisance fitting, decoder selection, abstention and final decoded word are all functions only of those permitted inputs. Then

\[
(\widehat H,\widehat y)\perp X_j\mid(p,S,G).
\]

This follows because measurable functions of variables independent of X_j remain independent of X_j. It permits an extensive p-derived search and selection by its carrier objective, including capture-dependent choices. It does not permit choosing a transform by row 0 score, maximum roster score, an empirical roster-average template, or decisions previously tuned against those scores on the evaluation material. Even an average over all n rows contains X_j/n. A leave-one-out construction is a different, per-candidate procedure requiring a separate analysis.

For the current one-sided score, condition also on the selected word y and set A={i:y_i=1}. Write

\[
a_i=\sqrt{(1-p_i)/p_i},\quad b_i=-\sqrt{p_i/(1-p_i)},\quad
K_y(t)=\sum_{i\in A}\log(q_i e^{t a_i}+(1-q_i)e^{t b_i}).
\]

For any positive t chosen using p and y alone,

\[
\Pr\left[S_j>\frac{K_y(t)+\log(H/\epsilon)}{t}\mid p,S,G,y\right]
\le\epsilon/H.
\]

Use a union bound over all H issued row/capture/decoder decisions. No extra transform-count factor is necessary when one transform is selected solely by the permitted image/p objective and only that output is tested: conditioning on its final y already handles the search. If scores from several transforms can trigger an accusation, count all of them. Optimization over t is legitimate because its inputs exclude X_j. Any finite positive t is valid in exact arithmetic; numerical overflow, rounding and threshold error still require a conservative implementation audit. The existing helper's `+1e-9` is not a certified arithmetic bound.

Bias matching does not produce a positive innocent-score drift under this CGF:

\[
E[U_{ji}\mid p_i]=(q_i-p_i)/\sqrt{p_i(1-p_i)}\le0.
\]

In exact Bernoulli(p) arithmetic the mean is zero, even if y_i is chosen as 1[p_i>1/2]. Such a word has high ordinary bit agreement with many rows; that is not calibrated attribution. A capture containing only the shared mean can synchronize and still contains no recipient-specific evidence under the model. Its score must use the actual selected active set and q-aware CGF, not a Gaussian approximation or a fixed threshold transplanted from another decoder.

This argument is an inference from the specified probability model and the inspected score, not a new security theorem. Tardos explicitly constructs conditionally independent Bernoulli columns and centers innocent contributions; his paper separates soundness from completeness and notes that its innocent-user bound does not use marking. It also explicitly leaves physical hiding outside its model. [Tardos, *Optimal Probabilistic Fingerprint Codes*, Sections 1 and 2](https://www.renyi.hu/~tardos/fingerprint.pdf).

The deterministic AES/HMAC prototype is not literally that independent random experiment. A computational interpretation needs an explicit secure-stream/domain-separation hybrid and secret-state assumptions; conditioning on the actual master key fixes every row. Public deterministic benchmark keys supply neither an information-theoretic rare-event guarantee nor resistance to deliberate framing. Physical decoding need not satisfy marking, so neither a conditional-null pass nor synchronization quality establishes collusion completeness. Accusation-driven adaptive repeated queries need fresh analysis or independent keying; an ordinary finite union budget alone does not repair loss of independence.

## Expected carrier and its actual rendering response

For block i let T_i be its keyed signed template, including polarity, with pixels ±1. Let s_i=2X_i−1 and μ_i=2q_i−1. Before rendering the expected signed pattern is μ_i T_i. This expectation requires no recipient row and no empirical codebook average.

The production overlay is **alpha compositing toward white or black**, not addition of ±strength. At a marked pixel, with a=clip(round(strength),0,255)/255 and ideal source channel value S,

\[
R_{s_i}(S)=(1-a)S+a\,127.5(1+s_iT_i).
\]

Consequently

\[
E[R(S)]-S=\underbrace{a(127.5-S)}_{\text{common brightness shift}}
+\underbrace{127.5a\,\mu_iT_i}_{\text{bias-dependent pilot}},
\]

and the zero-mean recipient residual is 127.5a(s_i−μ_i)T_i. Unused pixels have zero overlay, not this brightness shift. On pure white at strength 4, the ideal two outputs are 255 and 251: midpoint 253 and signed amplitude 2. At default strength 2.2, rounded alpha is 2/255 and signed amplitude 1. These formulas precede PDF rasterization, quantization, print and camera processing.

For a pixel response that depends on only one symbol, compute its two actual responses R_i^+(S),R_i^−(S), including known quantization/clipping, and use

\[
B_i=(R_i^++R_i^-)/2,\quad D_i=(R_i^+-R_i^-)/2,\quad E[R_i]=B_i+\mu_iD_i.
\]

In particular, do not create a fractional-alpha PDF from μ and assume it equals the mean of binary releases. Likewise C(E[R]) generally differs from E[C(R)] for nonlinear camera response C. A white-clipping response mapping both 251 and 255 to 255 makes D_i exactly zero and destroys this pilot. Averaging endpoints **after** that clipping captures the loss; clipping their mean can produce a false prediction.

The renderer may interpolate across several blocks, and physical blur mixes symbols before a nonlinear response. Then the two single-symbol endpoint formula does not cover the entire pixel: use the linear pre-quantization expectation plus an explicit approximation error, or enumerate the local symbol configurations with their product Bernoulli probabilities. Two whole-page renders (all-zero and all-one) cannot generally be mixed pixelwise with a local q after cross-block interpolation/nonlinearity. Endpoint renders are synthetic counterfactuals, not recipient copies, but their use must pass renderer self-checks. Keep the registration template in floating point so its subpixel bias differences survive.

The initial experiment below uses the actual native PDF response on smooth source areas and a fixed **linear** blur approximation. It makes no claim to invert an unknown physical nonlinear response. The source-edge mask limits layout and renderer interference; the erasure controls test whether the approximation can produce misleading registration peaks.

### Is the implicit pilot large enough to try?

Ignoring quantization and using p rather than q only for the following closed-form scale estimate, the untruncated arcsine law gives E[μ²]=1/2 and E[1−μ²]=1/2. With this prototype's cutoff δ=1/1500, let r=arcsin(sqrt(δ)) and L=π/2−2r. Then

\[
E[\mu^2]=\tfrac12-\frac{\sin(4r)}{4L}=0.4830321,
\qquad E[4p(1-p)]=0.5169679.
\]

Thus about 48.3% of **signed** carrier energy is in the conditional mean and 51.7% in recipient residuals. This excludes the common brightness shift and all source/image energy. At strength 4 the corresponding marked-pixel RMS values are approximately 1.390 and 1.438 grayscale units before physical losses. The q correction to μ is less than 2^-31. For actual experiments compute sums from realized q, response D, and the fixed mask, rather than using the distribution averages.

For disjoint equal-amplitude blocks and an exactly aligned additive channel, correlation with μ_i has mean proportional to Σμ_i² and recipient-induced variance proportional to Σμ_i²(1−μ_i²). Aggregation over thousands of independently sampled symbols can therefore locate a weak shared pattern. This is a plausibility calculation, not a camera SNR prediction: source residuals, blur, clipping and shading dominate in real material. Weighting exclusively toward extreme biases also gives synchronization less recipient-specific information; retain all available symbols for the unchanged accusation decoder.

An equal average of c independent recipient copies keeps the common mean and divides recipient-residual variance by c in a linear channel. Hence an average can become easier to synchronize while becoming harder to attribute. Other collusion strategies need not preserve this expectation. A shared pilot can also expose structure to an estimator; it is not an added security claim.

## Fixed first experiment

The following is a proposed preregistration, not a run. Values are engineering choices made before new scoring; changing them creates a new experiment.

1. **Inputs and separation.** Use source, realized p/q, geometry, recorded strength 4, and original capture pixels. Generate p without generating or loading the roster into the registration process. Commit input hashes, source response arrays, library versions and all parameters. Freeze the selected transforms and decoded words before a separate scoring process reads the roster. Do not inspect alternative-profile scores while developing registration.
2. **Initial transform.** Reuse the fixed ORB → ECC-affine algorithm from the retained diagnostic. No selection between affine and homography. Failed initialization is an explicit abstention.
3. **Search domain.** Compose reference-frame translations dx,dy in {−2,−1.75,…,2} pixels with that transform: 289 candidates at 144 DPI. Render each candidate directly from the original capture with the same Lanczos interpolation and border handling. No cascade of image resamplings. This deliberately tests only local translation, not full perspective correction or curved-page recovery. Resolve exact ties by smallest displacement, then dx, then dy.
4. **Template.** Form the native rendered midpoint B and bias component W from the actual overlay response as above. Apply one fixed Gaussian blur with sigma 0.75 reference pixels to B and W. No blur-bank selection in this first experiment. Native response verification is a prerequisite, not an adjustable nuisance parameter. White clipping is an explicit mismatch/erasure control, not something this linear template claims to model.
5. **Source/coverage mask.** Retain complete carrier blocks whose source-luma range is at most 8 in their 18×18 neighborhood (the 6×6 block with a six-pixel margin), and whose pixels are supported for every candidate transform. Fix this common mask before maximizing the objective. Require at least 1000 blocks and at least 20% of the page's unmasked predicted pilot energy; otherwise abstain. These are fixed feasibility gates, not statistical confidence thresholds.
6. **Nuisance projection.** On the common mask, subtract a least-squares plane separately in fixed 96×96 reference tiles, then subtract each carrier block's mean. Apply the same fixed linear projection P to candidate residuals and W. This removes slow illumination and block DC while largely preserving the half-block template. Do not fit per-block gradients, use recipient-dependent edge exclusions, or vary the mask to favor a transform. Discard tiles with rank-deficient plane design before any candidate is examined.
7. **Objective.** For aligned luma Y_H maximize the signed normalized correlation J(H)=〈P(Y_H−B),PW〉/(||P(Y_H−B)|| ||PW||) on that mask. If either norm is zero, the candidate is invalid. A negative or zero maximum abstains from refinement; otherwise select the deterministic maximum. Positive J is only an alignment criterion, never evidence of an identity. Record the entire objective surface and runner-up displacement. If the maximum lies on the search boundary, report an out-of-range registration failure instead of enlarging the search after seeing scores.
8. **Decoder.** Use the existing unweighted block-sign decoder with original source subtraction on the selected final image. Do not subtract the shared mean in the accusation stage in this experiment, alter its threshold rule, or score only high-bias symbols. The masked objective chooses geometry; the accusation decoder retains its existing symbol scope.
9. **Physical family, only after self-checks.** Evaluate all four existing captures with the fixed affine baseline and the single selected refinement, showing every result including failure. Allocate a clearly labeled new diagnostic family of H=4×2×1000=8000 and epsilon=10^-6 using the conditional helper. The 289 objective-only candidates do not multiply H. This new allocation does not retrospectively create a lifetime error budget across earlier experiments. Existing captures are exploratory because prior scores already influenced the choice to study this direction.
10. **Decision.** Report objective change, mask/energy retention, chosen displacement, image similarity, zero-correlation fraction, all scores, conditional thresholds and accusations, and runtime. A useful exploratory outcome retains akshay3's attribution and recovers akshay2 with no other row accused under the new family. A worse or unchanged result remains a result. Only new secret-key documents and independently captured pages can confirm improvement; known-row progress on this page alone does not establish a novel or operational capability.

The narrow search is intentional: there is a known working affine baseline for one image, and a 6-pixel carrier can be sensitive to subpixel translation. If the frozen search reaches its boundary or fails under synthetic residual affine distortion, a separately specified affine experiment is warranted. Do not silently convert this experiment into a flexible local-warp optimizer.

## Required synthetic self-checks before physical scoring

| Check | Fixed construction | What must be established |
|---|---|---|
| Renderer expectation | Tiny black/white/gray/ramp source tiles, both template orientations/polarities, strengths 4.0 and 2.2; enumerate all words for a 2×2 symbol region | Analytical expected pixels match the probability-weighted actual renderer output within a declared precision; identify interpolation/rounding errors rather than hiding them in a strength fit. |
| Transform direction | Exact ±1 and ±0.5 pixel shifts of synthetic marked pages; compose baseline and correction | Correct sign and single final resampling; recovered residual shift within one grid step in the identity channel. |
| Shared-signal recovery | 32 independently sampled ideal rows for fixed fresh synthetic biases; impose each of four shifts (±1,0),(0,±1), then identity and fixed sigma-0.75 blur channels | At least 95% of the 256 marked cases recover within 0.25 pixel per axis; publish every case. This checks implementation at the proposed resolution, not print robustness. |
| Independence boundary | Registration function has no row/roster input; swap unused innocent roster data after capture is fixed | Transform, mask, nuisance projection and decoded-word hashes remain bit-identical. Test fails if any roster average or row score enters selection. |
| Proper null | Tiny m=12 toy code with fixed p spanning the supported interval; enumerate all 4096 innocent rows and exact product probabilities for selected y, including y=1[p>1/2] and words from source-only searches | Direct log-MGF agrees with K_y; exact tail is bounded by the computed Chernoff value. Use a toy alpha such as 0.05 so enumeration is informative; do not call a small simulation a 10^-6 measurement. |
| Erasure and shared-only controls | Unmarked source; endpoint white clipping that makes D=0; synthetic B+W without recipient residual; wrong independent geometry | Erased theoretical pilot reports zero energy. Generic search can still find a positive noise peak, which must never itself trigger attribution. Shared-only input may register correctly but has no positive innocent-score drift under independent null rows. |
| Nuisance robustness | Fixed luminance gain 0.85 plus offset 15; fixed slow planar shading; source-edge-only image; near-white quantization | Report objective surfaces and geometrical error. Failure under these controls prevents a claim that physical illumination or clipping has been handled. |

The toy null self-check can verify the tail calculation after arbitrary permitted p-dependent selection by conditioning on each resulting y. It cannot certify the deployed stream generator or prove a physical false-accusation probability. Synthetic row draws are for tests only; they never replace the analytically constructed registration template.

## Closest primary-source work and novelty boundary

| Primary source | Relevant established idea | Difference remaining to investigate here |
|---|---|---|
| [Tardos, *Optimal Probabilistic Fingerprint Codes*](https://www.renyi.hu/~tardos/fingerprint.pdf), STOC 2003 / JACM 2008 | Shared random biases, conditional Bernoulli rows, centered attribution, and collusion-resistant code scaling | Provides the mathematical nonzero mean, but does not implement physical watermark synchronization. |
| [Pereira and Pun, *Robust template matching for affine resistant image watermarks*](https://archive-ouverte.unige.ch/unige:47477), IEEE TIP 2000 | Adds a Fourier-domain template and recovers affine changes before watermark decoding | A fixed synchronization pilot is established prior art. This candidate attempts to reuse the existing conditional mean without adding another embedded layer. |
| [Lin, *Video and Image Watermark Synchronization*](https://www.cerias.purdue.edu/apps/reports_and_papers/view/2858), Purdue dissertation 2005 | Uses temporal/spatial redundancy, including induced autocorrelation structure, for synchronization | Synchronizing from watermark structure itself is established; the proposed p-derived mean is a specific first-moment source of structure. |
| [Mathon, Bas, Cayre and Macq, *Impacts of watermarking security on Tardos-based fingerprinting*](https://research.dial.uclouvain.be/entities/publication/35e8ed6f-e4c7-4db1-a722-0494ec36fa8d), IEEE TIFS 2013 | Studies embedding security, symbol-estimation errors, collusion strategies and attribution together | Directly relevant warning that stronger detectability/registration cannot be equated with stronger collusion security. The abstract does not establish this particular synchronization construction. |
| [Kim et al., *Convolutional Neural Network Architecture for Recovering Watermark Synchronization*](https://arxiv.org/abs/1805.06199), 2018 | Learns a template and extracts its spatial locations to recover synchronization | Template-assisted learned registration predates this proposal; no learned component is proposed here. |
| [Fernandez et al., *Geometric Image Synchronization with Deep Watermarking*](https://arxiv.org/html/2509.15208v1), 2025 preprint | SyncSeal adds a synchronization watermark, predicts geometry, and improves other watermark decoders | A contemporary comparator for utility, but its reported image tests do not validate 6×6 low-amplitude PDF print/camera recovery. |

Searches combined Tardos/fingerprinting with bias, expected carrier, template and synchronization, and followed primary author/institutional records. They did not identify a verified primary publication using exactly the analytic p-derived mean to register this kind of binary spatial fingerprint. That is a limited search result, not an absence proof, patent review, or grounds for a new-name novelty claim. The responsible claim, if an experiment succeeds, is an evaluated application of shared-bias carrier expectation with explicit conditional-null accounting and measured renderer/channel limits.

## Show-stoppers and claim limits

- If print/camera response makes both symbol endpoints equal over the usable page, geometry cannot recover the erased pilot or recipient residual. If only the shared mean survives, registration can succeed while attribution remains impossible.
- The ideal 48.3% energy fraction is meaningful only before loss and source interference. It is not 48.3% of captured image energy, nor evidence of sufficient physical signal.
- A single global transform cannot undo curved paper, rolling-shutter distortion or local print scaling. The proposed translation experiment cannot settle those causes.
- A wrong renderer response, mismatch in source/layout, clipping, or incorrect strength can make the objective favor the wrong transform. Freeze and validate the response before physical scoring.
- A visible shared pattern may be removable or reveal keyed structure. Evaluate removal/collusion separately; do not turn synchronization success into a security claim.
- Recipient access, empirical roster averaging, score-based tuning or adaptive row-dependent feedback invalidates the stated conditional argument. Secret ideal sampling is an assumption, not demonstrated by this public fixture.
- No implementation, production change, physical scoring, dataset download or new physical evidence was performed for this note. Existing artifacts were preserved.
