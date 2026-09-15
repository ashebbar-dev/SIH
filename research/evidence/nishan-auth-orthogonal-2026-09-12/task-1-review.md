# Task 1 independent review

Date: 2026-09-12  
Scope: complete four-new-file diff, frozen spec, implementer report, and preserved `run-01` manifest/results/artifacts.  
Method: read-only review; the stable eight-test suite and sole full study were not rerun.

## Spec Compliance

**Verdict: PASS.** The implementation and preserved run satisfy the binding Task 1 behavior. Gate B's failure is the specified measured scientific outcome, not an implementation defect.

- The carrier fixes 144 DPI, 6-by-6 blocks, strength 4.0, 52,500 Tardos symbols, 72 raw bits, 126 encoded bits, and 200 repeats (`research/experiments/auth_orthogonal_v1/carrier.py:21`, `research/experiments/auth_orthogonal_v1/carrier.py:25`). The premeasurement manifest independently records the same profile, including Tardos `n=1000`, `c=5`, and `epsilon=1e-6` (`research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/manifest.json:5`, `research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/manifest.json:25`).
- The recovered index correspondence is correct: the authenticator PRF selects Tardos **symbol indices**, maps those through `order` to physical block positions, and flips the corresponding symbol orientations (`research/experiments/auth_orthogonal_v1/carrier.py:145`). The unchanged dependency establishes that `order` contains physical positions while `orientations` is symbol-indexed (`prototypes/nishan_pq/nishan/tardos_carrier.py:82`). This resolves the named risk of mixing symbol and block-position index spaces.
- The runner creates five Tardos-only and five matched Tardos-plus-auth PDFs per source, then applies the same coalition prefixes and transform loop to both channels (`research/experiments/auth_orthogonal_v1/run_study.py:405`, `research/experiments/auth_orthogonal_v1/run_study.py:439`). The one-member PNG shortcut is equivalent to an average of one rendered `uint8` page; the unchanged multi-member helper takes the mean and converts to `uint8` before PNG output (`prototypes/nishan_pq/nishan/watermark.py:207`). This resolves the named risk of unmatched rounding/transform policy.
- Independently recomputing Gate A from leaf observations, rather than trusting `gates.gate_a`, gives 44/44 participating exact matches, 36/36 other-issued rejections, 60/60 direct-negative rejections, 6/6 changed-context rejections, and 200/200 wrong-key rejections. The preserved result contains 16 authenticator-positive artifacts, five candidates per artifact, 126 raw sums per candidate, 32 complete 1,000-row Tardos score vectors, and ten fidelity measurements per source. The recorded summary agrees (`research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json:158142`, `research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json:158146`).
- The copying helper's public signature and invocation carry only donor, target, and destination paths (`research/experiments/auth_orthogonal_v1/carrier.py:343`, `research/experiments/auth_orthogonal_v1/run_study.py:613`). It reconstructs each observed image with its soft mask (`research/experiments/auth_orthogonal_v1/carrier.py:365`, `research/experiments/auth_orthogonal_v1/carrier.py:376`). Read-only `pdfimages -list` inspection found two 1190-by-1684 donor images with two soft masks and the same two-image/two-mask structure in the copied PDF.
- The copied target has different bytes and extracted text from the donor while retaining the target's modified text (`research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json:6177`). Both copied artifacts exactly match donor row 0 (`research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json:1697`, `research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json:4779`), so the independently checked Gate B result is correctly false (`research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json:158156`). This supports only the no-go conclusion for transplant-resistant content authentication; it is not a recipient-controlled, asymmetric, or full-system forgery result.
- Evidence integrity checks passed: all 97 paths in `generated_artifact_sha256` match their current files; all ten study/import source hashes match the manifest; all 21 frozen prototype/submission/source/spec/plan hashes match `frozen-inputs.sha256`; and all 26 secret/private-material files checked are mode 0600. The manifest timestamp precedes the earliest transform artifact, and `results.json` follows them. Only `run-01` is present.

## Strengths

