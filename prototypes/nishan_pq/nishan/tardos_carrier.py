"""A measured PDF carrier for a binary Tardos fingerprint codeword.

Each fingerprint symbol occupies one 6-by-6 rendered-pixel block at 144 DPI.
A keyed permutation hides the symbol-to-block mapping, and a keyed choice of
low-frequency template encodes the symbol.  The overlay is added to the
original PDF, so its existing text and vector objects remain in the file.

The carrier and the Tardos theorem have separate scopes.  The theorem applies
only when the decoded pirate word obeys the marking condition.  This module
therefore reports marking-condition errors for every attack instead of assuming
that JPEG, print/scan, or geometric distortion preserves it.
"""

from __future__ import annotations

import hashlib
import hmac
import io
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pymupdf as fitz
from PIL import Image

from . import registration, watermark


@dataclass(frozen=True)
class CarrierMetrics:
    pages: int
    capacity_symbols: int
    embedded_symbols: int
    block_size_pixels: int
    dpi: int
    strength: float
    psnr_db: float
    text_preserved: bool
    source_text_sha3_256: str
    marked_text_sha3_256: str


@dataclass(frozen=True)
class DocumentPairMetrics:
    """Observable fidelity properties of a released PDF against its source."""

    pages: int
    dpi: int
    psnr_db: float
    text_preserved: bool
    source_text_sha3_256: str
    marked_text_sha3_256: str


def _prf_bytes(secret: bytes, context: str, purpose: bytes, length: int) -> bytes:
    prefix = b"NISHAN-TARDOS-CARRIER/v1\x00" + purpose + b"\x00" + context.encode(
        "utf-8"
    )
    output = bytearray()
    for counter in range(math.ceil(length / hashlib.sha3_256().digest_size)):
        output.extend(
            hmac.new(
                secret,
                prefix + counter.to_bytes(8, "big"),
                hashlib.sha3_256,
            ).digest()
        )
    return bytes(output[:length])


