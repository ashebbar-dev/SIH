# Task 2 independent source review

## Spec compliance

**Verdict: NEEDS FIXES.** The eight-file Task 2 change substantially implements
the presentation/evidence contract, but three Important source issues remain.
There are no Critical findings.

**Binary-layout status: cannot verify; pending controller review.** The PPTX is an
opaque binary in the supplied diff. I did not export, render or visually inspect
it. The unchanged old PDF is intentional at this source gate, not a missing Task
2 implementation. Matching PDF export, six-page render/layout inspection and
artifact-level draft/strict verification remain controller-owned after fixes.

Review basis: the complete task-only snapshot diff, current changed-file source,
the Task 2 brief, binding readiness specification and editorial brief, the Task
2 handoff report, current `demo/results.json`, and the supplied stable log. I did
not rerun a suite. The stable log records `Ran 28 tests in 7.746s` and `OK`; the
earlier `task-2-deck-suite-final.txt` correctly remains a failed wording run.

## Strengths

- `deck_evidence.py` requires the exact 12 unique reviewed case names, Boolean
  true case/summary verdicts, real ML-KEM-768 and ML-DSA-65 readiness, a nonempty
  OpenSSL version, limitations, and required hash coverage for all 16 `nishan`
  modules plus the runner and two review tests. All 19 hashes in the current
  report match the current files.
- `build_deck.py` validates fresh evidence before saving an output; the verifier
  independently rejects missing, malformed, failed or hash-drifted evidence.
- The six official sections are pitch-led and use editable-shape source. Detailed
  audit context moved to notes; current exported notes contain every R1–R14 and
  P1–P24 label exactly once.
- The central claim boundaries are unusually disciplined: R8 remains NOT MET;
  validator/witness custody is co-located; software/key custody, framing,
  removal/retyping, non-blind tracing and session-not-human-guilt limits remain.
- Demo scope is stated correctly in the primary locations: `build_deck.py:548`
  says `wrong pin blocks release; rollback blocks release + trace`, and
  `deck_evidence.py:390` says the tested wrong pin is release-only while the
  tested rollback covers release and trace.
- Historical 30/30 JPEG-Q55 evidence is labeled a one-document/codebook
  visual-channel study, not current strict-PDF attribution. Physical evidence is
  preserved as shipped 0/4 and the same exploratory 1/4 capture in both profiles.
  Different encodings are not presented as independent administrative
  authorities.
- `DEMO_RUNBOOK.md` otherwise gives a useful five-minute flow, fresh/no-overwrite
  behavior, exact case names, fail-closed checkpoints, and the committed-record
  boundary. Team name, team ID and repository remain explicit placeholders;
  draft allowance and strict failure are preserved.

## Critical issues

None.

## Important issues

### 1. The fresh-evidence schema check is too shallow for the claims it gates

**Files:** `submissions/SIH26237_NISHAN_PQ/deck_evidence.py:92`,
`submissions/SIH26237_NISHAN_PQ/deck_evidence.py:118`,
`submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py:148`

**Evidence:** `validate_safeguard_evidence` accepts any object or list as a
case's `observed` value and accepts an empty `profile` object. For example, a
case named `wrong_pin_rejected` with `passed: true` and `observed: {}` passes the
validator. The builder then emits specific claims about output nonpublication,
distinct rows, corroborated/empty attribution, read-only hashes and preserved
destinations. Exact names and true verdict flags are necessary, but they do not
detect a missing or drifted observation schema. The new tests exercise names,
verdicts, PQC and hashes, but not nested observation/profile structure.

**How to fix:** validate the required profile fields and types, then define
per-scenario required observation fields/types and the minimal invariants used
by the deck (for example distinct rows/sessions; actual hash equals signed hash;
clean corroboration; empty raster/short-PDF attribution; release-only wrong-pin
rejection; release+trace rollback rejection; equal trace hashes; no publication
and preserved destination). Add mutations that remove or mistype those fields
and prove both the builder and verifier reject them.

### 2. The fresh judge-run example writes secret-bearing demo state inside the future repository tree

**File:** `submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md:15` and
`submissions/SIH26237_NISHAN_PQ/DEMO_RUNBOOK.md:25`