- The implementation keeps carrier mechanics reusable and attack-independent: exact decoding retains all 126 summed correlations and compares all 72 decoded bits (`research/experiments/auth_orthogonal_v1/carrier.py:309`, `research/experiments/auth_orthogonal_v1/carrier.py:327`).
- Baseline/auth source, row, coalition, and transform correspondence is explicit in one loop, reducing outcome-selection and comparison drift (`research/experiments/auth_orthogonal_v1/run_study.py:394`).
- Negative controls are observed rather than pre-labelled; changed contexts rebuild both tag and placement/polarity plan, and all wrong-key observations are retained (`research/experiments/auth_orthogonal_v1/run_study.py:490`, `research/experiments/auth_orthogonal_v1/run_study.py:532`).
- The interpretation is appropriately narrow. It does not infer human invisibility, theorem applicability after marking-condition violations, asymmetric security, malicious-provider resistance, or product readiness from the passing digital-replication gate.
- No new dependency, external service, hardware, prototype change, presentation change, submission change, or historical-evidence mutation is present in the reviewed final state.

## Critical findings

None.

## Important findings

None.

## Minor findings

1. **The report's first Gate B sentence is grammatically contradictory.** It says, “Both 0/2 copied-overlay artifacts rejected the donor tag” before correctly explaining that the donor tag survived in both (`research/evidence/nishan-auth-orthogonal-2026-09-12/task-1-report.md:16`). The machine result and the rest of the report are unambiguous: zero of two rejected, both matched, and Gate B failed. Suggested wording: “0/2 copied-overlay artifacts rejected the donor tag.”

2. **The orthogonal-orientation unit test does not exercise a non-identity Tardos order.** Its assertion indexes `tardos_orientation` by `plan.positions`, but `self.order` is identity, so the test cannot detect a symbol-index/physical-position mix-up (`research/experiments/auth_orthogonal_v1/test_carrier.py:90`). The production implementation is correct when checked against the unchanged `_plan` contract; this is a coverage weakness, not a result defect. A future test should use a non-identity permutation and compare against the selected symbol indices.

3. **Gate aggregation relies on upstream completeness rather than enforcing the frozen cardinalities.** `_gate_results` applies `all()` to the observations it receives but does not require 16 positive artifacts or the fixed decision counts (`research/experiments/auth_orthogonal_v1/run_study.py:676`). The current runner reaches this function only after fixed loops complete, and the preserved result has every required case, so the reported outcome is unaffected. Explicit count assertions would make future incomplete-data failures fail closed.

4. **Changed-source state is attached dynamically and accompanied by a dead local.** `DocumentState` does not declare `changed_source_hash`; the runner mutates it later, `_run_document` retrieves it through `getattr`, and `other_source_hash` is unused (`research/experiments/auth_orthogonal_v1/run_study.py:491`, `research/experiments/auth_orthogonal_v1/run_study.py:494`, `research/experiments/auth_orthogonal_v1/run_study.py:766`). Declaring the field would improve type clarity and remove a small maintenance hazard.

## Cannot verify from preserved evidence

- The code calls `secrets.token_bytes`, UUID generation, and ML-DSA-65 key generation, and the manifest contains unique hashes for 2/2 authority secrets, 10/10 authenticator secrets, 200/200 wrong secrets, 10/10 sessions, and 10/10 public keys. Static artifacts cannot independently prove operating-system entropy provenance.
- The directory, progress ledger, report, and timestamps show one `run-01` and no repaired run. Without an external immutable execution log, the review cannot prove that no discarded or deleted run ever occurred or that the quoted console/test transcript is verbatim.
- Current hashes prove that frozen prototype, submission, fixture, spec, and plan inputs match their preflight values. Hashes cannot prove the absence of transient edit-and-restore activity.
- The stable eight-test transcript was reviewed but not rerun, per the controller instruction. No additional targeted test was needed after the concrete dependency questions were resolved by source inspection and preserved artifacts.
- Digital render/text measurements do not verify subjective visibility, accessibility, signature preservation, print/scan recovery, deployment generalization, novelty, or protocol-level security; the implementation does not claim otherwise.

## Task Quality

**Approved.** The minor findings are cleanup and defense-in-depth items; none changes the fixed-input correspondence, matched comparison, control matrix, observed-image copying, artifact integrity, or evidence-backed Gate A/Gate B outcomes.
