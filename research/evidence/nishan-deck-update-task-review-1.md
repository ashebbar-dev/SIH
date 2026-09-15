# Task1 independent review — gpt-5.6-sol, high

Verdict: spec issues found; quality Needs fixes. No Critical findings.
Controller's final artifact checks passed; content framing and editable/notes
integration were strengths. This review concerns the fail-closed build contract.

## Important findings

1. `deck_evidence.py:99`: historical competing-score check is unreachable/inverted:
   the previous branch rejects competing accusations, then the historical check
   requires one. Reject `highest_other_score > historical_threshold` when the
   competing historical accusation is absent, symmetric with conditional logic.
   Add a negative test where conditional threshold is higher than historical.
2. `deck_evidence.py:47`, `build_deck.py:410`, `verify_submission.py:179`: loader
   accepts any four names and only aggregates, but slides/notes hard-code
   akshay2/akshay3 and same-capture recovery. Enforce exact capture and recovery
   identity (or derive/verify them) with explicit ValueError, plus renamed and
   recovery-swapped record tests. Missing expected names must not reach KeyError.
3. `build_deck.py:565`, `deck_evidence.py:169,176`, `tests/test_deck_update.py:189`:
   visible `120`, `Four captures`, `One page / four captures` and multiple notes
   result counts are manual literals. Derive all experimental numbers from the
   JSON summary and passed evidence; test generation from safely mutated copies
   rather than checking only canonical strings. Fixed parameter-comparison math
   is context, not a new physical experiment.

## Minor finding

`build_deck.py:551,497,674`: unused jpeg_violation_rate calculation and measured /
evidence_chart inputs remain. Remove dead calculation and either document
compatibility-only parameters or retire them deliberately.

Fix base archive:
`submissions/SIH26237_NISHAN_PQ/archive/2026-09-11-review-round-1/`.
No prototype/evidence modifications are authorized by these findings.
