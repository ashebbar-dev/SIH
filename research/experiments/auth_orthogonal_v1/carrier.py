"""Isolated orthogonal authenticator carrier for the prospective study.

This module is experiment code, not a production authentication protocol.  It
implements the fixed profile in ``NISHAN_AUTH_ORTHOGONAL_SPEC_2026-09-12.md``.
"""

from __future__ import annotations

import hashlib
import hmac
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf as fitz

from nishan import layout_tag, registration, tardos_carrier, watermark


DPI = 144
BLOCK_SIZE = 6
STRENGTH = 4.0
SYMBOLS = 52_500
TAG_RAW_BITS = 72
TAG_ENCODED_BITS = 126
REPEATS = 200
PLACEMENTS = TAG_ENCODED_BITS * REPEATS
PROTOCOL = "nishan-auth-carrier-study/v1"
PROFILE = "orthogonal-144-6-4-exact72"


@dataclass(frozen=True)
class AuthPlan:
    raw_bits: np.ndarray
    encoded_bits: np.ndarray
    positions: np.ndarray
    orientations: np.ndarray
    polarities: np.ndarray


def _require_ascii(value: object, name: str, *, nonempty: bool = True) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if nonempty and not value:
        raise ValueError(f"{name} must not be empty")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must contain only ASCII characters") from exc
    return value


def _require_sha3_hex(value: object, name: str) -> str:
    text = _require_ascii(value, name)
    if len(text) != 64 or any(character not in "0123456789abcdef" for character in text):
        raise ValueError(f"{name} must be a lowercase 64-character hexadecimal digest")
    return text


def _require_secret(secret: object) -> bytes:
    if not isinstance(secret, bytes):
        raise TypeError("secret must be bytes")
    if len(secret) < 32:
        raise ValueError("secret must contain at least 32 bytes")
    return secret


