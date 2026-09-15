# NISHAN symmetric finite-length parameter audit

Date: 2026-09-10. Scope: independent mathematical audit; no production changes or physical-image rescoring.

## Verdict

**PASS for the ideal symmetric construction; NEEDS FIX for the reported numerical provenance; NOT YET CERTIFIED for the keyed finite-precision implementation.**

The finite design with 1,000 users, coalition limit five, and 12,331 binary positions satisfies the finite-length sufficient conditions with the existing failure budgets. This result does not use the asymptotic coefficient 4.93 and is an established baseline, not NISHAN novelty. Relative to the current 52,500-position baseline, the count falls by 76.5124%. This is a code-position comparison, not a verified print-capacity or physical-capture result.

Recommended exact specification:

\[
\begin{aligned}
 n&=1000,& c&=5,& \varepsilon_1&=10^{-6},\\
 k&=\ln(10^9),&\eta&=5/4,&\varepsilon_2&=(10^{-9})^{5/4},\\
 (d_\ell,d_z,d_\delta,d_\alpha,r,s,g)
   &=(23.8,8.08,28.31,4.58,0.67,1.07,0.49),\\
 \ell_0&=595\ln(10^9),&m&=\lceil\ell_0\rceil=12331,\\
 \delta&=\frac1{141.55},&
 Z&=40.4\ln(10^9)+0.098\bigl(12331-595\ln(10^9)\bigr).
\end{aligned}
\]

Thus **δ = 0.00706464146944542564465** and **Z = 837.28430886028977619314**. The exact expressions govern; decimal displays are approximations. Accuse precisely when the symmetric total score exceeds Z.

## Primary source and conditions

