# Claude Opus 5 hostile review prompt

Work in `/home/user_end4/MySpace/SIH`. Act as a hostile cryptography,
document-forensics, and SIH finale reviewer. Do not praise the project and do
not repeat its README. Your job is to disprove claims, construct attacks, and
rank the remaining blockers. You may run any local code and create throwaway
files under `/tmp`, but do not edit the repository.

The target is SIH26237, NISHAN-PQ. Start by reading and then running:

- `prototypes/nishan_pq/nishan/core.py`
- `prototypes/nishan_pq/nishan/tardos.py`
- `prototypes/nishan_pq/nishan/tardos_carrier.py`
- `prototypes/nishan_pq/nishan/live_pdf.py`
- `prototypes/nishan_pq/nishan/layout_tag.py`
- `prototypes/nishan_pq/nishan/identity.py`
- `prototypes/nishan_pq/nishan/ledger.py`
- `prototypes/nishan_pq/nishan/witness.py`
- `prototypes/nishan_pq/nishan/pqc.py`
- `prototypes/nishan_pq/nishan/demo.py`
- all files under `prototypes/nishan_pq/tests/` and
  `prototypes/nishan_pq/tools/`
- `artifacts/nishan/measured-results.json`
- `artifacts/nishan/tardos-pdf-benchmark.json`
- `artifacts/nishan/tardos-independent-codebook-study.json`
- `artifacts/nishan/end-to-end-jpeg-trials.json`
- `research/NISHAN_NOVELTY_AND_PRIOR_ART.md`
- `submissions/SIH26237_NISHAN_PQ/paste_ready_submission.md`
- `submissions/SIH26237_NISHAN_PQ/NISHAN-PQ_SIH26237.pdf`

Run the test suite, evidence exporter, verifier, and any focused experiments
needed. Inspect source rather than trusting JSON output. Pay special attention
to these questions:

1. Are the original Tardos constants, one-sided score, family-wide union bound,
   and theorem scope implemented and described correctly? Check against primary
   sources. Distinguish code-level assumptions from carrier measurements.
2. Can a malformed, transplanted, partially overlapping, removed, unissued, or
   ambiguous carrier ever produce an attribution contrary to the written
   fail-closed policy? Try runnable counterexamples.
3. Can a forged key, valid receipt replay, duplicate row, mixed scheme,
   malformed event, algorithm-label change, registry edit, replica fork,
   coordinated truncation, or witness-history manipulation evade a gate? Check
   exactly what each signature covers.
4. Look for TOCTOU, concurrent row allocation, non-atomic ledger writes,
   post-commit output failure, symlink/path abuse, parser ambiguity, denial of
   service, and media-type/downgrade issues. Separate prototype limitations from
   claims that are already false.
5. Does the 30-run study truly exercise 30 fresh cryptographic releases and all
   1,000 rows, or is it tautological/leaky? Recalculate headline values.
6. Does the current PDF preserve usable text, search, vectors, metadata,
   signatures, forms, accessibility, and multi-page semantics? Identify the
   narrow truth and any overclaim.
7. The distributor still controls the Tardos codebook and carrier secret. Assess
   dishonest-provider framing against the asymmetric Tardos literature. Decide
   whether an independently escrowed recipient-generated session secret and a
   recipient-side robust authenticator could materially reduce framing, what it
   would and would not prove, and whether a full buyer-seller/asymmetric protocol
   is required.
8. Search primary papers and patents for the exact claimed contribution:
   collusion-code visual channel + independent live-PDF structural authenticator
   + one signed session + exact set-equality/abstention under transplantation.
   Report close prior art with direct links. Absence from your search is not
   proof of novelty.
9. Judge the project separately for internal selection, national shortlisting,
   and winning a five-team WESEE finale. Assume rivals will also have working
   watermark/blockchain prototypes.

Return one Markdown report with:

- a one-line verdict;
- a table of findings ordered Critical/High/Medium/Low, each with exact file and
  line, a runnable proof or concrete reasoning, the claim affected, and the
  smallest correct fix;
- every headline number you independently reproduced;
- claims safe to say, claims that must be narrowed, and claims prohibited;
- a novelty ruling based on cited primary prior art;
- the three highest-value next implementations, in order;
- a red-team demo script designed to make this project fail in front of judges.

Do not suggest generic UI work, an LLM, a public blockchain, or more slides.
Prefer one demonstrated technical correction over ten feature ideas.
