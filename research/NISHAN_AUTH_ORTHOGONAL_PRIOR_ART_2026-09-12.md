# Orthogonal recipient authenticator: narrow prior-art and threat review

**Review date:** 12 September 2026  
**Scope:** the isolated proposal to add a recipient-keyed, visually embedded 72-bit HMAC authenticator to a visual Tardos carrier, encode it with Hamming(7,4), repeat it spatially in carrier-orthogonal templates, bind it to source hash / recipient key / session (and preferably the Tardos row), and detect it non-blindly with the original reference and the candidate release context. This is a go/no-go review of the security claim, not a review of the whole NISHAN system.

## Verdict

**No-go** for either of these claims:

- “The second visual tag solves dishonest-provider framing.”
- “Context binding prevents copied-overlay or transplantation attacks.”

**Go**, with a materially narrower claim, for an experiment showing that a *separately controlled corroboration channel* can coexist with the Tardos carrier and reject **cross-context** copies under an explicit fail-closed decision rule.

The construction has two distinct possible meanings:

1. **Single-process fresh-secret carrier harness:** no anti-framing result. If one process creates the Tardos state, recipient HMAC keys, tag plans, final marked copies, and verification inputs, the “recipient” secret is only a test vector. The provider can generate a fully consistent copy and can choose the context accepted by its own verifier. A provider-only negative control merely measures accidental decoder cross-talk.
2. **Recipient-controlled protocol:** potentially useful evidence, but only if the provider never learns the recipient secret **and never obtains the final recipient-authenticated carrier**, the recipient contribution is committed to the exact release before delivery, the verifier derives context from authenticated records rather than claimant input, and an independent adjudicator can verify without trusting the provider. Those are protocol properties, not consequences of HMAC, Hamming coding, repetition, or orthogonal templates.

Even in the second case this is not an asymmetric Tardos construction: the Tardos word and its scoring state remain provider-controlled unless the separate asymmetric-Tardos commitments and accusation procedure are also implemented.

## Threat assumptions and what the tag changes

| Threat / assumption | What the proposed tag can establish | What it cannot establish |
|---|---|---|
| Provider knows every HMAC key or generates every tag | Engineering coexistence, decoder separation, and robustness on the tested samples | Any reduction in provider framing power |
| Recipient alone controls the HMAC key, but provider sees the final marked pixels/PDF | Provider may be unable to synthesize a fresh tag from the key | The observed tag is still a transferable bearer signal; the provider can try to estimate/copy the overlay or retain the final issued copy |
| Recipient controls the key and adds the tag after a one-way handoff, so provider never sees the final copy | Under HMAC/PRF assumptions, provider cannot generate the expected fresh tag from scratch | Recipient can omit, damage, or strip its own channel; secure enrollment, commitment, escrow/recovery, and dispute resolution are still needed |
| Verifier obtains source hash, session, recipient public key, row, and algorithm version from an authenticated issuance record | A tag copied to a *different* bound source, session, recipient, or row should decode to the old value and fail comparison | A tag copied within the *same* bound context remains valid by design; accepting attacker-supplied “candidate context” defeats the binding |
| Final policy requires both Tardos attribution and recipient authenticator agreement | Provider-only Tardos evidence can be made insufficient for attribution | Availability drops: stripping the second tag must cause abstention, not a fallback Tardos accusation, if anti-framing is the claimed benefit |
| Independent judge verifies fixed codebook/bias commitments and recipient evidence | Can reduce reliance on provider testimony | A provider-run detector and provider-retained secrets do not provide this property |

The 72-bit HMAC truncation supplies a nominal single-target cryptographic guessing work factor of about `2^72` if the key is secret and the MAC input is canonically encoded. Hamming(7,4) and repetition add noise tolerance, not authenticity; measured false acceptance must include all tested recipients, documents, contexts, alignments, decoder searches, and threshold choices. “Orthogonal” describes carrier interference, not adversarial independence.

## Closest primary literature

1. **Charpentier, Fontaine, Furon, and Cox, “An Asymmetric Fingerprinting Scheme based on Tardos Codes” (2010).** The paper identifies two provider threats that the added HMAC does not itself repair: a provider who knows a buyer fingerprint can forge a marked work, and a provider can manipulate the secret Tardos probability vector used at accusation. Its proposed remedy makes the buyer participate in fingerprint generation without learning the provider's secret vector, publishes immutable construction material, uses secure/homomorphic embedding so the provider does not learn the full fingerprint/final copy, and sends accusation to a judge. The authors expressly describe embedding and adjudication as protocol components, not merely another watermark payload. [Full arXiv HTML](https://arxiv.org/html/1010.2621v1)

