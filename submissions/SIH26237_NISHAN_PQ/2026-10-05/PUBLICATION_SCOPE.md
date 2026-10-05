# What was published, and what was deliberately kept local

This release adds a dated submission package to the stable public repository.
It is not a raw workspace backup and does not make research guarantees cumulative.

## Included

- The reviewed six-page Aevrix PDF, byte-for-byte with its requested name correction.
- Six September benchmark log/JSON files and a separate safeguard result summary.
- Physical-research results, negative findings and a chart/data pair.
- A clearly labelled public R15 summary derivative with local input bindings omitted.
- 57 original research-tip entries with source-only patches (one control-only empty
  patch), original commit identifiers, included/excluded path lists, source hashes
  and successful baseline application checks.
- Claim qualifications, dependency/reproduction guidance and a SHA-256 checksum list.
- A fresh October core validation: 59 tests passed; real ML-KEM-768 and ML-DSA-65
  available through OpenSSL 3.6.5 on the existing host environment.

## Excluded

Original phone captures and transport files; real account credentials; all private
runtime keys, including synthetic ones; identity/ledger/witness state; raw third-party
datasets; generated research PDFs/images/arrays with incompletely reviewed provenance;
internal agent records/private chats; most local experiment outputs; unfinished video
production; and the complete raw research Git histories.

Existing public baseline files are retained. This publication review is not a
retroactive certification of every earlier public file or every dependency's license.

## Review and checks

The unpublished-history review considered 284 commits and 903 blobs, including
text extraction from 89 PDFs and OCR screening of 20 PNGs. No high-confidence
credential/private-key/token candidates were found. That scan did **not** establish
publication rights or provenance for all artifacts, so raw histories were withheld.

Every included research path was checked against the independent source/prose
allowlist. Local home/workspace prefixes and legacy personal capture basenames
were normalized in the source derivatives; original and exported hashes identify
those transformations. Generic device models, capture dimensions and non-secret
hashes remain as scientific context, not as original capture files.

Every exported Python file parsed. Each nonempty patch applied cleanly to a fresh
baseline index and reproduced its recorded exported tree. This verifies packaging,
not the completeness, correctness or performance of each experiment. No full
experimental test suite or physical study was rerun for this publication.

The stable application source remained unchanged; its fresh 59-test validation is
in `publication-check/`. Selected evidence has been checked for secret material;
the source manifest records export changes. These checks reduce publication risk
but are not a security certification or an independent scientific replication.
