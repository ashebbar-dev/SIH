"""Text-preserving PDF layout carrier for controlled digital-PDF fixtures.

The carrier encodes bits as tiny positive or negative ``TJ`` text-position
adjustments after ASCII spaces.  It modifies content streams in place instead
of rendering each page to an image, so supported PDFs retain their text, fonts,
vector content, links, and other document objects.

This is deliberately a narrow prototype:

* it supports hexadecimal strings in ``TJ`` arrays for simple 8-bit fonts;
* extraction is exact from the marked digital PDF, not robust to arbitrary
  optimizer rewrites, print/scan, OCR, or photography;
* layout positions are not independent watermark channels, and this module
  does not make a Tardos theorem apply to the physical carrier.

Those boundaries are part of the evidence, not hidden implementation details.
"""

from __future__ import annotations

import hashlib
import hmac
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pymupdf as fitz


_TJ_ARRAY = re.compile(rb"\[(?P<body>.*?)\]\s*TJ", re.DOTALL)
_TOKEN = re.compile(
    rb"<(?P<hex>[0-9A-Fa-f]*)>|(?P<number>[-+]?(?:\d+(?:\.\d*)?|\.\d+))"
)


@dataclass(frozen=True)
class EmbedResult:
    capacity_bits: int
    payload_bits: int
    modified_streams: int
    adjustment_magnitude: float
    text_preserved: bool
    source_text_sha3_256: str
    marked_text_sha3_256: str


def _matched_tokens(body: bytes) -> list[re.Match[bytes]] | None:
    tokens = list(_TOKEN.finditer(body))
    remainder = _TOKEN.sub(b"", body)
    if remainder.strip() or not tokens:
        return None
    return tokens


def _eligible_spaces_in_body(body: bytes) -> int:
    tokens = _matched_tokens(body)
    if tokens is None:
        return 0
    return sum(
        bytes.fromhex(match.group("hex").decode("ascii")).count(b" ")
        for match in tokens
        if match.group("hex") is not None
    )


def _eligible_spaces(stream: bytes) -> int:
    return sum(
        _eligible_spaces_in_body(match.group("body"))
        for match in _TJ_ARRAY.finditer(stream)
    )


def capacity(path: Path) -> int:
    """Count supported ASCII-space positions across all content streams."""

    document = fitz.open(path)
    try:
        xrefs = list(
            dict.fromkeys(xref for page in document for xref in page.get_contents())
        )
        return sum(
            _eligible_spaces(document.xref_stream(xref))
            for xref in xrefs
        )
    finally:
        document.close()


def _prf_bytes(secret: bytes, context: str, purpose: bytes, length: int) -> bytes:
    prefix = b"NISHAN-LIVE-PDF/v1\x00" + purpose + b"\x00" + context.encode("utf-8")
    output = bytearray()
    counter = 0
    while len(output) < length:
        output.extend(
            hmac.new(
                secret,
                prefix + counter.to_bytes(8, "big"),
                hashlib.sha3_256,
            ).digest()
        )
        counter += 1
    return bytes(output[:length])


def _prf_bits(secret: bytes, context: str, purpose: bytes, length: int) -> np.ndarray:
    if length == 0:
        return np.empty(0, dtype=np.uint8)
    material = _prf_bytes(secret, context, purpose, math.ceil(length / 8))
    return np.unpackbits(np.frombuffer(material, dtype=np.uint8))[:length]


def _permutation(secret: bytes, context: str, length: int) -> np.ndarray:
    if length == 0:
        return np.empty(0, dtype=np.int64)
    keys = np.frombuffer(
        _prf_bytes(secret, context, b"order", length * 8), dtype="<u8"
    )
    return np.argsort(keys, kind="stable")


