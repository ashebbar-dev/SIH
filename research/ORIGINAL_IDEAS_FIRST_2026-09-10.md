# Current focus: improve NISHAN and Dhruva first

## User decision

On 10 September the user explicitly requested: first try our best on the two
existing ideas; consider other problem statements only if they produce no
useful results. This supersedes the earlier wake-word-first research allocation.
NISHAN remains the prepared SIH entry. Dhruva is again an active improvement
track, not rejected because one simple estimator missed its target.

The full ambition remains a genuinely novel, significantly better solution and
a strong SIH entry. Ordinary engineering improvements are useful progress but
will not be presented as proof of a new world-leading method.

## Why this is a reasonable research allocation

Lower final competition can help a strong submission. Early portal counters
are not final team counts or evidence of competitor strength. A crowded
technology does not itself prove that a particular PS will be crowded. The
earlier obscure-statement strategy therefore remains relevant, but cannot
replace technical evidence. Existing working prototypes, requirement knowledge
and prepared artifacts justify deeper investigation before paying switching
costs under the 15 September internal deadline.

## Dhruva: diagnose before adding model complexity

The measured S1 60-second median drift is 18.342%; the legacy diagnostic yields
13.211% using both reference heading and an outage-start reference-speed offset.
That diagnostic changes two factors, so it does not isolate heading alone.
Neither result is a performance ceiling.
The current pipeline omits significant PS requirements and freezes
sequence-specific calibration. **Further inspection found a benchmark defect:**
S4 phone rows35185/35186 are312.142 seconds apart while the corresponding
VBOX rows are0.1 seconds apart. The loader ignores those timestamps and pairs
rows directly. The earlier47.5–63.7% transfer drifts therefore cannot be used as
clean evidence of estimator generalization; repair alignment and missing-data
handling first. The raw gap has been independently verified by the main agent.

Immediate work is to separate speed estimation from timing, heading and
mounting errors with controlled oracle ablations; those reference-assisted
results must never be labeled phone-only navigation. Follow with causal,
pre-outage calibration and learned-speed improvements, then road constraints.
Compare held-out journeys, all errors and failure buckets, not only a favorable
median. Reserve new journeys for confirmation after experimental selection.

The [timestamp-aligned factorial experiment](DHRUVA_ALIGNED_ABLATION_FINDINGS_2026-09-10.md)
now has completed numerical review:370 valid common60s windows,13 fixed
methods, and all outcomes retained. Learned speed remains a major limitation,
especially onS3a; oracle results are not navigation performance. A follow-on
[source-reference check](DHRUVA_REFERENCE_QUALITY_FINDINGS_2026-09-10.md) found
GPS speed dropouts among71 S1 training samples and a few evaluation intervals.
The independent [raw-reference audit](DHRUVA_REFERENCE_QUALITY_AUDIT_2026-09-10.md)
now quantifies channel disagreements and affected intervals. These findings
do not explain all remaining model error. No existing sample exclusions or
evidence have been changed.

## NISHAN: strengthen the actual forensic task

Keep real PQ operations and the repaired evidence policy intact. Investigate
physical-channel estimation and recovery on the same marked documents before
changing the entire architecture: source cancellation, print/camera response,
registration error and local reliability may affect the current hard decoder.
Noise-aware soft Tardos decoding already exists and is a comparator, not an
invention. Any candidate physical-channel estimator needs an exact mechanism,
closest-prior-art check and matched testing before a novelty claim.

Useful improvement must increase correct recovery at controlled erroneous
attribution and visual distortion, rather than simply lowering thresholds or
abstaining more. Use independent documents and real captures; simulation is
development evidence only. A malicious-distributor non-framing protocol remains
a separate hard cryptographic problem, not something recipient signatures
already solve.

A [fixed-fixture capture diagnostic](NISHAN_CAPTURE_DECODER_FINDINGS_2026-09-10.md)
now recovers the correct row in 7/8 simulated conditions rather than 6/8 using
a known conditional-threshold baseline. This is useful exploratory progress,
not a new algorithm, physical-capture validation or a measured false-accusation
guarantee. The production decision rule has not been changed.

The user has now supplied a [real printed-page Doc Scanner capture](NISHAN_FIRST_PHYSICAL_CAPTURE_2026-09-10.md).
The unchanged decoder recovers no row and accuses nobody else; this physical
failure is retained. A normal-camera photo of the same sheet has been requested
to help separate printing loss from app processing. Physical diagnosis takes
priority over the saved, not-yet-executed synthetic tone-probe plan.

Update after all four supplied files: the larger camera JPEG `akshay3.jpeg`
retains useful watermark signal. The previously reviewed conditional rule
recovers only its correct row (score1357.130, threshold1077.189,
highest-other588.274), while the old threshold2100 misses it. All other files
remain no-accusation. Independent review verified the evidence; one printed
fixture does not establish novelty, broad physical robustness or security.

Further [physical alignment controls](NISHAN_PHYSICAL_ALIGNMENT_FINDINGS_2026-09-10.md)
strengthen the akshay3 correct-row score with affine refinement, but recover
no additional capture. Homography improves text alignment while losing that
watermark decision, including in a single-final-resampling control. All
profiles and failures remain recorded; no score-based transform selection
has been adopted. A bias-derived registration objective is now implemented
and synthetically checked, but physical improvement remains unproven.

The [bias-derived design audit](NISHAN_BIAS_SYNC_DESIGN_2026-09-10.md) is now
complete and the fixed synthetic gate has passed independent review:256/256
shift recoveries and8/8 renderer cases. The
[fixed physical task](NISHAN_BIAS_PHYSICAL_FINDINGS_2026-09-11.md) has now run:
akshay3's match strengthens but no additional capture is recovered; akshay2
still fails. Two other refinement profiles hit the search boundary. Its
independent implementation review is complete; the final review found no
Critical/Important issues. The process froze all image/
bias-only transforms and words before a separate process generated the roster.
Scientific gate failures must remain failures, not a reason to tune against
the known recipient.

## Paused work and confirmed equipment

- Wake-word source research, downloaded models/validation features and scoring
  work are retained. Its implementation worker was interrupted on the user's
  focus change; unfinished runtime tests are not a completed application.
- No further alternative downloads, training or firmware work is scheduled.
- ESP32 is identified as ESP32-D0WD-V3 rev3.1 with 4MB flash. Its firmware was
  not written or erased. Flash size is not RAM usage.
- Earbuds/earphones are available, but the kit has no microphone. The stage mic
  would only be received on stage and is not development equipment. No mic
  purchase is needed for the two active projects.
- Six people, printer/scanner access, an RTX3060 laptop and optional free GPU
  sessions remain the working resource assumptions; no remote GPU session has
  been provisioned here.

## Revisit condition

Do not revive alternatives after one failed run. First test credible,
cause-driven changes and strong comparisons on both ideas, preserve negative
results, and assess useful gains and remaining deadline risk with the user.
Neither project has yet established the original world-leading novelty goal.
