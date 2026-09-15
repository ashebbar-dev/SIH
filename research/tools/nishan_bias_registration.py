"""Research-only shared-bias response and translation registration.

No recipient rows, roster access, accusation scores, or physical-file loading.
Source/midpoint/pilot are reference-resolution scalar luma. Blocks are 6x6.
"""
from dataclasses import replace
import hashlib
import io
import json
import time

import cv2
import numpy as np
import pymupdf as fitz
from PIL import Image

from nishan import tardos, tardos_carrier, watermark

BLOCK = 6
TILE = 96
GRID = np.arange(-2., 2.0001, .25)


def array_hash(array):
    a = np.ascontiguousarray(array)
    return hashlib.sha256(str((a.shape, a.dtype.str)).encode() + a.tobytes()).hexdigest()


def keyed_biases(config, secret: bytes, context: str) -> np.ndarray:
    """Zero-row research view; not a valid enrollment/theorem profile."""
    p, empty = tardos.generate_keyed(replace(config, roster_size=0), secret, context)
    assert empty.shape == (0, config.code_length)
    if not np.all(np.isfinite(p) & (p > 0) & (p < 1)):
        raise ValueError("biases must be finite and strictly between zero and one")
    return p


def endpoint_expectation(r0, r1, q_image):
    r0, r1, q = (np.asarray(a, dtype=np.float64) for a in (r0, r1, q_image))
    if r0.ndim != 2 or r0.shape != r1.shape or r0.shape != q.shape:
        raise ValueError("endpoints and q_image must have the same scalar image shape")
    if not all(np.isfinite(a).all() for a in (r0, r1, q)) or np.any((q < 0) | (q > 1)):
        raise ValueError("finite endpoints and probabilities in [0,1] required")
    return (r0 + r1) / 2, (2 * q - 1) * (r1 - r0) / 2


def render_native(source, pattern, strength=4.0):
    """Actual binary overlay through MuPDF at exact 144-DPI native geometry.

    This synthetic raster-source helper deliberately does not replace Task2's
    original source-PDF rendering and production _plan mapping.
    """
    source = np.asarray(source)
    pattern = np.asarray(pattern)
    if source.dtype != np.uint8 or source.ndim not in (2, 3) or source.shape[:2] != pattern.shape:
        raise ValueError("native source must be uint8 scalar/RGB and match pattern")
    if not np.isin(pattern, [-1, 0, 1]).all():
        raise ValueError("only binary signed templates and unused zero pixels allowed")
    height, width = pattern.shape
    stream = io.BytesIO()
    Image.fromarray(source).save(stream, format="PNG")
    with fitz.open() as document:
        page = document.new_page(width=width / 2, height=height / 2)
        page.insert_image(page.rect, stream=stream.getvalue())
        page.insert_image(page.rect, stream=tardos_carrier._transparent_overlay(pattern, strength))
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), colorspace=fitz.csRGB, alpha=False)
        rgb = np.frombuffer(pix.samples, dtype=np.uint8).reshape(height, width, 3).copy()
    return watermark._luma(rgb).astype(np.float64)


def translation(dx, dy):
    return np.array([[1., 0., dx], [0., 1., dy], [0., 0., 1.]])


def render_capture(capture, combined, reference_shape):
    """Warp original dtype/channels once, then apply existing RGB luma math."""
    height, width = reference_shape
    border = 255 if capture.ndim == 2 else (255, 255, 255)
    rendered = cv2.warpPerspective(capture, combined, (width, height),
                                   flags=cv2.INTER_LANCZOS4,
                                   borderMode=cv2.BORDER_CONSTANT, borderValue=border)
    return (rendered.astype(np.float64) if rendered.ndim == 2
            else watermark._luma(rendered).astype(np.float64))


def common_coverage(reference_shape, capture_shape, baseline):
    """Intersection of original-capture support over all 289 fixed candidates."""
    height, width = reference_shape
    raw_height, raw_width = capture_shape[:2]
    y, x = np.indices((height, width), dtype=np.float64)
    support = np.ones((height, width), bool)
    for dx in GRID:
        for dy in GRID:
            inv = np.linalg.inv(translation(dx, dy) @ baseline)
            denominator = inv[2, 0] * x + inv[2, 1] * y + inv[2, 2]
            with np.errstate(divide="ignore", invalid="ignore"):
                rx = (inv[0, 0] * x + inv[0, 1] * y + inv[0, 2]) / denominator
                ry = (inv[1, 0] * x + inv[1, 1] * y + inv[1, 2]) / denominator
            support &= (np.isfinite(rx) & np.isfinite(ry) & (rx >= 4) &
                        (rx <= raw_width - 1 - 4) & (ry >= 4) & (ry <= raw_height - 1 - 4))
    return support


