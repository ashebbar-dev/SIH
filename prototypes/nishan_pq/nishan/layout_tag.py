"""Short cryptographic session tag for the live-PDF text-layout channel.

The visual Tardos carrier has enough page-pixel capacity for collusion tracing but
is a separately addressable PDF image.  This channel stores a domain-separated
keyed session authenticator in text-position adjustments.  A Hamming(7,4) code expands
72 authenticator bits to 126 layout symbols and corrects one flipped symbol in
each seven-symbol block.

This tag is not a collusion-secure fingerprint code.  Its role is attack
complementarity: it can identify an editable PDF after the visual overlay is
removed, while the Tardos channel handles rendered copies that have no PDF text
operators.  The tracer must report conflicts rather than choosing whichever
channel names a convenient suspect.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

import numpy as np


TAG_BITS = 72
ENCODED_BITS = TAG_BITS // 4 * 7


@dataclass(frozen=True)
class DecodeResult:
    bits: np.ndarray
    corrected_blocks: int
    blocks: int


def tag_bits(
    secret: bytes,
    document_id: str,
    session_id: str,
    user_index: int,
) -> np.ndarray:
    if len(secret) < 32:
        raise ValueError("secret must contain at least 32 bytes")
    if user_index < 0:
        raise ValueError("user_index must be non-negative")
    material = (
        f"NISHAN-LAYOUT-TAG/v1|{document_id}|{session_id}|{user_index}"
    ).encode("utf-8")
    digest = hmac.new(secret, material, hashlib.sha3_256).digest()
    return np.unpackbits(np.frombuffer(digest[: TAG_BITS // 8], dtype=np.uint8))


def hamming74_encode(bits: np.ndarray | list[int]) -> np.ndarray:
    data = np.asarray(bits, dtype=np.uint8)
    if data.ndim != 1 or data.size % 4 or np.any((data != 0) & (data != 1)):
        raise ValueError("input must be a one-dimensional binary sequence divisible by four")
    nibbles = data.reshape(-1, 4)
    words = np.zeros((len(nibbles), 7), dtype=np.uint8)
    # One-indexed Hamming positions: parity at 1,2,4; data at 3,5,6,7.
    words[:, [2, 4, 5, 6]] = nibbles
    words[:, 0] = words[:, 2] ^ words[:, 4] ^ words[:, 6]
    words[:, 1] = words[:, 2] ^ words[:, 5] ^ words[:, 6]
    words[:, 3] = words[:, 4] ^ words[:, 5] ^ words[:, 6]
    return words.reshape(-1)


def hamming74_decode(encoded: np.ndarray | list[int]) -> DecodeResult:
    values = np.asarray(encoded, dtype=np.uint8)
    if values.ndim != 1 or values.size % 7 or np.any((values != 0) & (values != 1)):
        raise ValueError("encoded input must be a one-dimensional binary sequence divisible by seven")
    words = values.reshape(-1, 7).copy()
    syndrome_one = words[:, 0] ^ words[:, 2] ^ words[:, 4] ^ words[:, 6]
    syndrome_two = words[:, 1] ^ words[:, 2] ^ words[:, 5] ^ words[:, 6]
    syndrome_four = words[:, 3] ^ words[:, 4] ^ words[:, 5] ^ words[:, 6]
    syndromes = syndrome_one + 2 * syndrome_two + 4 * syndrome_four
    corrected = syndromes != 0
    for row, syndrome in zip(np.flatnonzero(corrected), syndromes[corrected], strict=True):
        words[row, int(syndrome) - 1] ^= 1
    data = words[:, [2, 4, 5, 6]].reshape(-1)
    return DecodeResult(
        bits=data,
        corrected_blocks=int(np.count_nonzero(corrected)),
        blocks=len(words),
    )


def encoded_tag(
    secret: bytes,
    document_id: str,
    session_id: str,
    user_index: int,
) -> np.ndarray:
    return hamming74_encode(tag_bits(secret, document_id, session_id, user_index))


def matches(
    decoded_bits: np.ndarray,
    secret: bytes,
    document_id: str,
    session_id: str,
    user_index: int,
) -> bool:
    expected = np.packbits(tag_bits(secret, document_id, session_id, user_index)).tobytes()
    observed = np.packbits(np.asarray(decoded_bits, dtype=np.uint8)).tobytes()
    return hmac.compare_digest(expected, observed)
