# Orthogonal authenticator: first-run decision

12 September 2026. **Scientific decision: retain as a digital carrier experiment; do not promote as anti-framing or content-authentication protection.** Independent task and final reviews approved the declared scope, with no Critical or Important findings. Production NISHAN and the selection PPTX/PDF remain unchanged.

## What was newly established

The recovered Sol Ultra probe has now been prospectively reimplemented with a frozen profile, fresh random keys, actual generated recipient public-key fingerprints, real source hashes and fresh sessions. The sole run used two synthetic one-page PDFs, five issued recipients per source, and coalition sizes 1, 2, 3 and 5, rendered as PNG and JPEG Q55. It was not an exact reproduction of the deleted September 10 artifacts.

| Predeclared test | Observed result | Meaning |
|---|---|---|
| Exact auth recovery | 44/44 participating tags; expected match set on all 16 auth artifacts | The extra channel worked in this small digital sample |
| Other-issued candidates | 0/36 extra matches | No extra issued tag matched in these correlated observations |
| Tardos-only/unmarked, changed-context and fresh wrong-key controls | 0/60, 0/6 and 0/200 matches respectively | Tested key/context discrimination; not a calibrated deployment false-attribution bound |
| Copied observed overlay on changed content | Donor tag matched in 2/2 artifacts: PDF and JPEG Q55 | A genuine tag can survive transplantation onto edited content |
| Matched Tardos baseline comparison | Exact expected sets on all 16 Tardos-only artifacts and all 16 added-auth artifacts | No additional identification accuracy was demonstrated over this baseline |

All 20 marked PDFs retained the source's extracted text. Tardos-only PSNR was 41.863–41.927 dB; added-auth PSNR was 38.577–38.640 dB. The additional channel therefore costs visual fidelity in this comparison. PSNR and text extraction do not establish perceptual invisibility, accessibility, or preservation of existing PDF signatures.

The eight unit tests passed. The one full study completed in 114.054313 seconds. This is whole-study runtime, not release latency. The controller independently checked all 97 manifest-listed artifact hashes and all 10 study source/import hashes. It also visually confirmed the attack JPEG displays `quantity 920` where the original fixture had `quantity 120`.

## The decisive distinction

The attack helper took only the observed marked PDF, the modified target PDF and an output path. It copied both image objects and their alpha masks, without a key, plan, codeword or regenerated overlay. Both Tardos and the second tag still selected donor row 0 under the genuine donor context; the modified PDF's text and file hash differed from the donor.

Using a *changed candidate context* rejected the tag, but using the *genuine donor context* on the edited content accepted it. Including the original source hash in a repeated visual payload does not, by itself, verify the received artifact's local content. This is not a newly demonstrated bypass of production NISHAN: the experiment does not invoke its release ledger, structural channel or strict attribution policy.

The narrow surviving interpretation is **association with a copied donor pattern**, not proof that the edited content was the signed output, that the recipient produced it, or that the recipient leaked it. Exact-file hash verification can reject the altered PDF as an exact output; transformed artifacts need a separately justified association policy.

## Why this is not the missing breakthrough

Asymmetric Tardos work already addresses provider-controlled fingerprints and manipulated accusation state through a protocol involving protected generation/embedding and adjudication. A new random HMAC key inside the same harness does not provide those properties. [Charpentier et al., 2010](https://arxiv.org/html/1010.2621v1)

Hybrid robust/fragile watermarking has also combined separate identity and content-authentication channels, with copy-attack rejection. The robust, transformation-tolerant content-binding problem is distinct from simply naming the pristine source in a payload. This is close conceptual prior art, not an apples-to-apples performance comparison with NISHAN. [Deguillaume et al., 2002](https://cvml.unige.ch/publications/postscript/2002/DeguillaumeVoloshynovskiyPun_EUSIPCO2002.pdf)

The present run has no independent recipient custody, enrollment, recipient-signature protocol, escrow, ledger or adjudicator. It supplies no physical print/scan/camera result, no externally held-out population, and no competitive superiority result. The Tardos extraction reports also contain marking-condition violations for JPEG and combined-layer cases; empirical row recovery is not a proof of collusion completeness for that image channel. Formal code-level soundness and completeness have distinct assumptions and should not be conflated.

## Submission decision

Keep the reviewed selection deck unchanged. Do not advertise this as a fix for operator framing, real photographs or general transplantation. Preserve the code and results as research evidence; do not export its private experimental material with the submission.

Further recipient/adjudicator implementation is not justified by these results alone. It needs a distinct, literature-informed threat model and a protocol that actually changes who can construct the accepted artifact. Physical watermark improvement remains a separate unresolved experiment requiring fresh captures of whichever new carrier is tested.

## Reproducibility pointers

- [Frozen specification](/home/user_end4/MySpace/SIH/research/NISHAN_AUTH_ORTHOGONAL_SPEC_2026-09-12.md)
- [Implementation and run instructions](/home/user_end4/MySpace/SIH/research/experiments/auth_orthogonal_v1/README.md)
- [Full task report](/home/user_end4/MySpace/SIH/research/evidence/nishan-auth-orthogonal-2026-09-12/task-1-report.md)
- [Premeasurement manifest](/home/user_end4/MySpace/SIH/research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/manifest.json)
- [Complete observations](/home/user_end4/MySpace/SIH/research/evidence/nishan-auth-orthogonal-2026-09-12/run-01/results.json)
- [Independent prior-art review](/home/user_end4/MySpace/SIH/research/NISHAN_AUTH_ORTHOGONAL_PRIOR_ART_2026-09-12.md)

`results.json` SHA256: `1e9d8c827bf987bf101a2107940351b5c8cf0ef5b1fd463c330ee1ecce4e2e80`.
