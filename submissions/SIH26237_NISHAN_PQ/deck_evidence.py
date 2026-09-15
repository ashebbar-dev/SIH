#!/usr/bin/env python3
"""Validated evidence summaries and audit notes for the NISHAN-PQ deck."""

from __future__ import annotations

import json
import hashlib
import math
from pathlib import Path
import re
from typing import Any


PROFILES = ("affine_baseline", "affine_bias_translation")
CAPTURES = ("akshay.jpeg", "akshay1.jpeg", "akshay2.jpeg", "akshay3.jpeg")
EXPECTED_RECOVERY = {profile: {"akshay3.jpeg"} for profile in PROFILES}
EXPECTED_BOUNDARY_FAILURES = {
    ("akshay.jpeg", "affine_bias_translation"),
    ("akshay1.jpeg", "affine_bias_translation"),
}
SAFEGUARD_VERSION = "nishan-selection-safeguards/v1"
EXPECTED_SAFEGUARD_CASES = (
    "concurrent_distinct_sessions_rows",
    "third_release_row",
    "signed_copy_hash_match",
    "clean_pdf_trace",
    "trace_read_only",
    "rendered_transplant_abstains",
    "low_capacity_pdf_abstains",
    "wrong_pin_rejected",
    "rollback_release_rejected",
    "rollback_trace_rejected",
    "checkpoint_failure_no_publication",
    "checkpoint_failure_preserves_existing_output",
)
REQUIRED_SAFEGUARD_HASHES = (
    "prototypes/nishan_pq/nishan/__init__.py",
    "prototypes/nishan_pq/nishan/__main__.py",
    "prototypes/nishan_pq/nishan/cli.py",
    "prototypes/nishan_pq/nishan/core.py",
    "prototypes/nishan_pq/nishan/demo.py",
    "prototypes/nishan_pq/nishan/identity.py",
    "prototypes/nishan_pq/nishan/layout_tag.py",
    "prototypes/nishan_pq/nishan/ledger.py",
    "prototypes/nishan_pq/nishan/live_pdf.py",
    "prototypes/nishan_pq/nishan/pqc.py",
    "prototypes/nishan_pq/nishan/registration.py",
    "prototypes/nishan_pq/nishan/tardos.py",
    "prototypes/nishan_pq/nishan/tardos_carrier.py",
    "prototypes/nishan_pq/nishan/util.py",
    "prototypes/nishan_pq/nishan/watermark.py",
    "prototypes/nishan_pq/nishan/witness.py",
    "prototypes/nishan_pq/tests/test_pdf_format_policy.py",
    "prototypes/nishan_pq/tests/test_release_safeguards.py",
    "prototypes/nishan_pq/tools/demo_release_safeguards.py",
)


def _validate_safeguard_profile(profile: Any) -> None:
    if not isinstance(profile, dict):
        raise ValueError("safeguard profile must be an object")

    def exact_integer(field: str, expected: int) -> None:
        value = profile.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value != expected:
            raise ValueError(f"safeguard profile {field} must be integer {expected}")

    exact_integer("roster_size", 1_000)
    exact_integer("coalition_limit", 5)
    epsilon = profile.get("familywise_epsilon")
    if (
        isinstance(epsilon, bool)
        or not isinstance(epsilon, (int, float))
        or not math.isfinite(epsilon)
        or float(epsilon) != 1e-6
    ):
        raise ValueError("safeguard profile familywise_epsilon must be numeric 1e-6")
    if profile.get("fusion_policy") != "pdf-all-formats-corroboration/v1":
        raise ValueError(
            "safeguard profile fusion_policy must be pdf-all-formats-corroboration/v1"
        )
    expected_text = {
        "fixture": "nishan.demo._sample_pdf; public synthetic one-page PDF",
        "pin_provisioning": (
            "fresh local witness initialization in this demo; independent "
            "provisioning remains a deployment requirement"
        ),
    }
    for field, expected in expected_text.items():
        value = profile.get(field)
        if not isinstance(value, str) or value != expected:
            raise ValueError(f"safeguard profile {field} must match the reviewed fixture")