2. **Memon and Wong, “A Buyer-Seller Watermarking Protocol” (IEEE TIP, 2001).** This is the direct customer-rights baseline: the seller must not learn the exact watermarked copy delivered to the buyer, and a third-party dispute procedure is required. A recipient-secret HMAC produced inside the seller's process does not meet that condition. [Primary bibliographic page and abstract](https://pubmed.ncbi.nlm.nih.gov/18249653/) ([DOI](https://doi.org/10.1109/83.913598))

3. **Lei, Yu, Tsai, and Chan, “An Efficient and Anonymous Buyer-Seller Watermarking Protocol” (IEEE TIP, 2004).** This paper names the **unbinding problem**: after obtaining a buyer's watermark from one work/transaction, a seller can transplant it to another and fabricate evidence. Their protocol binds a common agreement specifying the content/transaction and introduces a watermark-certification authority plus arbitration evidence. This is close prior art to source/session/key binding, while also showing why a bound value alone is not enough without a protocol controlling generation, embedding, records, and adjudication. [Author-institution full paper](https://scholars.lib.ntu.edu.tw/server/api/core/bitstreams/a0f03c9c-3ec3-44eb-a4b4-c40f2cf6a44d/content) ([DOI](https://doi.org/10.1109/TIP.2004.837553))