def prepare_projection(source, pilot, coverage, active_blocks):
    source, pilot = (np.asarray(a, np.float64) for a in (source, pilot))
    coverage, active = np.asarray(coverage, bool), np.asarray(active_blocks, bool)
    if source.ndim != 2 or source.shape != pilot.shape or source.shape != coverage.shape:
        raise ValueError("source, pilot, coverage must have the same scalar image shape")
    height, width = source.shape
    rows, cols = height // BLOCK, width // BLOCK
    if active.shape != (rows, cols):
        raise ValueError("active_blocks must be a boolean grid of reference 6x6 blocks")
    if not np.isfinite(source).all() or not np.isfinite(pilot).all():
        raise ValueError("source and pilot must be finite")
    kept = []
    for by, bx in np.argwhere(active):
        y, x = int(by * BLOCK), int(bx * BLOCK)
        if y < 6 or x < 6 or y + 12 > height or x + 12 > width:
            continue
        if np.ptp(source[y - 6:y + 12, x - 6:x + 12]) > 8:
            continue
        if coverage[y:y + 6, x:x + 6].all():
            kept.append((y, x))
    # Discard rank-deficient tiles before building the reusable operator.
    groups = {}
    for y, x in kept:
        groups.setdefault((y // TILE, x // TILE), []).append((y, x))
    block_indices, tile_plans, discarded = [], [], 0
    for tile, locations in sorted(groups.items()):
        indices = np.array([[(y + dy) * width + x + dx for dy in range(6) for dx in range(6)]
                            for y, x in locations], dtype=np.int64)
        flat = indices.ravel()
        design = np.column_stack((np.ones(flat.size), flat % width - tile[1] * TILE,
                                  flat // width - tile[0] * TILE)).astype(np.float64)
        if np.linalg.matrix_rank(design) < 3:
            discarded += len(locations)
            continue
        start = len(block_indices) * 36
        block_indices.extend(indices)
        tile_plans.append((start, start + flat.size, design, np.linalg.pinv(design)))
    indices = np.asarray(block_indices, dtype=np.int64).reshape(-1, 36)
    mask = np.zeros(source.shape, bool)
    mask.ravel()[indices.ravel()] = True
    full_energy = float(np.sum(pilot * pilot))
    masked_energy = float(np.sum(pilot[mask] ** 2))
    return {"shape": source.shape, "indices": indices, "tiles": tile_plans, "mask": mask,
            "blocks": len(indices), "masked_pixels": int(mask.sum()), "active_blocks": int(active.sum()),
            "rank_discarded_blocks": discarded, "full_pilot_energy": full_energy,
            "masked_pilot_energy": masked_energy,
            "pilot_energy_fraction": masked_energy / full_energy if full_energy > 0 else 0.,
            "projection_sha256": array_hash(indices) + ":" + hashlib.sha256(
                b"".join(d.tobytes() + p.tobytes() for _, _, d, p in tile_plans)).hexdigest()}


def project(values, prepared):
    values = np.asarray(values, dtype=np.float64)
    if values.shape != prepared["shape"]:
        raise ValueError("projection image shape mismatch")
    selected = values.ravel()[prepared["indices"].ravel()].copy()
    for start, stop, design, pinv in prepared["tiles"]:
        section = selected[start:stop]
        coeff = np.einsum("ij,j->i", pinv, section)
        section -= np.einsum("ij,j->i", design, coeff)
    blocks = selected.reshape(-1, 36)
    blocks -= blocks.mean(axis=1, keepdims=True)
    return selected


def search_translation(capture, source, baseline_raw_to_reference, midpoint, pilot, active_blocks):
    started = time.perf_counter()
    capture, source, midpoint, pilot = map(np.asarray, (capture, source, midpoint, pilot))
    baseline = np.asarray(baseline_raw_to_reference, np.float64)
    if source.ndim != 2 or midpoint.shape != source.shape or pilot.shape != source.shape:
        raise ValueError("source, midpoint and pilot must be matching scalar images")
    if capture.ndim not in (2, 3) or (capture.ndim == 3 and capture.shape[2] != 3):
        raise ValueError("capture must be scalar or RGB")
    if baseline.shape != (3, 3) or not np.isfinite(baseline).all() or np.linalg.det(baseline) == 0:
        raise ValueError("baseline must be a finite nonsingular 3x3 transform")
    if not np.isfinite(midpoint).all():
        raise ValueError("midpoint must be finite")
    coverage = common_coverage(source.shape, capture.shape, baseline)
    prepared = prepare_projection(source, pilot, coverage, active_blocks)
    w = project(pilot, prepared)
    wn = float(np.sqrt(np.einsum("i,i->", w, w)))
    reason = None
    if prepared["blocks"] < 1000:
        reason = "fewer_than_1000_blocks"
    elif prepared["full_pilot_energy"] <= 0:
        reason = "zero_full_pilot_energy"
    elif prepared["pilot_energy_fraction"] < .2:
        reason = "pilot_energy_below_20_percent"
    elif not np.isfinite(wn) or wn == 0:
        reason = "zero_or_nonfinite_projected_pilot"
    objectives = []
    for dx in GRID:
        for dy in GRID:
            candidate = {"dx": float(dx), "dy": float(dy), "objective": None,
                         "valid": False, "invalid_reason": reason, "residual_norm": None}
            if reason is None:
                rendered = render_capture(capture, translation(dx, dy) @ baseline, source.shape)
                r = project(rendered - midpoint, prepared)
                rn = float(np.sqrt(np.einsum("i,i->", r, r)))
                candidate["residual_norm"] = rn if np.isfinite(rn) else None
                if np.isfinite(rn) and rn > 0:
                    objective = float(np.einsum("i,i->", r, w) / (rn * wn))
                    if np.isfinite(objective):
                        candidate.update(objective=objective, valid=True, invalid_reason=None)
                    else:
                        candidate["invalid_reason"] = "nonfinite_objective"
                else:
                    candidate["invalid_reason"] = "zero_or_nonfinite_residual"
            objectives.append(candidate)
    ranked = sorted((c for c in objectives if c["valid"]),
                    key=lambda c: (-c["objective"], c["dx"] ** 2 + c["dy"] ** 2, c["dx"], c["dy"]))
    best = ranked[0] if ranked else None
    status = "abstain"
    if best is not None:
        if best["objective"] <= 0:
            reason = "nonpositive_best_objective"
        elif abs(best["dx"]) == 2 or abs(best["dy"]) == 2:
            status, reason = "boundary_failure", "maximum_on_search_boundary"
        else:
            status, reason = "accepted", None
    elif reason is None:
        reason = "all_candidates_invalid"
    combined = translation(best["dx"], best["dy"]) @ baseline if best else None
    result = {"status": status, "reason": reason, "dx": best["dx"] if best else None,
              "dy": best["dy"] if best else None, "best_objective": best["objective"] if best else None,
              "raw_to_reference": combined.tolist() if status == "accepted" else None,
              "diagnostic_raw_to_reference": combined.tolist() if combined is not None else None,
              "objectives": objectives, "valid_candidates": len(ranked),
              "exact_best_ties": sum(c["objective"] == best["objective"] for c in ranked) if best else 0,
              "runner_up": ranked[1] if len(ranked) > 1 else None,
              "objective_gap": best["objective"] - ranked[1]["objective"] if len(ranked) > 1 else None,
              "mask_sha256": array_hash(prepared["mask"]),
              "projection_sha256": prepared["projection_sha256"],
              "transform_sha256": array_hash(combined) if combined is not None else None,
              "objectives_sha256": hashlib.sha256(json.dumps(objectives, sort_keys=True).encode()).hexdigest(),
              "projected_pilot_energy": wn * wn,
              "statistics": {k: prepared[k] for k in ("blocks", "masked_pixels", "active_blocks", "rank_discarded_blocks",
                  "full_pilot_energy", "masked_pilot_energy", "pilot_energy_fraction")},
              "elapsed_seconds": time.perf_counter() - started}
    return result
