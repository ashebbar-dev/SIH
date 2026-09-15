"""Auditable reference implementation of Tardos's original binary code.

This module follows Section 2.1 of Gábor Tardos, "Optimal probabilistic
fingerprint codes" (STOC 2003 / JACM 2008).  It intentionally uses the
paper's conservative constants rather than presenting an empirical threshold as
a theorem:

* k = ceil(log(1 / epsilon_user))
* m = 100 c^2 k
* cutoff t = 1 / (300 c)
* accusation threshold Z = 20 c k

For a familywise target epsilon over n enrolled sessions, the reference profile
uses epsilon_user = epsilon / n.  The paper's Corollary 3 applies for c >= 4
under the marking condition.  NumPy's deterministic generator is used here for
reproducible research fixtures; a deployed codebook needs an audited
cryptographic DRBG and protected codebook state.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import math
from dataclasses import asdict, dataclass
from typing import Literal

import numpy as np
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes


Attack = Literal["interleaving", "majority", "minority", "coin_flip"]


@dataclass(frozen=True)
class Parameters:
    roster_size: int
    coalition_limit: int
    familywise_epsilon: float
    per_user_epsilon: float
    k: int
    code_length: int
    cutoff: float
    threshold: float
    marking_assumption_required: bool
    theorem_profile: str


def parameters(
    roster_size: int,
    coalition_limit: int,
    familywise_epsilon: float,
) -> Parameters:
    if roster_size < 2:
        raise ValueError("roster_size must be at least 2")
    if coalition_limit < 4 or coalition_limit > roster_size:
        raise ValueError(
            "the original familywise reference profile requires 4 <= coalition_limit <= roster_size"
        )
    if not 0.0 < familywise_epsilon < 1.0:
        raise ValueError("familywise_epsilon must be between 0 and 1")
    per_user = familywise_epsilon / roster_size
    k = math.ceil(math.log(1.0 / per_user))
    return Parameters(
        roster_size=roster_size,
        coalition_limit=coalition_limit,
        familywise_epsilon=familywise_epsilon,
        per_user_epsilon=per_user,
        k=k,
        code_length=100 * coalition_limit * coalition_limit * k,
        cutoff=1.0 / (300.0 * coalition_limit),
        threshold=float(20 * coalition_limit * k),
        marking_assumption_required=True,
        theorem_profile="Tardos F_(n,c,epsilon/n), original conservative constants",
    )


def theorem_bounds(config: Parameters) -> dict[str, float | str]:
    """Return the paper-level bounds, separate from any empirical simulation."""

    per_user = config.per_user_epsilon
    fixed_innocent = per_user
    any_innocent_union = (config.roster_size - 1) * per_user
    no_colluder = per_user ** (config.coalition_limit / 4.0)
    return {
        "soundness_fixed_innocent_strict_upper": fixed_innocent,
        "soundness_any_innocent_union_upper": any_innocent_union,
        "completeness_no_colluder_strict_upper": no_colluder,
        "combined_error_upper": any_innocent_union + no_colluder,
        "scope": "random code construction; coalition obeys the marking condition",
    }


def generate(
    config: Parameters,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate bias vector p and the n-by-m binary fingerprint codebook."""

    angle_cutoff = math.asin(math.sqrt(config.cutoff))
    angles = rng.uniform(
        angle_cutoff,
        math.pi / 2.0 - angle_cutoff,
        size=config.code_length,
    )
    biases = np.square(np.sin(angles)).astype(np.float64)
    codebook = (
        rng.random((config.roster_size, config.code_length)) < biases
    ).astype(np.uint8)
    return biases, codebook


def _aes_ctr_stream(
    master_secret: bytes,
    context: str,
    purpose: bytes,
):
    if len(master_secret) < 32:
        raise ValueError("master_secret must contain at least 32 bytes")
    material = hmac.new(
        master_secret,
        b"NISHAN-TARDOS-CODEBOOK/v1\x00"
        + purpose
        + b"\x00"
        + context.encode("utf-8"),
        hashlib.sha3_512,
    ).digest()
    return Cipher(algorithms.AES(material[:32]), modes.CTR(material[32:48])).encryptor()


def generate_keyed(
    config: Parameters,
    master_secret: bytes,
    context: str,
    row_chunk: int = 32,
) -> tuple[np.ndarray, np.ndarray]:
    """Generate a secret reproducible codebook from independent AES-CTR streams.

    This avoids using a predictable scientific PRNG for the operational prototype.
    Biases use 53 random bits and Bernoulli samples use 32 random bits, so this is
    a finite-precision implementation of the paper's ideal random construction.
    The cryptography library supplies AES; this function is not itself an audited
    DRBG implementation.
    """

    if row_chunk < 1:
        raise ValueError("row_chunk must be positive")
    bias_stream = _aes_ctr_stream(master_secret, context, b"biases")
    raw_biases = np.frombuffer(
        bias_stream.update(bytes(config.code_length * 8)) + bias_stream.finalize(),
        dtype="<u8",
    )
    uniform = ((raw_biases >> 11).astype(np.float64) + 0.5) / float(1 << 53)
    angle_cutoff = math.asin(math.sqrt(config.cutoff))
    angles = angle_cutoff + uniform * (math.pi / 2.0 - 2.0 * angle_cutoff)
    biases = np.square(np.sin(angles)).astype(np.float64)

    sample_stream = _aes_ctr_stream(master_secret, context, b"bernoulli-samples")
    thresholds = np.floor(biases * float(1 << 32)).astype(np.uint64)
    codebook = np.empty(
        (config.roster_size, config.code_length), dtype=np.uint8
    )
    for start in range(0, config.roster_size, row_chunk):
        stop = min(start + row_chunk, config.roster_size)
        rows = stop - start
        raw = sample_stream.update(bytes(rows * config.code_length * 4))
        samples = np.frombuffer(raw, dtype="<u4").reshape(rows, config.code_length)
        codebook[start:stop] = (samples < thresholds).astype(np.uint8)
    sample_stream.finalize()
    return biases, codebook


