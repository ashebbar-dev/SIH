# NISHAN-PQ — Aevrix submission evidence

**Team:** Aevrix · **Team ID:** 152425 · **Problem statement:** SIH26237.
Publication date: 5 October 2026. This package does not mean the SIH portal entry
has been finally submitted.

## Start here

- [Six-page Aevrix PDF](NISHAN-PQ_SIH26237_Aevrix.pdf): the user-prepared deck, with
  the requested team-name correction. Its numerical/security wording has not been
  silently revised; read the qualifications below before relying on it.
- [Claim qualifications](CLAIM_QUALIFICATIONS.md): what the tests do and do not establish.
- [Publication scope](PUBLICATION_SCOPE.md): exactly what was included, excluded and checked.
- [Reproduction instructions](REPRODUCE.md): stable baseline, bounded commands,
  dependencies and separate physical-data limitations.
- `stable-runs-2026-09-28/`: historical logs and structured benchmark results supporting
  the deck. These are measured runs, not evidence of universal robustness.
- `physical-research/`: reviewed development-corpus findings, including failures.
- [Research source archive](research-source/README.md): 57 filtered source-only
  snapshots with original branch/commit provenance and explicit exclusions; not
  the original research Git histories and not merged into the demo.
- `SOURCE_MANIFEST.json`: source hashes and any export transformations. The public
  R15 summary omits local input bindings/original-photo filenames; all numerical
  rows, counts and timings are unchanged. The chart-data source path is also normalized.
- `SHA256SUMS`: checksums of this package's files, excluding the checksum file itself.

## What is demonstrated

The stable prototype encrypts one payload, personalizes an authorized decryption,
binds it to a recipient-signed ML-DSA-65 release, and checks quorum/witness state
before output publication. Key encapsulation uses ML-KEM-768; bulk encryption uses
AES-256-GCM. The live-PDF path combines a Tardos visual carrier with a layout tag.

The 28 September evidence reports 59 core tests, 12 safeguard scenarios and 25
carrier attack expectations passing; the separate code-level study covers 120
codebook/strategy cases. Thirty JPEG-Q55 release trials recovered the expected
visual row without extra threshold-crossing rows. **A raster match is an investigative
lead, not a two-channel attribution verdict.** Some successful benchmark expectations
are deliberate abstentions, not recovered recipients.

## What is still research

On the fixed Test3 development corpus, R15 improved finite-registry associations
from **4/24 to 9/24**, while exact token recovery improved from **0/24 to 2/24**.
All **six marked tilted captures remained unresolved**. Neither this result nor
later clean-render experiments establish a reliable print/camera/scanner system.

The signed-compact adapter is a separate experimental digital path; its reported
13 adapter and 63 compatibility tests do not transfer the full Tardos carrier's
collusion guarantees to a compact physical token. Research source publication is
not a merge, production endorsement, or claim of complete implementation of every
prior research proposal.

## Publication scope

The stable application code is deliberately unchanged from commit
`f37e861dc02815adf1bebb3e1b45ff222dccf821`. The public release adds reviewed artifacts
and discovery/reproduction documentation; research versions remain separate.

Excluded: private keys (including synthetic runtime keys), credentials, live
identity/ledger/witness folders, original phone captures, raw third-party datasets,
private chats, working caches and video-production files. Those exclusions mean
**not every local artifact is public**, and the physical experiments cannot be
repeated from this repository alone. Reports and input hashes remain useful for
audit, but hashes are not a substitute for the underlying photographs.

No independently governed validator deployment, issuer non-framing guarantee,
human-guilt conclusion, rare false-attribution rate, or general physical robustness
is established by this package. See the qualification file for precise boundaries.
