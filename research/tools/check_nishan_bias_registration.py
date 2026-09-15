#!/usr/bin/env python3
"""Frozen synthetic gates only. No physical captures or recipient scoring."""
import argparse
from dataclasses import replace
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import time

import cv2
import numpy as np
import PIL
import pymupdf as fitz
import scipy
from scipy.special import logsumexp

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "prototypes/nishan_pq"))
from nishan import tardos, tardos_carrier
import nishan_bias_registration as reg
from probe_nishan_capture_channel import conditional_null_threshold

SEED = 2026091007
SHIFTS = [(1., 0.), (-1., 0.), (0., 1.), (0., -1.)]
CONTROL_NAMES = ["gain_0.85_plus15", "planar_shading", "near_white_quantization",
                 "unmarked_source", "white_endpoint_clipping250", "B_plus_W_only",
                 "independent_wrong_geometry", "source_edge_only"]


def dump(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def block_image(values, shape):
    rows, cols = shape[0] // 6, shape[1] // 6
    return np.asarray(values).reshape(rows, cols, 6, 6).transpose(0, 2, 1, 3).reshape(shape)


def pattern(word, geometry, shape):
    order, orientations, polarities = geometry
    blocks = np.zeros((shape[0] // 6 * (shape[1] // 6), 6, 6))
    blocks[order] = ((2 * np.asarray(word, dtype=np.int8) - 1)[:, None, None] *
                     polarities[:, None, None] * tardos_carrier._templates(6)[orientations])
    return block_image(blocks, shape)


def q_pixels(q, geometry, shape):
    blocks = np.full((shape[0] // 6 * (shape[1] // 6), 6, 6), .5)
    blocks[geometry[0]] = q[:, None, None]
    return block_image(blocks, shape)


def endpoints(source, q, geometry, strength=4.):
    r0 = reg.render_native(source, pattern(np.zeros(len(q), np.uint8), geometry, source.shape), strength)
    r1 = reg.render_native(source, pattern(np.ones(len(q), np.uint8), geometry, source.shape), strength)
    b, w = reg.endpoint_expectation(r0, r1, q_pixels(q, geometry, source.shape))
    return r0, r1, b, w


def blur(image):
    return cv2.GaussianBlur(image, (0, 0), .75)


def shifted(image, dx, dy):
    return reg.render_capture(image, reg.translation(dx, dy), image.shape[:2])


def decode(image, source, geometry):
    """Unweighted production block-sign rule, with original-source subtraction."""
    height, width = source.shape
    blocks = (image - source).reshape(height // 6, 6, width // 6, 6).transpose(0, 2, 1, 3).reshape(-1, 6, 6)
    order, orientations, polarities = geometry
    signed = tardos_carrier._templates(6)[orientations] * polarities[:, None, None]
    correlations = np.sum(blocks[order] * signed, axis=(1, 2))
    return (correlations > 0).astype(np.uint8)


def evaluate(capture, source, b, w, active, expected, geometry, baseline=None):
    baseline = np.eye(3) if baseline is None else baseline
    result = reg.search_translation(capture, source, baseline, b, w, active)
    if result["dx"] is None:
        error = None
    else:
        error = [abs(result["dx"] - expected[0]), abs(result["dy"] - expected[1])]
    result["expected_correction"] = list(expected)
    result["coordinate_absolute_error"] = error
    result["recovered"] = result["status"] == "accepted" and error is not None and max(error) <= .25
    matrix = np.asarray(result["raw_to_reference"]) if result["status"] == "accepted" else baseline
    word = decode(reg.render_capture(capture, matrix, source.shape), source, geometry)
    result["decoded_word"] = word.tolist()
    result["decoded_word_sha256"] = reg.array_hash(word)
    result["word_scope"] = "selected_accepted_transform" if result["status"] == "accepted" else "baseline_diagnostic_only"
    return result


def renderer_gate():
    q = np.array([.1, .3, .7, .9])
    geometry = (np.arange(4), np.array([0, 1, 0, 1]), np.array([1, 1, -1, -1]))
    sources = {"black": np.zeros((12, 12), np.uint8), "white": np.full((12, 12), 255, np.uint8),
               "gray128": np.full((12, 12), 128, np.uint8),
               "ramp": np.tile(np.rint(np.linspace(0, 255, 12)).astype(np.uint8), (12, 1))}
    y, x = np.indices((12, 12))
    boundary = ((x % 6 == 0) | (x % 6 == 5) | (y % 6 == 0) | (y % 6 == 5))
    cases = []
    for name, source in sources.items():
        for strength in (4., 2.2):
            _, _, b, w = endpoints(source, q, geometry, strength)
            actual = np.zeros(source.shape)
            for bits in itertools.product((0, 1), repeat=4):
                word = np.asarray(bits, np.uint8)
                probability = float(np.prod(np.where(word, q, 1 - q)))
                actual += probability * reg.render_native(source, pattern(word, geometry, source.shape), strength)
            difference = actual - (b + w)
            record = {"source": name, "strength": strength, "enumerated_words": 16}
            for label, mask in (("all", np.ones((12, 12), bool)), ("block_interiors", ~boundary),
                                ("block_boundaries", boundary)):
                d = difference[mask]
                record[label] = {"maximum_error": float(np.max(np.abs(d))),
                                 "rms_error": float(np.sqrt(np.mean(d ** 2)))}
            record["passed"] = record["all"]["maximum_error"] <= 1.01 and record["all"]["rms_error"] <= .25
            cases.append(record)
    return {"passed": all(c["passed"] for c in cases), "cases": cases}


def null_gate(control_words):
    p = np.array([.01, .03, .08, .15, .25, .4, .6, .75, .85, .92, .97, .99])
    q = np.floor(p * 2**32) / 2**32
    rows = np.array(list(itertools.product((0, 1), repeat=12)), np.uint8)
    log_probability = np.sum(np.where(rows, np.log(q), np.log1p(-q)), axis=1)
    words = {"all_one": np.ones(12, np.uint8), "all_zero": np.zeros(12, np.uint8),
             "p_gt_half": (p > .5).astype(np.uint8), "p_lt_half": (p < .5).astype(np.uint8),
             **{name: np.asarray(word[:12], np.uint8) for name, word in control_words.items()}}
    cases = []
    for name, word in words.items():
        active = word.astype(bool)
        pos, neg = np.sqrt((1 - p) / p), -np.sqrt(p / (1 - p))
        scores = np.sum(np.where(rows[:, active], pos[active], neg[active]), axis=1)
        mgfs = []
        for theta in (.01, .1, 1.):
            direct = float(logsumexp(log_probability + theta * scores))
            product = float(np.logaddexp(np.log(q[active]) + theta * pos[active],
                                         np.log1p(-q[active]) + theta * neg[active]).sum())
            error = float(abs(np.expm1(direct - product)))
            mgfs.append({"theta": theta, "direct_log_mgf": direct, "product_cgf": product,
                         "relative_error": error, "passed": error <= 1e-10})
        threshold = conditional_null_threshold(p, word, .05, 1)
        if threshold["threshold"] is None:
            tail, passed_tail = None, not active.any()
        else:
            tail = float(np.exp(logsumexp(log_probability[scores > threshold["threshold"]])))
            passed_tail = tail <= threshold["modeled_per_hypothesis_upper"] + 1e-12 and tail <= .05 + 1e-12
        cases.append({"name": name, "word": word.tolist(), "mgfs": mgfs, "threshold": threshold,
                      "strict_tail_probability": tail, "tail_passed": bool(passed_tail),
                      "passed": bool(passed_tail and all(m["passed"] for m in mgfs))})
    return {"passed": all(c["passed"] for c in cases), "enumerated_rows": 4096,
            "probability_sum": float(np.exp(logsumexp(log_probability))), "cases": cases,
            "scope": "exact tiny ideal null enumeration, not a physical rare-event measurement"}


def run(output):
    start = time.perf_counter()
    cv2.setNumThreads(2)
    output.mkdir(parents=False, exist_ok=False)
    code_paths = [Path(__file__), ROOT / "research/tools/nishan_bias_registration.py",
                  ROOT / "prototypes/nishan_pq/tests/test_bias_registration.py",
                  ROOT / "prototypes/nishan_pq/nishan/tardos.py",
                  ROOT / "prototypes/nishan_pq/nishan/tardos_carrier.py",
                  ROOT / "prototypes/nishan_pq/nishan/watermark.py",
                  ROOT / "research/tools/probe_nishan_capture_channel.py"]
    cases = [{"row": row, "shift": list(shift), "channel": channel}
             for row in range(32) for shift in SHIFTS for channel in ("identity", "sigma0.75")]
    manifest = {"seed": SEED, "code_sha256": {str(p.relative_to(ROOT)): digest(p) for p in code_paths},
                "libraries": {"python": platform.python_version(), "numpy": np.__version__,
                              "opencv": cv2.__version__, "pymupdf": fitz.VersionBind,
                              "pillow": PIL.__version__, "scipy": scipy.__version__},
                "settings": {"dpi": 144, "block": 6, "tile": 96, "source_shape": [240, 240],
                             "source_luma": 245, "cutoff": 1 / 1500, "strength": 4.,
                             "grid": reg.GRID.tolist(), "source_neighborhood": 18,
                             "source_range_max": 8, "capture_support_margin": 4,
                             "minimum_blocks": 1000, "minimum_pilot_energy_fraction": .2,
                             "blur_sigma": .75, "recovery_fraction_min": .95,
                             "coordinate_tolerance": .25, "renderer_max_error": 1.01,
                             "renderer_rms_error": .25, "null_mgf_relative_tolerance": 1e-10,
                             "null_theta": [.01, .1, 1.], "null_epsilon": .05, "null_H": 1,
                             "opencv_threads": 2, "device": "CPU"},
                "recovery_cases": cases,
                "renderer_cases": {"sources": ["black", "white", "gray128", "ramp"],
                                   "ramp": "12 integer columns rint(linspace(0,255,12))",
                                   "strengths": [4., 2.2], "q": [.1, .3, .7, .9],
                                   "orientations": [0, 1, 0, 1], "polarities": [1, 1, -1, -1],
                                   "words": "all16", "boundaries": "first/last pixel rows or columns of each6x6 block"},
                "controls": {"names": CONTROL_NAMES, "shift": [1., 0.],
                             "gain": ".85*first_native_row+15, float64",
                             "shading": "first_native_row+8*x/width+5*y/height, float64",
                             "near_white": "source255 native strength4 first row, nearest4 levels, clip[0,255], uint8",
                             "erasure": "source255 native endpoints251/255, map values>=250 to255 on endpoints and capture",
                             "shared_only": "native B+W before fixed blur, no recipient residual",
                             "wrong_geometry": "fresh independent secret and context, first row",
                             "edge_only": "source245 with one-pixel black line x=120, identical reference, no carrier",
                             "abstention_words": "baseline diagnostic only"},
                "composition_cases": {"half_pixel_shifts": [[.5, 0], [-.5, 0], [0, .5], [0, -.5]],
                                      "rectangle_baseline": [-5, 3], "rectangle_residual": [-2, 1]},
                "null_p": [.01, .03, .08, .15, .25, .4, .6, .75, .85, .92, .97, .99],
                "scope": "synthetic research only; no novelty/security/physical robustness claim"}
    dump(output / "manifest.json", manifest)
    rng = np.random.default_rng(SEED)
    secret = rng.bytes(32)
    geometry_secret = rng.bytes(32)
    config = replace(tardos.parameters(5, 5, .05), code_length=1600)
    p = reg.keyed_biases(config, secret, "bias-registration-synthetic-2026-09-10/p")
    q = np.floor(p * 2**32) / 2**32
    geometry = tardos_carrier._plan(geometry_secret, "bias-registration-synthetic-2026-09-10/geometry", 1600, 1600)
    rows = (rng.random((32, 1600)) < q).astype(np.uint8)
    source = np.full((240, 240), 245, np.uint8)
    active = np.ones((40, 40), bool)
    r0, r1, native_b, native_w = endpoints(source, q, geometry)
    b, w = blur(native_b), blur(native_w)
    prepared = reg.prepare_projection(source, w, reg.common_coverage(source.shape, source.shape, np.eye(3)), active)
    np.savez_compressed(output / "synthetic_inputs.npz", p=p, q=q, rows=rows, source=source,
                        order=geometry[0], orientations=geometry[1], polarities=geometry[2],
                        r0=r0, r1=r1, midpoint=b, pilot=w, mask=prepared["mask"],
                        bias_secret=np.frombuffer(secret, np.uint8), geometry_secret=np.frombuffer(geometry_secret, np.uint8))
    results = {"completed": False, "physical_gate_passed": False, "renderer": renderer_gate(),
               "recovery": {"cases": []}, "controls": [], "manifest_sha256": digest(output / "manifest.json")}
    dump(output / "results.json", results)
    print("renderer: " + json.dumps({"passed": results["renderer"]["passed"], "cases": len(results["renderer"]["cases"])}), flush=True)
    native_rows = []
    for row_index, row in enumerate(rows):
        native = reg.render_native(source, pattern(row, geometry, source.shape))
        native_rows.append(native)
        for shift in SHIFTS:
            for channel in ("identity", "sigma0.75"):
                image = native if channel == "identity" else blur(native)
                result = evaluate(shifted(image, *shift), source, b, w, active,
                                  (-shift[0], -shift[1]), geometry)
                result.update(row=row_index, shift=list(shift), channel=channel)
                results["recovery"]["cases"].append(result)
        dump(output / "results.json", results)
        recovered = sum(c["recovered"] for c in results["recovery"]["cases"])
        print(f"recovery: {len(results['recovery']['cases'])}/256 complete; {recovered} recovered; elapsed={time.perf_counter()-start:.3f}s", flush=True)
    recovered = sum(c["recovered"] for c in results["recovery"]["cases"])
    results["recovery"].update(total=256, recovered=recovered, fraction=recovered / 256,
                               passed=recovered / 256 >= .95)
    composition = []
    for shift in ((.5, 0.), (-.5, 0.), (0., .5), (0., -.5)):
        record = evaluate(shifted(native_rows[0], *shift), source, b, w, active, (-shift[0], -shift[1]), geometry)
        record["shift"] = list(shift)
        composition.append(record)
    rectangle = np.full((64, 64), 255, np.uint8)
    rectangle[20:32, 20:34] = 80
    raw = shifted(rectangle, 7, -4)
    combined = reg.translation(-2, 1) @ reg.translation(-5, 3)
    rectangle_pass = np.array_equal(combined, reg.translation(-7, 4)) and np.array_equal(
        reg.render_capture(raw, combined, rectangle.shape), rectangle)
    results["composition"] = {"passed": bool(rectangle_pass and all(c["recovered"] for c in composition)),
                              "half_pixel_cases": composition, "integer_rectangle_passed": bool(rectangle_pass),
                              "integer_combined_transform": combined.tolist()}
    capture = shifted(native_rows[0], 1, 0)
    unused_roster = np.zeros((3, 12), np.uint8)
    first = evaluate(capture, source, b, w, active, (-1., 0.), geometry)
    unused_roster = np.ones((7, 12), np.uint8)
    second = evaluate(capture, source, b, w, active, (-1., 0.), geometry)
    fields = ["transform_sha256", "objectives_sha256", "mask_sha256", "projection_sha256", "decoded_word_sha256"]
    results["independence"] = {"passed": all(first[k] == second[k] for k in fields),
                               "before": {k: first[k] for k in fields}, "after": {k: second[k] for k in fields},
                               "unused_roster_shapes": [[3, 12], list(unused_roster.shape)],
                               "scope": "mechanical input isolation, not a cryptographic independence proof"}
    white = np.full(source.shape, 255, np.uint8)
    wr0, wr1, wb, ww = endpoints(white, q, geometry)
    white_native = reg.render_native(white, pattern(rows[0], geometry, source.shape))
    clipped0, clipped1 = np.where(wr0 >= 250, 255., wr0), np.where(wr1 >= 250, 255., wr1)
    erased_b, erased_w = reg.endpoint_expectation(clipped0, clipped1, q_pixels(q, geometry, source.shape))
    y, x = np.indices(source.shape)
    edge_source = source.copy()
    edge_source[:, 120] = 0
    _, _, eb, ew = endpoints(edge_source, q, geometry)
    wrong_secret = rng.bytes(32)
    wrong_geometry = tardos_carrier._plan(wrong_secret, "bias-registration-synthetic-2026-09-10/wrong-geometry", 1600, 1600)
    wrong = reg.render_native(source, pattern(rows[0], wrong_geometry, source.shape))
    control_specs = [
        ("gain_0.85_plus15", native_rows[0] * .85 + 15, source, b, w, False),
        ("planar_shading", native_rows[0] + 8 * x / 240 + 5 * y / 240, source, b, w, False),
        ("near_white_quantization", np.clip(np.rint(white_native / 4) * 4, 0, 255).astype(np.uint8), white, blur(wb), blur(ww), False),
        ("unmarked_source", source, source, b, w, True),
        ("white_endpoint_clipping250", np.where(white_native >= 250, 255., white_native), white, blur(erased_b), blur(erased_w), True),
        ("B_plus_W_only", native_b + native_w, source, b, w, True),
        ("independent_wrong_geometry", wrong, source, b, w, False),
        ("source_edge_only", edge_source, edge_source, blur(eb), blur(ew), True)]
    source_words = {}
    control_arrays = {}
    for name, image, reference, cb, cw, source_only in control_specs:
        control_capture = shifted(image, 1, 0)
        record = evaluate(control_capture, reference, cb, cw, active, (-1., 0.), geometry)
        record.update(name=name, source_only=source_only,
                      limitation="Positive alignment objectives are not recipient evidence; this control does not establish physical robustness.")
        if source_only:
            source_words[name] = record["decoded_word"]
        control_arrays[name + "_capture"] = control_capture
        control_arrays[name + "_source"] = reference
        control_arrays[name + "_midpoint"] = cb
        control_arrays[name + "_pilot"] = cw
        results["controls"].append(record)
        print("control: " + json.dumps({"name": name, "status": record["status"], "dx": record["dx"],
                                          "dy": record["dy"], "recovered": record["recovered"]}), flush=True)
    np.savez_compressed(output / "control_inputs.npz", **control_arrays)
    results["erasure"] = {"passed": bool(np.count_nonzero(erased_w) == 0 and
        next(c for c in results["controls"] if c["name"] == "white_endpoint_clipping250")["status"] == "abstain"),
        "native_pilot_energy": float(np.sum(erased_w ** 2)), "endpoint_values_before": [float(wr0.min()), float(wr0.max())]}
    results["null"] = null_gate(source_words)
    results["physical_gate_passed"] = all(results[k]["passed"] for k in
        ("renderer", "recovery", "null", "composition", "independence"))
    results["completed"] = True
    results["elapsed_seconds"] = time.perf_counter() - start
    results["artifact_sha256"] = {p.name: digest(p) for p in (output / "synthetic_inputs.npz", output / "control_inputs.npz")}
    results["limitations"] = ["Synthetic result only; no photos loaded or physical scoring authorized by this runner.",
        "Ideal row draws and tiny exact null enumeration do not certify deployed cryptographic independence or rare physical tails.",
        "Threshold helper has numerical tolerance, not certified conservative arithmetic.",
        "Native raster-source response must be adapted to original source PDF and production mapping only in separately authorized Task2.",
        "Nuisance recovery outcomes cannot establish security, novelty, or print/camera robustness."]
    dump(output / "results.json", results)
    print("final: " + json.dumps({k: results[k]["passed"] for k in
        ("renderer", "recovery", "null", "composition", "independence", "erasure")}), flush=True)
    print("physical_gate_passed=" + str(results["physical_gate_passed"]) +
          f"; elapsed={results['elapsed_seconds']:.3f}s; results_sha256={digest(output / 'results.json')}", flush=True)
    return 0 if results["physical_gate_passed"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.output))
