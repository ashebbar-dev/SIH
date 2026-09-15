# NISHAN deck — controller artifact validation

Date: 11 September 2026. Presentation-only task; no new prototype experiments.

Final editable artifact: `a6d194e11fb589c8831829407b6c702860735433a4e337dc169119ce1981ef88`.

| Check | Evidence | Result |
|---|---|---|
| Final authorized LibreOffice export | chunk `941da5`, session21092 | Exit0; final PPT converted to canonical PDF |
| Draft package verification | chunk `19daf8`, session86455 | Exit0, `ok: true`, no errors; four placeholder strings warned |
| Strict package verification | chunk `4c96b6` | Exit1, `ok: false`; only error is missing team ID/name/repository fields |
| Six-page PDF and format | chunk `989717` | Six pages,960.009x540pt,PDF1.7,959155bytes |
| Final rendering | chunks `5731a7`/`32b78c`, session68616 | Exit0; all six pages rendered under `/tmp/nishan-deck-review.Cjh7YU/final-*.png` |
| Visual inspection | Controller viewed all six final rendered pages | Readable; no visible collisions/overflow. Changed slides2/4 clarify same capture; slide5 includes multi-page validation |
| Editable PPT ZIP and focused tests | worker chunk `96299d` | ZIP clean,11/11 focused tests passed; not redundantly rerun by controller |
| Protected sources/evidence | controller chunk `7197dc` | All21 unchanged hashes passed |

Draft and strict verification also checked six PPT slides, embedded/exported
notes consistency, exact R1-R14/P1-P24 coverage, current physical summary and
historical digital evidence. Physical summary:4 captures,0 historical recovery,
1 recovery in each named profile,2 boundary failures.

Final deliverable SHA-256 from chunk `56ab58`:

```text
a6d194e11fb589c8831829407b6c702860735433a4e337dc169119ce1981ef88  NISHAN-PQ_SIH26237.pptx
9890c84ca2342a4e04f1f59f00872dd75f1e3f77f60753ac83086d38eb09810f  NISHAN-PQ_SIH26237.pdf
67b6b85d5c74a1f422be4dcd1ed4821ab0d67ceeb27da300004ba9bc735c396a  NISHAN-PQ_SIH26237_speaker_notes.md
```

These checks complete the pending controller artifact steps in the worker's
report. Unknown submission fields remain intentional; no upload has occurred.

## Review-fix refresh (supersedes the deliverable hashes above)

Following Task1 review fixes, the controller exported PPT `43189cec…` once
(chunk `2ce6fe`, session9028, exit0). Draft verifier `4a3150` passes with only
placeholder warnings; strict `939d60` fails only on those same unknown fields.
Both report the exact named recovery (`akshay3.jpeg` in each profile) and exact
two boundary-failure identities.

All6 pages rendered successfully (`686a06`/`e45054`, session76984). Pages1/3/5/6
are byte-identical PNGs to the already visually inspected final render. Root
viewed changed pages2/4: count labels are readable and there is no collision.
PDF check `2822fb`:6 pages,960.009x540pt,959326bytes,PDF1.7.

Current handoff hashes, chunk `26b620`:

```text
43189cec6406875c77183481671330e18c6a722f4adcf64739823a06d641f1b2  NISHAN-PQ_SIH26237.pptx
280d3d00f7fe3fd9ba8d64b5f2c3cd87d6c4877d7c84bd853da6135777eb8a2c  NISHAN-PQ_SIH26237.pdf
e667055fbcb987d269764201d57af37fb183754661cf9de47865f0c12a1023e2  NISHAN-PQ_SIH26237_speaker_notes.md
```
