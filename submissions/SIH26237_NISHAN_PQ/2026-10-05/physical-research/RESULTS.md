# Physical watermark research — 28 September 2026

This is an evidence summary for the current research campaign, not a production
qualification or a claim that the SIH submission must be selected.

## Fresh stable-system verification, separate from physical robustness

On28September the unchanged main product passed59unit/integration tests and
a fresh replay of all12synthetic release-safeguard scenarios using real
ML-KEM-768/ML-DSA-65. The scenario replay covers concurrent releases, exact
signed-output hashes, clean dual-channel trace, read-only tracing, transplant
and low-capacity abstention, wrong witness pin, rollback refusal, and
checkpoint-failure publication safety. Evidence and limitations are in
`fresh-foundation-check.md` and `fresh-stable-safeguards-v1/results.json`.
These are implementation checks, not certification or physical recovery.

## Best completed result

The local source-content alignment plus fixed contrast receiver **R15** improves
correct Test3 finite-registry session associations from **4/24 to 9/24** with
unchanged marks, payloads and acceptance thresholds. No earlier successful
Test3 association is lost. Exact token reconstruction improves from **0/24 to
2/24**. On the older eight marked paired-glyph photos, finite associations stay
**5/8**, while exact reconstruction improves from **0/8 to 1/8**.

This is a real improvement on the tested, now-known images. It is **not enough
to claim general print/photo/scanner robustness**. In particular, all six marked
Test3 tilted photographs still fail.

| Test3 route | Marked cases | Original finite associations | R15 finite associations | R15 exact tokens |
|---|---:|---:|---:|---:|
| Normal camera photo | 6 | 1 | 2 | 1 |
| WhatsApp photo transformation | 6 | 2 | 3 | 0 |
| Real tilted capture | 6 | 0 | 0 | 0 |
| Scanner-app image | 6 | 1 | 4 | 1 |
| **Total** | **24** | **4** | **9** | **2** |

The same R15 Test3 results by printed profile are linear RS(17,9): **5/8**, 
spread RS(17,9): **3/8**, and capacity RS(35,9): **1/8**. Each profile includes
normal, WhatsApp, tilted and scanner routes for two printed sessions. The longer
code is not empirically better on this set. Do not headline a selected easy-route
subset as general robustness; the full denominator and all tilt failures remain
part of the result.

R15 produced no association for any tested control: 12 Test3 control/profile
applications and four older controls. These are **eight unique control photos
from two control sheets**, not 16 independent physical experiments and not a
measured zero false-attribution probability.

### What the two result types mean

- **Finite-registry association:** the observed bits satisfy the unchanged
  `2e+s < dmin` unique-distance rule against a fixed synthetic 1,000-record
  registry, after the pilot gate. This associates a source copy/session; it is
  not independent recovery of the complete token and is not a calibrated
  false-positive probability.
- **Exact token reconstruction:** the RS decoder reconstructs the 72-bit token
  without searching the registry for the closest row; that token then exactly
  matches a registry record. The token is a lookup identifier, not a full
  post-quantum signature, ledger proof or proof of a human's culpability.

These are compact printed session-token carriers, not successful recovery of
the original 52,500-symbol Tardos channel. Keeping Tardos elsewhere in the
architecture does not transfer its collusion guarantee to a photographed copy
when only the compact token survives.

The successful exact Test3 cases are `03-scanner` (synthetic recipient/session
19) and `04-normal` (synthetic recipient/session 7). R15 also exactly recovers
the older `03-normal` case. Physical identity labels are based on the user's
download-order attestation; image metadata corroborates routes, not the hidden
printed recipient identity.

## Completed receiver comparisons

Every full paired-glyph comparison uses the same 44 inputs: four clean renders,
28 Test3 files and 12 older Test2 files. The 40 physical files contain 32 marked
applications and 16 control/profile applications. Do not add these repeated
replays together and call them independent new trials.

