# SDD ledger — plan: docs/superpowers/plans/2026-09-11-dhruva-speed-state.md

Previous goal turn: progress. NISHAN's fixed physical experiment and reviews
completed, with no additional capture recovery and unchanged production code.
Current turn adds a vehicle-comparator audit and a corrected interval-target
design. The broad SIH novelty/performance goal remains active; no blocker is
active. User was asked nonblockingly whether a teammate can record phone data
as a passenger in a car; current public-data work does not require an answer.

## Task state

Task1: running in fresh implementer `/root/dhruva_speed_state_kernel`
(gpt-5.6-sol, high), requirements `dhruva-speed-state-task-1-brief.md`,
report `dhruva-speed-state-task-1-report.md`. No real data or fitting in Task1.
Task2: not started; waits for Task1 independent spec/quality gate.

The skill workspace script was run and failed read-only with not-a-Git-repository.
Use this plan-specific research ledger/brief/report/snapshot naming instead;
do not initialize Git or remove any evidence. Generic Git worktree/finishing
skills and final requesting-code-review template are not installed. Existing
implementation/task/scoped-review templates supply the available review flow.

## Preflight

| Pair/task | Agreement check | Result |
|---|---|---|
| Task1 target→Task2 fit | Backward two-row support, common mask | Exact20495/20415 rows; forward target would violate cutoff and is excluded |
| Task1 propagation→Task2 metrics | n=L+1 state/acceleration, ignore first acceleration | Position uses output[:-1]; signed state never receives clipping feedback |
| Task1 absolute→Task2 replay | Old clipping-before-offset ordering | Same branch arithmetic retained |
| Task1 metrics→Task2 summary | dt weights, reference heading, common distance | All370 valid,355 eligible,400×8 complete records |
| Task1 own tests→code | Arbitrary increments, onset/braking, bias and clipping | Meaningful numerical assertions, invalid inputs explicit |
| Task2 own tests→run | Metadata/hash/output guards and reference boundary | No training for tests; real run once after focused green |
| Task2 inputs→fit | Existing manifest/raw hashes, stored clocks, path equality | No new window, calibration or quality-by-error choices |
| Task2 evaluation→decision | Prespecified median/tail/corroboration gates in both arms | Failures retained; historical mismatch disables advance, not data retention |

Ruling: retain snapshots/reports instead of Git commits/worktrees — initialization remains reserved — cost: no commit-based recovery.

Ruling: use backward single-interval targets instead of trailing one-second or forward targets — match the propagated interval and preserve all frozen training rows before cutoff — cost: target noise is not reduced by one-second averaging; this is current-interval estimation, not forecasting.

Ruling: apply the two-endpoint NZ2 mask to both targets — isolate target formulation from row membership — cost:80 rather than71 records are removed from the absolute-speed sensitivity arm; remaining labels are not certified clean.

Ruling: retain a signed accumulated speed state and clip only output — expose bias without introducing another state-projection algorithm — cost: negative internal state can delay output recovery after stopping; report it explicitly.

Ruling: keep reference-heading and reference-initial-speed privileges for this speed diagnostic — isolate the measured bottleneck before full navigation comparisons — cost: improved results would still require deployable initialization, heading and independent-journey validation.

Ruling: use fixed advance criteria and historical-control replay without post-result adjustment — make this branch falsifiable — cost: a real but differently shaped gain may fail this gate and would need a separately specified follow-up.
