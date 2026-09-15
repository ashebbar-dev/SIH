#!/usr/bin/env python3
"""Run the one-shot frozen empirical compact-carrier pilot."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import shutil
import sys
import time
import traceback
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image, ImageFilter

from nishan import tardos, tardos_carrier, watermark

from profiles import (
    DPI,
    PROFILES,
    STRENGTH,
    array_commitment,
    collapse_correlations,
    context_for_profile,
    original_configuration,
    profile_manifest,
    sha3_file,
    symmetric_configuration,
    symmetric_scores,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE = REPO_ROOT / "artifacts/nishan/synthetic-source.pdf"
ISSUED_ROWS = (0, 7)
TRANSFORMS = ("clean", "jpeg55", "blur1", "blur2", "half-resize")
SCHEMA_VERSION = "nishan-compact-carrier-run/v1"
PROFILE_VERSION = "compact-carrier-v1"


def create_output_directory(output: Path) -> None:
    output.mkdir(parents=True, exist_ok=False)


def build_declared_matrix() -> list[dict[str, object]]:
    matrix: list[dict[str, object]] = []
    for profile in PROFILES:
        for row in ISSUED_ROWS:
            for transform in TRANSFORMS:
                matrix.append(
                    {
                        "kind": "positive",
                        "profile": profile,
                        "row": row,
                        "transform": transform,
                    }
                )
    for profile in PROFILES:
        for transform in TRANSFORMS:
            matrix.append(
                {
                    "kind": "unmarked",
                    "profile": profile,
                    "row": None,
                    "transform": transform,
                }
            )
    for kind in ("wrong-key", "wrong-context"):
        for profile in PROFILES:
            for row in ISSUED_ROWS:
                matrix.append(
                    {
                        "kind": kind,
                        "profile": profile,
                        "row": row,
                        "transform": "clean",
                    }
                )
    identities = {
        (item["kind"], item["profile"], item["row"], item["transform"])
        for item in matrix
    }
    if len(matrix) != 57 or len(identities) != 57:
        raise RuntimeError("frozen matrix construction is invalid")
    return matrix


def _json_write(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="utf-8",
    )


def _relative(path: Path, output: Path) -> str:
    return path.relative_to(output).as_posix()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _secret_commitment(secret: bytes) -> str:
    return hashlib.sha3_256(secret).hexdigest()


def _environment_versions() -> dict[str, str]:
    versions = {"python": platform.python_version()}
    for package in ("numpy", "pillow", "pymupdf", "cryptography"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = "unavailable"
    return versions


def _source_hashes() -> dict[str, str]:
    paths = {
        "tardos.py": REPO_ROOT / "prototypes/nishan_pq/nishan/tardos.py",
        "tardos_carrier.py": REPO_ROOT
        / "prototypes/nishan_pq/nishan/tardos_carrier.py",
        "watermark.py": REPO_ROOT / "prototypes/nishan_pq/nishan/watermark.py",
    }
    experiment = sorted(Path(__file__).resolve().parent.glob("*"))
    for path in experiment:
        if path.is_file() and path.suffix in {".py", ".md"}:
            paths[f"experiment/{path.name}"] = path
    return {name: sha3_file(path) for name, path in paths.items()}


def _family_for_profile(
    profile_name: str,
    original_biases: np.ndarray,
    original_codebook: np.ndarray,
    symmetric_biases: np.ndarray,
    symmetric_codebook: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    if PROFILES[profile_name].family == "original":
        return original_biases, original_codebook
    return symmetric_biases, symmetric_codebook


def _render_single_page(path: Path) -> Image.Image:
    pages, _ = watermark.load_pages(path, dpi=DPI)
    if len(pages) != 1:
        raise RuntimeError("frozen pilot source must render as exactly one page")
    return Image.fromarray(pages[0], mode="RGB")


def _write_transforms(
    clean: Image.Image,
    directory: Path,
) -> tuple[dict[str, Path], dict[str, float]]:
    directory.mkdir(parents=True, exist_ok=True)
    paths: dict[str, Path] = {}
    timings: dict[str, float] = {}
    operations = {
        "clean": lambda image: image.copy(),
        "jpeg55": lambda image: image.copy(),
        "blur1": lambda image: image.filter(ImageFilter.GaussianBlur(radius=1.0)),
        "blur2": lambda image: image.filter(ImageFilter.GaussianBlur(radius=2.0)),
        "half-resize": lambda image: image.resize(
            (max(1, image.width // 2), max(1, image.height // 2)),
            Image.Resampling.LANCZOS,
        ).resize(image.size, Image.Resampling.LANCZOS),
    }
    for name in TRANSFORMS:
        started = time.perf_counter()
        transformed = operations[name](clean)
        suffix = ".jpg" if name == "jpeg55" else ".png"
        path = directory / f"{name}{suffix}"
        if name == "jpeg55":
            transformed.save(
                path,
                format="JPEG",
                quality=55,
                subsampling=0,
                optimize=False,
            )
        else:
            transformed.save(path, format="PNG")
        paths[name] = path
        timings[name] = time.perf_counter() - started
    return paths, timings


def _summary(values: np.ndarray) -> dict[str, float]:
    values = np.asarray(values, dtype=np.float64)
    return {
        "minimum": float(values.min()),
        "maximum": float(values.max()),
        "mean": float(values.mean()),
        "standard_deviation": float(values.std()),
    }


def _score_observation(
    index: int,
    declaration: dict[str, object],
    suspect: Path,
    output: Path,
    source_copy: Path,
    carrier_key: bytes,
    wrong_carrier_key: bytes,
    context_uuid: str,
    original_biases: np.ndarray,
    original_codebook: np.ndarray,
    symmetric_biases: np.ndarray,
    symmetric_codebook: np.ndarray,
) -> dict[str, object]:
    profile_name = str(declaration["profile"])
    profile = PROFILES[profile_name]
    row_value = declaration["row"]
    row = int(row_value) if row_value is not None else None
    kind = str(declaration["kind"])
    biases, codebook = _family_for_profile(
        profile_name,
        original_biases,
        original_codebook,
        symmetric_biases,
        symmetric_codebook,
    )
    decode_key = wrong_carrier_key if kind == "wrong-key" else carrier_key
    context = context_for_profile(context_uuid, profile_name)
    if kind == "wrong-context":
        context = f"{context}/intentionally-wrong"

    decode_started = time.perf_counter()
    _, correlations, diagnostics = tardos_carrier.decode_word_with_diagnostics(
        source_copy,
        suspect,
        profile.physical_placements,
        decode_key,
        context,
        dpi=DPI,
        block_size=profile.block_size,
        registration_mode="off",
    )
    decode_seconds = time.perf_counter() - decode_started
    logical_word, logical_sums = collapse_correlations(
        correlations, profile.logical_positions, profile.repetitions
    )

    scoring_started = time.perf_counter()
    if profile.scorer == "original-one-sided":
        scores = tardos.accusation_scores(biases, codebook, logical_word)
    else:
        scores = symmetric_scores(codebook, biases, logical_word)
    scoring_seconds = time.perf_counter() - scoring_started
    if scores.shape != (1000,) or not np.all(np.isfinite(scores)):
        raise RuntimeError("scorer did not return 1000 finite row scores")
    ratios = scores / profile.threshold
    selected = np.flatnonzero(scores > profile.threshold)

    arrays_directory = output / "arrays"
    arrays_directory.mkdir(parents=True, exist_ok=True)
    arrays_path = arrays_directory / f"observation-{index:03d}.npz"
    np.savez(
        arrays_path,
        scores=np.asarray(scores, dtype=np.float64),
        score_threshold_ratios=np.asarray(ratios, dtype=np.float64),
        physical_correlations=np.asarray(correlations, dtype=np.float64),
        logical_summed_correlations=np.asarray(logical_sums, dtype=np.float64),
        decoded_word=np.asarray(logical_word, dtype=np.uint8),
    )

    positive = kind == "positive"
    intended_score = float(scores[row]) if positive and row is not None else None
    intended_ratio = float(ratios[row]) if positive and row is not None else None
    intended_rank = (
        1 + int(np.count_nonzero(scores > scores[row]))
        if positive and row is not None
        else None
    )
    other_rows = [issued for issued in ISSUED_ROWS if issued != row]
    unissued_mask = np.ones(1000, dtype=bool)
    unissued_mask[list(ISSUED_ROWS)] = False
    ber = (
        float(np.count_nonzero(logical_word != codebook[row]) / profile.logical_positions)
        if positive and row is not None
        else None
    )
    marking = (
        tardos_carrier.marking_condition_errors(logical_word, codebook[[row]])
        if positive and row is not None
        else None
    )
    return {
        **declaration,
        "suspect_path": _relative(suspect, output),
        "arrays_path": _relative(arrays_path, output),
        "arrays_sha3_256": sha3_file(arrays_path),
        "registration_mode": "off",
        "registration": diagnostics,
        "selected_rows": [int(value) for value in selected],
        "selected_count": int(selected.size),
        "maximum_score": float(scores.max()),
        "maximum_score_threshold_ratio": float(ratios.max()),
        "maximum_score_row": int(np.argmax(scores)),
        "intended_score": intended_score,
        "intended_score_threshold_ratio": intended_ratio,
        "intended_row_rank": intended_rank,
        "other_issued_maximum_score": float(scores[other_rows].max()),
        "other_issued_maximum_ratio": float(ratios[other_rows].max()),
        "unissued_maximum_score": float(scores[unissued_mask].max()),
        "unissued_maximum_ratio": float(ratios[unissued_mask].max()),
        "logical_ber": ber,
        "negative_ber": None if not positive else "not-applicable",
        "marking_condition": marking,
        "negative_marking_condition_reason": (
            "no participating source row; marking-condition BER is undefined"
            if not positive
            else None
        ),
        "physical_correlation_summary": _summary(correlations),
        "logical_correlation_summary": _summary(logical_sums),
        "decode_seconds": decode_seconds,
        "scoring_seconds": scoring_seconds,
    }


def _validate_observation_matrix(
    declared_matrix: list[dict[str, object]], observations: list[dict[str, object]]
) -> None:
    expected = {
        (kind, profile, row, transform)
        for kind, profile, row, transform in (
            (
                item["kind"],
                item["profile"],
                item["row"],
                item["transform"],
            )
            for item in declared_matrix
        )
    }
    observed = {
        (o["kind"], o["profile"], o["row"], o["transform"])
        for o in observations
    }
    if len(observations) != 57 or len(expected) != 57 or observed != expected:
        raise RuntimeError("fixed observation matrix is incomplete or duplicated")


def _profile_transform_summary(
    observations: list[dict[str, object]],
) -> list[dict[str, object]]:
    summary: list[dict[str, object]] = []
    for profile in PROFILES:
        for transform in TRANSFORMS:
            cases = [
                item
                for item in observations
                if item["kind"] == "positive"
                and item["profile"] == profile
                and item["transform"] == transform
            ]
            summary.append(
                {
                    "profile": profile,
                    "transform": transform,
                    "rows": [int(item["row"]) for item in cases],
                    "intended_score_threshold_ratios": [
                        item["intended_score_threshold_ratio"] for item in cases
                    ],
                    "logical_ber": [item["logical_ber"] for item in cases],
                    "selected_rows": [item["selected_rows"] for item in cases],
                    "intended_row_ranks": [item["intended_row_rank"] for item in cases],
                }
            )
    return summary


def _advancement(
    observations: list[dict[str, object]], issued: list[dict[str, object]]
) -> dict[str, object]:
    compact = ("symmetric-6-r4", "symmetric-12-r1")
    clean_compact = [
        item
        for item in observations
        if item["kind"] == "positive"
        and item["profile"] in compact
        and item["transform"] == "clean"
    ]
    clean_selection = len(clean_compact) == 4 and all(
        item["selected_rows"] == [item["row"]] for item in clean_compact
    )
    compact_text = all(
        item["text_preserved"] for item in issued if item["profile"] in compact
    )
    negatives = [item for item in observations if item["kind"] != "positive"]
    negatives_clear = len(negatives) == 27 and all(
        not item["selected_rows"] for item in negatives
    )
    prerequisites = clean_selection and compact_text and negatives_clear

    positive_lookup = {
        (str(item["profile"]), int(item["row"]), str(item["transform"])): item
        for item in observations
        if item["kind"] == "positive"
    }
    candidates: dict[str, object] = {}
    for profile in compact:
        winning_transforms: list[str] = []
        comparisons: list[dict[str, object]] = []
        for transform in ("blur1", "blur2", "half-resize"):
            row_comparisons: list[dict[str, object]] = []
            wins = True
            for row in ISSUED_ROWS:
                candidate = positive_lookup[(profile, row, transform)]
                original = positive_lookup[("original-6-r1", row, transform)]
                no_extra = candidate["selected_rows"] == [row]
                ratio_win = float(candidate["intended_score_threshold_ratio"]) > float(
                    original["intended_score_threshold_ratio"]
                )
                wins = wins and no_extra and ratio_win
                row_comparisons.append(
                    {
                        "row": row,
                        "compact_ratio": candidate[
                            "intended_score_threshold_ratio"
                        ],
                        "original_ratio": original[
                            "intended_score_threshold_ratio"
                        ],
                        "compact_selected_rows": candidate["selected_rows"],
                        "ratio_exceeds_original": ratio_win,
                        "no_extra_selected_rows": no_extra,
                    }
                )
            if wins:
                winning_transforms.append(transform)
            comparisons.append(
                {
                    "transform": transform,
                    "wins_both_rows_without_extra_selections": wins,
                    "rows": row_comparisons,
                }
            )
        candidates[profile] = {
            "worth_fresh_physical_test": prerequisites
            and len(winning_transforms) >= 2,
            "winning_transforms": winning_transforms,
            "required_winning_transform_count": 2,
            "comparisons": comparisons,
        }
    return {
        "rule": (
            "Fixed empirical pilot prioritization rule from the frozen specification; "
            "not statistical significance or a superiority test."
        ),
        "prerequisites_met": prerequisites,
        "prerequisite_details": {
            "both_compact_profiles_clean_select_only_intended": clean_selection,
            "both_compact_profiles_text_unchanged": compact_text,
            "all_27_negative_observations_select_no_rows": negatives_clear,
        },
        "profiles": candidates,
    }


def _artifact_hashes(output: Path) -> dict[str, str]:
    return {
        _relative(path, output): sha3_file(path)
        for path in sorted(output.rglob("*"))
        if path.is_file() and path.name not in {"results.json", "failure.json"}
    }


def _physical_instructions(output: Path) -> None:
    lines = [
        "# Physical capture instructions",
        "",
        "This packet has no physical result. It identifies the three row-0 PDFs for a fresh test:",
        "",
    ]
    for profile in PROFILES:
        lines.append(f"- `issued/{profile}/row-0.pdf`")
    lines.extend(
        [
            "",
            "Print each PDF at actual size using the same printer settings. Photograph the full page from the same distance and under the same lighting. Retain the original, unfiltered camera files and label each capture with its profile.",
            "",
            "Supply only the capture image and profile label for scoring. Do not send the private replay state. No physical result exists until fresh images are supplied and evaluated.",
        ]
    )
    (output / "physical-capture-instructions.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def run(output: Path) -> dict[str, object]:
    create_output_directory(output)
    run_started = time.perf_counter()
    try:
        if not SOURCE.is_file():
            raise FileNotFoundError(f"frozen source is missing: {SOURCE}")
        source_directory = output / "source"
        source_directory.mkdir()
        source_copy = source_directory / "synthetic-source.pdf"
        shutil.copy2(SOURCE, source_copy)
        source_hash = sha3_file(SOURCE)
        if sha3_file(source_copy) != source_hash:
            raise RuntimeError("copied source hash does not match frozen input")

        original_config = original_configuration()
        symmetric_config = symmetric_configuration()
        original_key = os.urandom(32)
        symmetric_key = os.urandom(32)
        carrier_key = os.urandom(32)
        wrong_carrier_key = os.urandom(32)
        context_uuid = str(uuid.uuid4())

        generation_started = time.perf_counter()
        original_biases, original_codebook = tardos.generate_keyed(
            original_config, original_key, f"{context_uuid}/original-codebook"
        )
        original_generation_seconds = time.perf_counter() - generation_started
        generation_started = time.perf_counter()
        symmetric_biases, symmetric_codebook = tardos.generate_keyed(
            symmetric_config, symmetric_key, f"{context_uuid}/symmetric-codebook"
        )
        symmetric_generation_seconds = time.perf_counter() - generation_started

        private_directory = output / "private"
        private_directory.mkdir()
        replay_path = private_directory / "replay-state.npz"
        np.savez(
            replay_path,
            original_biases=np.asarray(original_biases, dtype=np.float64),
            original_codebook=np.asarray(original_codebook, dtype=np.uint8),
            original_key=np.frombuffer(original_key, dtype=np.uint8),
            symmetric_biases=np.asarray(symmetric_biases, dtype=np.float64),
            symmetric_codebook=np.asarray(symmetric_codebook, dtype=np.uint8),
            symmetric_key=np.frombuffer(symmetric_key, dtype=np.uint8),
            carrier_key=np.frombuffer(carrier_key, dtype=np.uint8),
            wrong_carrier_key=np.frombuffer(wrong_carrier_key, dtype=np.uint8),
            context_uuid=np.asarray(context_uuid),
        )
        replay_path.chmod(0o600)

        capacities = {
            str(block): tardos_carrier.capacity(source_copy, dpi=DPI, block_size=block)
            for block in (6, 12)
        }
        for profile in PROFILES.values():
            if capacities[str(profile.block_size)] < profile.physical_placements:
                raise RuntimeError(f"rendered capacity is insufficient for {profile.name}")

        issued: list[dict[str, object]] = []
        observation_paths: dict[tuple[str, int | None, str], Path] = {}
        transform_timings: list[dict[str, object]] = []
        for profile_name, profile in PROFILES.items():
            _, codebook = _family_for_profile(
                profile_name,
                original_biases,
                original_codebook,
                symmetric_biases,
                symmetric_codebook,
            )
            for row in ISSUED_ROWS:
                logical_word = codebook[row]
                physical_word = np.tile(logical_word, profile.repetitions)
                if physical_word.shape != (profile.physical_placements,):
                    raise RuntimeError("physical word shape violates frozen profile")
                pdf_path = output / "issued" / profile_name / f"row-{row}.pdf"
                embed_started = time.perf_counter()
                carrier_metrics = tardos_carrier.embed_pdf(
                    source_copy,
                    pdf_path,
                    physical_word,
                    carrier_key,
                    context_for_profile(context_uuid, profile_name),
                    strength=STRENGTH,
                    dpi=DPI,
                    block_size=profile.block_size,
                )
                embed_seconds = time.perf_counter() - embed_started
                measured = tardos_carrier.measure_pdf_pair(
                    source_copy, pdf_path, dpi=DPI
                )
                issued.append(
                    {
                        "profile": profile_name,
                        "row": row,
                        "pdf_path": _relative(pdf_path, output),
                        "pdf_sha3_256": sha3_file(pdf_path),
                        "file_size_bytes": pdf_path.stat().st_size,
                        "source_file_size_bytes": source_copy.stat().st_size,
                        "embed_seconds": embed_seconds,
                        **asdict(carrier_metrics),
                        "measured_pair": asdict(measured),
                    }
                )
                render_started = time.perf_counter()
                clean = _render_single_page(pdf_path)
                render_seconds = time.perf_counter() - render_started
                paths, timings = _write_transforms(
                    clean, output / "rasters" / profile_name / f"row-{row}"
                )
                for transform, path in paths.items():
                    observation_paths[(profile_name, row, transform)] = path
                    transform_timings.append(
                        {
                            "profile": profile_name,
                            "row": row,
                            "transform": transform,
                            "render_seconds": render_seconds
                            if transform == "clean"
                            else 0.0,
                            "transform_seconds": timings[transform],
                            "path": _relative(path, output),
                        }
                    )

        source_render_started = time.perf_counter()
        source_clean = _render_single_page(source_copy)
        source_render_seconds = time.perf_counter() - source_render_started
        source_paths, source_transform_timings = _write_transforms(
            source_clean, output / "rasters" / "unmarked"
        )
        for transform, path in source_paths.items():
            observation_paths[("unmarked", None, transform)] = path
            transform_timings.append(
                {
                    "profile": None,
                    "row": None,
                    "transform": transform,
                    "render_seconds": source_render_seconds
                    if transform == "clean"
                    else 0.0,
                    "transform_seconds": source_transform_timings[transform],
                    "path": _relative(path, output),
                }
            )

        declared_matrix = build_declared_matrix()
        manifest = {
            "schema_version": SCHEMA_VERSION,
            "profile_version": PROFILE_VERSION,
            "created_at_utc": _now(),
            "scope": (
                "Isolated empirical one-source carrier pilot; no physical result, "
                "probability certification, production attribution, collusion guarantee, "
                "novelty, or superiority claim."
            ),
            "source": {
                "input_path": "artifacts/nishan/synthetic-source.pdf",
                "run_path": "source/synthetic-source.pdf",
                "sha3_256": source_hash,
            },
            "versions": _environment_versions(),
            "implementation_sha3_256": _source_hashes(),
            "profiles": {
                name: profile_manifest(profile) for name, profile in PROFILES.items()
            },
            "generator_configurations": {
                "original": {**asdict(original_config), "theorem_certified": False},
                "symmetric": {**asdict(symmetric_config), "theorem_certified": False},
            },
            "families": {
                "original": {
                    "biases_sha3_256": array_commitment(original_biases, "<f8"),
                    "codebook_sha3_256": array_commitment(original_codebook, "u1"),
                    "codebook_shape": list(original_codebook.shape),
                    "generator_key_commitment_sha3_256": _secret_commitment(
                        original_key
                    ),
                    "empirical_inherited_sampler": (
                        "53-bit/float64 biases and 32-bit Bernoulli thresholds"
                    ),
                },
                "symmetric": {
                    "biases_sha3_256": array_commitment(symmetric_biases, "<f8"),
                    "codebook_sha3_256": array_commitment(symmetric_codebook, "u1"),
                    "codebook_shape": list(symmetric_codebook.shape),
                    "generator_key_commitment_sha3_256": _secret_commitment(
                        symmetric_key
                    ),
                    "empirical_inherited_sampler": (
                        "53-bit/float64 biases and 32-bit Bernoulli thresholds"
                    ),
                    "same_codebook_for_both_symmetric_profiles": True,
                },
            },
            "carrier": {
                "key_commitment_sha3_256": _secret_commitment(carrier_key),
                "wrong_key_commitment_sha3_256": _secret_commitment(
                    wrong_carrier_key
                ),
                "profile_context_commitments_sha3_256": {
                    profile: hashlib.sha3_256(
                        context_for_profile(context_uuid, profile).encode("utf-8")
                    ).hexdigest()
                    for profile in PROFILES
                },
                "profile_contexts_are_distinct": True,
                "dpi": DPI,
                "strength": STRENGTH,
                "rendered_capacities": capacities,
            },
            "private_replay": {
                "path": "private/replay-state.npz",
                "sha3_256": sha3_file(replay_path),
                "mode": "0600",
            },
            "declared_matrix": declared_matrix,
            "declared_observation_count": 57,
            "manifest_provenance_limitation": (
                "This local manifest is not independently signed provenance."
            ),
        }
        _json_write(output / "manifest.json", manifest)

        observations: list[dict[str, object]] = []
        for index, declaration in enumerate(declared_matrix):
            profile_name = str(declaration["profile"])
            row_value = declaration["row"]
            row = int(row_value) if row_value is not None else None
            transform = str(declaration["transform"])
            if declaration["kind"] == "unmarked":
                suspect = observation_paths[("unmarked", None, transform)]
            else:
                suspect = observation_paths[(profile_name, row, transform)]
            observations.append(
                _score_observation(
                    index,
                    declaration,
                    suspect,
                    output,
                    source_copy,
                    carrier_key,
                    wrong_carrier_key,
                    context_uuid,
                    original_biases,
                    original_codebook,
                    symmetric_biases,
                    symmetric_codebook,
                )
            )
        _validate_observation_matrix(declared_matrix, observations)
        _physical_instructions(output)

        duration = time.perf_counter() - run_started
        results: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "completed_at_utc": _now(),
            "status": "complete",
            "empirical_only": True,
            "limitations": [
                "One source document and two issued copies per profile.",
                "No physical print/camera result; synthetic blur is only diagnostic.",
                "No theorem probability certification for the inherited keyed sampler or noisy decoded words.",
                "No collusion guarantee, production attribution, novelty, or superiority claim.",
                "Equal nominal carrier area does not imply equal perceptual fidelity.",
                "The local manifest is not independently signed provenance.",
            ],
            "duration_seconds": duration,
            "preparation_seconds": {
                "original_codebook_generation": original_generation_seconds,
                "symmetric_codebook_generation": symmetric_generation_seconds,
            },
            "observation_counts": {
                "total": len(observations),
                "positive": sum(o["kind"] == "positive" for o in observations),
                "unmarked": sum(o["kind"] == "unmarked" for o in observations),
                "wrong-key": sum(o["kind"] == "wrong-key" for o in observations),
                "wrong-context": sum(
                    o["kind"] == "wrong-context" for o in observations
                ),
            },
            "issued_pdfs": issued,
            "transform_timings": transform_timings,
            "observations": observations,
            "profile_transform_summary": _profile_transform_summary(observations),
            "advancement": _advancement(observations, issued),
            "artifact_sha3_256": _artifact_hashes(output),
        }
        _json_write(output / "results.json", results)
        return results
    except Exception as error:
        failure = {
            "schema_version": SCHEMA_VERSION,
            "failed_at_utc": _now(),
            "error_type": type(error).__name__,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "retained_run": True,
        }
        _json_write(output / "failure.json", failure)
        raise


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = run(args.output)
    print(
        json.dumps(
            {
                "status": results["status"],
                "output": str(args.output),
                "duration_seconds": results["duration_seconds"],
                "observation_counts": results["observation_counts"],
                "advancement": results["advancement"],
            },
            sort_keys=True,
            allow_nan=False,
        )
    )


if __name__ == "__main__":
    main()