| Arm | Mechanism | Test3 finite / exact | Older finite / exact | Interpretation |
|---|---|---|---|---|
| Frozen baseline | Original retained receiver | 4/24 · 0/24 | 5/8 · 0/8 | Reference |
| R9 | Numerical rectangle-grid repair | 4/24 · 0/24 | 5/8 · 0/8 | Correctness repair, no recovery gain |
| R10 | Global high-resolution content refinement | 4/24 · 0/24 | 5/8 · 0/8 | Every refinement falls back |
| R11 | Fixed source-ink contrast | 4/24 · 0/24 | 5/8 · 0/8 | More observable marks, no association gain |
| R12 | Strict page-channel/template evidence | 0/24 · 0/24 | 0/8 · 0/8 | Rejected candidate; loses clean support too |
| R13 | Validated local source-content mesh | 8/24 · 2/24 | 5/8 · 0/8 | Positive measured alignment gain |
| **R15** | **R13 followed by fixed contrast** | **9/24 · 2/24** | **5/8 · 1/8** | **Best completed receiver** |
| R16 | Contrast before local tracking as well | 9/24 · 2/24 | 5/8 · 0/8 | No additional recovery; loses one R15 exact result |
| R14 | Public-pilot global synchronization | No valid physical comparison | No valid physical comparison | Sparse/full sampling parity fails before search; raw all-abstaining run retained |
| R19 | R14 repaired native sampling, fixed content-candidate veto | 0/24 · 0/24 | 0/8 · 0/8 | Clean support restored; physical alignment gates reject every applicable case |

No receiver union is used: these are separate full-corpus arms, not the best
answer selected separately for each photo.

### R22-A: stopped during source-only qualification

The coarse-content alternative at `7123d08` was not run on photographs.
After a pre-physical Pro-reviewed change to use the same fixed Gaussian
geometry representation at both pyramid levels, both retained fractional-shift
failures passed. A frozen 18-window by 6-shift matrix then accepted 88 of 90
nonzero source-only cases, all within 0.04126 pixels per component. However,
one of 18 zero-shift cases incorrectly passed the no-improvement acceptance
gate, so the prescribed STOP A rule applied. This is a qualification failure,
not a physical recovery gain or proof that all coarse alignment is futile.

The final 108-case artifact SHA256 is
`e2832ff4633fd293a28b7543680beff9152e8f7be05686a0ea9b478b214a2012`, at
`../.runtime/task4-coarse-source-qualification-20260928-final.json`.
Its bounded source-qualification/evidence review is complete; three separate
cache-integrity implementation findings remain deferred, and the branch is not
integration-ready. No thresholds were changed to rescue the failed case; field
integration was not attempted.

### Mechanism checks and stopped directions

The H0 sampler-only control reconstructs the original normalized images and
substitutes the local mesh's sampler with a zero field. All marked hard-bit
vectors stay unchanged. Mere sampler substitution did not reproduce the R13
gains on this corpus.

The fixed Pro soft-RS certificate was checked again after R15 improved image
evidence. Two qualifying Test3 codewords were already exactly recovered; the
third still fails the unchanged pilot gate. No new gated correct recovery is
possible under that particular frozen certificate. This is a truth-assisted
feasibility diagnostic, not an implemented GMD decoder or a claim against all
soft decoding methods.

Pro's proposed blur-matched tracking experiment required an already accepted
nonzero channel blur estimate for a failed tilted capture. None of the six
marked Test3 tilts qualifies. Its stop rule was followed; no arbitrary sigma
search was started.

## Completed CoreMark-inspired receiver transfers

The CM-NISHAN geometry transfer R17 exposed a spurious field on clean source
renders, so it was stopped before physical testing. R20's matched-raster source
reference removed that confound under source checks while preserving the final
600-DPI decoder and thresholds. Its full physical replay is now complete.

| Separate CM arm | Marked physical sessions | Controls abstaining | Marked clean renders |
|---|---:|---:|---:|
| Original CM baseline | 0/16 | 8/8 | — |
| R18 source-referenced photometry | 0/16 | 8/8 | 4/4 |
| R20 validated matched-raster local geometry | 0/16 | 8/8 | 4/4 |
| R21 combined frozen geometry/photometry | 0/16 | 8/8 | 4/4 |
| R22B fixed-axis core / hard reference decision | 0/16 | 8/8 | 4/4 |

