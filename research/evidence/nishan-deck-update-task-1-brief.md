### Task 1: Update the evidence-led deck and verification

**Files:**
- Modify: `submissions/SIH26237_NISHAN_PQ/build_deck.py`
- Modify: `submissions/SIH26237_NISHAN_PQ/verify_submission.py`
- Create: `submissions/SIH26237_NISHAN_PQ/deck_evidence.py`
- Create: `submissions/SIH26237_NISHAN_PQ/tests/test_deck_update.py`
- Generate: `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx`
- Generate: `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pdf`
- Generate: `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237_speaker_notes.md`
- Report: `research/evidence/nishan-deck-update-task-1-report.md`

**Interfaces:**
- Consume existing JSON paths and records specified in the full spec. Read the spec in full; its exact content allocation and notes coverage are binding.
- `deck_evidence.load_physical(path: Path) -> dict`: validated summary plus fixed capture/profile records; exact8 records,4captures, two named profiles; reject missing/duplicate/malformed records and inconsistent accusation/threshold/status fields. Derive counts per profile, no best-profile score selection.
- `deck_evidence.speaker_notes(...) -> list[str]`: six note blocks with corrected14 requirements/P1-P24/source paths and URLs; experimental numerical values come from passed loaded evidence.
- Existing `build(...)` gains optional keyword parameters `physical_path: Path | None = None, repository_url: str = "[INSERT PUBLIC REPOSITORY LINK BEFORE UPLOAD]"`; None resolves the fixed documented physical JSON, not an evidence-free fallback. CLI gains --physical-evidence and --repository-url.
- Preserve `verify(root: Path, allow_placeholders: bool) -> dict` and all valid existing historical artifact checks; add current physical summary and forbidden-claim checks for slide/PDF text. Never reject a negated contextual quotation in notes as if it were an asserted slide claim.

- [ ] **Step 1: Add focused RED tests before implementation.**

Use real small document generation for notes/slide-content tests; no prototype runs.
The following assertions are the numerical contract:

```python
summary = deck_evidence.load_physical(ROOT / "research/evidence/nishan-bias-physical-2026-09-10/scores.json")
self.assertEqual(summary["captures"], 4)
self.assertEqual(summary["historical_recovered"], 0)
self.assertEqual(summary["baseline_recovered"], 1)
self.assertEqual(summary["refined_recovered"], 1)
self.assertEqual(summary["boundary_failures"], 2)
```

Test missing input raises FileNotFoundError; duplicate record, missing profile,
scored record with nonfinite/missing threshold, false counted success all fail
ValueError. Use tempfile and JSON serialization to mutate only test copies.
Check generated PPTX has6slides, notes on6slides, each P1..P24 and R1..R14 exact
labels, supplied team/repository text and no unchanged placeholders when all
supplied. Check rendered slide text forbids the known stale literal phrases
"real physical captures pending" and "Synthetic perspective passes; hardware pending".
Test verifier against temporary copied package outputs with a stale phrase
introduced into slide/PDF text, and with missing physical evidence. Tests should
show negative behavior, not merely membership in a constant list.

Run:
```bash
.venv/bin/python -B -m unittest discover -s submissions/SIH26237_NISHAN_PQ/tests -p 'test_deck_update.py' -v
```
Record the actual RED output/chunk ID.

- [ ] **Step 2: Implement the deck module, notes and all six updated slides.**

Use existing helpers/layout aesthetics; do not introduce new dependencies.
Implement physical summary using fixed records keyed by `(capture, profile)`;
read the existing lists `historical_accused`/`conditional_accused` and matching
expected_row. Never derive successful recovery from a score alone without
checking the saved accusation and competing rows.

Attach/export notes with the same strings:
```python
for slide, note in zip(prs.slides, notes, strict=True):
    slide.notes_slide.notes_text_frame.text = note
```

Keep slide text editable. Adjust geometry/font size deliberately for readability,
but retain the six specified sections and visible material limitations. Remove
the old chart from the slide if replaced by the physical/digital evidence cards;
do not delete the chart file. No generic status matrix of14 green checks.

- [ ] **Step 3: Update verification and run focused GREEN.**

Replace stale REQUIRED_TEXT items with the new exact current claim anchors
chosen in the slide implementation. Compare physical results to the saved source
and verify six notes blocks, R1..R14/P1..P24 coverage and notes export consistency.
Do not weaken existing digital evidence checks or placeholder strictness.
Add actionable errors for missing/malformed physical files.
Run the focused command above and include all output in report.

- [ ] **Step 4: Build artifacts and export matching PDF.**

Controller preserves old files before dispatch. Then:
```bash
.venv/bin/python -B submissions/SIH26237_NISHAN_PQ/build_deck.py
libreoffice -env:UserInstallation=file:///tmp/nishan-deck-review.Cjh7YU/lo-profile --headless --convert-to pdf --outdir submissions/SIH26237_NISHAN_PQ submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx
.venv/bin/python -B submissions/SIH26237_NISHAN_PQ/verify_submission.py --allow-placeholders
.venv/bin/python -B submissions/SIH26237_NISHAN_PQ/verify_submission.py
unzip -t submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx
pdfinfo submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pdf
```
Strict verification is expected to fail only on unknown team/repo placeholders;
it must pass if user supplies all details before the final rebuild. If headless
LibreOffice needs outside-sandbox permission, request normal tool escalation;
do not bypass it. Never overwrite the PPT with rasterized pages.

- [ ] **Step 5: Self-review and report.**

Render all6pages into `/tmp/nishan-deck-review.Cjh7YU/after-*.png` using
pdftoppm; inspect each with view_image. Report any unresolved visual issues.
Record actual build/conversion/verifier/test outcomes and SHA256 of deliverables.
Use before snapshots rather than Git commits because Git initialization is
reserved and the current directory is not a Git repository. No deletion.
Return short DONE/concerns report contract and leave independent review to root.

## Plan self-review

| Check | Result |
|---|---|
| Spec six-slide contents against task | Exact allocation and source data included by binding spec |
| Notes versus slide/PDF claims | Details in notes; material limitations remain visible |
| Tests versus interfaces | Exact physical summary keys and failure types stated |
| Verifier versus placeholders | Draft-mode success distinct from strict upload readiness |
| Files versus task scope | Only deck pipeline, tests and presentation outputs; no prototype changes |