def canonical_context(
    source_hash: str,
    recipient_key_hash: str,
    session_id: str,
    row: int,
) -> str:
    """Return the fixed, canonical ASCII JSON context for one issued row."""

    import json

    source = _require_sha3_hex(source_hash, "source_hash")
    recipient = _require_sha3_hex(recipient_key_hash, "recipient_key_hash")
    session = _require_ascii(session_id, "session_id")
    if isinstance(row, bool) or not isinstance(row, int):
        raise TypeError("row must be an integer")
    if row < 0:
        raise ValueError("row must be non-negative")
    return json.dumps(
        {
            "profile": PROFILE,
            "protocol": PROTOCOL,
            "recipient_public_key_sha3_256": recipient,
            "row": row,
            "session_id": session,
            "source_sha3_256": source,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    )


def auth_bits(secret: bytes, context: str) -> np.ndarray:
    key = _require_secret(secret)
    canonical = _require_ascii(context, "context")
    payload = hmac.new(
        key,
        b"NISHAN-RECIPIENT-AUTH/v1|" + canonical.encode("ascii"),
        hashlib.sha3_256,
    ).digest()[: TAG_RAW_BITS // 8]
    return np.unpackbits(np.frombuffer(payload, dtype=np.uint8)).copy()


def make_plan(
    secret: bytes,
    context: str,
    tardos_order: np.ndarray,
    tardos_orientation: np.ndarray,
) -> AuthPlan:
    """Create the fixed authenticator plan from a full Tardos carrier plan."""

    key = _require_secret(secret)
    canonical = _require_ascii(context, "context")
    order = np.asarray(tardos_order)
    orientation = np.asarray(tardos_orientation)
    if order.ndim != 1 or order.size != SYMBOLS:
        raise ValueError(f"tardos_order must contain exactly {SYMBOLS} positions")
    if orientation.shape != (SYMBOLS,):
        raise ValueError(f"tardos_orientation must contain exactly {SYMBOLS} values")
    if not np.issubdtype(order.dtype, np.integer):
        raise ValueError("tardos_order must be an integer array")
    order = order.astype(np.int64, copy=False)
    if np.any(order < 0) or np.unique(order).size != SYMBOLS:
        raise ValueError("tardos_order positions must be non-negative and unique")
    if not np.all(np.isin(orientation, (0, 1))):
        raise ValueError("tardos_orientation must be binary")
    orientation = orientation.astype(np.uint8, copy=False)

    raw = auth_bits(key, canonical)
    encoded = layout_tag.hamming74_encode(raw)
    selection_keys = np.frombuffer(
        tardos_carrier._prf_bytes(
            key, canonical, b"auth-symbol-order", SYMBOLS * 8
        ),
        dtype="<u8",
    )
    selected_indices = np.argsort(selection_keys, kind="stable")[:PLACEMENTS]
    positions = order[selected_indices].astype(np.int64, copy=True)
    orientations = (1 - orientation[selected_indices]).astype(np.uint8, copy=True)
    polarity_bits = np.unpackbits(
        np.frombuffer(
            tardos_carrier._prf_bytes(
                key,
                canonical,
                b"auth-polarities",
                math.ceil(PLACEMENTS / 8),
            ),
            dtype=np.uint8,
        )
    )[:PLACEMENTS]
    polarities = (2 * polarity_bits.astype(np.int8) - 1).astype(np.int8, copy=False)
    return AuthPlan(
        raw_bits=raw,
        encoded_bits=encoded,
        positions=positions,
        orientations=orientations,
        polarities=polarities,
    )


def _validate_plan(plan: AuthPlan) -> None:
    if not isinstance(plan, AuthPlan):
        raise TypeError("plan must be an AuthPlan")
    if plan.raw_bits.shape != (TAG_RAW_BITS,) or not np.all(np.isin(plan.raw_bits, (0, 1))):
        raise ValueError("plan raw bits do not match the fixed profile")
    if plan.encoded_bits.shape != (TAG_ENCODED_BITS,) or not np.all(
        np.isin(plan.encoded_bits, (0, 1))
    ):
        raise ValueError("plan encoded bits do not match the fixed profile")
    if plan.positions.shape != (PLACEMENTS,) or not np.issubdtype(
        plan.positions.dtype, np.integer
    ):
        raise ValueError("plan positions do not match the fixed profile")
    if np.unique(plan.positions).size != PLACEMENTS:
        raise ValueError("plan positions must be unique")
    if plan.orientations.shape != (PLACEMENTS,) or not np.all(
        np.isin(plan.orientations, (0, 1))
    ):
        raise ValueError("plan orientations do not match the fixed profile")
    if plan.polarities.shape != (PLACEMENTS,) or not np.all(
        np.isin(plan.polarities, (-1, 1))
    ):
        raise ValueError("plan polarities do not match the fixed profile")


def embed_auth(
    base: Path,
    destination: Path,
    plan: AuthPlan,
    shapes: list[tuple[int, int]],
) -> None:
    """Add the fixed-strength authenticator as full-page transparent images."""

    _validate_plan(plan)
    base = Path(base)
    destination = Path(destination)
    if base.suffix.lower() != ".pdf" or destination.suffix.lower() != ".pdf":
        raise ValueError("authenticator embedding requires PDF input and output")
    if not isinstance(shapes, list) or not shapes:
        raise ValueError("shapes must be a non-empty page-shape list")
    normalized_shapes: list[tuple[int, int]] = []
    for shape in shapes:
        if (
            not isinstance(shape, tuple)
            or len(shape) != 2
            or any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in shape)
        ):
            raise ValueError("each shape must be a positive integer (height, width) tuple")
        normalized_shapes.append(shape)
    rendered, _ = watermark.load_pages(base, dpi=DPI)
    actual_shapes = [page.shape[:2] for page in rendered]
    if actual_shapes != normalized_shapes:
        raise ValueError("supplied shapes do not match the rendered base PDF")
    capacities = [
        (height // BLOCK_SIZE) * (width // BLOCK_SIZE)
        for height, width in normalized_shapes
    ]
    capacity = sum(capacities)
    if capacity != SYMBOLS:
        # The fixed plan addresses a permutation of the first 52,500 blocks.  A
        # page may offer more blocks; it may not offer fewer.
        if capacity < SYMBOLS:
            raise ValueError(
                f"fixed profile needs at least {SYMBOLS} blocks but PDF capacity is {capacity}"
            )
    if int(plan.positions.min()) < 0 or int(plan.positions.max()) >= capacity:
        raise ValueError("plan positions exceed rendered PDF capacity")

    templates = tardos_carrier._templates(BLOCK_SIZE)
    payload = np.tile(plan.encoded_bits, REPEATS)
    encoded_blocks = (
        (2 * payload.astype(np.int8) - 1)[:, None, None]
        * plan.polarities[:, None, None]
        * templates[plan.orientations]
    ).astype(np.float32)
    all_blocks = np.zeros((capacity, BLOCK_SIZE, BLOCK_SIZE), dtype=np.float32)
    all_blocks[plan.positions] = encoded_blocks

    patterns: list[np.ndarray] = []
    offset = 0
    for (height, width), page_capacity in zip(
        normalized_shapes, capacities, strict=True
    ):
        rows = height // BLOCK_SIZE
        columns = width // BLOCK_SIZE
        page_blocks = all_blocks[offset : offset + page_capacity]
        crop = (
            page_blocks.reshape(rows, columns, BLOCK_SIZE, BLOCK_SIZE)
            .transpose(0, 2, 1, 3)
            .reshape(rows * BLOCK_SIZE, columns * BLOCK_SIZE)
        )
        pattern = np.zeros((height, width), dtype=np.float32)
        pattern[: crop.shape[0], : crop.shape[1]] = crop
        patterns.append(pattern)
        offset += page_capacity

    document = fitz.open(base)
    try:
        if document.page_count != len(patterns):
            raise ValueError("base PDF page count changed during embedding")
        for page, pattern in zip(document, patterns, strict=True):
            page.insert_image(
                page.rect,
                stream=tardos_carrier._transparent_overlay(pattern, STRENGTH),
                overlay=True,
                keep_proportion=False,
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        document.save(destination, garbage=0, clean=False, deflate=True)
    finally:
        document.close()


def residual_blocks(reference: Path, suspect: Path) -> np.ndarray:
    """Render, align and subtract a suspect into fixed 6-by-6 luma blocks."""

    reference_pages, _ = watermark.load_pages(Path(reference), dpi=DPI)
    suspect_pages, _ = watermark.load_pages(Path(suspect), dpi=DPI)
    if len(reference_pages) != len(suspect_pages):
        raise ValueError("reference and suspect must have the same page count")
    if not reference_pages:
        raise ValueError("reference and suspect must contain at least one page")
    all_blocks: list[np.ndarray] = []
    for original, observed in zip(reference_pages, suspect_pages, strict=True):
        aligned, _ = registration.align_page(original, observed)
        if aligned.shape != original.shape:
            raise ValueError("aligned suspect geometry does not match the reference")
        residual = watermark._luma(aligned) - watermark._luma(original)
        height, width = original.shape[:2]
        rows = height // BLOCK_SIZE
        columns = width // BLOCK_SIZE
        cropped = residual[: rows * BLOCK_SIZE, : columns * BLOCK_SIZE]
        all_blocks.append(
            cropped.reshape(rows, BLOCK_SIZE, columns, BLOCK_SIZE)
            .transpose(0, 2, 1, 3)
            .reshape(rows * columns, BLOCK_SIZE, BLOCK_SIZE)
        )
    return np.concatenate(all_blocks, axis=0)


def decode(blocks: np.ndarray, plan: AuthPlan) -> dict[str, object]:
    """Decode one candidate and return the complete fixed-rule observation."""

    _validate_plan(plan)
    values = np.asarray(blocks)
    if values.ndim != 3 or values.shape[1:] != (BLOCK_SIZE, BLOCK_SIZE):
        raise ValueError("blocks must have shape (capacity, 6, 6)")
    if not np.issubdtype(values.dtype, np.number) or not np.all(np.isfinite(values)):
        raise ValueError("blocks must contain only finite numbers")
    if int(plan.positions.min()) < 0 or int(plan.positions.max()) >= values.shape[0]:
        raise ValueError("plan positions exceed block capacity")
    templates = tardos_carrier._templates(BLOCK_SIZE)
    correlations = np.sum(
        values[plan.positions]
        * templates[plan.orientations]
        * plan.polarities[:, None, None],
        axis=(1, 2),
    ).reshape(REPEATS, TAG_ENCODED_BITS)
    raw_sums = correlations.sum(axis=0)
    observed_encoded = (raw_sums > 0).astype(np.uint8)
    decoded = layout_tag.hamming74_decode(observed_encoded)
    return {
        "exact_match": bool(np.array_equal(decoded.bits, plan.raw_bits)),
        "decoded_bit_distance": int(np.count_nonzero(decoded.bits != plan.raw_bits)),
        "encoded_bit_distance": int(
            np.count_nonzero(observed_encoded != plan.encoded_bits)
        ),
        "corrected_blocks": int(decoded.corrected_blocks),
        "raw_sums": [float(value) for value in raw_sums],
        "decoded_bits": decoded.bits.astype(int).tolist(),
        "observed_encoded_bits": observed_encoded.astype(int).tolist(),
    }


def copy_observed_overlays(donor: Path, target: Path, destination: Path) -> None:
    """Copy observed donor image objects, including soft masks, onto a target.

    Deliberately accepts no carrier key or plan.  This models an attacker who
    can inspect the marked PDF's image objects but has no experimental secrets.
    """

    donor = Path(donor)
    target = Path(target)
    destination = Path(destination)
    if any(path.suffix.lower() != ".pdf" for path in (donor, target, destination)):
        raise ValueError("observed-overlay copying requires PDF inputs and output")
    donor_document = fitz.open(donor)
    target_document = fitz.open(target)
    try:
        if donor_document.page_count != target_document.page_count:
            raise ValueError("donor and target page counts differ")
        for page_index in range(donor_document.page_count):
            donor_page = donor_document[page_index]
            target_page = target_document[page_index]
            if donor_page.rect != target_page.rect:
                raise ValueError("donor and target page geometry differs")
            image_entries = donor_page.get_images(full=True)
            for entry in image_entries:
                xref, smask = int(entry[0]), int(entry[1])
                rectangles = donor_page.get_image_rects(xref)
                if not rectangles:
                    raise ValueError(f"donor image xref {xref} has no page placement")
                base_pixmap = fitz.Pixmap(donor_document, xref)
                try:
                    if smask:
                        mask_pixmap = fitz.Pixmap(donor_document, smask)
                        try:
                            combined = fitz.Pixmap(base_pixmap, mask_pixmap)
                        finally:
                            mask_pixmap = None
                    else:
                        combined = base_pixmap
                    stream = combined.tobytes("png")
                finally:
                    combined = None
                    base_pixmap = None
                for rectangle in rectangles:
                    target_page.insert_image(
                        rectangle,
                        stream=stream,
                        overlay=True,
                        keep_proportion=False,
                    )
        destination.parent.mkdir(parents=True, exist_ok=True)
        target_document.save(destination, garbage=0, clean=False, deflate=True)
    finally:
        donor_document.close()
        target_document.close()
