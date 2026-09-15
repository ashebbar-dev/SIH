#!/usr/bin/env python3
"""Run the frozen prospective orthogonal-authenticator carrier study once."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import secrets
import shutil
import sys
import time
import traceback
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
import PIL
import pymupdf as fitz
from PIL import Image

from carrier import (
    BLOCK_SIZE,
    DPI,
    PLACEMENTS,
    PROFILE,
    PROTOCOL,
    REPEATS,
    STRENGTH,
    SYMBOLS,
    AuthPlan,
    canonical_context,
    copy_observed_overlays,
    decode,
    embed_auth,
    make_plan,
    residual_blocks,
)
from nishan import layout_tag, pqc, registration, tardos, tardos_carrier, watermark


WORKSPACE = Path(__file__).resolve().parents[3]
SOURCE_A = WORKSPACE / "artifacts/nishan/synthetic-source.pdf"
COALITIONS = (1, 2, 3, 5)
ROWS = tuple(range(5))
TARDOS_CONTEXT_PREFIX = "nishan-auth-carrier-study/tardos/v1|"
FIXED_Z = 2100.0


@dataclass
class DocumentState:
    name: str
    source: Path
    source_sha3_256: str
    authority_secret: bytes
    tardos_context: str
    config: tardos.Parameters
    biases: np.ndarray
    codebook: np.ndarray
    tardos_order: np.ndarray
    tardos_orientation: np.ndarray
    auth_secrets: list[bytes]
    public_key_hashes: list[str]
    sessions: list[str]
    contexts: list[str]
    plans: list[AuthPlan]
    wrong_secrets: list[bytes]
    changed_session: str
    shapes: list[tuple[int, int]]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha3_file(path: Path) -> str:
    digest = hashlib.sha3_256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha3_bytes(value: bytes) -> str:
    return hashlib.sha3_256(value).hexdigest()


def _array_sha3(array: np.ndarray, dtype: str) -> str:
    return _sha3_bytes(np.ascontiguousarray(array, dtype=dtype).tobytes())


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _finite_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _finite_json(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_finite_json(item) for item in value]
    if isinstance(value, np.generic):
        return _finite_json(value.item())
    if isinstance(value, float) and not np.isfinite(value):
        if np.isnan(value):
            return "unavailable:nan"
        return "unavailable:+infinity" if value > 0 else "unavailable:-infinity"
    return value


def _write_json(path: Path, value: Any, *, private: bool = False) -> None:
    payload = json.dumps(
        _finite_json(value), sort_keys=True, indent=2, allow_nan=False
    ) + "\n"
    path.write_text(payload, encoding="utf-8")
    if private:
        os.chmod(path, 0o600)


def _pdf_text(path: Path) -> str:
    with fitz.open(path) as document:
        return "\f".join(page.get_text() for page in document)


def _text_observation(path: Path) -> dict[str, Any]:
    text = _pdf_text(path)
    return {
        "file_sha256": _sha256(path),
        "text_sha3_256": _sha3_bytes(text.encode("utf-8")),
        "text": text,
    }


def _create_fixture_b(path: Path, extracted_text_path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=fitz.paper_rect("a4").width, height=fitz.paper_rect("a4").height)
    page.insert_text((48, 48), "AUTHENTICATOR RESEARCH FIXTURE B", fontname="helv", fontsize=16)
    page.insert_text(
        (48, 72),
        "Synthetic logistics record - not operational data",
        fontname="helv",
        fontsize=11,
    )
    for number in range(1, 25):
        if number % 2:
            line = f"Item {number:02d} | quantity 120 | bay 04 | release 09:30"
        else:
            line = f"Check {number:02d}: verify seal, reference number, and dispatch count."
        page.insert_text((48, 100 + (number - 1) * 17), line, fontname="helv", fontsize=10)
    left, top, right, bottom = 48.0, 525.0, 547.0, 735.0
    for x in np.linspace(left, right, 5):
        page.draw_line((float(x), top), (float(x), bottom), width=0.7)
    for y in np.linspace(top, bottom, 8):
        page.draw_line((left, float(y)), (right, float(y)), width=0.7)
    headings = ("Record", "Status", "Owner", "Checkpoint")
    for index, heading in enumerate(headings):
        page.insert_text((left + index * (right - left) / 4 + 5, top + 18), heading, fontname="helv", fontsize=9)
    for row in range(1, 7):
        values = (f"R-{row:02d}", "research", "unassigned", f"C-{row:02d}")
        for column, value in enumerate(values):
            page.insert_text(
                (left + column * (right - left) / 4 + 5, top + 18 + row * 27),
                value,
                fontname="helv",
                fontsize=8,
            )
    document.save(path, deflate=True)
    document.close()
    extracted_text_path.write_text(_pdf_text(path), encoding="utf-8")


def _write_secret(path: Path, value: bytes) -> None:
    path.write_bytes(value)
    os.chmod(path, 0o600)


def _plan_manifest(plan: AuthPlan) -> dict[str, str]:
    return {
        "raw_bits_sha3_256": _array_sha3(plan.raw_bits, "u1"),
        "encoded_bits_sha3_256": _array_sha3(plan.encoded_bits, "u1"),
        "positions_sha3_256": _array_sha3(plan.positions, "<i8"),
        "orientations_sha3_256": _array_sha3(plan.orientations, "u1"),
        "polarities_sha3_256": _array_sha3(plan.polarities, "i1"),
    }


def _prepare_document(
    name: str,
    source: Path,
    root: Path,
) -> tuple[DocumentState, dict[str, Any]]:
    print(f"[{name}] generating fixed inputs and fresh material", flush=True)
    material_dir = root / "material" / name
    material_dir.mkdir(parents=True)
    source_hash = _sha3_file(source)
    authority = secrets.token_bytes(32)
    _write_secret(material_dir / "authority-secret.bin", authority)
    config = tardos.parameters(1000, 5, 1e-6)
    if config.code_length != SYMBOLS or config.threshold != FIXED_Z:
        raise RuntimeError("current Tardos helper does not match the frozen profile")
    tardos_context = TARDOS_CONTEXT_PREFIX + source_hash
    biases, codebook = tardos.generate_keyed(config, authority, tardos_context)
    pages, _ = watermark.load_pages(source, dpi=DPI)
    shapes = [page.shape[:2] for page in pages]
    capacity = sum((height // BLOCK_SIZE) * (width // BLOCK_SIZE) for height, width in shapes)
    if len(pages) != 1:
        raise ValueError(f"{name} must be exactly one page")
    if capacity < SYMBOLS:
        raise ValueError(f"{name} capacity {capacity} is below {SYMBOLS}")
    order, orientation, _ = tardos_carrier._plan(
        authority, tardos_context, capacity, SYMBOLS
    )

    auth_secrets: list[bytes] = []
    public_key_hashes: list[str] = []
    sessions: list[str] = []
    contexts: list[str] = []
    plans: list[AuthPlan] = []
    row_material: list[dict[str, Any]] = []
    for row in ROWS:
        recipient_secret = secrets.token_bytes(32)
        secret_path = material_dir / f"auth-secret-row-{row}.bin"
        _write_secret(secret_path, recipient_secret)
        private_key = material_dir / f"ml-dsa-65-row-{row}-private.pem"
        public_key = material_dir / f"ml-dsa-65-row-{row}-public.pem"
        pqc.generate_keypair("ML-DSA-65", private_key, public_key)
        recipient_hash = _sha3_file(public_key)
        session = str(uuid.uuid4())
        context = canonical_context(source_hash, recipient_hash, session, row)
        plan = make_plan(recipient_secret, context, order, orientation)
        auth_secrets.append(recipient_secret)
        public_key_hashes.append(recipient_hash)
        sessions.append(session)
        contexts.append(context)
        plans.append(plan)
        row_material.append(
            {
                "row": row,
                "session_id": session,
                "context": context,
                "auth_secret_sha3_256": _sha3_bytes(recipient_secret),
                "private_key_sha256": _sha256(private_key),
                "public_key_sha256": _sha256(public_key),
                "public_key_sha3_256": recipient_hash,
                "plan": _plan_manifest(plan),
            }
        )
    wrong_secrets = [secrets.token_bytes(32) for _ in range(100)]
    _write_secret(material_dir / "wrong-secrets.bin", b"".join(wrong_secrets))
    changed_session = str(uuid.uuid4())
    private_material = {
        "warning": "NON-PRODUCTION RESEARCH MATERIAL. DO NOT SUBMIT OR PUBLISH. CONTAINS ALL EXPERIMENTAL SECRETS.",
        "document": name,
        "source_sha3_256": source_hash,
        "authority_secret_sha3_256": _sha3_bytes(authority),
        "tardos_context": tardos_context,
        "changed_session_control": changed_session,
        "rows": row_material,
        "wrong_secret_sha3_256": [_sha3_bytes(value) for value in wrong_secrets],
    }
    _write_json(material_dir / "material.json", private_material, private=True)
    (material_dir / "DO_NOT_SHARE.txt").write_text(
        "NON-PRODUCTION RESEARCH MATERIAL. DO NOT SUBMIT OR PUBLISH.\n",
        encoding="ascii",
    )
    state = DocumentState(
        name=name,
        source=source,
        source_sha3_256=source_hash,
        authority_secret=authority,
        tardos_context=tardos_context,
        config=config,
        biases=biases,
        codebook=codebook,
        tardos_order=order,
        tardos_orientation=orientation,
        auth_secrets=auth_secrets,
        public_key_hashes=public_key_hashes,
        sessions=sessions,
        contexts=contexts,
        plans=plans,
        wrong_secrets=wrong_secrets,
        changed_session=changed_session,
        shapes=shapes,
    )
    public_manifest = {
        "name": name,
        "source_path": str(source.relative_to(root)),
        "source_sha256": _sha256(source),
        "source_sha3_256": source_hash,
        "source_text_sha3_256": _sha3_bytes(_pdf_text(source).encode("utf-8")),
        "page_shapes_hwc": [list(page.shape) for page in pages],
        "capacity_blocks": capacity,
        "authority_secret_sha3_256": _sha3_bytes(authority),
        "tardos_context": tardos_context,
        "biases_sha3_256": _array_sha3(biases, "<f8"),
        "codebook_sha3_256": _array_sha3(codebook, "u1"),
        "tardos_order_sha3_256": _array_sha3(order, "<i8"),
        "tardos_orientation_sha3_256": _array_sha3(orientation, "u1"),
        "changed_session_control": changed_session,
        "rows": row_material,
        "wrong_secret_sha3_256": private_material["wrong_secret_sha3_256"],
    }
    return state, public_manifest


def _source_code_hashes() -> dict[str, str]:
    files = [
        Path(__file__).with_name("carrier.py"),
        Path(__file__),
        Path(__file__).with_name("test_carrier.py"),
        Path(__file__).with_name("README.md"),
        Path(tardos_carrier.__file__),
        Path(layout_tag.__file__),
        Path(watermark.__file__),
        Path(registration.__file__),
        Path(pqc.__file__),
        Path(tardos.__file__),
    ]
    return {str(path.relative_to(WORKSPACE)): _sha256(path) for path in files}


def _pair_metrics(source: Path, marked: Path) -> dict[str, Any]:
    return asdict(tardos_carrier.measure_pdf_pair(source, marked, dpi=DPI))


def _score_tardos(
    state: DocumentState,
    artifact: Path,
    participating: list[int],
) -> dict[str, Any]:
    word, correlations, diagnostics = tardos_carrier.decode_word_with_diagnostics(
        state.source,
        artifact,
        SYMBOLS,
        state.authority_secret,
        state.tardos_context,
        dpi=DPI,
        block_size=BLOCK_SIZE,
    )
    scores = tardos.accusation_scores(state.biases, state.codebook, word)
    selected = tardos.accuse(scores, state.config).astype(int).tolist()
    selected_set = set(selected)
    participating_set = set(participating)
    return {
        "fixed_threshold_z": FIXED_Z,
        "selected_rows": selected,
        "participating_rows": participating,
        "selected_participating_rows": sorted(selected_set & participating_set),
        "selected_nonparticipating_rows": sorted(selected_set - participating_set),
        "all_1000_scores": scores.tolist(),
        "correlations_sha3_256": _array_sha3(correlations, "<f8"),
        "marking_condition": tardos_carrier.marking_condition_errors(
            word, state.codebook[participating]
        ),
        "registration": diagnostics,
    }


def _auth_candidates(blocks: np.ndarray, plans: list[AuthPlan]) -> list[dict[str, Any]]:
    return [{"row": row, **decode(blocks, plan)} for row, plan in enumerate(plans)]


def _make_png(source: Path, destination: Path) -> None:
    pages, _ = watermark.load_pages(source, dpi=DPI)
    if len(pages) != 1:
        raise ValueError("transform inputs must be one page")
    Image.fromarray(pages[0]).save(destination, format="PNG")


def _make_jpeg(source: Path, destination: Path) -> None:
    pages, _ = watermark.load_pages(source, dpi=DPI)
    if len(pages) != 1:
        raise ValueError("transform inputs must be one page")
    Image.fromarray(pages[0]).save(
        destination, format="JPEG", quality=55, optimize=True
    )


def _artifact_record(path: Path) -> dict[str, Any]:
    return {"path": str(path), "sha256": _sha256(path)}


def _run_document(state: DocumentState, root: Path) -> dict[str, Any]:
    started = time.monotonic()
    document_dir = root / "documents" / state.name
    copies_dir = document_dir / "copies"
    attacks_dir = document_dir / "transforms"
    copies_dir.mkdir(parents=True)
    attacks_dir.mkdir(parents=True)
    baselines: list[Path] = []
    auth_copies: list[Path] = []
    fidelity: list[dict[str, Any]] = []
    print(f"[{state.name}] embedding ten matched copies", flush=True)
    for row in ROWS:
        baseline = copies_dir / f"row-{row}-tardos-only.pdf"
        marked = copies_dir / f"row-{row}-tardos-plus-auth.pdf"
        tardos_carrier.embed_pdf(
            state.source,
            baseline,
            state.codebook[row],
            state.authority_secret,
            state.tardos_context,
            strength=STRENGTH,
            dpi=DPI,
            block_size=BLOCK_SIZE,
        )
        embed_auth(baseline, marked, state.plans[row], state.shapes)
        baselines.append(baseline)
        auth_copies.append(marked)
        fidelity.extend(
            [
                {
                    "row": row,
                    "channel": "tardos-only",
                    "artifact": _artifact_record(baseline),
                    "measurement": _pair_metrics(state.source, baseline),
                },
                {
                    "row": row,
                    "channel": "tardos-plus-auth",
                    "artifact": _artifact_record(marked),
                    "measurement": _pair_metrics(state.source, marked),
                },
            ]
        )

    cases: list[dict[str, Any]] = []
    for count in COALITIONS:
        participating = list(range(count))
        for channel, copies in (("tardos-only", baselines), ("tardos-plus-auth", auth_copies)):
            average = attacks_dir / f"{channel}-coalition-{count}-average.png"
            jpeg = attacks_dir / f"{channel}-coalition-{count}-average-q55.jpg"
            if count == 1:
                _make_png(copies[0], average)
            else:
                watermark.average_collusion(copies[:count], average, dpi=DPI)
            _make_jpeg(average, jpeg)
            for transform, artifact in (("average-png", average), ("average-jpeg-q55", jpeg)):
                case_started = time.monotonic()
                print(
                    f"[{state.name}] {channel} coalition={count} {transform}",
                    flush=True,
                )
                record: dict[str, Any] = {
                    "case_id": f"{channel}/coalition-{count}/{transform}",
                    "channel": channel,
                    "coalition_size": count,
                    "participating_rows": participating,
                    "transform": transform,
                    "artifact": _artifact_record(artifact),
                    "tardos": _score_tardos(state, artifact, participating),
                }
                if channel == "tardos-plus-auth":
                    blocks = residual_blocks(state.source, artifact)
                    record["auth_candidates"] = _auth_candidates(blocks, state.plans)
                    record["expected_auth_rows"] = participating
                    record["extra_exact_auth_rows"] = [
                        item["row"]
                        for item in record["auth_candidates"]
                        if item["exact_match"] and item["row"] not in participating
                    ]
                record["runtime_seconds"] = round(time.monotonic() - case_started, 6)
                cases.append(record)

    print(f"[{state.name}] direct, changed-context and 100 wrong-key controls", flush=True)
    direct_controls: list[dict[str, Any]] = []
    for label, artifact in [("unmarked-source", state.source)] + [
        (f"tardos-only-row-{row}", path) for row, path in enumerate(baselines)
    ]:
        blocks = residual_blocks(state.source, artifact)
        direct_controls.append(
            {
                "artifact_label": label,
                "artifact": _artifact_record(artifact),
                "auth_candidates": _auth_candidates(blocks, state.plans),
            }
        )

    row_zero_blocks = residual_blocks(state.source, auth_copies[0])
    other_source_hash = None  # filled by the caller before this function
    changed_context_controls: list[dict[str, Any]] = []
    # The source-hash value is injected on the state for an actual other fixture hash.
    changed_source_hash = getattr(state, "changed_source_hash")
    changed_definitions = [
        (
            "changed-source-hash",
            canonical_context(
                changed_source_hash,
                state.public_key_hashes[0],
                state.sessions[0],
                0,
            ),
        ),
        (
            "fresh-session-id",
            canonical_context(
                state.source_sha3_256,
                state.public_key_hashes[0],
                state.changed_session,
                0,
            ),
        ),
        (
            "another-recipient-public-key",
            canonical_context(
                state.source_sha3_256,
                state.public_key_hashes[1],
                state.sessions[0],
                0,
            ),
        ),
    ]
    for label, context in changed_definitions:
        candidate_plan = make_plan(
            state.auth_secrets[0], context, state.tardos_order, state.tardos_orientation
        )
        changed_context_controls.append(
            {"control": label, "context": context, "observation": decode(row_zero_blocks, candidate_plan)}
        )

    wrong_key_controls: list[dict[str, Any]] = []
    for index, wrong_secret in enumerate(state.wrong_secrets):
        wrong_plan = make_plan(
            wrong_secret,
            state.contexts[0],
            state.tardos_order,
            state.tardos_orientation,
        )
        wrong_key_controls.append(
            {
                "wrong_key_index": index,
                "secret_sha3_256": _sha3_bytes(wrong_secret),
                "observation": decode(row_zero_blocks, wrong_plan),
            }
        )
    return {
        "name": state.name,
        "fidelity": fidelity,
        "positive_transform_cases": cases,
        "negative_controls": {
            "direct": direct_controls,
            "changed_context": changed_context_controls,
            "wrong_key": wrong_key_controls,
        },
        "copy_paths": {
            "baselines": [str(path) for path in baselines],
            "auth": [str(path) for path in auth_copies],
        },
        "runtime_seconds": round(time.monotonic() - started, 6),
    }


def _modify_fixture(source: Path, destination: Path) -> dict[str, Any]:
    document = fitz.open(source)
    try:
        page = document[0]
        matches = page.search_for("quantity 120")
        if not matches:
            raise RuntimeError("fixture B contains no quantity 120 text to modify")
        rectangle = matches[0]
        page.add_redact_annot(rectangle, fill=(1, 1, 1))
        page.apply_redactions()
        page.insert_text(
            (rectangle.x0, rectangle.y1 - 1.5),
            "quantity 920",
            fontname="helv",
            fontsize=10,
        )
        destination.parent.mkdir(parents=True, exist_ok=True)
        document.save(destination, garbage=0, clean=False, deflate=True)
    finally:
        document.close()
    source_text = _pdf_text(source)
    target_text = _pdf_text(destination)
    if source_text == target_text or "quantity 920" not in target_text:
        raise RuntimeError("modified fixture did not produce the required text change")
    if source.read_bytes() == destination.read_bytes():
        raise RuntimeError("modified fixture bytes unexpectedly equal source bytes")
    return {
        "changed_occurrences": 1,
        "source": _text_observation(source),
        "target": _text_observation(destination),
        "extracted_text_differs": source_text != target_text,
        "file_bytes_differ": source.read_bytes() != destination.read_bytes(),
    }


def _copied_overlay_attack(
    state: DocumentState,
    document_results: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    print("[source-b] copied-overlay falsification attack", flush=True)
    attack_dir = root / "documents/source-b/copied-overlay-attack"
    attack_dir.mkdir(parents=True)
    donor = Path(document_results["copy_paths"]["auth"][0])
    target = attack_dir / "content-modified-target.pdf"
    copied_pdf = attack_dir / "observed-overlays-on-modified-target.pdf"
    copied_jpeg = attack_dir / "observed-overlays-on-modified-target-q55.jpg"
    modification = _modify_fixture(state.source, target)
    # The helper invocation below intentionally carries only three paths.
    copy_observed_overlays(donor, target, copied_pdf)
    _make_jpeg(copied_pdf, copied_jpeg)
    with fitz.open(donor) as donor_document, fitz.open(copied_pdf) as copied_document:
        donor_image_counts = [len(page.get_images(full=True)) for page in donor_document]
        copied_image_counts = [len(page.get_images(full=True)) for page in copied_document]

    changed_source_context = canonical_context(
        _sha3_file(target),
        state.public_key_hashes[0],
        state.sessions[0],
        0,
    )
    changed_source_plan = make_plan(
        state.auth_secrets[0],
        changed_source_context,
        state.tardos_order,
        state.tardos_orientation,
    )
    artifact_results: list[dict[str, Any]] = []
    for transform, artifact in (("copied-pdf", copied_pdf), ("copied-jpeg-q55", copied_jpeg)):
        case_started = time.monotonic()
        print(f"[source-b] copied-overlay {transform}", flush=True)
        blocks = residual_blocks(state.source, artifact)
        candidates = _auth_candidates(blocks, state.plans)
        artifact_results.append(
            {
                "transform": transform,
                "artifact": _artifact_record(artifact),
                "tardos": _score_tardos(state, artifact, [0]),
                "auth_candidates_under_issued_donor_contexts": candidates,
                "exact_auth_rows": [item["row"] for item in candidates if item["exact_match"]],
                "donor_row_exact_match": bool(candidates[0]["exact_match"]),
                "donor_secret_changed_source_context": {
                    "context": changed_source_context,
                    "observation": decode(blocks, changed_source_plan),
                },
                "runtime_seconds": round(time.monotonic() - case_started, 6),
            }
        )
    donor_observation = _text_observation(donor)
    target_observation = _text_observation(target)
    output_observation = _text_observation(copied_pdf)
    distinctions = {
        "donor_vs_target_file_hash_mismatch": donor_observation["file_sha256"] != target_observation["file_sha256"],
        "donor_vs_output_file_hash_mismatch": donor_observation["file_sha256"] != output_observation["file_sha256"],
        "target_vs_output_file_hash_mismatch": target_observation["file_sha256"] != output_observation["file_sha256"],
        "donor_vs_target_text_mismatch": donor_observation["text_sha3_256"] != target_observation["text_sha3_256"],
        "donor_vs_output_text_mismatch": donor_observation["text_sha3_256"] != output_observation["text_sha3_256"],
        "target_vs_output_text_equal": target_observation["text_sha3_256"] == output_observation["text_sha3_256"],
    }
    return {
        "helper_inputs": [str(donor), str(target), str(copied_pdf)],
        "helper_received_secrets_or_plans": False,
        "modification": modification,
        "donor": donor_observation,
        "target": target_observation,
        "copied_pdf": output_observation,
        "image_object_counts": {"donor": donor_image_counts, "copied_pdf": copied_image_counts},
        "distinctions": distinctions,
        "artifacts": artifact_results,
    }


def _gate_results(document_results: list[dict[str, Any]], attack: dict[str, Any]) -> dict[str, Any]:
    participating: list[bool] = []
    nonparticipating: list[bool] = []
    direct: list[bool] = []
    changed: list[bool] = []
    wrong: list[bool] = []
    positive_artifacts = 0
    for document in document_results:
        for case in document["positive_transform_cases"]:
            if case["channel"] != "tardos-plus-auth":
                continue
            positive_artifacts += 1
            expected = set(case["expected_auth_rows"])
            for candidate in case["auth_candidates"]:
                if candidate["row"] in expected:
                    participating.append(bool(candidate["exact_match"]))
                else:
                    nonparticipating.append(not bool(candidate["exact_match"]))
        controls = document["negative_controls"]
        direct.extend(
            not bool(candidate["exact_match"])
            for artifact in controls["direct"]
            for candidate in artifact["auth_candidates"]
        )
        changed.extend(
            not bool(control["observation"]["exact_match"])
            for control in controls["changed_context"]
        )
        wrong.extend(
            not bool(control["observation"]["exact_match"])
            for control in controls["wrong_key"]
        )
    gate_a = all(participating + nonparticipating + direct + changed + wrong)
    transplant_rejections = [
        not bool(item["donor_row_exact_match"]) for item in attack["artifacts"]
    ]
    return {
        "gate_a": gate_a,
        "gate_a_components": {
            "positive_artifacts": positive_artifacts,
            "participating_exact": sum(participating),
            "participating_total": len(participating),
            "nonparticipating_rejected": sum(nonparticipating),
            "nonparticipating_total": len(nonparticipating),
            "direct_negative_rejected": sum(direct),
            "direct_negative_total": len(direct),
            "changed_context_rejected": sum(changed),
            "changed_context_total": len(changed),
            "wrong_key_rejected": sum(wrong),
            "wrong_key_total": len(wrong),
        },
        "gate_b": all(transplant_rejections),
        "gate_b_components": {
            "copied_overlay_donor_tag_rejected": sum(transplant_rejections),
            "copied_overlay_artifacts": len(transplant_rejections),
        },
    }


def _all_existing_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): _sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file() and path.name not in {"results.json", "failure.json"}
    }


def run(output: Path) -> None:
    overall_started = time.monotonic()
    support = pqc.support()
    if not support.ml_dsa_65:
        raise RuntimeError(
            f"ML-DSA-65 is unavailable in {support.openssl_version}; study cannot run"
        )
    sources_dir = output / "sources"
    sources_dir.mkdir(parents=True)
    if not SOURCE_A.is_file():
        raise FileNotFoundError(f"missing required source {SOURCE_A}")
    source_a = sources_dir / "source-a-synthetic.pdf"
    source_b = sources_dir / "source-b-fixed-fixture.pdf"
    shutil.copyfile(SOURCE_A, source_a)
    _create_fixture_b(source_b, sources_dir / "source-b-extracted-text.txt")

    states: list[DocumentState] = []
    document_manifests: list[dict[str, Any]] = []
    for name, source in (("source-a", source_a), ("source-b", source_b)):
        state, document_manifest = _prepare_document(name, source, output)
        states.append(state)
        document_manifests.append(document_manifest)
    # Use the other actual fixed fixture hash for each changed-source control.
    states[0].changed_source_hash = states[1].source_sha3_256
    states[1].changed_source_hash = states[0].source_sha3_256

    manifest = {
        "study": "NISHAN orthogonal authenticator prospective carrier falsification gate",
        "scope": "isolated carrier-only research; not production security integration",
        "created_at_utc": _utc_now(),
        "configuration": {
            "dpi": DPI,
            "block_size": BLOCK_SIZE,
            "tardos": {"n": 1000, "c": 5, "epsilon": 1e-6, "symbols": SYMBOLS, "strength": STRENGTH, "fixed_z": FIXED_Z},
            "auth": {"strength": STRENGTH, "hmac": "HMAC-SHA3-256", "raw_bits": 72, "encoded_bits": 126, "repeats": REPEATS, "placements": PLACEMENTS, "decision": "summed correlation > 0 then Hamming(7,4), exact 72-bit equality"},
            "coalition_prefixes": list(COALITIONS),
            "jpeg_quality": 55,
            "jpeg_optimize": True,
            "protocol": PROTOCOL,
            "profile": PROFILE,
        },
        "documents": document_manifests,
        "source_code_sha256": _source_code_hashes(),
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "openssl": support.openssl_version,
            "packages": {
                "numpy": np.__version__,
                "pymupdf": fitz.VersionBind,
                "pillow": PIL.__version__,
                "opencv": cv2.__version__,
                "cryptography": importlib.metadata.version("cryptography"),
            },
        },
        "premeasurement_manifest_written_at_utc": _utc_now(),
    }
    _write_json(output / "manifest.json", manifest)
    print("[study] premeasurement manifest written", flush=True)

    document_results = [_run_document(state, output) for state in states]
    attack = _copied_overlay_attack(states[1], document_results[1], output)
    gates = _gate_results(document_results, attack)
    results = {
        "study": manifest["study"],
        "completed_at_utc": _utc_now(),
        "documents": document_results,
        "copied_overlay_attack": attack,
        "gates": gates,
        "generated_artifact_sha256": _all_existing_hashes(output),
        "runtime_seconds": round(time.monotonic() - overall_started, 6),
        "interpretation": {
            "gate_a": "limited digital replication only",
            "gate_b": "content-binding hypothesis under observed overlay transplantation",
            "changed_context_boundary": "Rejection under a changed candidate context does not establish rejection of edited content evaluated under the genuine donor context.",
            "security_boundary": "No enrollment, independent custody, escrow, ledger, signature protocol, adjudicator, asymmetric carrier security, physical recovery, population estimate, novelty, superiority, or production claim is established.",
        },
    }
    _write_json(output / "results.json", results)
    print(
        f"[study] complete Gate A={gates['gate_a']} Gate B={gates['gate_b']} runtime={results['runtime_seconds']}s",
        flush=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    output = arguments.output
    if output.exists():
        parser.error(f"refusing to overwrite existing output directory: {output}")
    output.mkdir(parents=True)
    try:
        run(output)
    except BaseException as exc:
        _write_json(
            output / "failure.json",
            {
                "failed_at_utc": _utc_now(),
                "exception_type": type(exc).__name__,
                "exception": str(exc),
                "traceback": traceback.format_exc(),
            },
        )
        raise


if __name__ == "__main__":
    main()