Laarhoven and de Weger, *Optimal symmetric Tardos traitor tracing schemes*, Designs, Codes and Cryptography 71 (2014), 83–103, DOI 10.1007/s10623-012-9718-y: [author-hosted primary paper](https://deweger.net/papers/%5B47%5DLdW-OptTTTS-DCC%5B2014%5D.pdf). Relevant locations: Definition 1, Section 2.1, Theorems 3–5, and Appendix A. The article explicitly grants Creative Commons Attribution reuse on page 99. Equations below are credited to that paper; parameter substitutions, coalition-size checks, and implementation audit are independent calculations.

Write H(x) = (exp(x) − 1 − x)/x² and let h be its inverse on x > 0, so h(r) solves H(h(r)) = r. The paper calls H “h⁻¹”; interpreting that notation as a reciprocal would be wrong. For positive constants with dδ > 1 and r > 1/2, the four required margins are:

\[
\begin{aligned}
 M_{S1}&=d_\alpha-\frac{\sqrt{d_\delta}}{h(r)\sqrt c}\ge0,\\
 M_{S2}&=\frac{d_z}{d_\alpha}-\frac{r d_\ell}{d_\alpha^2}-1\ge0,\\
 M_{C1'}&=\frac{2-4/d_\delta}{\pi}
            -\frac{H(s)s}{\sqrt{d_\delta c}}-g\ge0,\\
 M_{C2}&=g d_\ell-d_z-\eta\sqrt{\frac{d_\delta}{s^2c}}\ge0.
\end{aligned}
\]

Theorems 3 and 4 apply when these conditions hold. The paper's convenient printed constants for all c ≥ 2 and η ≤ 1 do not alone establish the required η = 1.25 case; the direct numerical check below does. The coefficient π²/2 ≈ 4.93 is an asymptotic result and supplies no substitute for these finite-c inequalities.

## Budgets and numerical correction

The current [tardos.py](../prototypes/nishan_pq/nishan/tardos.py) metadata uses per-user ε = 10⁻⁹, a nonempty-coalition union bound of 999 × 10⁻⁹, and miss bound ε^(5/4). This audit preserves those *reported budgets*; it does not independently reprove the original asymmetric theorem.

Here k is the unrounded natural logarithm, 20.72326583694641115616; the existing implementation's integer k = 21 is a different parameterization. Since ε₂ = 5.623413251903490804 × 10⁻¹², η = ln(ε₂)/ln(ε₁/n) is exactly 1.25. The symmetric statements are weak probability bounds, “≤”; copy neither the existing `strict_upper` field names nor an unstated relaxation to η = 1.

For each fixed nonempty coalition C of size q ≤ 5 and admissible pirate strategy:

- Each fixed innocent has accusation probability ≤ 10⁻⁹.
- Any innocent is accused with probability ≤ (1000 − q)10⁻⁹ ≤ 9.99 × 10⁻⁷.
- No colluder is accused with probability ≤ 5.623413251903490804 × 10⁻¹².
- The union of those failures has probability ≤ 9.990056234132519035 × 10⁻⁷.

These are probabilities over code construction and any strategy randomness. They are not a simultaneous guarantee for every coalition or every future accusation on one fixed codebook. Empty coalitions do not receive a completeness statement; a soundness bound for an empty coalition would use all 1,000 users.

Independent 60-digit decimal arithmetic gives:

| Quantity | Value |
|---|---:|
| h(0.67) | 0.82004753304656321720 |
| H(1.07) | 0.73838719536815151880 |
| Unrounded ℓ₀ | 12330.34317298311463791634 |
| m − ℓ₀ | 0.65682701688536208366 |
| Unrounded Z₀ | 837.21993981263501070894 |
| Theorem 5 corrected Z | 837.28430886028977619314 |
| Effective dℓ = m/(25k) | 23.80126780599554794118 |
| Effective dz = Z/(5k) | 8.08062122493781849118 |

| Margin | Unrounded design | Integer design, same dα = 4.58 |
|---|---:|---:|
| S1 | 1.67834412151633569717 | 1.67834412151633569717 |
| S2 | 0.00400450029557025991 | 0.00409964437168396717 |
| C1′ | 0.03523799993856370289 | 0.03523799993856370289 |
| C2 | 0.80221525128436083501 | 0.80221525128436083501 |

Theorem 5 increases Z by (g/c)(m − ℓ₀), preserving C2. Although its general proof permits changing auxiliary dα, direct substitution here shows the original 4.58 already works after rounding.

The previously proposed Z = 837.2663899 is **not** the Theorem 5 correction for the supplied constants. Nevertheless, with m = 12331 and that exact decimal threshold, direct evaluation yields S2 margin 0.004061885489707775 and C2 margin 0.802388186963811797, so that alternative also passes. Its threshold provenance and the quoted C2 margin 0.802349 need correction, not rejection of the 12,331-position design. The recommendation above uses the explicit Theorem 5 construction.

For additional numerical cross-checks, the corrected design's moment bounds are approximately 9.18550844217503 × 10⁻¹⁰ per innocent and 3.18694046542462 × 10⁻¹⁵ for a five-member coalition miss. The declared budgets remain the original, weaker values. These calculations do not reserve or prove an implementation error allowance.

## Coverage for every actual coalition size

Checking c = 5 alone should not be justified by adding hypothetical guilty users: accusing a padded user would not ensure accusation of a real colluder. Instead, hold the actual construction m, Z, δ fixed and, for q ∈ {2,3,4,5}, reparameterize the integer-design proof constants using a = 5/q:

\[
d_\ell(q)=a^2d_\ell^*,\quad d_z(q)=a d_z^*,\quad
d_\delta(q)=a d_\delta,\quad d_\alpha(q)=a d_\alpha.
\]

Leave r, s, g, k, and η unchanged. Then m = dℓ(q)q²k, Z = dz(q)qk, and δ = 1/(dδ(q)q) are identical. S1's margin scales by a; S2's margin is unchanged; C1′ improves because its negative 4/dδ term decreases and dδ(q)q is constant. C2's new margin is a times the original margin plus g dℓ* a(a − 1), hence nonnegative.

| Actual q | S1 margin | S2 margin | C1′ margin | C2 margin |
|---|---:|---:|---:|---:|
| 2 | 4.19586030 | 0.00409964 | 0.06222294 | 45.74036772 |
| 3 | 2.79724020 | 0.00409964 | 0.05322796 | 14.29549345 |
| 4 | 2.09793015 | 0.00409964 | 0.04423298 | 4.64733820 |
| 5 | 1.67834412 | 0.00409964 | 0.03523800 | 0.80221525 |

For q = 1, the marking condition forces y to equal that user's entire codeword. Every symmetric contribution is positive and at least √(δ/(1 − δ)); therefore the guilty score is at least 1040.11862402590 > Z and the miss probability is zero. The innocent-score proof remains applicable with one guilty user because its conditional zero-mean and unit-second-moment calculations do not require two pirates.

## Required score, sampling law, and inequalities

For an ideal independent Uᵢ uniform on [0,1], take a₀ = arcsin√δ and pᵢ = sin²(a₀ + Uᵢ(π/2 − 2a₀)). This gives the truncated arcsine density 1/((π − 4a₀)√(p(1 − p))) on [δ,1 − δ]. Conditional on the bias vector, sample every code bit independently with probability pᵢ of one.

The score contribution must be

\[
S_{ji}=(2y_i-1)\frac{X_{ji}-p_i}{\sqrt{p_i(1-p_i)}},
\qquad S_j=\sum_{i=1}^{12331}S_{ji}.
\]

In particular, y = 0 contributes −√((1 − p)/p) for X = 1 and +√(p/(1 − p)) for X = 0. The current `accusation_scores` drops all y = 0 positions and therefore **cannot** implement this profile merely by replacing its length, cutoff, and threshold.

Accusation uses Sⱼ > Z. No accusation implies every colluder score ≤ Z and total coalition score S ≤ qZ. Section 4's proof writes a strict inequality at this point; the rigorous version is P[miss] ≤ P[S ≤ qZ] ≤ exp(βqZ)E[exp(−βS)]. Ordinary Markov with ≥ in its exponential event gives the same bound, including ties. Theorems' parameter inequalities allow equality, and this candidate has positive margins. Numerical score rounding still requires a separate implementation argument.

The strategy may depend on the coalition's codewords, including across positions. It must preserve every unanimous position, produce a complete binary word, and receive no extra secret bias or innocent-codeword access beyond the stated model. Soundness can be conditioned on the pirate word and bias vector before bounding independent innocent bits; completeness uses the conditional per-column maximum in Appendix A. Arbitrary output correlations should not be justified by an unsupported assertion that the unconditional scores are independent.

## Implementation and physical-channel gaps

Inspection of `generate_keyed` shows AES-CTR streams derived through HMAC-SHA3-512 with distinct purposes, nominal 53-bit bias uniforms, and 32-bit Bernoulli samples. For fixed secret and context the entire codebook is deterministic. A computational pseudorandomness claim requires a random protected key and a reduction/security assumption; the paper's information-theoretic random experiment does not automatically transfer.

The actual Bernoulli parameter is qᵢ = floor(2³²pᵢ)/2³², whereas scoring uses stored pᵢ. Thus |qᵢ − pᵢ| < 2⁻³² but exact score centering is lost: for y = 1, E[Sⱼᵢ | pᵢ] = (qᵢ − pᵢ)/√(pᵢ(1 − pᵢ)); the sign reverses for y = 0. A crude bit-coupling bound over the whole 1000 × 12331 codebook is 0.0028710346669, and even five rows give 0.0000143551733. These upper bounds are far too large to certify the stated tiny budgets; they are not lower bounds on actual failure and do not prove the sampler unsafe. A sharper finite-precision moment analysis is required.

Bias quantization and floating-point sin, square root, score summation, and threshold representation add separate issues. Nominal 53-bit midpoint arithmetic itself rounds in float64. A discrete bias distribution has total variation distance one from an ideal continuous distribution, so a naive small-total-variation argument for the bias vector cannot bridge the theorem. A useful transfer must instead control the finite-dimensional code/output law or the actual moments and score error. Changing scoring to use qᵢ would address one centering issue but also changes the bias distribution and does not finish that proof.

The required budget-preserving transfer would bound the combined effects of pseudorandom generation, quantization, and arithmetic within the available theoretical slack, or establish new moments directly. No such transfer is supplied here. Existing reproducibility and simulated-attack tests do not establish it.

Likewise, optical errors, erased positions, guessed fills, coordinate remapping, soft scores, or calibration on the observed pirate word are outside this calculation. The full decoded binary word must satisfy the marking assumption for the claimed completeness bound. A 12,331-position design requires a newly generated bias vector/codebook and a matching symmetric detector; old codebook commitments, physical captures, and asymmetric scores cannot be relabeled as evidence for it. No physical observations were rescored in this audit.

## Reproduce the audit arithmetic

Run the following with standard-library Python 3; no NumPy or arbitrary-precision package is needed. Decimal arithmetic uses 60 digits, a 60-digit π literal, and monotone bisection for h. Values printed above are rounded. The positive margins are large relative to numerical precision; this is a high-precision numerical audit, not a formal interval proof.

```python
from decimal import Decimal as D, getcontext, ROUND_CEILING

getcontext().prec = 60
pi = D("3.14159265358979323846264338327950288419716939937510582097494459")
n, c, e1, eta = D(1000), D(5), D("1e-6"), D("1.25")
k = (n / e1).ln()
dl, dz, dd, da, r, s, g = map(
    D, ["23.8", "8.08", "28.31", "4.58", ".67", "1.07", ".49"]
)
H = lambda x: (x.exp() - 1 - x) / x**2
lo, hi = D("0.01"), D(2)
for _ in range(190):
    mid = (lo + hi) / 2
    if H(mid) < r:
        lo = mid
    else:
        hi = mid
h = (lo + hi) / 2

def margins(t, dl_, dz_, dd_, da_):
    return (
        da_ - dd_.sqrt() / (h * t.sqrt()),
        dz_ / da_ - r * dl_ / da_**2 - 1,
        (2 - 4 / dd_) / pi - H(s) * s / (dd_ * t).sqrt() - g,
        g * dl_ - dz_ - eta * (dd_ / (s * s * t)).sqrt(),
    )

l0 = dl * c * c * k
m = l0.to_integral_value(rounding=ROUND_CEILING)
z0 = dz * c * k
z = z0 + g / c * (m - l0)
delta = 1 / (dd * c)
dl1, dz1 = m / (c * c * k), z / (c * k)
print("k, h(r), H(s):", k, h, H(s))
print("l0, m, z0, Z, delta:", l0, m, z0, z, delta)
print("effective dl, dz:", dl1, dz1)
print("original margins:", margins(c, dl, dz, dd, da))
for q in range(2, 6):
    t = D(q)
    a = c / t
    result = margins(t, dl1 * a**2, dz1 * a, dd * a, da * a)
    assert all(v > 0 for v in result)
    print("actual coalition", q, "margins:", result)
print("previous threshold margins:",
      margins(c, dl1, D("837.2663899") / (c * k), dd, da))
solo = m * (delta / (1 - delta)).sqrt()
assert solo > z
print("solo minimum:", solo)
print("declared miss budget:", (-eta * k).exp())
print("sound moment bound:", (-k * (dz1 / da - r * dl1 / da**2)).exp())
print("miss moment bound:", (-s * (c / dd).sqrt() * (g * dl1 - dz1) * k).exp())
print("32-bit coupling ceilings:", n * m / D(2)**32, c * m / D(2)**32)
```
