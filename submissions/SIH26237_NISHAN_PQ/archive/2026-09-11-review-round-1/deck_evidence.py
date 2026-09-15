#!/usr/bin/env python3
"""Validated evidence summaries and audit notes for the NISHAN-PQ deck."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


PROFILES = ("affine_baseline", "affine_bias_translation")


def _finite(value: Any, field: str, key: tuple[str, str]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{key}: {field} must be a finite number")
    return float(value)


def _accused(value: Any, field: str, key: tuple[str, str]) -> list[int]:
    if not isinstance(value, list) or any(isinstance(item, bool) or not isinstance(item, int) for item in value):
        raise ValueError(f"{key}: {field} must be a list of integer rows")
    if len(value) != len(set(value)):
        raise ValueError(f"{key}: {field} contains duplicate rows")
    return value


def load_physical(path: Path) -> dict[str, Any]:
    """Load and strictly validate the fixed four-capture/two-profile study."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"physical evidence is missing: {path}")
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"physical evidence is unreadable or malformed: {path}: {exc}") from exc
    if not isinstance(data, dict) or data.get("schema") != "nishan.bias-physical-scores/v1":
        raise ValueError("physical evidence has an unsupported schema")

    settings = data.get("settings")
    if not isinstance(settings, dict):
        raise ValueError("physical evidence settings are missing")
    captures = settings.get("captures")
    profiles = settings.get("profiles")
    if not isinstance(captures, list) or len(captures) != 4 or len(set(captures)) != 4:
        raise ValueError("physical evidence must name exactly four unique captures")
    if not isinstance(profiles, list) or set(profiles) != set(PROFILES) or len(profiles) != 2:
        raise ValueError(f"physical evidence must contain the two profiles {PROFILES}")
    historical_threshold = _finite(settings.get("historical_threshold"), "historical_threshold", ("settings", "settings"))

    records = data.get("records")
    if not isinstance(records, list):
        raise ValueError("physical evidence records must be a list")
    by_key: dict[tuple[str, str], dict[str, Any]] = {}
    boundary_failures = 0
    for record in records:
        if not isinstance(record, dict):
            raise ValueError("each physical evidence record must be an object")
        key = (record.get("capture"), record.get("profile"))
        if key in by_key:
            raise ValueError(f"duplicate physical evidence record: {key}")
        if key[0] not in captures or key[1] not in PROFILES:
            raise ValueError(f"unexpected physical record key: {key}")
        status = record.get("status")
        historical = _accused(record.get("historical_accused"), "historical_accused", key)
        conditional = _accused(record.get("conditional_accused"), "conditional_accused", key)
        row0_accused = record.get("row0_accused")
        if not isinstance(row0_accused, bool):
            raise ValueError(f"{key}: row0_accused must be boolean")
        if status == "boundary_failure":
            boundary_failures += 1
            null = record.get("conditional_null")
            threshold = null.get("threshold") if isinstance(null, dict) else None
            if any(record.get(name) is not None for name in ("expected_row", "expected_score", "highest_other_score", "bit_error_fraction")):
                raise ValueError(f"{key}: boundary_failure contains scored values")
            if threshold is not None or historical or conditional or row0_accused:
                raise ValueError(f"{key}: boundary_failure contains an accusation or threshold")
        elif status == "scored":
            expected_row = record.get("expected_row")
            if isinstance(expected_row, bool) or not isinstance(expected_row, int):
                raise ValueError(f"{key}: scored record is missing expected_row")
            expected_score = _finite(record.get("expected_score"), "expected_score", key)
            highest_other = _finite(record.get("highest_other_score"), "highest_other_score", key)
            _finite(record.get("bit_error_fraction"), "bit_error_fraction", key)
            null = record.get("conditional_null")
            if not isinstance(null, dict):
                raise ValueError(f"{key}: scored record is missing conditional_null")
            threshold = _finite(null.get("threshold"), "threshold", key)
            historical_expected = expected_score > historical_threshold
            conditional_expected = expected_score > threshold
            if (expected_row in historical) != historical_expected:
                raise ValueError(f"{key}: historical accusation is inconsistent with score/threshold")
            if (expected_row in conditional) != conditional_expected:
                raise ValueError(f"{key}: conditional accusation is inconsistent with score/threshold")
            if row0_accused != (expected_row == 0 and expected_row in conditional):
                raise ValueError(f"{key}: row0_accused is inconsistent with the saved accusation")
            if any(row != expected_row for row in historical + conditional):
                raise ValueError(f"{key}: saved accusation contains an unexpected competing row")
            if any(row != expected_row for row in historical) and highest_other > historical_threshold:
                raise ValueError(f"{key}: highest competing row and historical accusations are inconsistent")
            if highest_other > threshold and not any(row != expected_row for row in conditional):
                raise ValueError(f"{key}: highest competing row crosses the conditional threshold without accusation")
        else:
            raise ValueError(f"{key}: status must be scored or boundary_failure")
        by_key[key] = record

    if len(records) != 8:
        raise ValueError("physical evidence must contain exactly eight records")

    expected_keys = {(capture, profile) for capture in captures for profile in PROFILES}
    if set(by_key) != expected_keys:
        missing = sorted(expected_keys - set(by_key))
        raise ValueError(f"physical evidence records do not cover every capture/profile; missing {missing}")

    def recovered(profile: str) -> int:
        return sum(
            record["status"] == "scored"
            and record["expected_row"] in record["conditional_accused"]
            for (capture, name), record in by_key.items()
            if name == profile
        )

    historical_captures = {
        capture
        for (capture, _profile), record in by_key.items()
        if record["status"] == "scored" and record["expected_row"] in record["historical_accused"]
    }
    return {
        "source": str(path),
        "captures": len(captures),
        "capture_names": tuple(captures),
        "profiles": {profile: {capture: by_key[(capture, profile)] for capture in captures} for profile in PROFILES},
        "records": tuple(by_key[key] for key in sorted(by_key)),
        "historical_recovered": len(historical_captures),
        "baseline_recovered": recovered("affine_baseline"),
        "refined_recovered": recovered("affine_bias_translation"),
        "boundary_failures": boundary_failures,
        "historical_threshold": historical_threshold,
    }


