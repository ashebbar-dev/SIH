"""Detector and fail-closed policy for the published NISHAN test fixture."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from nishan import layout_tag, live_pdf, tardos, tardos_carrier


FIXTURE_SECRET = hashlib.sha3_256(
    b"NISHAN Tardos carrier public fixture v1"
).digest()
CODEBOOK_CONTEXT = "public-benchmark-codebook/v1"
CARRIER_CONTEXT = "synthetic-source/full-tardos-profile-v1"
FIXTURE_SESSION = "public-fixture-session-0000"
FIXTURE_ROW = 0
LAYOUT_ADJUSTMENT_MAGNITUDE = 0.001


@dataclass(frozen=True)
class PublicMaterial:
    config: tardos.Parameters
    biases: np.ndarray
    codebook: np.ndarray
    document_id: str


def build_material(reference: Path) -> PublicMaterial:
    config = tardos.parameters(1_000, 5, 1e-6)
    biases, codebook = tardos.generate_keyed(
        config, FIXTURE_SECRET, CODEBOOK_CONTEXT
    )
    return PublicMaterial(
        config=config,
        biases=biases,
        codebook=codebook,
        document_id=hashlib.sha3_256(reference.read_bytes()).hexdigest(),
    )


def _registration_is_credible(pages: list[dict[str, object]]) -> tuple[bool, str]:
    if not pages:
        return False, "No registration diagnostics were produced."
    for page in pages:
        if page.get("rejection_reason"):
            return False, f"Registration rejected the page: {page['rejection_reason']}."
        similarity = float(page.get("registered_similarity", 0.0))
        if similarity < 0.08:
            return False, "Registered content similarity was too weak."
        if page.get("method") == "ORB + RANSAC homography":
            if int(page.get("ransac_inliers", 0)) < 10:
                return False, "Too few geometric inliers supported the alignment."
            if float(page.get("ransac_inlier_ratio", 0.0)) < 0.15:
                return False, "The geometric inlier ratio was too weak."
    return True, "The suspect page passed content-registration quality gates."


def decode_public(
    reference: Path,
    suspect: Path,
    input_type: str,
    material: PublicMaterial,
) -> dict[str, object]:
    """Extract the real carriers and return channel facts, never a guessed row."""

    word, correlations, preprocessing = tardos_carrier.decode_word_with_diagnostics(
        reference,
        suspect,
        material.config.code_length,
        FIXTURE_SECRET,
        CARRIER_CONTEXT,
    )
    scores = tardos.accusation_scores(material.biases, material.codebook, word)
    accused = {int(index) for index in tardos.accuse(scores, material.config)}
    registration_ok, registration_reason = _registration_is_credible(
        list(preprocessing.get("pages", []))
    )
    if not registration_ok:
        accused = set()

    layout_matches: set[int] = set()
    layout_details: dict[str, object] = {
        "available": input_type == "pdf",
        "authenticated_rows": [],
        "carrier_symbols": None,
        "status": "Raster inputs do not contain the editable-PDF layout channel.",
    }
    if input_type == "pdf":
        carrier = live_pdf.read_carrier(
            suspect, adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE
        )
        layout_details["carrier_symbols"] = int(carrier.size)
        if carrier.size >= layout_tag.ENCODED_BITS:
            context = (
                f"layout:{material.document_id}:{FIXTURE_SESSION}:{FIXTURE_ROW}"
            )
            encoded = live_pdf.decode_carrier(
                carrier,
                layout_tag.ENCODED_BITS,
                FIXTURE_SECRET,
                context,
            )
            decoded = layout_tag.hamming74_decode(encoded)
            if layout_tag.matches(
                decoded.bits,
                FIXTURE_SECRET,
                material.document_id,
                FIXTURE_SESSION,
                FIXTURE_ROW,
            ):
                layout_matches.add(FIXTURE_ROW)
            layout_details.update(
                {
                    "authenticated_rows": sorted(layout_matches),
                    "corrected_blocks": decoded.corrected_blocks,
                    "status": (
                        "The documented public fixture tag matched."
                        if layout_matches
                        else "No documented public fixture tag matched."
                    ),
                }
            )
        else:
            layout_details["status"] = "Too few signed layout symbols remain."

    ranking = np.argsort(scores)[::-1][:5]
    visual = {
        "threshold": material.config.threshold,
        "accused_rows": sorted(accused),
        "fixture_row_score": round(float(scores[FIXTURE_ROW]), 6),
        "median_absolute_block_correlation": round(
            float(np.median(np.abs(correlations))), 6
        ),
        "top_rows": [
            {"row": int(index), "score": round(float(scores[index]), 6)}
            for index in ranking
        ],
        "registration_accepted": registration_ok,
        "registration_reason": registration_reason,
    }
    digital_match = accused == {FIXTURE_ROW} and layout_matches == {FIXTURE_ROW}
    raster_lead = (
        input_type != "pdf"
        and registration_ok
        and accused == {FIXTURE_ROW}
    )
    if digital_match:
        decision = "fixture_match"
    elif raster_lead:
        decision = "research_lead"
    else:
        decision = "inconclusive"
    return {
        "decision": decision,
        "visual": visual,
        "layout": layout_details,
        "preprocessing": preprocessing,
        "conflict": bool(accused or layout_matches) and accused != layout_matches,
    }
