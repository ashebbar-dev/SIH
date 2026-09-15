#!/usr/bin/env python3
"""Measure the narrow live-text PDF carrier on the synthetic demo document."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pymupdf as fitz

from nishan import live_pdf, tardos


def _render(document: fitz.Document, page_index: int = 0, dpi: int = 144) -> np.ndarray:
    matrix = fitz.Matrix(dpi / 72.0, dpi / 72.0)
    pixmap = document[page_index].get_pixmap(
        matrix=matrix, alpha=False, colorspace=fitz.csRGB
    )
    return np.frombuffer(pixmap.samples, dtype=np.uint8).reshape(
        pixmap.height, pixmap.width, 3
    )


def _sha3(path: Path) -> str:
    return hashlib.sha3_256(path.read_bytes()).hexdigest()


def run(source: Path, marked: Path, payload_size: int = 96) -> dict[str, object]:
    secret = hashlib.sha3_256(b"NISHAN live-text reproducible fixture").digest()
    context = "synthetic-source/session-reference"
    bits = np.random.default_rng(20260910).integers(
        0, 2, size=payload_size, dtype=np.uint8
    )
    embed_result = live_pdf.embed(source, marked, bits, secret, context)
    recovered = live_pdf.extract(marked, payload_size, secret, context)

    with fitz.open(source) as original, fitz.open(marked) as output:
        original_text = "\f".join(page.get_text() for page in original)
        output_text = "\f".join(page.get_text() for page in output)
        original_words = [word for page in original for word in page.get_text("words")]
        output_words = [word for page in output for word in page.get_text("words")]
        if [word[4] for word in original_words] != [word[4] for word in output_words]:
            raise AssertionError("word sequence changed")
        coordinate_deltas = [
            max(abs(float(before[index]) - float(after[index])) for index in range(4))
            for before, after in zip(original_words, output_words, strict=True)
        ]
        rendered_source = _render(original)
        rendered_marked = _render(output)
        difference = rendered_marked.astype(np.float32) - rendered_source.astype(np.float32)
        mse = float(np.square(difference).mean())
        psnr = float("inf") if mse == 0 else 20 * math.log10(255 / math.sqrt(mse))
        document_properties = {
            "page_count_equal": original.page_count == output.page_count,
            "text_extraction_equal": original_text == output_text,
            "word_sequence_equal": True,
            "search_query": "trusted offline viewer",
            "search_hits_in_marked_pdf": sum(
                len(page.search_for("trusted offline viewer")) for page in output
            ),
            "source_image_objects": sum(
                len(page.get_images(full=True)) for page in original
            ),
            "marked_image_objects": sum(len(page.get_images(full=True)) for page in output),
            "source_font_references": sum(
                len(page.get_fonts(full=True)) for page in original
            ),
            "marked_font_references": sum(
                len(page.get_fonts(full=True)) for page in output
            ),
            "source_vector_drawings": sum(len(page.get_drawings()) for page in original),
            "marked_vector_drawings": sum(len(page.get_drawings()) for page in output),
            "max_word_bbox_coordinate_shift_points": max(coordinate_deltas, default=0.0),
            "median_word_bbox_coordinate_shift_points": float(
                np.median(coordinate_deltas) if coordinate_deltas else 0.0
            ),
            "render_psnr_db_144dpi": psnr,
        }

    formal = tardos.parameters(1_000, 5, 1e-6)
    capacity_shortfall = formal.code_length - embed_result.capacity_bits
    return {
        "schema": "nishan.live-text-pdf-fixture/v1",
        "claim_boundary": {
            "demonstrated": (
                "Exact payload recovery from this unrewritten digital PDF while text, "
                "search, fonts, and vector drawing objects remain present."
            ),
            "not_demonstrated": (
                "Robustness after PDF content-stream rewriting, print/scan, OCR, crop, "
                "photography, or collusion; accessibility-tag preservation on tagged PDFs."
            ),
            "not_novel_alone": (
                "Text-layout marking is established prior art. This carrier is an "
                "engineering prerequisite, not the standalone research contribution."
            ),
        },
        "source": {
            "path": str(source),
            "sha3_256": _sha3(source),
            "bytes": source.stat().st_size,
        },
        "marked": {
            "path": str(marked),
            "sha3_256": _sha3(marked),
            "bytes": marked.stat().st_size,
        },
        "embedding": asdict(embed_result),
        "payload": {
            "bits": payload_size,
            "bit_errors": int(np.count_nonzero(bits != recovered)),
            "bit_error_rate": float(np.mean(bits != recovered)),
        },
        "document_properties": document_properties,
        "formal_profile_capacity_check": {
            "profile": "n=1000, c=5, familywise epsilon=1e-6",
            "required_symbols_original_tardos": formal.code_length,
            "supported_word_space_positions_this_document": embed_result.capacity_bits,
            "fits": embed_result.capacity_bits >= formal.code_length,
            "shortfall_symbols": max(0, capacity_shortfall),
            "meaning": (
                "The present one-page layout carrier cannot host the full conservative "
                "proof profile; the theorem and carrier are not yet integrated."
            ),
        },
        "fixture_warning": (
            "The embedded key and payload are deterministic test fixtures and must not be "
            "used as deployment secrets."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("artifacts/nishan/synthetic-source.pdf")
    )
    parser.add_argument(
        "--marked", type=Path, default=Path("artifacts/nishan/live-text-marked.pdf")
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("artifacts/nishan/live-text-carrier-evidence.json"),
    )
    parser.add_argument("--payload-size", type=int, default=96)
    args = parser.parse_args()
    result = run(args.source, args.marked, args.payload_size)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