def _record(physical: dict[str, Any], capture: str, profile: str) -> dict[str, Any]:
    return physical["profiles"][profile][capture]


def speaker_notes(
    physical: dict[str, Any],
    *,
    team_id: str,
    team_name: str,
    repository_url: str,
    digital: dict[str, Any],
) -> list[str]:
    """Return the six-slide audit record embedded in and exported from the deck."""
    latest = _record(physical, "akshay3.jpeg", "affine_bias_translation")
    baseline = _record(physical, "akshay3.jpeg", "affine_baseline")
    akshay2 = _record(physical, "akshay2.jpeg", "affine_bias_translation")
    common = (
        f"Team ID: {team_id}; team name: {team_name}; repository: {repository_url}. "
        "Status date: 11 September 2026. This is an audit record, not marketing copy."
    )
    return [
        "\n".join([
            "Slide 1 — scope and official requirements",
            common,
            "R1: Unique invisible watermark at decryption — demonstrated on the controlled release path; the trusted viewer and allocation-race caveats remain.",
            "R2: Recipient/session specificity — each release has an explicit session and row; initial row allocation can still race.",
            f"R3: Visually identical / forensically distinct — five PDFs preserve extracted text and average {digital['psnr_mean']:.2f} dB PSNR; this is not universal invisibility.",
            "P22: Team ID, registered team name and repository URL remain explicit placeholders unless supplied through the build CLI; strict verification then fails.",
        ]),
        "\n".join([
            "Slide 2 — workflow and extraction evidence",
            "R9: Extract mark from leak — digital fixtures recover, while shipped physical evidence is historical 0/4 and experimental 1/4 per profile; this is not robust deployment.",
            f"P10: Physical evidence is historical {physical['historical_recovered']}/{physical['captures']} and experimental {physical['baseline_recovered']}/{physical['captures']} in each profile, with the same akshay3 capture recovered in both—not two recovered captures. Latest akshay3 is {latest['expected_score']:.3f} vs {latest['conditional_null']['threshold']:.3f}; baseline is {baseline['expected_score']:.3f} vs {baseline['conditional_null']['threshold']:.3f}. akshay2 latest is {akshay2['expected_score']:.3f} vs {akshay2['conditional_null']['threshold']:.3f}; neither first capture recovered, refinement adds no capture, and {physical['boundary_failures']} boundary failures remain failures. These are visual-code-row results on one printed single-page public fixture, not end-to-end signed physical attribution or independent documents.",
            f"P11: The {digital['jpeg_exact']}/{digital['jpeg_trials']} end-to-end JPEG-Q55 runs are one person across 30 accumulated issued sessions (rows 0..29); other-issued score is null once and non-null 29 times, not a 20-person test.",
            "P12: All 30 end-to-end trials reuse the same document, authority secret and codebook; no independent-document or independent-authority inference follows.",
            f"P13: The 30-codebook × 4-strategy study has {digital['code_cases']} code-level cases; it is not carrier, PDF or physical evidence.",
            f"Digital context: all {digital['roster_rows']:,} rows were scored per session; {digital['jpeg_false']} extra row was accused; mean {digital['jpeg_mean']:.3f}, population SD {digital['jpeg_sd']:.3f}.",
            "Sources: artifacts/nishan/end-to-end-jpeg-trials.json; artifacts/nishan/tardos-independent-codebook-study.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.",
        ]),
        "\n".join([
            "Slide 3 — architecture, binding and audit limits",
            "R4: Cryptographic binding to recipient identity — enrollment-bound prototype receipts are checked; identity and key custody remain a deployment assumption.",
            "R5: Recipient's own private signing key — ML-DSA signing is demonstrated, but exclusive human custody of that key is unproven.",
            "R6: NIST PQC KEX/signatures — ML-KEM-768 and ML-DSA-65 are used, with no classical fallback in the measured path.",
            "R7: Blockchain/DLT audit — only a local, co-located 3-of-4 quorum demonstrator is implemented.",
            "R8: No single administrator can alter/delete history — NOT MET; independent key/peer custody and an enforced witness are absent.",
            "R10: Ledger lookup — implemented for available valid records, but coordinated valid-prefix rollback can erase the association unless the separate witness is consulted.",
            "P1: A separate witness detects the recorded rollback; trace/release do not enforce it, so integration alone does not prevent or recover deletion.",
            "P2: Allocation race — append locks start too late; protect the initial read through commit and avoid nested lock reacquisition.",
            "P3: A rasterized transplant bypasses layout corroboration; the parser already rejects renamed or prefixed PDF content masquerading as a raster/image.",
            "P4: Insufficient 126-symbol layout capacity disables that protection; shortness is only one cause. Fail/restrict release policy is proposed, not implemented.",
            "P5: The authority can regenerate both carriers for an existing signed session without forging a fresh recipient signature.",
            "P6: Removing both carriers leaves readable content and no attribution signal on the tested fixture.",
            "P7: The trusted viewer can access clean plaintext before marking; ordinary output is released only after commit.",
            "P8: Non-blind extraction requires the retained original and the correct version.",
            "P17: Witness capability remains a separate audit tool, not enforced trace-path protection.",
            "P18: Unconditional transplant-abstention is false for raster or low-capacity paths where layout corroboration is unavailable.",
            "Carrier correction (unnumbered): tardos_carrier.py uses fixed 6x6 Tardos templates; watermark.pattern() is not the carrier, and shorter code does not enlarge blocks.",
            "Sources: artifacts/nishan/measured-results.json; artifacts/nishan/tardos-pdf-benchmark.json.",
        ]),
        "\n".join([
            "Slide 4 — feasibility and unresolved risks",
            "R11: Verifiable associated recipient/event — signature checks work; authority framing and copy-to-human inference limits remain.",
            "P9: Evidence identifies a session/copy association, not which human intentionally leaked it.",
            "P14: Signed-PDF preservation is an expected compatibility issue because changed bytes normally invalidate signatures; damage to tagged PDF structure is untested, not demonstrated.",
            "P15: Main published experiments are single-page. Page loops exist in code, but there is no validated multi-page benchmark.",
            "P16: This task corrects PPT/PDF/verifier stale physical-pending wording only; other historical prose is not claimed updated.",
            "P19: Registration and 1,000-row scoring do not prove photo robustness; fine cell alignment and measured few-thousand-symbol physical capacity remain unresolved.",
            "P20: Co-located quorum is a real limitation and was already partly disclosed on slide 4; it is not administrator-resistant DLT.",
            "P21: No Git repository was initialized. Local version history and publishing are distinct actions; controller backups are retained.",
            "Additional limits: requiring current layout on every raster would lose legitimate screenshot/JPEG verdicts; no zero-operational-loss policy, 35 dB invisibility guarantee or population safety rate is claimed.",
        ]),
        "\n".join([
            "Slide 5 — operational value and remaining requirements",
            "R12: Offline/air-gapped operation — demonstrated in a local architecture, not an audited hardened deployment.",
            "R13: No cloud KMS — the implemented workflow has no required external KMS dependency.",
            "R14: No public blockchain — the local demonstrator has no public-chain dependency.",
            "Gate 1: security boundaries and claims. Gate 2: independent documents, keys, recipients, signed/tagged PDFs and negative attacks. Gate 3: held-out physical comparisons at matched visibility/security budgets.",
            "Required future scope: multi-page material, protected key custody, external checkpoints, release-bound policy and real printer/camera validation. This is investigative assistance, not operational accusation readiness.",
        ]),
        "\n".join([
            "Slide 6 — research boundary and sources",
            "P23: The stray file '=4.11' is retained outside presentation scope because this update is non-destructive; it was not silently deleted.",
            "P24: Novelty is unestablished. TRACE concerns trajectory watermarking, physical comparators already exist, and set equality has not been shown novel; no competitor-superiority or winning-probability inference is supported.",
            "Parameter context (unnumbered): current n=1000,c=5,epsilon=1e-6 gives m=52500; roster-only n=20 gives m=42500; n=20,c=4,epsilon=1e-3 gives m=16000 but changes three assumptions. Rows are sessions. Ideal symmetric m=12331 is a separate audit requiring another decoder and implementation proof, not physical evidence or novelty.",
            "Shorter-code and stronger/lower-frequency carrier ideas remain unvalidated hypotheses.",
            "URLs: https://www.sih.gov.in/sih2026PS ; https://arxiv.org/abs/2607.08400 (TRACE is LLM-agent trajectories, not direct PDF physical comparison) ; https://www.matthewtancik.com/stegastamp ; https://arxiv.org/abs/2304.12682 ; https://doi.org/10.1145/3494106.3528674 ; https://www.renyi.hu/~tardos/fingerprint.pdf ; https://doi.org/10.1109/49.464718 ; https://doi.org/10.1109/83.951542 ; https://doi.org/10.1109/ICIP.2001.958536 ; https://csrc.nist.gov/pubs/fips/203/final ; https://csrc.nist.gov/pubs/fips/204/final.",
            "Evidence paths: artifacts/nishan/measured-results.json; artifacts/nishan/tardos-pdf-benchmark.json; artifacts/nishan/tardos-independent-codebook-study.json; artifacts/nishan/end-to-end-jpeg-trials.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.",
            common,
        ]),
    ]
