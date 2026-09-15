# Controller artifact validation — 12 September 2026

The current editable PPTX and matching PDF are a validated **draft**, not an uploaded or accepted submission. Team name, team ID and repository URL remain unknown.

## Export and structure

After Task 2 source approval, the controller exported with LibreOffice 26.8.0.3 using the official-template PPTX and a fresh profile under `/tmp/nishan-selection-4FsFm3/lo-profile`. The initial export (exec session68129) completed exit0; a Mesa/libclc environment warning was observed, but export and subsequent validation succeeded. The visual-fix re-export (session88176) also completed exit0. Neither process is left running. The old PDF remains recoverable in the preserved snapshots.

Command: `libreoffice --headless --convert-to pdf --outdir /home/user_end4/MySpace/SIH/submissions/SIH26237_NISHAN_PQ -env:UserInstallation=file:///tmp/nishan-selection-4FsFm3/lo-profile /home/user_end4/MySpace/SIH/submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pptx`.

The final artifact verifier reads six PDF pages and six PPTX slides. PDF size is 960.009 × 540 points (expected rounded960 ×540). PPTX compressed data passed integrity checks; all slides retain editable content and matching embedded/exported notes. Required text, R1–R14/P1–P24 note coverage, numerical historical evidence and current safeguard evidence checks pass.

## Visual inspection

All six pages of the first export were rendered with `pdftoppm -r 100 -png` and individually viewed by the controller. The only issue found was slide2's long green headline reaching the SIH logo. A bounded source fix shortened the headline and constrained its native textbox right edge to10.3in; a regression failed before the fix and passed afterward. Scoped source re-review approved the change.

The final PDF was rendered to `/tmp/nishan-selection-4FsFm3/final-slide-1.png` through `final-slide-6.png`. The controller viewed final slide2 and confirmed its headline visibly clears the logo. Byte-for-byte `cmp` checks for slides1,3,4,5,6 against the previously inspected renders all returned exit0. Thus all six final renders are covered by actual visual inspection, with no remaining observed clipping or overlaps. Small reference/footnote type is intentional; principal slide content is readable.

## Actual verifier outcomes

- `.venv/bin/python submissions/SIH26237_NISHAN_PQ/verify_submission.py --allow-placeholders`: exit0, `ok:true`, no errors. Saved exact output in `draft-verification.json`.
- The same command without `--allow-placeholders`: exit1, `ok:false`, **only** the missing-placeholder error. Saved exact output in `strict-verification.json`.
- Four placeholder tokens represent three user-supplied values: registered team name (two render variants), team ID, and public repository URL. Strict readiness has deliberately not been claimed.
- Fresh evidence:12/12 named scenarios, real PQC ready,19 current code hashes verified. These are synthetic security scenarios, not population trials.
- Separate stable suites: prototype59/59 (`task-1-fix1-suite-final.txt`); presentation33/33 (`task-2-fix2-deck-suite-final.txt`). These suite runs were not duplicated by the controller.

Final deliverable hashes are in `final-artifacts.sha256`. Historical inputs/template are checked against `presentation-inputs-before.sha256`. The original Sol Ultra reviews were consulted, but its unreplicated authenticator probe numbers and anti-framing claims are not presentation results.

## Remaining boundaries

Local validator/witness governance and software/key custody remain trusted; this does not meet R8 against one administrator controlling all state. Operator framing, watermark removal/retyping, reference-assisted detection and session-not-human-guilt limits remain disclosed. Historical physical recovery is0/4 at the shipped threshold; exploratory profiles recover the same1/4 capture. Independent governance, portable independent proof verification and robust physical recovery remain future work.