def _validate_safeguard_observations(cases: dict[str, dict[str, Any]]) -> None:
    hash_pattern = re.compile(r"[0-9a-f]{64}")

    def fail(case: str, message: str) -> None:
        raise ValueError(f"safeguard case {case}: {message}")

    def observed_object(case: str) -> dict[str, Any]:
        observed = cases[case]["observed"]
        if not isinstance(observed, dict):
            fail(case, "observed must be an object")
        return observed

    def required_bool(case: str, obj: dict[str, Any], field: str, expected: bool) -> None:
        value = obj.get(field)
        if not isinstance(value, bool) or value is not expected:
            fail(case, f"{field} must be boolean {expected}")

    def required_int(case: str, obj: dict[str, Any], field: str) -> int:
        value = obj.get(field)
        if isinstance(value, bool) or not isinstance(value, int):
            fail(case, f"{field} must be an integer")
        return value

    def required_text(case: str, obj: dict[str, Any], field: str) -> str:
        value = obj.get(field)
        if not isinstance(value, str) or not value.strip():
            fail(case, f"{field} must be a nonempty string")
        return value

    def required_hash(case: str, obj: dict[str, Any], field: str) -> str:
        value = required_text(case, obj, field)
        if hash_pattern.fullmatch(value) is None:
            fail(case, f"{field} must be 64 lowercase hexadecimal characters")
        return value

    concurrent_name = "concurrent_distinct_sessions_rows"
    concurrent = observed_object(concurrent_name)
    required_bool(concurrent_name, concurrent, "barrier_before_decrypt", True)
    if required_int(concurrent_name, concurrent, "processes") != 2:
        fail(concurrent_name, "processes must be 2")
    rows = concurrent.get("rows")
    if (
        not isinstance(rows, list)
        or len(rows) != 2
        or any(isinstance(row, bool) or not isinstance(row, int) for row in rows)
        or set(rows) != {0, 1}
    ):
        fail(concurrent_name, "rows must be the two distinct integers 0 and 1")
    sessions = concurrent.get("sessions")
    if (
        not isinstance(sessions, list)
        or len(sessions) != 2
        or any(not isinstance(session, str) or not session.strip() for session in sessions)
        or len(set(sessions)) != 2
    ):
        fail(concurrent_name, "sessions must be two distinct nonempty strings")

    third_name = "third_release_row"
    third = observed_object(third_name)
    if required_int(third_name, third, "row") != 2:
        fail(third_name, "row must be 2")
    third_session = required_text(third_name, third, "session")
    if third_session in sessions:
        fail(third_name, "session must differ from both concurrent sessions")

    hash_name = "signed_copy_hash_match"
    copies = cases[hash_name]["observed"]
    if not isinstance(copies, list) or len(copies) != 3:
        fail(hash_name, "observed must contain exactly three signed-copy records")
    copy_sessions: list[str] = []
    for index, copy_record in enumerate(copies):
        if not isinstance(copy_record, dict):
            fail(hash_name, f"record {index} must be an object")
        actual = required_hash(hash_name, copy_record, "actual")
        signed = required_hash(hash_name, copy_record, "signed")
        if actual != signed:
            fail(hash_name, f"record {index} actual hash must equal signed hash")
        copy_sessions.append(required_text(hash_name, copy_record, "session"))
    if len(set(copy_sessions)) != 3 or set(copy_sessions) != set(sessions + [third_session]):
        fail(hash_name, "records must cover the two concurrent and third release sessions")

    clean_name = "clean_pdf_trace"
    clean = observed_object(clean_name)
    attribution = clean.get("attribution")
    if not isinstance(attribution, list) or len(attribution) != 1:
        fail(clean_name, "attribution must contain exactly one selected release")
    selected = attribution[0]
    if not isinstance(selected, dict):
        fail(clean_name, "selected attribution must be an object")
    required_bool(clean_name, selected, "recipient_signature_valid", True)
    required_bool(clean_name, selected, "selected_by_fusion", True)
    selected_index = required_int(clean_name, selected, "fingerprint_user_index")
    if required_text(clean_name, selected, "recipient_id") != "alice":
        fail(clean_name, "selected recipient_id must be alice")
    selected_session = required_text(clean_name, selected, "session_id")
    if selected_session not in sessions:
        fail(clean_name, "selected session must be one of the concurrent releases")
    layout_tag = selected.get("layout_tag")
    if not isinstance(layout_tag, dict):
        fail(clean_name, "selected layout_tag must be an object")
    required_bool(clean_name, layout_tag, "match", True)
    required_bool(clean_name, layout_tag, "suspect_is_pdf", True)
    required_bool(clean_name, layout_tag, "release_channel_available", True)
    decision = clean.get("decision")
    if not isinstance(decision, dict):
        fail(clean_name, "decision must be an object")
    if decision.get("decision") != "corroborated_channels":
        fail(clean_name, "decision must be corroborated_channels")
    required_bool(clean_name, decision, "corroboration_required", True)
    if decision.get("selected_indices") != [selected_index]:
        fail(clean_name, "selected_indices must match the selected attribution")
    witness = clean.get("ledger_witness")
    if not isinstance(witness, dict):
        fail(clean_name, "ledger_witness must be an object")
    required_bool(clean_name, witness, "valid", True)
    required_bool(clean_name, witness, "witness_enforced", True)
    required_hash(clean_name, witness, "witness_public_key_sha3_256")
    if witness.get("ledger_comparison") != "consistent":
        fail(clean_name, "ledger_witness comparison must be consistent")

    read_only_name = "trace_read_only"
    read_only = observed_object(read_only_name)
    before_hash = required_hash(read_only_name, read_only, "before_sha256")
    after_hash = required_hash(read_only_name, read_only, "after_sha256")
    if before_hash != after_hash:
        fail(read_only_name, "before_sha256 must equal after_sha256")

    def validate_abstention(
        case: str, expected_decision: str
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        observed = observed_object(case)
        if observed.get("attribution") != []:
            fail(case, "attribution must be an empty list")
        case_decision = observed.get("decision")
        if not isinstance(case_decision, dict):
            fail(case, "decision must be an object")
        if case_decision.get("decision") != expected_decision:
            fail(case, f"decision must be {expected_decision}")
        required_bool(case, case_decision, "corroboration_required", True)
        if case_decision.get("selected_indices") != []:
            fail(case, "selected_indices must be an empty list")
        lead_indices = case_decision.get("screening_lead_indices")
        if (
            not isinstance(lead_indices, list)
            or not lead_indices
            or any(isinstance(index, bool) or not isinstance(index, int) for index in lead_indices)
        ):
            fail(case, "screening_lead_indices must contain integer research leads")
        leads = observed.get("visual_only_research_leads")
        if not isinstance(leads, list) or not leads:
            fail(case, "visual_only_research_leads must be nonempty")
        for lead in leads:
            if not isinstance(lead, dict):
                fail(case, "each visual-only research lead must be an object")
            required_bool(case, lead, "selected_by_fusion", False)
            required_bool(case, lead, "recipient_signature_valid", True)
        observed_lead_indices = [
            required_int(case, lead, "fingerprint_user_index") for lead in leads
        ]
        if observed_lead_indices != lead_indices:
            fail(case, "research-lead identities must match screening_lead_indices")
        layout_observation = case_decision.get("layout_observation")
        if not isinstance(layout_observation, dict):
            fail(case, "layout_observation must be an object")
        return observed, layout_observation

    _rendered, rendered_layout = validate_abstention(
        "rendered_transplant_abstains", "abstain_missing_layout_channel"
    )
    required_bool(
        "rendered_transplant_abstains", rendered_layout, "suspect_is_pdf", False
    )
    low_name = "low_capacity_pdf_abstains"
    low, low_layout = validate_abstention(
        low_name, "abstain_inadequate_release_capacity"
    )
    required_bool(low_name, low_layout, "suspect_is_pdf", True)
    policy = low.get("signed_fingerprint_policy")
    if not isinstance(policy, dict):
        fail(low_name, "signed_fingerprint_policy must be an object")
    required_bool(low_name, policy, "corroboration_required", True)
    if policy.get("fusion_policy_version") != "pdf-all-formats-corroboration/v1":
        fail(low_name, "fusion_policy_version must be pdf-all-formats-corroboration/v1")
    layout_policy = policy.get("layout_tag")
    if not isinstance(layout_policy, dict):
        fail(low_name, "signed layout_tag policy must be an object")
    required_bool(low_name, layout_policy, "available", False)
    supported = required_int(low_name, layout_policy, "supported_capacity_bits")
    encoded = required_int(low_name, layout_policy, "encoded_bits")
    if supported < 0 or supported >= encoded:
        fail(low_name, "supported capacity must be nonnegative and below encoded bits")

    wrong_pin_name = "wrong_pin_rejected"
    wrong_pin = observed_object(wrong_pin_name)
    required_bool(wrong_pin_name, wrong_pin, "rejected", True)
    required_bool(wrong_pin_name, wrong_pin, "output_exists", False)
    required_text(wrong_pin_name, wrong_pin, "error_type")
    if "pin" not in required_text(wrong_pin_name, wrong_pin, "error").lower():
        fail(wrong_pin_name, "error must identify the pin rejection")

    release_rollback_name = "rollback_release_rejected"
    release_rollback = observed_object(release_rollback_name)
    required_bool(release_rollback_name, release_rollback, "rejected", True)
    required_bool(release_rollback_name, release_rollback, "output_exists", False)
    required_bool(release_rollback_name, release_rollback, "ledger_quorum_valid", True)
    if release_rollback.get("comparison") != "rollback_detected":
        fail(release_rollback_name, "comparison must be rollback_detected")
    required_text(release_rollback_name, release_rollback, "error_type")
    if "rollback" not in required_text(release_rollback_name, release_rollback, "error").lower():
        fail(release_rollback_name, "error must identify rollback")

    trace_rollback_name = "rollback_trace_rejected"
    trace_rollback = observed_object(trace_rollback_name)
    required_bool(trace_rollback_name, trace_rollback, "rejected", True)
    required_text(trace_rollback_name, trace_rollback, "error_type")
    if "rollback" not in required_text(trace_rollback_name, trace_rollback, "error").lower():
        fail(trace_rollback_name, "error must identify rollback")

    for checkpoint_name, expected_existing in (
        ("checkpoint_failure_no_publication", False),
        ("checkpoint_failure_preserves_existing_output", True),
    ):
        checkpoint = observed_object(checkpoint_name)
        required_bool(checkpoint_name, checkpoint, "rejected", True)
        required_bool(checkpoint_name, checkpoint, "destination_preserved", True)
        required_bool(
            checkpoint_name, checkpoint, "existing_destination", expected_existing
        )
        before_length = required_int(checkpoint_name, checkpoint, "before_length")
        after_length = required_int(checkpoint_name, checkpoint, "after_length")
        if after_length != before_length + 1:
            fail(checkpoint_name, "ledger length must increase by one committed record")
        if checkpoint.get("comparison") != "unwitnessed_extension":
            fail(checkpoint_name, "comparison must be unwitnessed_extension")
        required_text(checkpoint_name, checkpoint, "error")
        required_text(checkpoint_name, checkpoint, "error_type")


def validate_safeguard_evidence(evidence: dict) -> dict:
    """Validate the fresh selection-safeguard report against current source.

    The report is accepted only when it represents the exact reviewed scenario
    set, every verdict and the real-PQC readiness check passed, and the required
    source/test/runner hashes still match files in this workspace.
    """
    if not isinstance(evidence, dict):
        raise ValueError("safeguard evidence must be an object")
    if evidence.get("version") != SAFEGUARD_VERSION:
        raise ValueError(f"safeguard evidence version must be {SAFEGUARD_VERSION}")
    if evidence.get("all_passed") is not True:
        raise ValueError("safeguard evidence all_passed verdict must be true")

    cases = evidence.get("cases")
    if not isinstance(cases, list):
        raise ValueError("safeguard evidence cases must be a list")
    names: list[str] = []
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ValueError(f"safeguard case {index} must be an object")
        name = case.get("name")
        # Validate type before hashing or set membership so malformed names
        # consistently raise ValueError rather than leaking TypeError.
        if not isinstance(name, str):
            raise ValueError(f"safeguard case {index} name must be a string")
        if not name:
            raise ValueError(f"safeguard case {index} name must not be empty")
        passed = case.get("passed")
        if not isinstance(passed, bool):
            raise ValueError(f"safeguard case {name} passed verdict must be boolean")
        if passed is not True:
            raise ValueError(f"safeguard case {name} passed verdict is false")
        if "observed" not in case or not isinstance(case["observed"], (dict, list)):
            raise ValueError(f"safeguard case {name} observed result must be an object or list")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("safeguard scenario names contain duplicates")
    expected = set(EXPECTED_SAFEGUARD_CASES)
    actual = set(names)
    if len(names) != len(EXPECTED_SAFEGUARD_CASES) or actual != expected:
        raise ValueError(
            "safeguard scenario coverage must be the exact 12 reviewed cases; "
            f"missing={sorted(expected - actual)}, unexpected={sorted(actual - expected)}"
        )
    cases_by_name = {case["name"]: case for case in cases}
    _validate_safeguard_observations(cases_by_name)

    if evidence.get("pqc_ready") is not True:
        raise ValueError("real PQC readiness must be true")
    pqc = evidence.get("pqc_profile")
    if not isinstance(pqc, dict):
        raise ValueError("PQC profile must be an object")
    if pqc.get("ml_kem_768") is not True:
        raise ValueError("PQC profile must confirm ML-KEM-768")
    if pqc.get("ml_dsa_65") is not True:
        raise ValueError("PQC profile must confirm ML-DSA-65")
    if not isinstance(pqc.get("openssl_version"), str) or not pqc["openssl_version"].strip():
        raise ValueError("PQC profile must record a nonempty OpenSSL version")
    if not isinstance(evidence.get("command"), str) or not evidence["command"].strip():
        raise ValueError("safeguard evidence command must be a nonempty string")
    _validate_safeguard_profile(evidence.get("profile"))
    limitations = evidence.get("limitations")
    if (
        not isinstance(limitations, list)
        or not limitations
        or any(not isinstance(item, str) or not item.strip() for item in limitations)
    ):
        raise ValueError("safeguard evidence limitations must be nonempty strings")

    hashes = evidence.get("code_sha256")
    if not isinstance(hashes, dict):
        raise ValueError("safeguard code_sha256 must be an object")
    if any(not isinstance(path, str) for path in hashes):
        raise ValueError("safeguard hash path names must be strings")
    missing_hashes = sorted(set(REQUIRED_SAFEGUARD_HASHES) - set(hashes))
    if missing_hashes:
        raise ValueError(f"safeguard SHA-256 coverage is missing required files: {missing_hashes}")

    root = Path(__file__).resolve().parents[2]
    for relative, expected_hash in hashes.items():
        if (
            not isinstance(expected_hash, str)
            or re.fullmatch(r"[0-9a-f]{64}", expected_hash) is None
        ):
            raise ValueError(f"safeguard SHA-256 for {relative!r} must be 64 lowercase hex characters")
        relative_path = Path(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(f"safeguard hash path must be workspace-relative: {relative!r}")
        current_path = root / relative_path
        if not current_path.is_file():
            raise ValueError(f"safeguard hashed file is missing: {relative}")
        current_hash = hashlib.sha256(current_path.read_bytes()).hexdigest()
        if current_hash != expected_hash:
            raise ValueError(
                f"safeguard SHA-256 drift for {relative}: expected {expected_hash}, got {current_hash}"
            )
    return evidence


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
    if not isinstance(captures, list):
        raise ValueError("physical evidence capture names must be a list")
    if any(not isinstance(capture, str) for capture in captures):
        raise ValueError("physical evidence capture names must all be strings")
    if len(captures) != len(set(captures)):
        raise ValueError("physical evidence capture names contain duplicates")
    if set(captures) != set(CAPTURES) or len(captures) != len(CAPTURES):
        missing = sorted(set(CAPTURES) - set(captures))
        unexpected = sorted(set(captures) - set(CAPTURES))
        raise ValueError(
            "physical evidence capture names must be exactly "
            f"{CAPTURES}; missing={missing}, unexpected={unexpected}"
        )
    if not isinstance(profiles, list):
        raise ValueError("physical evidence profile names must be a list")
    if any(not isinstance(profile, str) for profile in profiles):
        raise ValueError("physical evidence profile names must all be strings")
    if set(profiles) != set(PROFILES) or len(profiles) != 2:
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
        capture = record.get("capture")
        profile = record.get("profile")
        if not isinstance(capture, str) or not isinstance(profile, str):
            raise ValueError(
                "physical evidence record identity capture/profile names must be strings"
            )
        key = (capture, profile)
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
            if highest_other > historical_threshold and not any(
                row != expected_row for row in historical
            ):
                raise ValueError(
                    f"{key}: historical competing score crosses threshold without accusation"
                )
            if highest_other > threshold and not any(row != expected_row for row in conditional):
                raise ValueError(f"{key}: highest competing row crosses the conditional threshold without accusation")
            if any(row != expected_row for row in historical + conditional):
                raise ValueError(f"{key}: saved accusation contains an unexpected competing row")
        else:
            raise ValueError(f"{key}: status must be scored or boundary_failure")
        by_key[key] = record

    if len(records) != 8:
        raise ValueError("physical evidence must contain exactly eight records")

    expected_keys = {(capture, profile) for capture in captures for profile in PROFILES}
    if set(by_key) != expected_keys:
        missing = sorted(expected_keys - set(by_key))
        raise ValueError(f"physical evidence records do not cover every capture/profile; missing {missing}")

    def recovered_captures(profile: str) -> set[str]:
        return {
            capture
            for (capture, name), record in by_key.items()
            if name == profile
            and record["status"] == "scored"
            and record["expected_row"] in record["conditional_accused"]
        }

    historical_captures = {
        capture
        for (capture, _profile), record in by_key.items()
        if record["status"] == "scored" and record["expected_row"] in record["historical_accused"]
    }
    recovered_by_profile = {
        profile: recovered_captures(profile) for profile in PROFILES
    }
    for profile, expected in EXPECTED_RECOVERY.items():
        actual = recovered_by_profile[profile]
        if actual != expected:
            raise ValueError(
                f"physical recovery identity for {profile} must be akshay3.jpeg only; "
                f"got {sorted(actual)}"
            )
    boundary_failure_keys = {
        key for key, record in by_key.items() if record["status"] == "boundary_failure"
    }
    if boundary_failure_keys != EXPECTED_BOUNDARY_FAILURES:
        raise ValueError(
            "physical boundary-failure identities differ from the fixed study: "
            f"got {sorted(boundary_failure_keys)}"
        )
    if historical_captures:
        raise ValueError(
            "physical historical recovery identity must be empty; "
            f"got {sorted(historical_captures)}"
        )
    return {
        "source": str(path),
        "captures": len(captures),
        "capture_names": tuple(captures),
        "profiles": {profile: {capture: by_key[(capture, profile)] for capture in captures} for profile in PROFILES},
        "records": tuple(by_key[key] for key in sorted(by_key)),
        "historical_recovered": len(historical_captures),
        "historical_recovered_captures": tuple(sorted(historical_captures)),
        "baseline_recovered": len(recovered_by_profile["affine_baseline"]),
        "baseline_recovered_captures": tuple(
            sorted(recovered_by_profile["affine_baseline"])
        ),
        "refined_recovered": len(recovered_by_profile["affine_bias_translation"]),
        "refined_recovered_captures": tuple(
            sorted(recovered_by_profile["affine_bias_translation"])
        ),
        "boundary_failures": boundary_failures,
        "boundary_failure_keys": tuple(sorted(boundary_failure_keys)),
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
    safeguards: dict[str, Any],
) -> list[str]:
    """Return the six-slide audit record embedded in and exported from the deck."""
    latest = _record(physical, "akshay3.jpeg", "affine_bias_translation")
    baseline = _record(physical, "akshay3.jpeg", "affine_baseline")
    akshay2 = _record(physical, "akshay2.jpeg", "affine_bias_translation")
    common = (
        f"Team ID: {team_id}; team name: {team_name}; repository: {repository_url}. "
        "Status date: 12 September 2026. Selection deadline supplied by the team: 15 September. "
        "This is a tested research prototype, not production certification or a competition-outcome claim."
    )
    return [
        "\n".join([
            "Slide 1 — value proposition and scope",
            common,
            "R1: Unique invisible watermark at decryption — the controlled release path generates a marked, signed session copy before publication; the managed-process and authority-framing boundaries remain.",
            "R2: Recipient/session specificity — transaction-wide serialization now covers history validation, row allocation, signing, append, checkpoint and publication; the fresh concurrent scenario produced distinct rows and a later row 2.",
            f"R3: Visually identical / forensically distinct — {digital['pdf_count']} one-page PDFs preserve extracted text and average {digital['psnr_mean']:.2f} dB rendered PSNR; PDFs are not byte-identical, and this was not a human invisibility study.",
            "P22: Team ID, registered team name and repository URL remain explicit placeholders unless supplied through the build CLI; strict verification then fails.",
        ]),
        "\n".join([
            "Slide 2 — proposed solution and capabilities",
            "R4: Cryptographic binding to recipient identity — enrollment-bound recipient keys and an ML-DSA-signed canonical release event bind document, session, row and assurance mode; identity proofing and key custody remain deployment assumptions.",
            "R5: Recipient's own private signing key — ML-DSA receipt verification is implemented, but exclusive human custody is not established while demo keys remain local.",
            "R6: NIST PQC KEX/signatures — the fresh readiness check used real ML-KEM-768 and ML-DSA-65 through OpenSSL 3.6.4, with no classical fallback in the measured path; algorithm use does not certify the prototype.",
            "R9: Extract mark from leak — a supported clean PDF returns a signed source-copy session only when both channels corroborate; raster-only and inadequate-capacity PDF scores remain research leads with empty attribution.",
            "P5: The authority can reproduce both carriers for an already issued session without forging a new recipient receipt; exact source-copy evidence does not eliminate operator framing.",
            "P6: Removing both carriers or retyping content can leave readable material with no attribution signal.",
            "P7: The managed viewer can access authenticated clean plaintext before marking; publication is gated, but trusted software and endpoint control remain assumptions.",
            "P8: Extraction is non-blind and requires the retained original and correct source version.",
            "Source: research/evidence/nishan-selection-2026-09-12/demo/results.json.",
        ]),
        "\n".join([
            "Slide 3 — technical approach and release gates",
            "R7: Blockchain/DLT audit — the prototype implements a hash-linked, quorum-signed local 3-of-4 demonstrator; it is not independently administered blockchain infrastructure.",
            "R8: No single administrator can alter/delete history — NOT MET. All validator keys, replicas and witness material remain co-located. A configured pin helps only when the witness key and retained state are independently provisioned and trustworthy.",
            "R10: Ledger lookup — available valid records map rows to signed sessions. In configured witness mode, release rejects the tested wrong pin; release and trace both reject the tested coordinated valid-prefix rollback. Legacy unconfigured mode is explicitly unwitnessed.",
            "P1: The separate witness is now called on configured release and trace paths. It detects the tested rollback only while the pinned key and retained external state remain trusted; rolling back the witness too is outside the local guarantee.",
            "P2: Allocation race — corrected. The existing ledger transaction lock is held from history validation and row allocation through append, checkpoint and publication; fresh concurrent releases used distinct rows and a third release succeeded.",
            "P3: PDF policy — rendered/rasterized transplant now returns empty high-assurance attribution and retains only a research lead. Authenticated plaintext parsing prevents a metadata-only type bypass; renamed/prefixed PDFs cannot select generic-image handling.",
            f"P4: Insufficient {digital['layout_symbols']}-symbol layout capacity now yields a signed capacity limitation and abstention rather than PDF attribution.",
            "P17: Configured witness enforcement is implemented and tested on release and trace; the default compatibility mode remains explicitly unwitnessed, and trace records a checked snapshot rather than perpetual freshness.",
            "P18: All PDF-source traces now require visual/layout set equality, including raster suspects and low-capacity releases. Genuine raster-image screening is preserved and remains a different, research-only assurance class.",
            "Release ordering: validate → allocate/mark → recipient-sign → quorum append/re-audit → checkpoint/re-verify → atomic publication. A checkpoint failure leaves a committed authorization but publishes no new output.",
        ]),
        "\n".join([
            "Slide 4 — feasibility, evidence separation and boundaries",
            f"Fresh evidence: {len(safeguards['cases'])}/12 named safeguard scenarios passed; all_passed={safeguards['all_passed']}; pqc_ready={safeguards['pqc_ready']}; {len(safeguards['code_sha256'])} recorded SHA-256 entries match current files. These are scenario checks on public synthetic fixtures, not population experiments.",
            f"P10: Physical evidence is historical shipped-threshold {physical['historical_recovered']}/{physical['captures']} and exploratory {physical['baseline_recovered']}/{physical['captures']} in each profile, with the same akshay3 capture recovered in both—not two recovered captures. Latest akshay3 is {latest['expected_score']:.3f} vs {latest['conditional_null']['threshold']:.3f}; baseline is {baseline['expected_score']:.3f} vs {baseline['conditional_null']['threshold']:.3f}. akshay2 latest is {akshay2['expected_score']:.3f} vs {akshay2['conditional_null']['threshold']:.3f}; the first two refined-profile captures are boundary failures. This is one printed single-page public fixture, not end-to-end signed physical attribution.",
            f"P11: The {digital['jpeg_exact']}/{digital['jpeg_trials']} end-to-end JPEG-Q55 runs use one recipient identity across {digital['issued_session_count']} accumulated issued sessions (rows {digital['issued_row_min']}..{digital['issued_row_max']}); other-issued score is null {digital['other_score_null']} time and non-null {digital['other_score_nonnull']} times, not a multi-person test.",
            f"P12: All {digital['jpeg_trials']} end-to-end trials reuse the same document, authority secret and codebook; no independent-document or independent-authority inference follows.",
            f"P13: The {digital['codebooks']}-codebook × {digital['strategy_count']}-strategy study has {digital['code_cases']} code-level cases; it is not carrier, PDF or physical evidence.",
            "P14: Signed-PDF preservation is an expected compatibility issue because changed bytes normally invalidate signatures; damage to tagged PDF structure is untested, not demonstrated.",
            "P15: Main published experiments are single-page. Page loops exist in code, but there is no validated multi-page benchmark.",
            "P16: This selection update corrects deck, notes, verifier, paste-ready prose and runbook semantics; historical evidence artifacts and prototype code are not rewritten by Task 2.",
            f"P19: Registration and {digital['roster_rows']:,}-row scoring do not prove photo robustness; physical synchronization and useful capacity remain unresolved.",
            "P20: Co-located validator and witness administration remains a material limitation; the local quorum is not administrator-resistant DLT.",
            "P21: No Git repository was initialized. Local version history and publishing are distinct actions; controller backups are retained.",
            "Feasibility context (unnumbered): a confirmed six-person team has an existing offline laptop prototype, repeatable tests and saved evidence; neither GPU nor ESP32 is required for this measured workflow.",
            "Sources: demo/results.json; artifacts/nishan/end-to-end-jpeg-trials.json; artifacts/nishan/tardos-independent-codebook-study.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.",
        ]),
        "\n".join([
            "Slide 5 — impact, judge demo and next-round gates",
            "R11: Verifiable associated recipient/event — signature and ledger checks support a source-copy/session association; authority framing and copy-to-human inference limits remain.",
            "R12: Offline/air-gapped operation — demonstrated in a local architecture, not an audited hardened deployment.",
            "R13: No cloud KMS — the implemented workflow has no required external KMS dependency.",
            "R14: No public blockchain — the local demonstrator has no public-chain dependency.",
            "P9: Evidence identifies a released session/copy association, not which human intentionally disclosed it, received it successfully or read it.",
            "Five-minute judge flow: create a fresh demo output root; issue two recipients plus a repeated/third session; trace a clean PDF; show raster transplant and low-capacity PDF abstention; show wrong-pin release rejection and rollback rejection on both release and trace; inject checkpoint failure and show no new publication while explaining the committed authorization record.",
            "Next-round validation is narrow: independent administrative/key custody; larger multi-recipient and multi-page corpus; representative held-out print/camera testing; and a portable independent proof verifier. Neither GPU nor ESP32 is required for the measured workflow.",
            "Do not publish or reuse demo private keys. The runbook names new output roots and preserves historical evidence.",
        ]),
        "\n".join([
            "Slide 6 — prior art, references and differentiated integration",
            "P23: The stray file '=4.11' is retained outside presentation scope because this update is non-destructive; it was not silently deleted.",
            "P24: Novelty is unestablished. The engineering contribution is the tested integration of PQ-signed marked release, configured pinned-checkpoint gating and conservative two-channel PDF evidence. No component-level invention, competitor superiority or winning-probability claim is made. TRACE concerns LLM-agent trajectories and is omitted from scarce visible slide space.",
            "Parameter context (unnumbered): current n=1000,c=5,epsilon=1e-6 gives m=52500; roster-only n=20 gives m=42500; n=20,c=4,epsilon=1e-3 gives m=16000 but changes three assumptions. Rows are sessions. Ideal symmetric m=12331 is a separate audit requiring another decoder and implementation proof, not physical evidence or novelty.",
            "The recovered Sol Ultra session supplies no preserved authenticator probe artifacts, environment hashes or independently controlled secrets. Its adaptive strength-3 exact verifier recovered 3/5 after five-copy JPEG and failed perspective/10% crop; none of those numeric or recipient-controlled security claims are current deck evidence.",
            "URLs: https://www.sih.gov.in/sih2026PS ; https://csrc.nist.gov/pubs/fips/203/final ; https://csrc.nist.gov/pubs/fips/204/final ; https://www.cs.columbia.edu/cg/fontcode/ ; https://arxiv.org/abs/2010.06571 ; https://www.renyi.hu/~tardos/fingerprint.pdf.",
            "Evidence paths: artifacts/nishan/measured-results.json; artifacts/nishan/tardos-pdf-benchmark.json; artifacts/nishan/tardos-independent-codebook-study.json; artifacts/nishan/end-to-end-jpeg-trials.json; research/evidence/nishan-bias-physical-2026-09-10/scores.json.",
            common,
        ]),
    ]