R22B's new six-clean-input gate passed before the 24-photo replay: all four
152-bit marked vectors were exactly correct, with both controls abstaining
and the inherited R21 pixels/support unchanged. Physical evaluation at commit
`952e268f4f5e90c85e18dead467e2ca4a30b7de0` completed all 24 rows with no process
failure. **No complete marked physical token was recovered.**

The extractor change raised correct marked bits from 519 to 1,354 out of 2,432,
and reduced erasures from 1,737 to 456. However, 445 previously erased bits
became wrong, versus 836 becoming correct. Accuracy among observed bits fell
from 74.7% to 68.5%; full-denominator correct-bit fraction rose from 21.3% to
55.7%. These diagnostics show that the earlier extractor discarded surviving
signal, but removing its vetoes is not enough for exact session recovery.
Neither the pilot/ECC gates nor the printed marks were changed to rescue it.

R22B clean evaluation SHA256:
`4a17639dcf6316ecbd4d08950727c66b0914b0af8f5a3283b5bf6947296ad0f5`.
Physical evaluation SHA256:
`dee3f2cb83fb285f711945a104736112fcb3a5afa371b08238f2e8b8d404aa97`.
Artifacts are under `../worktrees/cm-paper-r22/outputs/cm-paper-r22-clean-v1`
and `cm-paper-r22-physical-v1`. Source/controller reviews are complete;
independent final evidence review accepted the complete bounded negative result
in `r22b-final-evidence-review.md`. This remains a component
ablation on known development captures, not a faithful CoreMark reproduction.

Both new arms retain both clean-control abstentions. R18 calibration applied
on all 21 inputs passing upstream geometry. R20 accepted a local correction on
14 physical inputs, retained H0 on 7, and did not run on 3 upstream rejections.
Neither changed the physical session-recovery count. These are completed
negative comparisons, not branches omitted because the results were poor.

R20 increases net correct observed payload/pilot bits from 559 to 601, but every
marked pilot vector is unchanged: no case has 14 observed pilots (maximum 10),
and all cases retain 14–17 erased RS bytes against an 8-byte erasure budget.
R18 reduces missing-core erasures but increases missing-reference and ambiguous
measurements. Its marked correct-bit count falls 559→529. Better visibility in
some regions therefore does not yet make either physical packet recoverable.
These counts explain the results; they are not inputs used to select a recipient.

These CM branches concern the already-printed **CoreMark-inspired** carrier,
not a faithful reproduction of the CoreMark paper. No new prints or payloads
are silently substituted.

R18 full-corpus evidence is in
`../worktrees/cm-photometry-r18/outputs/cm-photometry-r18-v1/summary.json`,
commit `b8ae70febe8a0878ec37f46abf77bec2c36b88ec`. Its 30-input replay has a
separate denominator from the paired-glyph Test3 results; do not add or combine
them into a best-of detector.

R20 evidence is in
`../worktrees/cm-matchedraster-r20/outputs/cm-matchedraster-r20-v1/summary.json`,
commit `b05a036595231ea6b82201bc9990bc99fb17c5f6`.
Independent evidence audits verified all 171 R18 and 172 R20 hash bindings,
all 30 exit-zero children per arm, fixed input/legacy-code commitments, and
the raw-bit/packet/session counts.

R19's complete 44-input replay at
`60190c2a0c96359ad1ab4797a9ab250ad7cb5788` restores exact native-sampling parity.
All three clean marked cases decode; the clean control abstains. All 47 physical
profile applications reaching synchronization are rejected under the frozen
alignment gates; one older control rejects upstream. Thus it recovers 0/24
Test3 and 0/8 older marked sessions, with all control applications abstaining.
Evidence: `../worktrees/receiver-pilotsync-r19/outputs/test3-pilotsync-r19-v1/summary.json`.
Independent audit verified all 44 exits, 191 artifact bindings and 14 code
dependencies. All 53 applications reaching synchronization have exact raw,
normalized and support zero-shift parity. Physical vetoes are 9 conditioning,
17 search-boundary and 21 content-optimum failures. This distinguishes the
repaired implementation from the still-unsuccessful physical mechanism.

