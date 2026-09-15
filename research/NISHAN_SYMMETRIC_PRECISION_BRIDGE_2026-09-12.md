# NISHAN symmetric finite-precision bridge: focused first pass

Date: 2026-09-12. Scope: read-only mathematical assessment and one research note; no implementation or production changes. This consumes the completed [ideal finite-length audit](NISHAN_SYMMETRIC_PARAMETER_AUDIT_2026-09-10.md), rather than repeating it.

## Verdict

**The current keyed implementation is not certified. A small, credible replacement precision profile can preserve the stated numerical budgets conditionally; it needs an implemented and checked sampler contract plus a quantified computational randomness assumption before certification.** This is not a reason to reject an explicitly empirical carrier comparison. Label that comparison empirical, keep its manifest separate, and do not import the ideal theorem bounds into its measured results.

The unchanged ideal target is n = 1000, coalition cap c = 5, m = 12331, δ = 1/141.55, and the exact audited Z = 837.284308860289776… expression. The budgets remain 10^-9 per innocent, at most (1000 − q)10^-9 for any innocent in a fixed nonempty q-person coalition experiment, and 10^-11.25 = 5.62341325190349… × 10^-12 for no colluder accused. None is a simultaneous guarantee across every coalition or repeated use of one codebook.

The key observation is that soundness and completeness need different bridges. Actual-probability scoring restores exact conditional soundness moments for *any* discrete bias distribution inside the cutoff. Completeness can couple only the q coalition rows to the ideal experiment, with a deterministic score perturbation allowance. There is no need to claim small total variation between a continuous bias and a discrete bias; that distance is one.

## Existing implementation and relevant primary work

The inspected [tardos.py](../prototypes/nishan_pq/nishan/tardos.py) uses nominal 53-bit midpoint bias uniforms evaluated in float64, 32-bit Bernoulli thresholds, and an asymmetric scorer that omits every y = 0 position. Its actual Bernoulli probability is floor(2^32 p)/2^32 while scores use p. Increasing Bernoulli bits alone neither fixes the asymmetric scorer nor certifies bias evaluation, score arithmetic, or keyed randomness.

