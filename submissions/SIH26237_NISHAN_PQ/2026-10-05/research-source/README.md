# Research source snapshots — separate from the stable demo

This archive covers **57 filtered tip snapshots**, exported as patches against
the already-public stable baseline `f37e861dc02815adf1bebb3e1b45ff222dccf821`.
[index.json](index.json) records each original local branch/tip, included source
blob hashes, normalized-path transformations, excluded paths, patch hashes and
successful apply checks. One control-only branch has no retained source difference;
its empty patch and exclusions remain recorded rather than inventing a contribution.

**These are not the original research Git histories.** The original 291-commit
local count is provenance metadata, not a claim that all 291 commits or their
artifacts are downloadable. Original tip IDs are inert references; they may not
resolve in a public clone. No raw unpublished research commit was made a parent
of this release, and no experimental branch was merged into the stable application.

## Useful entry points

| Track | Source patch | Meaning |
| --- | --- | --- |
| Best measured physical receiver, R15 | [Mesh + contrast](patches/codex__glyph-mesh-contrast-r15-20260928.patch) | 9/24 finite associations, 2/24 exact tokens on the fixed Test3 development corpus; 0/6 marked tilted successes. |
| Signed compact release, R23 | [Experimental signed adapter](patches/codex__signed-compact-release-20260928.patch) | Separate digital adapter; not a fresh physical success, no inherited compact-token collusion guarantee. |
| Paper-axis CoreMark-inspired probe, R22 | [Paper-axis receiver](patches/codex__cm-paper-r22.patch) | Negative physical reconstruction result; research implementation with deviations, not proof of a faithful published-paper reproduction. |
| Fresh carrier packet, R24 | [Integrated packet source](patches/codex__fresh-physical-r24.patch) | Source/clean-render checks and prospective experiment work; not completed physical validation. |
| Original-carrier receiver investigation | [Integrated N1 research](patches/codex__n1-integrated.patch) | Exploratory receiver work. Code presence does not establish completed matched-study acceptance gates. |

The index covers intermediate, negative and exploratory variants. Snapshots
contain only reviewed source/prose differences; generated captures, arrays,
fixtures, runtime JSON, internal agent records and uncertain-provenance binaries
are excluded. Research-specific dependencies and missing input paths are described
in the source and original reports; they are not automatically satisfied here.

## Open one snapshot without touching your demo

From a public repository clone, with a clean unused destination:

```bash
publication_repo="$PWD"
git worktree add -b inspect-r15 ../sih-r15-source f37e861dc02815adf1bebb3e1b45ff222dccf821
git -C ../sih-r15-source apply --check \
  "$publication_repo/submissions/SIH26237_NISHAN_PQ/2026-10-05/research-source/patches/codex__glyph-mesh-contrast-r15-20260928.patch"
git -C ../sih-r15-source apply \
  "$publication_repo/submissions/SIH26237_NISHAN_PQ/2026-10-05/research-source/patches/codex__glyph-mesh-contrast-r15-20260928.patch"
```

Use a different new branch/directory and patch for each variant. **Apply each patch
to the baseline, not on top of another variant or the current submission commit.**
The resulting changes are deliberately uncommitted in your inspection worktree.
Do not force overwrites if the destination or branch already exists.

## Export transformations and verification

Absolute private home/workspace prefixes were replaced with documented placeholders
such as `__PRIVATE_CAPTURE_WORKSPACE__/SIH` and `__PRIVATE_HOME__`. These are **not
functional default input directories**: supply your own permitted fixture locations
before running affected research scripts/tests. The original and exported source
hashes make the transformation visible. Legacy personal capture basenames were
also replaced consistently with neutral aliases. Generic device models, capture
dimensions and non-secret file hashes are retained as scientific method/provenance
metadata; they do not include the original photographs. No numerical research result was modified
or newly measured by this source export.

Every exported Python source parsed successfully. Every nonempty patch passed
`git apply` against a fresh baseline index, and each reconstructed tree matched
its recorded export tree. Those are packaging checks, **not reruns of experimental
tests**. The fresh 59-test run applies only to the unchanged stable prototype.
Full physical reproducibility still needs the excluded real captures, printed
source pack, evaluation manifests and dependencies.

No original private keys, real recipient data, credentials or phone photographs
are intended for publication. The history audit found no high-confidence secret
candidates; its other provenance/privacy concerns motivated these filtered snapshots.
Automated scans and manual review are safeguards, not a security certification.
