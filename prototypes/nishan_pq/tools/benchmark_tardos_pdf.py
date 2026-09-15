#!/usr/bin/env python3
"""Exercise the dual PDF carrier against complementary and transplant attacks.

This benchmark tests all 1,000 enrolled codebook rows, creates five marked PDF
copies, and reports the marking-condition status separately for every attack.
The rendered Tardos carrier and exact digital-PDF layout authenticator have
different failure modes.  The benchmark deletes and normalizes each channel,
deletes both, and transplants one recipient's visual carrier onto another
recipient's layout carrier.  The last case must abstain rather than frame either
recipient.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

import cv2
import numpy as np
import pymupdf as fitz
from PIL import Image

from nishan import layout_tag, live_pdf, tardos, tardos_carrier, watermark
from nishan.core import fuse_channel_indices


LAYOUT_ADJUSTMENT_MAGNITUDE = 0.001


def _evaluate(
    name: str,
    reference: Path,
    suspect: Path,
    coalition: np.ndarray,
    config: tardos.Parameters,
    biases: np.ndarray,
    codebook: np.ndarray,
    secret: bytes,
    context: str,
    document_id: str,
    session_ids: list[str],
    expected_decision: str,
    expected_selected: list[int],
) -> dict[str, object]:
    start = time.perf_counter()
    pirate, correlations, decoder_diagnostics = tardos_carrier.decode_word_with_diagnostics(
        reference,
        suspect,
        config.code_length,
        secret,
        context,
    )
    scores = tardos.accusation_scores(biases, codebook, pirate)
    accused = tardos.accuse(scores, config)
    colluder_hits = np.intersect1d(accused, coalition)
    innocent_hits = np.setdiff1d(accused, coalition)
    marking = tardos_carrier.marking_condition_errors(
        pirate, codebook[coalition]
    )
    issued_indices = set(range(len(session_ids)))
    issued_tardos = set(int(index) for index in accused) & issued_indices
    unissued_tardos = set(int(index) for index in accused) - issued_indices
    layout_matches: set[int] = set()
    layout_observation: dict[str, object] = {
        "suspect_is_pdf": suspect.read_bytes()[:5] == b"%PDF-",
        "carrier_symbols_read": None,
        "candidate_results": {},
    }
    if layout_observation["suspect_is_pdf"]:
        carrier = live_pdf.read_carrier(
            suspect, adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE
        )
        layout_observation["carrier_symbols_read"] = int(carrier.size)
        if carrier.size >= layout_tag.ENCODED_BITS:
            candidate_results: dict[str, object] = {}
            for user_index, session_id in enumerate(session_ids):
                encoded = live_pdf.decode_carrier(
                    carrier,
                    layout_tag.ENCODED_BITS,
                    secret,
                    f"layout:{document_id}:{session_id}:{user_index}",
                )
                decoded = layout_tag.hamming74_decode(encoded)
                matched = layout_tag.matches(
                    decoded.bits,
                    secret,
                    document_id,
                    session_id,
                    user_index,
                )
                candidate_results[str(user_index)] = {
                    "match": matched,
                    "corrected_blocks": decoded.corrected_blocks,
                }
                if matched:
                    layout_matches.add(user_index)
            layout_observation["candidate_results"] = candidate_results

    fusion = fuse_channel_indices(
        issued_tardos,
        layout_matches,
        unissued_tardos,
        require_corroboration=bool(layout_observation["suspect_is_pdf"]),
    )
    selected = [int(index) for index in fusion["selected_indices"]]
    benchmark_passed = (
        fusion["decision"] == expected_decision
        and selected == expected_selected
    )
    if name.startswith("carrier_realization_"):
        benchmark_passed = (
            benchmark_passed
            and colluder_hits.size >= 1
            and innocent_hits.size == 0
            and bool(marking["marking_condition_observed"])
        )
        fixture_scope = (
            "The attack word was generated from the five codewords under the named "
            "marking-condition strategy and then embedded as a fresh carrier. This tests "
            "carrier realization of a code-level word, not an attacker editing five PDFs."
        )
    else:
        fixture_scope = "The named file transformation was executed on released fixture copies."
    return {
        "attack": name,
        "suspect_sha3_256": hashlib.sha3_256(suspect.read_bytes()).hexdigest(),
        "coalition_user_indices": coalition.tolist(),
        "decoded_one_fraction": float(pirate.mean()),
        "block_correlation_absolute_median": float(np.median(np.abs(correlations))),
        "marking_condition": marking,
        "theorem_marking_condition_observed": marking["marking_condition_observed"],
        "accused_user_indices": accused.tolist(),
        "colluders_recovered": colluder_hits.tolist(),
        "colluders_recovered_count": int(colluder_hits.size),
        "innocent_accusations": innocent_hits.tolist(),
        "innocent_accusations_count": int(innocent_hits.size),
        "colluder_score_min": float(scores[coalition].min()),
        "colluder_score_max": float(scores[coalition].max()),
        "innocent_score_max": float(scores[np.setdiff1d(np.arange(len(scores)), coalition)].max()),
        "threshold": config.threshold,
        "decoder_preprocessing": decoder_diagnostics,
        "layout_channel": {
            **layout_observation,
            "matched_user_indices": sorted(layout_matches),
            "tag_bits": layout_tag.TAG_BITS,
            "encoded_bits": layout_tag.ENCODED_BITS,
        },
        "fusion": fusion,
        "expected": {
            "decision": expected_decision,
            "selected_indices": expected_selected,
        },
        "benchmark_passed": benchmark_passed,
        "fixture_scope": fixture_scope,
        "evaluation_seconds": time.perf_counter() - start,
    }


def _remove_overlay(source: Path, destination: Path) -> None:
    document = fitz.open(source)
    try:
        images = document[0].get_images(full=True)
        if not images:
            raise RuntimeError("marked PDF contains no removable image object")
        document[0].delete_image(images[0][0])
        document.save(destination, garbage=4, deflate=True)
    finally:
        document.close()


def _transplant_overlay(
    donor: Path,
    recipient: Path,
    destination: Path,
) -> None:
    """Replace the recipient's visual fingerprint with the donor's overlay."""

    donor_document = fitz.open(donor)
    try:
        donor_images = donor_document[0].get_images(full=True)
        if not donor_images:
            raise RuntimeError("donor PDF contains no image carrier")
        image_bytes = donor_document.extract_image(donor_images[0][0])["image"]
    finally:
        donor_document.close()

    recipient_document = fitz.open(recipient)
    try:
        recipient_images = recipient_document[0].get_images(full=True)
        if not recipient_images:
            raise RuntimeError("recipient PDF contains no image carrier")
        recipient_document[0].delete_image(recipient_images[0][0])
        recipient_document[0].insert_image(
            recipient_document[0].rect,
            stream=image_bytes,
            overlay=True,
            keep_proportion=False,
        )
        recipient_document.save(destination, garbage=4, deflate=True)
    finally:
        recipient_document.close()


def _replace_overlay_with_rendered_page(
    rendered_page: Path,
    recipient: Path,
    destination: Path,
) -> None:
    """Place a rendered pirate page over a live PDF while retaining its layout tag."""

    recipient_document = fitz.open(recipient)
    try:
        recipient_images = recipient_document[0].get_images(full=True)
        if not recipient_images:
            raise RuntimeError("recipient PDF contains no image carrier")
        recipient_document[0].delete_image(recipient_images[0][0])
        recipient_document[0].insert_image(
            recipient_document[0].rect,
            filename=str(rendered_page),
            overlay=True,
            keep_proportion=False,
        )
        recipient_document.save(destination, garbage=4, deflate=True)
    finally:
        recipient_document.close()


def _synthetic_perspective_photo(source: Path, destination: Path) -> None:
    """Place one rendered page in a deterministic perspective/lighting fixture."""

    page = watermark.load_pages(source, dpi=144)[0][0]
    page_height, page_width = page.shape[:2]
    canvas_width, canvas_height = 1_650, 1_950
    source_corners = np.float32(
        [[0, 0], [page_width - 1, 0], [page_width - 1, page_height - 1], [0, page_height - 1]]
    )
    destination_corners = np.float32(
        [[245, 105], [1_410, 205], [1_285, 1_835], [115, 1_660]]
    )
    transform = cv2.getPerspectiveTransform(source_corners, destination_corners)
    warped = cv2.warpPerspective(
        page,
        transform,
        (canvas_width, canvas_height),
        flags=cv2.INTER_LANCZOS4,
        borderValue=(0, 0, 0),
    )
    mask = cv2.warpPerspective(
        np.full((page_height, page_width), 255, dtype=np.uint8),
        transform,
        (canvas_width, canvas_height),
        flags=cv2.INTER_NEAREST,
        borderValue=0,
    )
    canvas = np.empty((canvas_height, canvas_width, 3), dtype=np.float32)
    canvas[:] = (44, 48, 55)
    page_pixels = mask > 0
    canvas[page_pixels] = warped[page_pixels]
    horizontal_light = np.linspace(0.88, 1.07, canvas_width, dtype=np.float32)
    vertical_light = np.linspace(1.04, 0.91, canvas_height, dtype=np.float32)
    illumination = vertical_light[:, None] * horizontal_light[None, :]
    canvas *= illumination[:, :, None]
    canvas = cv2.GaussianBlur(canvas, (3, 3), 0.45)
    noise = np.random.default_rng(20260910).normal(0.0, 0.8, canvas.shape)
    attacked = np.clip(canvas + noise, 0, 255).astype(np.uint8)
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(attacked).save(destination, format="JPEG", quality=88, optimize=True)


def _resave_pdf(source: Path, destination: Path) -> None:
    document = fitz.open(source)
    try:
        document.save(destination, garbage=4, clean=True, deflate=True)
    finally:
        document.close()


def _raster_attack(
    source: Path,
    destination: Path,
    *,
    scale: float = 1.0,
    crop_fraction: float = 0.0,
) -> None:
    page = watermark.load_pages(source, dpi=144)[0][0]
    height, width = page.shape[:2]
    if crop_fraction:
        x = round(width * crop_fraction)
        y = round(height * crop_fraction)
        page = page[y : height - y, x : width - x]
    if scale != 1.0:
        page = cv2.resize(
            page,
            (max(1, round(page.shape[1] * scale)), max(1, round(page.shape[0] * scale))),
            interpolation=cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LANCZOS4,
        )
    Image.fromarray(page).save(destination, format="PNG", optimize=True)


def _rotation_attack(source: Path, destination: Path, degrees: float) -> None:
    page = watermark.load_pages(source, dpi=144)[0][0]
    height, width = page.shape[:2]
    matrix = cv2.getRotationMatrix2D((width / 2, height / 2), degrees, 1.0)
    rotated = cv2.warpAffine(
        page,
        matrix,
        (width, height),
        flags=cv2.INTER_LANCZOS4,
        borderValue=(255, 255, 255),
    )
    Image.fromarray(rotated).save(destination, format="PNG", optimize=True)


def run(source: Path, destination: Path) -> dict[str, object]:
    config = tardos.parameters(1_000, 5, 1e-6)
    fixture_secret = hashlib.sha3_256(
        b"NISHAN Tardos carrier public fixture v1"
    ).digest()
    generation_start = time.perf_counter()
    biases, codebook = tardos.generate_keyed(
        config,
        fixture_secret,
        "public-benchmark-codebook/v1",
    )
    generation_seconds = time.perf_counter() - generation_start
    secret = fixture_secret
    context = "synthetic-source/full-tardos-profile-v1"
    document_id = hashlib.sha3_256(source.read_bytes()).hexdigest()
    session_ids = [f"public-fixture-session-{index:04d}" for index in range(config.coalition_limit)]

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="nishan-tardos-pdf-") as directory:
        root = Path(directory)
        copies: list[Path] = []
        carrier_metrics: list[dict[str, object]] = []
        for user_index in range(config.coalition_limit):
            visual_output = root / f"user-{user_index:04d}-visual.pdf"
            output = root / f"user-{user_index:04d}-dual.pdf"
            visual_metrics = tardos_carrier.embed_pdf(
                source,
                visual_output,
                codebook[user_index],
                secret,
                context,
                strength=4.0,
            )
            tag = layout_tag.encoded_tag(
                secret,
                document_id,
                session_ids[user_index],
                user_index,
            )
            layout_metrics = live_pdf.embed(
                visual_output,
                output,
                tag,
                secret,
                f"layout:{document_id}:{session_ids[user_index]}:{user_index}",
                adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
            )
            released_metrics = tardos_carrier.measure_pdf_pair(source, output)
            copies.append(output)
            carrier_metrics.append(
                {
                    "user_index": user_index,
                    "visual_tardos": asdict(visual_metrics),
                    "text_layout_tag": asdict(layout_metrics),
                    "released_document": asdict(released_metrics),
                }
            )

        attacks: list[tuple[str, Path, np.ndarray, str, list[int]]] = []
        attacks.append(
            ("single_digital_pdf", copies[0], np.array([0]), "corroborated_channels", [0])
        )
        resaved = root / "user-0000-resaved.pdf"
        _resave_pdf(copies[0], resaved)
        attacks.append(
            ("pdf_clean_resave", resaved, np.array([0]), "abstain_single_channel_editable_pdf", [])
        )
        screenshot = root / "user-0000-screenshot.png"
        _raster_attack(copies[0], screenshot)
        attacks.append(
            ("raster_screenshot", screenshot, np.array([0]), "tardos_channel_only", [0])
        )
        half_size = root / "user-0000-half-size.png"
        _raster_attack(copies[0], half_size, scale=0.5)
        attacks.append(
            ("raster_half_size", half_size, np.array([0]), "tardos_channel_only", [0])
        )
        crop_10 = root / "user-0000-crop-10pct-each-edge.png"
        _raster_attack(copies[0], crop_10, crop_fraction=0.10)
        attacks.append(
            ("raster_crop_10pct_each_edge", crop_10, np.array([0]), "tardos_channel_only", [0])
        )
        crop_30 = root / "user-0000-crop-30pct-each-edge.png"
        _raster_attack(copies[0], crop_30, crop_fraction=0.30)
        attacks.append(
            ("raster_crop_30pct_each_edge", crop_30, np.array([0]), "tardos_channel_only", [0])
        )
        crop_40 = root / "user-0000-crop-40pct-each-edge.png"
        _raster_attack(copies[0], crop_40, crop_fraction=0.40)
        attacks.append(
            ("raster_crop_40pct_each_edge", crop_40, np.array([0]), "no_attribution_signal", [])
        )
        rotated = root / "user-0000-rotate-2deg.png"
        _rotation_attack(copies[0], rotated, 2.0)
        attacks.append(
            ("raster_rotate_2deg", rotated, np.array([0]), "tardos_channel_only", [0])
        )
        jpeg = root / "user-0000-jpeg-q55.jpg"
        watermark.jpeg_attack(copies[0], jpeg, quality=55)
        attacks.append(("single_jpeg_q55", jpeg, np.array([0]), "tardos_channel_only", [0]))
        jpeg_q40 = root / "user-0000-jpeg-q40.jpg"
        Image.fromarray(watermark.load_pages(copies[0], dpi=144)[0][0]).save(
            jpeg_q40, format="JPEG", quality=40, optimize=True
        )
        attacks.append(
            ("single_jpeg_q40", jpeg_q40, np.array([0]), "tardos_channel_only", [0])
        )
        jpeg_q20 = root / "user-0000-jpeg-q20.jpg"
        Image.fromarray(watermark.load_pages(copies[0], dpi=144)[0][0]).save(
            jpeg_q20, format="JPEG", quality=20, optimize=True
        )
        attacks.append(
            ("single_jpeg_q20", jpeg_q20, np.array([0]), "no_attribution_signal", [])
        )
        perspective = root / "user-0000-synthetic-perspective-photo.jpg"
        _synthetic_perspective_photo(copies[0], perspective)
        attacks.append(
            (
                "single_synthetic_perspective_photo",
                perspective,
                np.array([0]),
                "tardos_channel_only",
                [0],
            )
        )
        for count in (2, 3, 5):
            averaged = root / f"{count}-copy-pixel-average.png"
            watermark.average_collusion(copies[:count], averaged)
            attacks.append(
                (
                    f"{count}_copy_pixel_average",
                    averaged,
                    np.arange(count),
                    "tardos_channel_only",
                    list(range(count)),
                )
            )
        removed = root / "user-0000-overlay-removed.pdf"
        _remove_overlay(copies[0], removed)
        attacks.append(
            ("pdf_overlay_object_removed", removed, np.array([0]), "abstain_single_channel_editable_pdf", [])
        )

        layout_removed = root / "user-0000-layout-normalized.pdf"
        live_pdf.strip_layout_adjustments(
            copies[0],
            layout_removed,
            adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
        )
        attacks.append(
            ("pdf_layout_normalized", layout_removed, np.array([0]), "abstain_single_channel_editable_pdf", [])
        )

        both_removed = root / "user-0000-both-channels-removed.pdf"
        live_pdf.strip_layout_adjustments(
            removed,
            both_removed,
            adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
        )
        attacks.append(
            ("pdf_both_channels_removed", both_removed, np.array([0]), "no_attribution_signal", [])
        )

        transplanted = root / "alice-visual-on-bob-layout.pdf"
        _transplant_overlay(copies[0], copies[1], transplanted)
        attacks.append(
            ("pdf_visual_carrier_transplanted", transplanted, np.array([0]), "abstain_channel_conflict", [])
        )
        transplanted_then_stripped = root / "alice-visual-on-bob-layout-stripped.pdf"
        live_pdf.strip_layout_adjustments(
            transplanted,
            transplanted_then_stripped,
            adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
        )
        attacks.append(
            (
                "pdf_visual_transplant_then_layout_strip",
                transplanted_then_stripped,
                np.array([0]),
                "abstain_single_channel_editable_pdf",
                [],
            )
        )

        # A partially overlapping identity set is still a conflict. Combine the
        # rendered Alice/Bob copies, graft that visual evidence onto Bob's live
        # PDF, and require abstention even though Bob appears in both channels.
        two_copy_rendering = root / "alice-bob-rendered-average.png"
        watermark.average_collusion(copies[:2], two_copy_rendering)
        partial_overlap = root / "alice-bob-visual-on-bob-layout.pdf"
        _replace_overlay_with_rendered_page(
            two_copy_rendering,
            copies[1],
            partial_overlap,
        )
        attacks.append(
            (
                "pdf_partial_overlap_visual_coalition_on_bob_layout",
                partial_overlap,
                np.array([0, 1]),
                "abstain_channel_conflict",
                [],
            )
        )

        for offset, attack_name in enumerate(
            ("interleaving", "majority", "minority", "coin_flip"), start=1
        ):
            coalition = np.arange(config.coalition_limit)
            pirate_word = tardos.simulate_attack(
                codebook[coalition],
                attack_name,
                np.random.default_rng(20260910 + offset),
            )
            predicted_scores = tardos.accusation_scores(biases, codebook, pirate_word)
            predicted = tardos.accuse(predicted_scores, config).tolist()
            forged = root / f"carrier-{attack_name}.pdf"
            tardos_carrier.embed_pdf(
                source,
                forged,
                pirate_word,
                secret,
                context,
                strength=4.0,
            )
            attacks.append(
                (
                    f"carrier_realization_{attack_name}_five_copy",
                    forged,
                    coalition,
                    "abstain_single_channel_editable_pdf",
                    [],
                )
            )

        evaluations = {
            name: _evaluate(
                name,
                source,
                suspect,
                coalition,
                config,
                biases,
                codebook,
                secret,
                context,
                document_id,
                session_ids,
                expected_decision,
                expected_selected,
            )
            for name, suspect, coalition, expected_decision, expected_selected in attacks
        }
        failed_attacks = [
            name for name, evidence in evaluations.items() if not evidence["benchmark_passed"]
        ]
        if failed_attacks:
            raise AssertionError(
                "dual-carrier decision failed for: " + ", ".join(failed_attacks)
            )

        with fitz.open(source) as original, fitz.open(copies[0]) as marked:
            live_document_checks = {
                "text_extraction_equal": original[0].get_text() == marked[0].get_text(),
                "word_sequence_equal": [w[4] for w in original[0].get_text("words")]
                == [w[4] for w in marked[0].get_text("words")],
                "search_hits_in_marked": len(marked[0].search_for("trusted offline viewer")),
                "source_image_objects": len(original[0].get_images(full=True)),
                "marked_image_objects": len(marked[0].get_images(full=True)),
                "source_vector_drawings": len(original[0].get_drawings()),
                "marked_vector_drawings": len(marked[0].get_drawings()),
            }

        shutil.copy2(copies[0], destination / "dual-carrier-user-0000-live-text.pdf")
        shutil.copy2(jpeg, destination / "tardos-user-0000-jpeg-q55.jpg")
        shutil.copy2(
            perspective,
            destination / "tardos-user-0000-synthetic-perspective-photo.jpg",
        )
        shutil.copy2(resaved, destination / "dual-carrier-user-0000-resaved.pdf")
        shutil.copy2(screenshot, destination / "dual-carrier-user-0000-screenshot.png")
        shutil.copy2(half_size, destination / "dual-carrier-user-0000-half-size.png")
        shutil.copy2(crop_10, destination / "dual-carrier-user-0000-crop-10pct.png")
        shutil.copy2(crop_30, destination / "dual-carrier-user-0000-crop-30pct.png")
        shutil.copy2(crop_40, destination / "dual-carrier-user-0000-crop-40pct.png")
        shutil.copy2(rotated, destination / "dual-carrier-user-0000-rotate-2deg.png")
        shutil.copy2(
            root / "5-copy-pixel-average.png",
            destination / "tardos-five-copy-average.png",
        )
        shutil.copy2(removed, destination / "tardos-overlay-removed.pdf")
        shutil.copy2(
            layout_removed,
            destination / "layout-normalized-tardos-survives.pdf",
        )
        shutil.copy2(
            both_removed,
            destination / "both-carriers-removed.pdf",
        )
        shutil.copy2(
            transplanted,
            destination / "visual-transplant-conflict.pdf",
        )
        shutil.copy2(
            transplanted_then_stripped,
            destination / "visual-transplant-layout-stripped-abstention.pdf",
        )
        shutil.copy2(
            partial_overlap,
            destination / "partial-overlap-abstention.pdf",
        )

    return {
        "schema": "nishan.dual-pdf-carrier-benchmark/v2",
        "date": "2026-09-10",
        "claim_boundary": {
            "demonstrated": (
                "One deterministic full-size Tardos profile over 1,000 codebook rows; five "
                "dual-carrier live-text PDFs; all-row scoring; independent channel deletion; "
                "both-channel deletion; disjoint and partially overlapping carrier transplantation; raster crop, "
                "resize, rotation and compression boundaries; one synthetic perspective-photo "
                "fixture; and carrier realizations of four five-user code-level strategies."
            ),
            "theorem": (
                "The recorded family-wide bound belongs to the original randomized Tardos "
                "construction and is conditional on a coalition of at most five obeying the "
                "marking condition. Attack rows explicitly report whether decoded symbols did."
            ),
            "not_demonstrated": (
                "A probability estimated across independent codebooks, real printer/scanner or "
                "phone-camera hardware, or a cryptographically audited random generator. The "
                "short layout tag is an exact-PDF authenticator, not a collusion-secure code."
            ),
        },
        "measured_failure_boundary": (
            "For an editable PDF the engine attributes only when both channels agree. Removing "
            "either carrier leaves a recorded screening lead but forces abstention; removing both "
            "leaves no signal. Disjoint, remove-after-transplant, and partial-overlap recombination "
            "all force abstention. The raster fixture recovers after 30% is cropped from every edge "
            "but not 40%, and at JPEG quality 40 but not quality 20."
        ),
        "source": {
            "path": str(source),
            "sha3_256": hashlib.sha3_256(source.read_bytes()).hexdigest(),
        },
        "code": {
            "generator": (
                "deterministic public fixture using the same HMAC-derived AES-CTR generator as the end-to-end path"
            ),
            "generation_seconds": generation_seconds,
            "manifest": tardos.manifest(config, biases, codebook),
            "fixture_note": (
                "The embedded public fixture key makes the artifact reproducible and is not a secret; "
                "production needs protected codebook state and an independently reviewed generator."
            ),
        },
        "carrier": {
            "strength": 4.0,
            "layout_adjustment_magnitude": LAYOUT_ADJUSTMENT_MAGNITUDE,
            "metrics_by_user": carrier_metrics,
            "live_document_checks": live_document_checks,
        },
        "attacks": evaluations,
        "attack_count": len(evaluations),
        "all_attack_expectations_passed": True,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=Path, default=Path("artifacts/nishan/synthetic-source.pdf")
    )
    parser.add_argument(
        "--output-directory", type=Path, default=Path("artifacts/nishan")
    )
    parser.add_argument(
        "--evidence",
        type=Path,
        default=Path("artifacts/nishan/tardos-pdf-benchmark.json"),
    )
    args = parser.parse_args()
    result = run(args.source, args.output_directory)
    args.evidence.parent.mkdir(parents=True, exist_ok=True)
    args.evidence.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