The source of the retained ideal moments is Laarhoven and de Weger, *Optimal symmetric Tardos traitor tracing schemes* (2014), Sections 3–4 and Appendix A. Its innocent proof conditions on the bias and pirate word; its coalition proof bounds the maximum over admissible per-column outputs after integrating the hidden bias. The audited constants already satisfy its finite-length conditions. [Author-hosted primary paper](https://deweger.net/papers/%5B47%5DLdW-OptTTTS-DCC%5B2014%5D.pdf).

The closest primary finite-precision analysis found is Nuida et al., *An improvement of discrete Tardos fingerprinting codes* (2009). Sections 3.2–4 explicitly allow approximated bias distributions and bounded score errors, with a tolerance parameter in the security calculation. But it uses Gauss–Legendre bias distributions and selects a highest-scoring user; its theorem does not certify this retained cutoff/arcsine/threshold construction. It demonstrates that finite precision is a tractable proof question. [Author-hosted primary paper](https://nuida.github.io/html/doc/DCC_2009_339_362.pdf).

Nuida et al.'s earlier *Optimization of Memory Usage in Tardos's Fingerprinting Codes* also evaluates score approximation in its length/threshold analysis. Laarhoven and de Weger's *Discrete Distributions in the Tardos Scheme, Revisited* studies discrete alternatives, but its distribution comparison includes heuristic length estimates, not a certificate for these exact implementation parameters. [Earlier primary preprint](https://arxiv.org/pdf/cs/0610036), [discrete-distribution primary preprint](https://arxiv.org/abs/1302.1741).

The bridge below is an independent derivation, not a theorem attributed to those discrete-code papers.

## Concrete minimal experimental profile with a certifiable contract

Use an isolated symmetric profile and fresh bias/codebook commitments. In the ideal-random-bits version of this profile:

1. Set N = 2^64. Draw an independent integer K uniformly from {0,…,N−1} for each column. Form the midpoint u = (K + 1/2)/N as an exact rational; do not convert K to float64 first.
2. For φ(u) = sin²(a + u(π/2 − 2a)), a = arcsin√δ, produce a rational approximation r with a **certified absolute error ≤ 2^-65**. This is a contract for the full transformation, including a and π. A nominal arithmetic precision or comparison against another floating-point library is not that certificate. Interval evaluation at higher precision is a plausible implementation route; only 12331 transformations are needed.
3. Compute T = clip(floor(Nr), L, N−L), where L = ceil(Nδ) is computed from the exact rational δ. Store the integer T, and define the actual bias b = T/N. For every code bit, draw an independent uniform 64-bit integer R and emit one exactly when R < T. This is *exactly* Bernoulli(b); there is no additional Bernoulli-rounding error relative to b.
4. Score all positions with the symmetric rule, using b as the mathematical scoring probability. A small deterministic implementation uses 40 fractional score bits. Compute integer weights

   A = isqrt(floor((N−T) 2^80 / T)),
   B = isqrt(floor(T 2^80 / (N−T))).

   These are exactly floor(2^40 √((1−b)/b)) and floor(2^40 √(b/(1−b))). Use contributions +A, −B, −A, +B for (y,X) = (1,1), (1,0), (0,1), (0,0), respectively. Sum integers exactly and compare with the certified integer threshold ceil(2^40 Z), accusing only on strict exceedance. This bounds every signed contribution error by 2^-40 without relying on floating-point square roots or accumulation. Use arbitrary-precision intermediates for the weight construction; the final accumulated magnitude is below 2^58, so signed 64-bit sums suffice when implemented without intermediate overflow.
5. Keep b as the integer/rational authority in the manifest and detector. A float64 display is harmless, but replacing b by that display in the sampler or treating it as the exact scoring probability changes the proof contract. Record stream format, profile version, rounding rule, threshold integer, and commitments.

This is deliberately only a proposed experimental specification. No version of these operations was implemented or verified during this subtask. If certified bias evaluation is deferred, the experiment remains useful, but its manifest must state that the sampling contract is unverified.

## Calculable precision allowance

Couple ideal U uniform on [0,1] to K = floor(NU). Since |φ′(u)| ≤ π/2 − 2a < 2, midpoint quantization moves the ideal probability by less than 2^-64. Adding the stipulated evaluation error and the inward dyadic rounding/clipping gives the conservative pointwise bound

|b − p| ≤ e = 2^-62 = 2.168404344971009 × 10^-19,

with both b and p in [δ,1−δ]. Clipping is safe here because the ideal midpoint value lies in that interval and the inward lattice endpoints lie within 1/N of it. This bound accounts for bias quantization and Bernoulli discretization together, rather than charging the latter twice.

The derivative magnitude of either unsigned symmetric weight is bounded on this interval by

D = 1/(2 δ^(3/2) √(1−δ)) < 850.

Hence on matching code bits and pirate output, one user's ideal and exact-at-b scores differ by at most mDe < 2.273 × 10^-12. Integer score truncation plus threshold rounding costs less than (m+1)2^-40 = 1.1215888662263751 × 10^-8. A single **E = 2 × 10^-8 score units** conservatively covers both effects and threshold representation. This allowance is deterministic, not a failure probability.

These arithmetic values were checked with standard-library Python and ordinary double arithmetic. Their deliberately loose inequalities are suitable targets for an eventual outward-rounded certificate, but this note is not that numerical implementation certificate.

## Soundness: direct conditional moments

For any actual bias b and fixed y, the exact score contribution s = (2y−1)(X−b)/√(b(1−b)), with X ~ Bernoulli(b), satisfies E[s] = 0 and E[s²] = 1. The cutoff bounds its magnitude. Conditioning on the complete bias vector and pirate word leaves the innocent bits independent under the stipulated no-leakage model. Therefore the original innocent exponential-moment argument applies directly, regardless of whether the bias distribution is continuous, discrete, or symmetric.

Let α = 1/(4.58·5) = 0.04366812227074236. Reusing the audited moment value B_S = 9.18550844217503 × 10^-10, the proposed finite score comparison has the conservative ideal-random-bits bound

P[fixed innocent accused] ≤ B_S exp(αE) ≈ 9.185508450197309 × 10^-10 < 10^-9.

No code-bit coupling penalty is necessary for soundness. For a fixed nonempty coalition, union bound over its actual innocent users; the worst-case 999-user ceiling is approximately 9.176322941747111 × 10^-7. A discrete bias law by itself causes no soundness loss when the bit law and scoring probability agree. The current mismatched 32-bit implementation cannot use this exact centering argument without an extra analysis.

## Completeness: couple the coalition transcript and move the threshold

For each of q ≤ 5 coalition rows, couple ideal Bernoulli(p) and finite Bernoulli(b) with a shared independent continuous uniform. The finite side has exactly the same marginal as the integer sampler above. A union bound gives

P[any coalition bit differs] ≤ qm e ≤ 1.3369296988918755 × 10^-14.

On matching coalition codewords, the same pirate algorithm with the same private randomness produces the same output, including arbitrary dependencies across columns. The ideal comparison algorithm is that same function of its coalition input; its knowledge of the public implementation does not prevent applying the ideal theorem. This argument requires that the pirate receives no secret bias, sampler state, or innocent codewords. It does not assume independence of the pirate's outputs.

On this matching event, failure to accuse any finite-profile colluder implies that each ideal colluder's score is at most Z + E, so the ideal coalition total is at most q(Z + E). Apply the audited coalition exponential moment at this shifted event, not a Gaussian approximation or continuity assumption about the score CDF.

For q = 5, β = 1.07√δ/5 = 0.01798700421789918 and the audited B_C = 3.18694046542462 × 10^-15 yield

P[no colluder accused] ≤ B_C exp(β·5E) + 5me
                         ≈ 1.6556237460075727 × 10^-14
                         < 5.62341325190349 × 10^-12.

For q = 2,3,4, reuse the completed audit's reparameterization. Its coalition lemma gives exp(β_q qZ − gβ_q m), β_q = 1.07√δ/q, g = 0.49. This bound decreases as q decreases; the exponent perturbation β_q qE is constant and qme also decreases. Thus the displayed q = 5 ceiling covers them. For q = 1, every actual contribution under marking is positive, and the score lower bound remains above 1040 after integer rounding, far above Z; miss probability is zero.

Crucially, this costs five rows, not all 1000 rows. It is a coupling of observable binary transcripts plus a deterministic score bound, not a small-total-variation claim for the bias itself. It provides an elementary route once the pointwise bias-error contract holds; a new direct discrete completeness moment calculation is optional, not necessary for this proposed precision profile.

## Keyed randomness and exact remaining proof obligations

The statistical calculations above use genuinely independent uniform finite bit strings. A deterministic codebook from a fixed secret has no such information-theoretic randomness guarantee by itself. For a random protected key, model the full HMAC-derived, domain-separated AES-CTR output as computationally indistinguishable from the required independent streams. A reduction must include key derivation, both streams, output lengths, distinct contexts/counter use, attacker runtime and allowed observations, and the experiment's failure predicate.

Write the resulting distinguishing advantages as Adv_S for the fixed-innocent experiment and Adv_C for the miss experiment. The keyed claims would be

P_key[fixed innocent accused] ≤ 9.1855084502 × 10^-10 + Adv_S,
P_key[miss] ≤ 1.6556237461 × 10^-14 + Adv_C.

For example, a *proved or explicitly assumed* bound of 10^-12 on each advantage would fit both declared budgets, giving about 9.19551 × 10^-10 and 1.01656 × 10^-12, respectively. These are example allocations, **not measured or established advantages for this repository's AES/HMAC use**. A direct familywise reduction may charge its advantage once to that event; union bounding per-user computational bounds charges it once per innocent. State which convention is used. Merely saying “AES-256” does not prove a concrete probability bound for an unrestricted adversary.

Nuida and Hanaoka, *On the Security of Pseudorandomized Information-Theoretically Secure Schemes* (2013), discusses stronger transfer techniques even for unbounded attack algorithms, with quantitative restrictions involving the information exposed to them. That is relevant prior work but has not been instantiated here for these codewords, keys, or budgets; do not silently use it to retain unrestricted information-theoretic security. [Author-hosted primary paper](https://nuida.github.io/html/doc/IEEEIT_2013_635_652.pdf).

Before a certification claim, complete these specific obligations:

- Implement and verify the uniform-integer sampler contract, certified full bias transformation, exact dyadic clipping, and independent randomness experiment. Verify the bound for every allowed midpoint, through validated arithmetic rather than enumerating all 2^64 inputs or relying only on sampled tests.
- Implement the full symmetric signed score table, exact integer arithmetic, and outward-certified threshold integer; check encodings, overflow, endpoint cases, ties, and manifests. Revalidate the conservative numerical ceilings with directed error bounds.
- Review the coupling/event proof under the exact attacker interface: fixed coalition size, complete binary marking-respecting word, hidden bias/codebook state, and no additional side information. Physical extraction errors, erasures, guessed fills, soft scores, or biased selection of a favorable codebook require their own analysis.
- Specify the random-key experiment and provide the computational reduction/assumption with a concrete advantage allowance. Repeated contexts, repeated accusations, or more information exposed across many copies require an expanded experiment and budget.

Until those obligations are discharged, the certificate verdict is **NO-GO for implemented theorem guarantees; GO for a clearly labeled isolated empirical compact-code/carrier comparison**. Retaining 12331 positions is numerically plausible under the explicit profile above; increasing precision alone is not a certificate.