def _plan(
    secret: bytes,
    context: str,
    capacity: int,
    symbols: int,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    if symbols > capacity:
        raise ValueError(
            f"codeword needs {symbols} blocks but rendered PDF capacity is {capacity}"
        )
    order_keys = np.frombuffer(
        _prf_bytes(secret, context, b"block-order", capacity * 8), dtype="<u8"
    )
    order = np.argsort(order_keys, kind="stable")[:symbols]
    controls = np.unpackbits(
        np.frombuffer(
            _prf_bytes(secret, context, b"templates", math.ceil(symbols * 2 / 8)),
            dtype=np.uint8,
        )
    )[: symbols * 2].reshape(symbols, 2)
    orientations = controls[:, 0]
    polarities = 2 * controls[:, 1].astype(np.int8) - 1
    return order, orientations, polarities


def _templates(block_size: int) -> np.ndarray:
    if block_size < 2 or block_size % 2:
        raise ValueError("block size must be a positive even integer of at least 2")
    vertical = np.ones((block_size, block_size), dtype=np.float32)
    vertical[:, block_size // 2 :] = -1
    horizontal = np.ones((block_size, block_size), dtype=np.float32)
    horizontal[block_size // 2 :, :] = -1
    return np.stack([vertical, horizontal])


def _page_geometry(
    source: Path,
    dpi: int,
    block_size: int,
) -> tuple[list[tuple[int, int]], list[int]]:
    pages, _ = watermark.load_pages(source, dpi=dpi)
    shapes = [page.shape[:2] for page in pages]
    capacities = [
        (height // block_size) * (width // block_size) for height, width in shapes
    ]
    return shapes, capacities


def capacity(source: Path, dpi: int = 144, block_size: int = 6) -> int:
    _, capacities = _page_geometry(source, dpi, block_size)
    return sum(capacities)


def _patterns(
    codeword: np.ndarray,
    page_shapes: list[tuple[int, int]],
    page_capacities: list[int],
    secret: bytes,
    context: str,
    block_size: int,
) -> list[np.ndarray]:
    total_capacity = sum(page_capacities)
    order, orientations, polarities = _plan(
        secret, context, total_capacity, int(codeword.size)
    )
    templates = _templates(block_size)
    symbol_signs = 2 * codeword.astype(np.int8) - 1
    encoded_blocks = (
        symbol_signs[:, None, None]
        * polarities[:, None, None]
        * templates[orientations]
    ).astype(np.float32)
    all_blocks = np.zeros(
        (total_capacity, block_size, block_size), dtype=np.float32
    )
    all_blocks[order] = encoded_blocks

    patterns: list[np.ndarray] = []
    block_offset = 0
    for (height, width), page_capacity in zip(
        page_shapes, page_capacities, strict=True
    ):
        rows = height // block_size
        columns = width // block_size
        page_blocks = all_blocks[block_offset : block_offset + page_capacity]
        crop = (
            page_blocks.reshape(rows, columns, block_size, block_size)
            .transpose(0, 2, 1, 3)
            .reshape(rows * block_size, columns * block_size)
        )
        pattern = np.zeros((height, width), dtype=np.float32)
        pattern[: crop.shape[0], : crop.shape[1]] = crop
        patterns.append(pattern)
        block_offset += page_capacity
    return patterns


def _transparent_overlay(pattern: np.ndarray, strength: float) -> bytes:
    desired = strength * pattern
    rgba = np.empty((*pattern.shape, 4), dtype=np.uint8)
    rgba[:, :, :3] = np.where((desired >= 0)[:, :, None], 255, 0).astype(np.uint8)
    rgba[:, :, 3] = np.clip(np.rint(np.abs(desired)), 0, 255).astype(np.uint8)
    stream = io.BytesIO()
    Image.fromarray(rgba).save(stream, format="PNG", optimize=True)
    return stream.getvalue()


def _text(document: fitz.Document) -> str:
    return "\f".join(page.get_text() for page in document)


def _digest_text(value: str) -> str:
    return hashlib.sha3_256(value.encode("utf-8")).hexdigest()


def measure_pdf_pair(
    source: Path,
    marked: Path,
    dpi: int = 144,
) -> DocumentPairMetrics:
    """Measure rendered distortion and extracted-text equality for two PDFs."""

    source_pages, _ = watermark.load_pages(source, dpi=dpi)
    marked_pages, _ = watermark.load_pages(marked, dpi=dpi)
    if len(source_pages) != len(marked_pages):
        raise ValueError("source and marked PDFs must have the same page count")
    squared_error = 0.0
    values = 0
    for original, released in zip(source_pages, marked_pages, strict=True):
        if original.shape != released.shape:
            raise ValueError("source and marked PDF pages must have the same rendered shape")
        difference = released.astype(np.float32) - original.astype(np.float32)
        squared_error += float(np.square(difference).sum())
        values += difference.size
    mse = squared_error / max(values, 1)
    psnr = float("inf") if mse == 0 else 20 * math.log10(255 / math.sqrt(mse))

    source_document = fitz.open(source)
    marked_document = fitz.open(marked)
    try:
        source_text = _text(source_document)
        marked_text = _text(marked_document)
    finally:
        source_document.close()
        marked_document.close()
    return DocumentPairMetrics(
        pages=len(source_pages),
        dpi=dpi,
        psnr_db=round(psnr, 3),
        text_preserved=marked_text == source_text,
        source_text_sha3_256=_digest_text(source_text),
        marked_text_sha3_256=_digest_text(marked_text),
    )


def embed_pdf(
    source: Path,
    destination: Path,
    codeword: np.ndarray,
    secret: bytes,
    context: str,
    strength: float = 2.2,
    dpi: int = 144,
    block_size: int = 6,
) -> CarrierMetrics:
    word = np.asarray(codeword, dtype=np.uint8)
    if word.ndim != 1 or np.any((word != 0) & (word != 1)):
        raise ValueError("codeword must be a one-dimensional binary array")
    if source.suffix.lower() != ".pdf" or destination.suffix.lower() != ".pdf":
        raise ValueError("the Tardos live-document carrier requires PDF input and output")
    if not math.isfinite(strength) or strength <= 0:
        raise ValueError("strength must be finite and positive")

    source_pages, _ = watermark.load_pages(source, dpi=dpi)
    page_shapes = [page.shape[:2] for page in source_pages]
    page_capacities = [
        (height // block_size) * (width // block_size)
        for height, width in page_shapes
    ]
    patterns = _patterns(
        word,
        page_shapes,
        page_capacities,
        secret,
        context,
        block_size,
    )

    document = fitz.open(source)
    try:
        original_text = _text(document)
        for page, pattern in zip(document, patterns, strict=True):
            page.insert_image(
                page.rect,
                stream=_transparent_overlay(pattern, strength),
                overlay=True,
                keep_proportion=False,
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        document.save(destination, garbage=0, clean=False, deflate=True)
    finally:
        document.close()

    pair_metrics = measure_pdf_pair(source, destination, dpi=dpi)
    return CarrierMetrics(
        pages=len(source_pages),
        capacity_symbols=sum(page_capacities),
        embedded_symbols=int(word.size),
        block_size_pixels=block_size,
        dpi=dpi,
        strength=strength,
        psnr_db=pair_metrics.psnr_db,
        text_preserved=pair_metrics.text_preserved,
        source_text_sha3_256=pair_metrics.source_text_sha3_256,
        marked_text_sha3_256=pair_metrics.marked_text_sha3_256,
    )


def decode_word(
    reference: Path,
    suspect: Path,
    symbol_count: int,
    secret: bytes,
    context: str,
    dpi: int = 144,
    block_size: int = 6,
) -> tuple[np.ndarray, np.ndarray]:
    """Hard-decode the pirate word and return it with raw block correlations."""

    word, correlations, _ = decode_word_with_diagnostics(
        reference,
        suspect,
        symbol_count,
        secret,
        context,
        dpi=dpi,
        block_size=block_size,
    )
    return word, correlations


def decode_word_with_diagnostics(
    reference: Path,
    suspect: Path,
    symbol_count: int,
    secret: bytes,
    context: str,
    dpi: int = 144,
    block_size: int = 6,
    registration_mode: str = "auto",
) -> tuple[np.ndarray, np.ndarray, dict[str, object]]:
    """Decode a word and retain page-alignment diagnostics.

    ``auto`` preserves same-size inputs pixel-for-pixel and registers differently
    shaped inputs. ``always`` also estimates a homography for same-size inputs.
    ``off`` performs only a deterministic resize.
    """

    if registration_mode not in {"auto", "always", "off"}:
        raise ValueError("registration_mode must be auto, always, or off")

    reference_pages, _ = watermark.load_pages(reference, dpi=dpi)
    suspect_pages, _ = watermark.load_pages(suspect, dpi=dpi)
    if len(reference_pages) != len(suspect_pages):
        raise ValueError("reference and suspect must have the same page count")
    page_shapes = [page.shape[:2] for page in reference_pages]
    page_capacities = [
        (height // block_size) * (width // block_size)
        for height, width in page_shapes
    ]
    total_capacity = sum(page_capacities)
    order, orientations, polarities = _plan(
        secret, context, total_capacity, symbol_count
    )
    templates = _templates(block_size)

    all_block_correlations: list[np.ndarray] = []
    registration_pages: list[dict[str, object]] = []
    for original, suspect_page, (height, width) in zip(
        reference_pages, suspect_pages, page_shapes, strict=True
    ):
        should_register = registration_mode in {"auto", "always"}
        if should_register:
            suspect_page, registration_metrics = registration.align_page(
                original, suspect_page
            )
            registration_pages.append(registration_metrics.to_dict())
        elif suspect_page.shape[:2] != (height, width):
            suspect_page = np.asarray(
                Image.fromarray(suspect_page).resize(
                    (width, height), Image.Resampling.LANCZOS
                ),
                dtype=np.uint8,
            )
            registration_pages.append(
                {
                    "method": "resize-only",
                    "applied": False,
                    "reference_width": width,
                    "reference_height": height,
                    "suspect_width": int(suspect_page.shape[1]),
                    "suspect_height": int(suspect_page.shape[0]),
                    "rejection_reason": "registration disabled",
                }
            )
        else:
            registration_pages.append(
                {
                    "method": "identity",
                    "applied": False,
                    "reference_width": width,
                    "reference_height": height,
                    "suspect_width": int(suspect_page.shape[1]),
                    "suspect_height": int(suspect_page.shape[0]),
                    "rejection_reason": None,
                }
            )
        residual = watermark._luma(suspect_page) - watermark._luma(original)
        rows = height // block_size
        columns = width // block_size
        cropped = residual[: rows * block_size, : columns * block_size]
        blocks = (
            cropped.reshape(rows, block_size, columns, block_size)
            .transpose(0, 2, 1, 3)
            .reshape(rows * columns, block_size, block_size)
        )
        all_block_correlations.append(blocks)
    blocks = np.concatenate(all_block_correlations, axis=0)
    selected = blocks[order]
    correlations = np.sum(
        selected * templates[orientations] * polarities[:, None, None], axis=(1, 2)
    )
    diagnostics = {
        "registration_mode": registration_mode,
        "pages": registration_pages,
    }
    return (correlations > 0).astype(np.uint8), correlations, diagnostics


def marking_condition_errors(
    pirate_word: np.ndarray,
    colluder_codewords: np.ndarray,
) -> dict[str, int | float]:
    """Count decoded errors in coordinates where every colluder has one symbol."""

    coalition = np.asarray(colluder_codewords, dtype=np.uint8)
    pirate = np.asarray(pirate_word, dtype=np.uint8)
    if coalition.ndim != 2 or pirate.shape != (coalition.shape[1],):
        raise ValueError("pirate word and coalition dimensions do not match")
    unanimous = coalition.min(axis=0) == coalition.max(axis=0)
    errors = int(np.count_nonzero(pirate[unanimous] != coalition[0, unanimous]))
    count = int(np.count_nonzero(unanimous))
    return {
        "unanimous_positions": count,
        "violations": errors,
        "violation_rate": 0.0 if count == 0 else errors / count,
        "marking_condition_observed": errors == 0,
    }