**Evidence:** the runbook says not to copy generated private material into the
repository, but its example output is
`research/evidence/.../demo-judges-run-01`. The runner's current output shape
includes `fixture/secret.bin` and witness/private-key state. The present
`.gitignore` has an exact rule for the reviewed `demo/fixture/secret.bin`, not
for a new `demo-judges-run-*/fixture/secret.bin`. No Git repository exists now
and these are synthetic test secrets, not production keys, but following the
runbook after repository initialization would create avoidable accidental-
publication risk.

**How to fix:** use a fresh external path such as
`/tmp/nishan-judges-run-01` in the invocation and both inspection commands.
Keep the no-overwrite rule and explicitly delete/trash that disposable run only
after the session if desired. Do not relocate or rewrite the reviewed Task 1
evidence.

### 3. Slide 2 mislabels two security mechanisms in visible copy

**File:** `submissions/SIH26237_NISHAN_PQ/build_deck.py:427` and
`submissions/SIH26237_NISHAN_PQ/build_deck.py:448`

**Evidence:** `configured mode also pins a signed checkpoint` names the wrong
object: the caller pins the actual witness verification key and verifies the
signed checkpoint chain. The flow label `Authorize / ML-KEM-768` can likewise
read as though ML-KEM performs authorization; FIPS 203 provides key
encapsulation, while authorization is enforced by the surrounding policy and
identity checks. The detailed notes are accurate, but these are prominent
judge-facing slide labels.

**How to fix:** use wording such as `verifies signed checkpoint state under a
caller-provisioned witness-key pin` and rename the flow step to `Deliver key /
ML-KEM-768` (or `Wrap key / ML-KEM-768`). Regenerate PPTX/notes afterward.

## Minor issues

### 1. The feasibility slide omits the confirmed six-person delivery capacity

**File:** `submissions/SIH26237_NISHAN_PQ/build_deck.py:530`

**Evidence:** slide 4 provides repeatable tests, saved evidence and prototype
results, but neither the slide nor its notes mention the confirmed six-person
team requested by the editorial brief's feasibility argument.

**How to fix:** add one compact feasibility line, for example `Six-person team ·
existing offline laptop prototype · repeatable saved evidence`. Treat this as
selection polish, not a prototype blocker.

### 2. Three helpers and two parameters became dead after the slide rewrite

**File:** `submissions/SIH26237_NISHAN_PQ/build_deck.py:397`,
`submissions/SIH26237_NISHAN_PQ/build_deck.py:514`,
`submissions/SIH26237_NISHAN_PQ/build_deck.py:520`,
`submissions/SIH26237_NISHAN_PQ/build_deck.py:566`

**Evidence:** `slide_two` no longer uses `physical` or `digital`, and
`metric_badge`, `risk_row` and `benefit_card` have no callers. This is a small
Speculative Generality/dead-code smell, not a behavior defect.

**How to fix:** remove the unused parameters/helpers and update the one call, or
leave them for a post-submission cleanup if minimizing churn before export.

## File-by-file disposition

- `DEMO_RUNBOOK.md`: strong flow and boundaries; Important output-root issue.
- `NISHAN-PQ_SIH26237.pptx`: changed binary acknowledged; visual/layout approval
  is not possible at this source gate.
- `NISHAN-PQ_SIH26237_speaker_notes.md`: compliant claim boundaries and exact
  audit-label coverage; no additional source finding.
- `build_deck.py`: correct six-slide architecture and evidence integration;
  Important crypto/pin wording plus Minor feasibility/dead-code findings.
- `deck_evidence.py`: correct exact-name/PQC/hash gate; Important nested-schema
  gap.
- `paste_ready_submission.md`: accurate main evidence section, including
  release-only wrong-pin and release+trace rollback observations; no additional
  finding.
- `tests/test_deck_update.py`: good RED/GREEN and drift/package coverage; nested
  schema gap belongs to Important issue 1.
- `verify_submission.py`: correctly requires fresh evidence and preserves
  placeholder behavior; no additional source finding. Portable independent
  verification remains an explicitly stated roadmap item.

## Quality verdict

**NEEDS FIXES.** Resolve the three Important items before the controller exports
the final PDF. The Minor items should not independently block export. After the
fix round, binary layout and artifact draft/strict results still require the
separate controller check described above.
