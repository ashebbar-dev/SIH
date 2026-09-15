# Dhruva time-alignment review package

Base: both implementation and test file absent before this task.
Head: current stable files reported by `/root/dhruva_time_alignment`.
Git state: no initialized repository; full new-file diff snapshots are retained.

Read the two complete diffs (relative to this directory):

- `dhruva-time-alignment-module-review.diff`
- `dhruva-time-alignment-tests-review.diff`

Task brief: `docs/superpowers/plans/2026-09-10-dhruva-time-alignment.md` (one task).
Report: `research/evidence/dhruva-time-alignment-implementation.md`.
Ledger: `research/evidence/dhruva-time-alignment-progress.md`.

Global constraints, verbatim from the plan:

- No alternative problem-statement work; NISHAN and Dhruva are the active tracks.
- Keep raw inputs and existing benchmark/results unchanged.
- Never interpolate across phone/reference gaps, logger resets or nonmonotonic timestamps.
- Clock calibration may use only the fixed healthy prefix, not evaluation labels or performance.
- Reference-assisted calibration is an offline benchmark operation, not proof of phone-only deployment.
- No Git initialization, commits, firmware, downloads or package changes.
- Use `apply_patch` for code edits; use the existing `.venv` for numerical tests.