4. **Kutter, Voloshynovskiy, and Herrigel, “Watermark Copy Attack” (SPIE, 2000).** The attack estimates an embedded watermark in the spatial domain and adapts/inserts it into a different image; it does not require the watermark key or algorithm details. This is the correct baseline for a copied residual/overlay test, including attacks that do not recover the HMAC bits or secret placement plan. [University of Geneva primary repository page and paper download](https://archive-ouverte.unige.ch/unige:47812) ([DOI](https://doi.org/10.1117/12.384991))

5. **Barreto, Kim, and Rijmen, “Toward a Secure Public-Key Blockwise Fragile Authentication Watermarking” (ICIP, 2001).** The paper shows that deterministic, limited content dependencies remain vulnerable to transplantation, especially in document images with large white regions. Its HBC2 response uses randomized signatures and signature dependency across blocks. The important comparison is that a single repeated global HMAC value—even one that names a source hash—is not a spatially content-dependent authentication chain and does not authenticate the local relationship between copied pixels and their destination. [Author-uploaded full text](https://www.researchgate.net/publication/3920113_Toward_a_secure_public-key_blockwise_fragile_authenticationwatermarking) ([DOI](https://doi.org/10.1109/ICIP.2001.958536))

6. **Deguillaume, Voloshynovskiy, and Pun, “Hybrid Robust Watermarking Resistant Against Copy Attack” (EUSIPCO, 2002).** This is technically close to the proposed carrier arrangement: a robust watermark is combined with a second fragile/semi-fragile, key-dependent hash channel; the channels are placed in largely nonoverlapping positions, the robust payload uses error correction and repeated structure, extraction produces separate results, and the decision rejects when the robust identity survives but integrity fails. It therefore substantially anticipates “orthogonal robust identity plus authentication channel and fail-closed fusion,” although not the exact Tardos/HMAC/PDF construction or recipient-custody protocol. [Author-university full paper](https://cvml.unige.ch/publications/postscript/2002/DeguillaumeVoloshynovskiyPun_EUSIPCO2002.pdf)

## Material security assessment

### Dishonest-provider framing

The visual tag **can materially reduce one framing route only under the recipient-controlled protocol assumptions above**: if the provider lacks both the HMAC key and any reusable final authenticator signal, and attribution requires the Tardos row and recipient tag to agree, the provider cannot simply create a consistent marked copy from provider state.

It does **not** establish non-framing in the recovered single-process harness. It also leaves the Tardos-specific accusation-state attack identified by Charpentier et al. unless the code-generation state is immutably committed and independently checked. A signed provider record is not enough when the provider chooses all values being signed.

There is a further protocol tension: letting the recipient add or control the tag protects against the provider, but also lets a malicious recipient omit or erase that channel. A system claiming anti-framing must abstain on Tardos-only evidence; otherwise the provider can bypass the safeguard by presenting a copy without the tag. Solving that tension normally requires an interactive buyer-seller/asymmetric embedding protocol, enforceable client, or trusted certification/adjudication role.

### Copied-overlay / transplantation attacks

Context binding is useful but narrower than “copy resistance”:

- **Cross-document, cross-session, cross-recipient, or cross-row copy:** expected to fail if the verifier recomputes a canonical context from independently authenticated release evidence and compares the decoded tag with that context.
- **Same document and same session/recipient context:** expected to pass. The identical HMAC is the correct value; neither HMAC nor ECC tells whether the signal was embedded during the genuine handoff or copied later.
- **Spatial transplant inside a document or patch collage:** a repeated global tag authenticates the value, not necessarily the placement/content relationship. Local or large-region copies may retain enough repeated placements to pass unless the tag is derived from local robust content/coordinates or the detector enforces a preregistered spatial-consistency test.
- **Residual estimation attack:** secrecy of positions/polarities is not a sufficient defense once an attacker has marked and reference-like material. Kutter et al.'s attack is explicitly estimation-based and keyless.
- **Different-content transplant with claimed old context:** fails only if the verifier refuses claimant-selected context and checks the candidate against the authoritative target source/release record.

Thus the proposed experiment can demonstrate rejection of tested *cross-context* transplants. It cannot demonstrate general copy resistance, provenance of the physical/digital instance, or that the provider did not reuse an authenticator it observed.

## Falsifying tests required before retaining even the narrow claim

1. **Real role separation:** generate recipient keys in separate processes/devices; preserve evidence that provider code never receives the keys. Repeat once with provider access to the final marked copy and once with a one-way recipient-finalization handoff.
2. **Provider-forgery test:** give the attacker all provider secrets, Tardos state, original references, issuance records, detector knowledge, and chosen-document capability, but not the recipient secret/finalized carrier. The acceptance policy must reject provider-only, wrong-key, and synthetic-tag attempts across a substantial innocent roster.
3. **Tardos-state substitution:** let the provider alter the bias vector, codebook, row mapping, thresholds, and claimed source/reference after seeing the leak. An independent verifier must detect every deviation from pre-release commitments.
4. **Full transplant matrix:** copy PDF image objects, pixel residuals, filtered watermark estimates, rectangular patches, and sufficient repeated placements across (a) different source/same recipient, (b) same source/different session, (c) same source/same session, (d) different recipient, and (e) different Tardos row. The preregistered expected result for (c) should be **attack succeeds**, unless an additional instance-unique mechanism is introduced.
5. **Context provenance:** run the detector with attacker-supplied versus signed-ledger-derived contexts, including ambiguous serialization, omitted fields, field reordering, and hash/reference substitution. Only canonical, authenticated context may affect acceptance.
6. **Strip-and-fallback test:** remove or damage only the recipient tag while preserving a high Tardos score. If the result still accuses, the second channel has not provided anti-framing protection.
7. **Recipient cheating and adjudication:** test refusal to reveal an HMAC key, false key submission, key rotation/revocation, escrow recovery, wrong adjudicator key, and proof that the recovered key/public-key binding existed before delivery.
8. **Predeclared statistics:** freeze strength, decoding radius, alignment search, spatial-consistency rule, and candidate roster before evaluation. Report empirical false accepts under fresh documents/keys in addition to the nominal 72-bit MAC bound.

## Claim that could survive

If the role separation and falsifying tests pass, the defensible claim is:

> We implemented a recipient-contributed, context-bound visual corroboration channel that coexists with a Tardos carrier. Under a fail-closed two-channel policy and an independently authenticated release context, the tested channel rejects cross-document, cross-session, cross-recipient, and cross-row overlay transplants when the provider lacks the recipient key and has not observed the finalized authenticator carrier.

Required qualifier:

> This is not a complete asymmetric Tardos or buyer-seller watermarking protocol; it does not prevent reuse of an observed authenticator within the same bound context, and it does not by itself prove that a recipient rather than the provider disclosed a copy.

For the present recovered single-process fresh-secret harness, the surviving claim is smaller still:

> In one synthetic non-blind carrier experiment, a repeated HMAC-coded visual channel was separable from the Tardos channel and discriminated the tested fresh keys/contexts under the reported transforms.

## Uncertainties

- This was a deliberately narrow search of six close primary sources, not a patentability or exhaustive novelty search.
- The papers use image/video watermarking models, not this exact PDF renderer, HMAC truncation, block template, or registration code. Their attacks and protocol lessons transfer conceptually; implementation success/failure must be measured.
- “Provider has not observed the finalized authenticator carrier” is a strong operational assumption and may be unrealistic for managed enterprise delivery. If it cannot be enforced, the proposed anti-framing claim should be abandoned or weakened to cross-context replay detection.
- Robust content binding that survives JPEG/scan/camera processing without enabling transplantation is a harder problem than hashing the pristine source. The proposed source-hash-in-payload design has not yet shown that property.
