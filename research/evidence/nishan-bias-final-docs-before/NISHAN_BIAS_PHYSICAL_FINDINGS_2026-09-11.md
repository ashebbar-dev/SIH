# NISHAN shared-bias alignment: physical result

The new fixed refinement strengthens the correct-recipient match on
`akshay3.jpeg`, but recovers no additional supplied photo. `akshay2.jpeg`
remains below its decision threshold. The other two refinement profiles fail
the prescribed search-boundary check. No incorrect recipient is accused in
this experiment. This is a negative result for the stated objective of adding
another physical recovery, alongside a modest score improvement.

The experiment started on 10 September and completed after midnight on
11 September, Asia/Kolkata. Its predeclared evidence-directory name retains
10 September. The physical task's independent spec/quality review is pending;
the synthetic prerequisite has already passed independent review.

## All fixed outcomes

Both profiles were predeclared for every supplied capture. The new diagnostic
family uses H=8000, epsilon=1e-6, and strict score>threshold. Thresholds are
word-dependent and differ from earlier families; none was fitted to make a
known row pass. These are modeled conditional-null thresholds, not certified
physical wrongful-attribution probabilities.

| Capture | Profile | Correct-row score | Highest other score | Threshold | Accused rows | Refinement status |
|---|---|---:|---:|---:|---|---|
| akshay | Affine baseline | 66.070 | 192.472 | 413.812 | None | Not applicable |
| akshay | Shared-bias translation | — | — | — | None | Boundary failure (1.75,2.0) |
| akshay1 | Affine baseline | -11.627 | 209.185 | 441.885 | None | Not applicable |
| akshay1 | Shared-bias translation | — | — | — | None | Boundary failure (-2.0,2.0) |
| akshay2 | Affine baseline | 788.315 | 534.078 | 1021.072 | None | Not applicable |
| akshay2 | Shared-bias translation | 835.191 | 540.986 | 1021.632 | None | Accepted (-0.5,-0.25) |
| akshay3 | Affine baseline | 1709.941 | 549.394 | 1097.482 | Only row0 | Not applicable |
| akshay3 | Shared-bias translation | 1827.334 | 518.086 | 1096.290 | Only row0 | Accepted (0,0.5) |

The historical threshold2100 accuses no row in any profile. Every successful
profile retains its full1000-score vector; failed refinements have no decoded
word and cannot silently fall back to a favorable result. All four baseline
score vectors and composed matrices match the earlier single-resampling affine
controls exactly (maximum differences0, required atol1e-9/rtol0).

For akshay2 the objective changes0.008447→0.008899 and bit-error fraction
0.477848→0.476514; for akshay3 they change0.014285→0.014662 and
0.446190→0.443143. Bit agreement alone is not attribution because the shared
biases affect ordinary agreement. The content-similarity diagnostic decreases
for both accepted refinements. Neither that metric nor any recipient score
selects a transform.

## Separation and checks

The implementation uses the original source PDF to render artificial binary
all-zero/all-one endpoints, the fixture's actual strength4/144DPI/6px geometry,
and the analytical mean derived from the shared biases. It does not use a
recipient template or empirical average of roster rows. A fixed sigma0.75
blur and fixed smooth-source/common-coverage mask precede the 289-candidate
translation search. Search limits are ±2 reference pixels in0.25px steps;
boundary maxima remain failures.

The prepare process saves transforms, complete objective surfaces, response
arrays, masks, correlations and decoded words, then writes a commitment hashing
the two prepared files. A separate process verifies those files before creating
the1000-row roster. It consumes saved words, never re-registering images.
The original RGB8→luma float32 hard-decoder arithmetic remains unchanged.
Prior score-bearing evidence is opened only in the scoring process for the
baseline comparison.

Eight focused process-boundary tests passed. The prerequisite synthetic suite
passed13 focused tests,8 renderer cases and256/256 fixed shift recoveries,
plus null, composition, independence and erasure checks. These synthetic
successes did not predict recovery of the smaller physical photos.

There was one physical prepare run and one separate score run. No original
photo, source PDF, production module or previous result was changed. No
threshold loosening, retry, score-based profile choice or expanded search was
performed after seeing these outcomes.

## What this means for the project

Akshay3 establishes useful physical signal on this printed fixture with the
experimental conditional decoder. This new translation method does not yet
establish increased capture robustness, a novel best-in-world method or a
production security guarantee. The public deterministic fixture, repeated
development use of one page, unverified physical channel and uncertified
numerical tail bound remain limitations. Zero observed incorrect accusations
is not a measured one-in-a-million false-accusation rate.

The new method's local translation scope cannot settle page curvature,
nonuniform scaling, clipping or signal lost during image processing. A further
geometry/channel study would need a separately fixed design and independent
documents/keys for confirmation; these results do not justify repeatedly
tuning the same photos until another row passes.

## Evidence

- [Physical task implementation and complete test/output record](evidence/nishan-bias-registration-task-2-report.md).
- [Prepared metadata and all objective surfaces](evidence/nishan-bias-physical-2026-09-10/preparation.json).
- [Frozen response arrays and words](evidence/nishan-bias-physical-2026-09-10/prepared.npz).
- [Preparation commitment](evidence/nishan-bias-physical-2026-09-10/commitment.json).
- [All scores, failures and baseline comparisons](evidence/nishan-bias-physical-2026-09-10/scores.json).
- [Design, conditional-model argument and prior art](NISHAN_BIAS_SYNC_DESIGN_2026-09-10.md).
- [Plan progress and decisions](evidence/nishan-bias-registration-progress.md).

The preparation commitment SHA256 is
`956678e16fac26228029f6ab34e7bb5e4ef76264b00d4a98898907dc6463c76c`;
the scores SHA256 is
`38ba1ddf81519415d56d70fa7c37fbee940eb1341a796d8cb9fc2ca5c3ad0b9b`.