def simulate_attack(
    colluder_codewords: np.ndarray,
    attack: Attack,
    rng: np.random.Generator,
) -> np.ndarray:
    """Create a pirate word under one named strategy and the marking condition."""

    if colluder_codewords.ndim != 2 or colluder_codewords.shape[0] < 1:
        raise ValueError("colluder_codewords must be a non-empty 2-D array")
    ones = colluder_codewords.sum(axis=0)
    coalition_size = colluder_codewords.shape[0]
    unanimous_zero = ones == 0
    unanimous_one = ones == coalition_size
    disagreement = ~(unanimous_zero | unanimous_one)
    pirate = np.zeros(colluder_codewords.shape[1], dtype=np.uint8)
    pirate[unanimous_one] = 1

    if attack == "interleaving":
        choices = rng.integers(0, coalition_size, size=int(disagreement.sum()))
        columns = np.flatnonzero(disagreement)
        pirate[columns] = colluder_codewords[choices, columns]
    elif attack == "coin_flip":
        pirate[disagreement] = rng.integers(
            0, 2, size=int(disagreement.sum()), dtype=np.uint8
        )
    elif attack in {"majority", "minority"}:
        twice_ones = 2 * ones
        if attack == "majority":
            pirate[twice_ones > coalition_size] = 1
        else:
            # On disagreement choose the less common symbol. Unanimous columns
            # were already fixed by the marking condition.
            pirate[disagreement & (twice_ones < coalition_size)] = 1
        ties = disagreement & (twice_ones == coalition_size)
        pirate[ties] = rng.integers(0, 2, size=int(ties.sum()), dtype=np.uint8)
    else:  # pragma: no cover - Literal protects normal callers
        raise ValueError(attack)

    if np.any(pirate[unanimous_zero] != 0) or np.any(pirate[unanimous_one] != 1):
        raise AssertionError("attack violated the marking condition")
    return pirate


def accusation_scores(
    biases: np.ndarray,
    codebook: np.ndarray,
    pirate_word: np.ndarray,
    row_chunk: int = 64,
) -> np.ndarray:
    """Compute the original one-sided Tardos accusation sum for every row."""

    if row_chunk < 1:
        raise ValueError("row_chunk must be positive")
    if codebook.ndim != 2:
        raise ValueError("codebook must be 2-D")
    if biases.shape != (codebook.shape[1],):
        raise ValueError("bias vector length does not match codebook")
    if pirate_word.shape != (codebook.shape[1],):
        raise ValueError("pirate word length does not match codebook")
    active = pirate_word.astype(bool)
    active_biases = biases[active]
    positive = np.sqrt((1.0 - active_biases) / active_biases)
    negative = -np.sqrt(active_biases / (1.0 - active_biases))
    scores = np.empty(codebook.shape[0], dtype=np.float64)
    for start in range(0, codebook.shape[0], row_chunk):
        stop = min(start + row_chunk, codebook.shape[0])
        rows = codebook[start:stop, active]
        contributions = np.where(rows == 1, positive, negative)
        scores[start:stop] = contributions.sum(axis=1)
    return scores


def accuse(scores: np.ndarray, config: Parameters) -> np.ndarray:
    return np.flatnonzero(scores > config.threshold)


def manifest(
    config: Parameters,
    biases: np.ndarray,
    codebook: np.ndarray,
) -> dict[str, object]:
    """Produce commitments and theorem metadata without exposing the codebook."""

    return {
        "parameters": asdict(config),
        "theorem_bounds": theorem_bounds(config),
        "biases_sha3_256": hashlib.sha3_256(
            np.ascontiguousarray(biases, dtype="<f8").tobytes()
        ).hexdigest(),
        "codebook_sha3_256": hashlib.sha3_256(
            np.ascontiguousarray(codebook, dtype="u1").tobytes()
        ).hexdigest(),
        "codebook_shape": list(codebook.shape),
        "commitment_encoding": "biases=<f8 row-major; codebook=u1 row-major",
        "implementation_note": (
            "Reproducible research generator; deployment requires protected state and an audited cryptographic DRBG."
        ),
    }


def canonical_manifest_bytes(value: dict[str, object]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