def _carrier_plan(
    secret: bytes,
    context: str,
    capacity_bits: int,
    payload_bits: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if payload_bits < 0 or payload_bits > capacity_bits:
        raise ValueError(
            f"payload needs {payload_bits} positions but supported capacity is {capacity_bits}"
        )
    order = _permutation(secret, context, capacity_bits)
    pad = _prf_bits(secret, context, b"pad", payload_bits)
    filler = _prf_bits(secret, context, b"filler", capacity_bits)
    return order, pad, filler


def _number(value: float) -> bytes:
    if not math.isfinite(value) or value <= 0:
        raise ValueError("adjustment magnitude must be finite and positive")
    if value.is_integer():
        return str(int(value)).encode("ascii")
    return (f"{value:.6f}".rstrip("0").rstrip(".")).encode("ascii")


def _rewrite_body(
    body: bytes,
    signs: Iterable[int],
    magnitude: bytes,
) -> tuple[bytes, int]:
    tokens = _matched_tokens(body)
    if tokens is None:
        return body, 0
    sign_iterator = iter(signs)
    rebuilt: list[bytes] = []
    used = 0
    for match in tokens:
        hex_value = match.group("hex")
        if hex_value is None:
            rebuilt.append(match.group(0))
            continue
        raw = bytes.fromhex(hex_value.decode("ascii"))
        start = 0
        for index, value in enumerate(raw):
            if value != 0x20:
                continue
            rebuilt.append(b"<" + raw[start : index + 1].hex().encode("ascii") + b">")
            bit = int(next(sign_iterator))
            rebuilt.append(magnitude if bit else b"-" + magnitude)
            used += 1
            start = index + 1
        if start < len(raw):
            rebuilt.append(b"<" + raw[start:].hex().encode("ascii") + b">")
        elif start == 0:
            rebuilt.append(match.group(0))
    return b" ".join(rebuilt), used


def _rewrite_stream(
    stream: bytes,
    signs: np.ndarray,
    offset: int,
    adjustment_magnitude: float,
) -> tuple[bytes, int]:
    magnitude = _number(adjustment_magnitude)

    def replace(match: re.Match[bytes]) -> bytes:
        nonlocal offset
        body = match.group("body")
        count = _eligible_spaces_in_body(body)
        if count == 0:
            return match.group(0)
        rewritten, used = _rewrite_body(body, signs[offset : offset + count], magnitude)
        if used != count:
            raise AssertionError("layout carrier position count changed during rewrite")
        offset += used
        return b"[" + rewritten + b"]TJ"

    return _TJ_ARRAY.sub(replace, stream), offset


def _document_text(document: fitz.Document) -> str:
    return "\f".join(page.get_text() for page in document)


def _text_digest(text: str) -> str:
    return hashlib.sha3_256(text.encode("utf-8")).hexdigest()


def embed(
    source: Path,
    destination: Path,
    bits: np.ndarray | list[int],
    secret: bytes,
    context: str,
    adjustment_magnitude: float = 0.5,
) -> EmbedResult:
    """Embed a binary payload while preserving supported PDF text objects."""

    payload = np.asarray(bits, dtype=np.uint8)
    if payload.ndim != 1 or np.any((payload != 0) & (payload != 1)):
        raise ValueError("bits must be a one-dimensional binary sequence")
    if source.suffix.lower() != ".pdf" or destination.suffix.lower() != ".pdf":
        raise ValueError("the live-text carrier accepts PDF input and output")
    _number(float(adjustment_magnitude))

    document = fitz.open(source)
    try:
        original_text = _document_text(document)
        stream_xrefs = list(
            dict.fromkeys(xref for page in document for xref in page.get_contents())
        )
        total_capacity = sum(
            _eligible_spaces(document.xref_stream(xref)) for xref in stream_xrefs
        )
        order, pad, carrier = _carrier_plan(
            secret, context, total_capacity, int(payload.size)
        )
        if payload.size:
            carrier[order[: payload.size]] = payload ^ pad

        offset = 0
        modified_streams = 0
        for xref in stream_xrefs:
            raw = document.xref_stream(xref)
            rewritten, new_offset = _rewrite_stream(
                raw, carrier, offset, float(adjustment_magnitude)
            )
            if rewritten != raw:
                document.update_stream(xref, rewritten, compress=True)
                modified_streams += 1
            offset = new_offset
        if offset != total_capacity:
            raise AssertionError("not every planned layout position was embedded")
        destination.parent.mkdir(parents=True, exist_ok=True)
        document.save(destination, garbage=0, clean=False, deflate=True)
    finally:
        document.close()

    marked = fitz.open(destination)
    try:
        marked_text = _document_text(marked)
    finally:
        marked.close()
    return EmbedResult(
        capacity_bits=total_capacity,
        payload_bits=int(payload.size),
        modified_streams=modified_streams,
        adjustment_magnitude=float(adjustment_magnitude),
        text_preserved=marked_text == original_text,
        source_text_sha3_256=_text_digest(original_text),
        marked_text_sha3_256=_text_digest(marked_text),
    )


def read_carrier(
    path: Path,
    adjustment_magnitude: float = 0.5,
) -> np.ndarray:
    """Read all signed layout symbols once for candidate-specific decoding."""

    target = float(adjustment_magnitude)
    tolerance = max(1e-6, target * 1e-6)
    encoded: list[int] = []
    document = fitz.open(path)
    try:
        xrefs = list(
            dict.fromkeys(xref for page in document for xref in page.get_contents())
        )
        for xref in xrefs:
            stream = document.xref_stream(xref)
            for array in _TJ_ARRAY.finditer(stream):
                tokens = _matched_tokens(array.group("body"))
                if tokens is None:
                    continue
                for index, token in enumerate(tokens[:-1]):
                    hex_value = token.group("hex")
                    if hex_value is None:
                        continue
                    raw = bytes.fromhex(hex_value.decode("ascii"))
                    following = tokens[index + 1].group("number")
                    if not raw.endswith(b" ") or following is None:
                        continue
                    value = float(following)
                    if abs(abs(value) - target) <= tolerance:
                        encoded.append(1 if value > 0 else 0)
            # A transformed trailing space can be followed by a final number;
            # the token-pair loop above includes that case.
    finally:
        document.close()
    return np.asarray(encoded, dtype=np.uint8)


def decode_carrier(
    carrier: np.ndarray | list[int],
    payload_bits: int,
    secret: bytes,
    context: str,
) -> np.ndarray:
    """Decode one candidate context from an already-read carrier sequence."""

    values = np.asarray(carrier, dtype=np.uint8)
    if values.ndim != 1 or np.any((values != 0) & (values != 1)):
        raise ValueError("carrier must be a one-dimensional binary sequence")
    order, pad, _ = _carrier_plan(secret, context, int(values.size), payload_bits)
    return values[order[:payload_bits]] ^ pad


def extract(
    marked: Path,
    payload_bits: int,
    secret: bytes,
    context: str,
    adjustment_magnitude: float = 0.5,
) -> np.ndarray:
    """Recover a payload from an unrewritten marked digital PDF."""

    carrier = read_carrier(marked, adjustment_magnitude)
    return decode_carrier(carrier, payload_bits, secret, context)


def strip_layout_adjustments(
    source: Path,
    destination: Path,
    adjustment_magnitude: float = 0.5,
) -> int:
    """Remove this prototype's signed ``TJ`` adjustments from an editable PDF.

    This is an attack fixture, not a sanitizer. It deliberately demonstrates that
    the layout tag also remains removable when an attacker normalizes the relevant
    content operators.
    """

    target = float(adjustment_magnitude)
    tolerance = max(1e-6, target * 1e-6)
    document = fitz.open(source)
    removed = 0
    try:
        xrefs = list(
            dict.fromkeys(xref for page in document for xref in page.get_contents())
        )
        for xref in xrefs:
            stream = document.xref_stream(xref)

            def strip_array(match: re.Match[bytes]) -> bytes:
                nonlocal removed
                tokens = _matched_tokens(match.group("body"))
                if tokens is None:
                    return match.group(0)
                kept: list[bytes] = []
                previous_hex_ended_space = False
                for token in tokens:
                    hex_value = token.group("hex")
                    number = token.group("number")
                    if number is not None:
                        value = float(number)
                        if previous_hex_ended_space and abs(abs(value) - target) <= tolerance:
                            removed += 1
                            previous_hex_ended_space = False
                            continue
                        kept.append(token.group(0))
                        previous_hex_ended_space = False
                        continue
                    kept.append(token.group(0))
                    raw = bytes.fromhex((hex_value or b"").decode("ascii"))
                    previous_hex_ended_space = raw.endswith(b" ")
                return b"[" + b" ".join(kept) + b"]TJ"

            normalized = _TJ_ARRAY.sub(strip_array, stream)
            if normalized != stream:
                document.update_stream(xref, normalized, compress=True)
        destination.parent.mkdir(parents=True, exist_ok=True)
        document.save(destination, garbage=0, clean=False, deflate=True)
    finally:
        document.close()
    return removed