## Final R21 composition preflight — completed, stop rule reached

Following Pro follow-up 5, R21 applies unchanged R18 photometry to cached,
validated R20 geometry. It uses the same prints and thresholds, reconstructs
and verifies the exact cached pixels/support, refits photometry on those
coordinates, and keeps canonical measurement masks unchanged. The producer
does not parse the registry. All measurement vectors are frozen before the
separate evaluator joins synthetic truth.

All **30 inputs completed successfully**: six clean and 24 physical. Diagnostic
packet replay recovers all four clean marked tokens and neither clean control.
It recovers **0/16 physical marked tokens**; all eight physical controls abstain.
Every physical marked packet fails the unchanged pilot gate. All retain 14–17
erased payload bytes, before accounting for erroneous observed bytes; the
RS(17,9) budget is only eight erasures or the equivalent `2E+S <= 8`.

The physical marked per-position comparison against R20 is:

- 80 erased bits become correct observations, and 35 become wrong observations.
- 217 observations become erasures.
- 32 wrong observations flip correct; 49 correct observations flip wrong.
- Net correct observed bits decline **601→519**, while erasures rise
  **1,635→1,737** across the same 16×152 bit positions.

No accepted-mesh marked case meets both the unchanged pilot gate and byte-RS
budget. The fixed experiment-wide decision is therefore **STOP**. No fresh
association replay, alternative photometric search, relaxed threshold or
per-photo receiver union follows this negative preflight. This is a measured
failure of this composition on these captures, not proof that all possible
CoreMark receivers or carriers are impossible.

Source commit: `e32364e526829844bc7184ec56fd2cd2b8ce2f37`.
Evidence directory: `../worktrees/cm-combined-r21/outputs/cm-combined-r21-preflight-v1`.
The separate execution audit passes all 30 exits, 60 events and 286 artifact
bindings, independently reproducing the packet/budget decision. It also binds
the exact evaluator, code commit and seven-field numerical runtime. Child
time totals 371.714 seconds; peak per-child RSS is 661,140 KiB. This is a
preflight plus diagnostic packet replay, not a production attribution result.
An independent reviewer also reproduced every per-position transition and byte
budget directly from the saved vectors. All 16 marked physical cases fail both
the pilot and RS gates; `2E+S` ranges from 16 to 20 against a maximum of eight.
The negative result is not an execution/provenance failure.

Evidence hashes:

- Run manifest: `f2a4f02b4cab8440bfa539305eabed7be3a12eb8d54972d4a3f3777cef7ca56c`.
- Evaluation: `a44fabf1240b722758e0dd9179a38a68f16217506d26474e614843b4f62c9075`.
- Execution audit: `cf4fe23b091ae4f8c2d39c77ade43ac0b2812dee0f5a43662361a19dda0247aa`.

R15 remains the best completed receiver. A faithful CoreMark reproduction is
still untested, not disproved by this CoreMark-inspired carrier. Testing a
different embedding physically requires fresh prints of that embedding; it
cannot be validated by changing the decoder on these existing photographs.

## Reproducibility and presentation boundaries

Best receiver commit: `f48f52b31bbbe8b0841e8f462d60009e21b5c3c0` in
`../worktrees/receiver-meshcontrast-r15`.

Its complete per-case evidence is
`../worktrees/receiver-meshcontrast-r15/outputs/test3-meshcontrast-r15-v1/summary.json`.
Input files, source, printed pack, decoder dependencies, code commit and timing
outputs are hash-bound. Baseline, unsuccessful arms and all failure cases are
retained. Main/demo code has not been replaced or pushed.

Safe presentation claim:

> On our fixed physical capture set, source-content local alignment and fixed
> contrast correction increased correct session associations from 4/24 to 9/24
> without changing the printed watermark or acceptance thresholds. We also
> reconstructed exact session tokens from two Test3 artifacts. Tilt robustness
> and generalization remain unresolved.

Do not claim 45/48 robustness, arbitrary scanner/filter survival, physical
collusion resistance, operator non-framing, general content authentication,
verified post-quantum provenance from these standalone token tests, independent
held-out performance, or guaranteed selection.
