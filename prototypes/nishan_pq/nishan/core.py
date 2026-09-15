from __future__ import annotations

import hashlib
import hmac
import math
import os
import tempfile
import uuid
from dataclasses import asdict
from contextlib import nullcontext
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist, fmean, pstdev
from typing import Any

import numpy as np
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from . import layout_tag, ledger, live_pdf, pqc, tardos, tardos_carrier, watermark, witness
from .identity import load_identity
from .util import b64d, b64e, canonical_json, read_json, sha3_bytes, sha3_file, write_json


DEFAULT_NULL_SAMPLES = 400
DEFAULT_FAMILYWISE_ALPHA = 0.01
TARDOS_ROSTER_SIZE = 1_000
TARDOS_COALITION_LIMIT = 5
TARDOS_FAMILYWISE_EPSILON = 1e-6
TARDOS_SCHEME = "nishan-tardos-live-pdf/v1"
LAYOUT_TAG_SCHEME = "nishan-hmac-layout-tag/v1"
LAYOUT_ADJUSTMENT_MAGNITUDE = 0.001


def _layout_context(document_id: str, session_id: str, user_index: int) -> str:
    return f"layout:{document_id}:{session_id}:{user_index}"


def _tag_commitment(bits: np.ndarray) -> str:
    return hashlib.sha3_256(np.packbits(bits).tobytes()).hexdigest()


@lru_cache(maxsize=2)
def _tardos_material(
    authority_secret: bytes,
    document_id: str,
) -> tuple[tardos.Parameters, np.ndarray, np.ndarray, dict[str, object]]:
    """Derive one protected per-document codebook for the prototype process."""

    config = tardos.parameters(
        TARDOS_ROSTER_SIZE,
        TARDOS_COALITION_LIMIT,
        TARDOS_FAMILYWISE_EPSILON,
    )
    biases, codebook = tardos.generate_keyed(
        config,
        authority_secret,
        f"document:{document_id}",
    )
    codebook_manifest = tardos.manifest(config, biases, codebook)
    codebook_manifest["generator"] = (
        "AES-256-CTR streams derived by HMAC-SHA3-512; 53-bit bias and 32-bit Bernoulli discretization"
    )
    codebook_manifest["generator_assurance"] = (
        "prototype construction using the cryptography library; no independent DRBG audit"
    )
    return config, biases, codebook, codebook_manifest


def _next_tardos_index(
    ledger_root: Path,
    document_id: str,
    roster_size: int,
    state: dict[str, Any] | None = None,
) -> int:
    if state is None:
        state = _require_healthy_signed_history(ledger_root)
    used: set[int] = set()
    for block in state["blocks"]:
        record = block["core"]["record"]
        event = record.get("event", {})
        if event.get("document_id") != document_id:
            continue
        fingerprint = event.get("fingerprint")
        if not isinstance(fingerprint, dict) or fingerprint.get("scheme") != TARDOS_SCHEME:
            raise RuntimeError("cannot mix legacy and Tardos fingerprints for one document")
        used.add(int(fingerprint["user_index"]))
    for index in range(roster_size):
        if index not in used:
            return index
    raise RuntimeError("the declared Tardos roster is exhausted for this document")


def _derive_kek(shared_secret: bytes, document_id: str, recipient_id: str) -> bytes:
    return HKDF(
        algorithm=hashes.SHA3_256(),
        length=32,
        salt=bytes.fromhex(document_id),
        info=f"NISHAN-DEK-WRAP/v1|{recipient_id}".encode(),
    ).derive(shared_secret)


def encrypt_once(
    source: Path,
    identities_root: Path,
    recipient_ids: list[str],
    package_path: Path,
) -> dict[str, Any]:
    plaintext = source.read_bytes()
    source_hash = sha3_bytes(plaintext)
    document_id = source_hash
    dek = AESGCM.generate_key(bit_length=256)
    document_nonce = os.urandom(12)
    encrypted_document = AESGCM(dek).encrypt(
        document_nonce, plaintext, document_id.encode("ascii")
    )
    envelopes: dict[str, dict[str, str]] = {}
    for recipient_id in recipient_ids:
        identity = load_identity(identities_root, recipient_id)
        kem_ciphertext, shared_secret = pqc.encapsulate(identity["kem_public"])
        kek = _derive_kek(shared_secret, document_id, recipient_id)
        wrap_nonce = os.urandom(12)
        wrapped_dek = AESGCM(kek).encrypt(
            wrap_nonce, dek, f"{document_id}|{recipient_id}".encode()
        )
        envelopes[recipient_id] = {
            "kem_ciphertext": b64e(kem_ciphertext),
            "wrap_nonce": b64e(wrap_nonce),
            "wrapped_dek": b64e(wrapped_dek),
            "kem_public_key_sha3_256": identity["profile"]["kem_public_key_sha3_256"],
        }
    package = {
        "version": "nishan-package/v1",
        "document_id": document_id,
        "source": {
            "filename": source.name,
            "sha3_256": source_hash,
            "media_type": "application/pdf" if watermark.is_pdf_document(source) else "image",
        },
        "content_cipher": {
            "algorithm": "AES-256-GCM",
            "nonce": b64e(document_nonce),
            "ciphertext": b64e(encrypted_document),
        },
        "key_distribution": {
            "algorithm": "ML-KEM-768 + HKDF-SHA3-256 + AES-256-GCM",
            "envelopes": envelopes,
        },
    }
    write_json(package_path, package)
    return package


def _validate_witness_arguments(
    ledger_root: Path, witness_root: Path | None, pin: str | None,
) -> str | None:
    if (witness_root is None) != (pin is None):
        raise ValueError("witness_root and witness_public_key_sha3_256 must be supplied together")
    if witness_root is None:
        return None
    if witness_root.resolve() == ledger_root.resolve():
        raise ValueError("witness root must differ from ledger root")
    return witness.validate_pin(pin)


def decrypt_and_attribute(
    package_path: Path,
    identities_root: Path,
    recipient_id: str,
    authority_secret_path: Path,
    ledger_root: Path,
    output_path: Path,
    watermark_strength: float = 2.2,
    *,
    witness_root: Path | None = None,
    witness_public_key_sha3_256: str | None = None,
) -> dict[str, Any]:
    pin = _validate_witness_arguments(ledger_root, witness_root, witness_public_key_sha3_256)
    with ledger.exclusive(ledger_root):
        with witness.exclusive(witness_root) if witness_root is not None else nullcontext():
            return _decrypt_and_attribute_locked(
                package_path, identities_root, recipient_id, authority_secret_path,
                ledger_root, output_path, watermark_strength,
                witness_root=witness_root, witness_public_key_sha3_256=pin,
            )


def _decrypt_and_attribute_locked(
    package_path: Path,
    identities_root: Path,
    recipient_id: str,
    authority_secret_path: Path,
    ledger_root: Path,
    output_path: Path,
    watermark_strength: float,
    *,
    witness_root: Path | None,
    witness_public_key_sha3_256: str | None,
) -> dict[str, Any]:
    package = read_json(package_path)
    envelope = package["key_distribution"]["envelopes"].get(recipient_id)
    if envelope is None:
        raise PermissionError(f"{recipient_id!r} is not an authorized recipient")
    # Validator endorsements do not replace the recipient's own signed receipt.
    # Refuse to decrypt while any canonical receipt is invalid, for every media
    # type, before plaintext is materialized on disk.
    ledger_state = _require_healthy_signed_history(ledger_root)
    assurance = {
        "version": "nishan-release-assurance/v1",
        "mode": "pinned_witness" if witness_root is not None else "unwitnessed",
        "witness_enforced": witness_root is not None,
        "record_meaning": "release authorized; not proof of delivery or reading",
    }
    checked_witness = None
    if witness_root is not None:
        checked_witness = witness.require_consistent(
            witness_root, ledger_state, witness_public_key_sha3_256
        )
        assurance["witness_public_key_sha3_256"] = witness_public_key_sha3_256
    identity = load_identity(identities_root, recipient_id)
    enrollment = _require_enrolled_identity(ledger_state, identity)
    if envelope.get("kem_public_key_sha3_256") != enrollment["kem_public_key_sha3_256"]:
        raise RuntimeError("package KEM envelope is not bound to the enrolled recipient key")
    shared_secret = pqc.decapsulate(
        identity["kem_private"], b64d(envelope["kem_ciphertext"])
    )
    kek = _derive_kek(shared_secret, package["document_id"], recipient_id)
    dek = AESGCM(kek).decrypt(
        b64d(envelope["wrap_nonce"]),
        b64d(envelope["wrapped_dek"]),
        f"{package['document_id']}|{recipient_id}".encode(),
    )
    plaintext = AESGCM(dek).decrypt(
        b64d(package["content_cipher"]["nonce"]),
        b64d(package["content_cipher"]["ciphertext"]),
        package["document_id"].encode("ascii"),
    )
    if sha3_bytes(plaintext) != package["source"]["sha3_256"]:
        raise ValueError("decrypted source hash does not match the package")

    session_id = str(uuid.uuid4())
    authority_secret = authority_secret_path.read_bytes()
    destination_suffix = Path(package["source"]["filename"]).suffix or output_path.suffix
    # Atomic publication requires staging on the destination filesystem. The
    # private 0700 directory is created only after history/pin/enrollment checks.
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".nishan-release-", dir=output_path.parent) as directory:
        root = Path(directory)
        plaintext_path = root / f"source{destination_suffix}"
        marked_path = root / f"marked{destination_suffix}"
        plaintext_path.write_bytes(plaintext)
        # Package labels are not authenticated profile selectors. Classify the
        # authenticated bytes themselves, including renamed/prefixed PDFs.
        source_is_pdf = watermark.is_pdf_document(plaintext_path)
        actual_media_type = "application/pdf" if source_is_pdf else "image"
        if package["source"].get("media_type") != actual_media_type:
            raise RuntimeError("package media type does not match authenticated plaintext")
        fingerprint: dict[str, Any]
        if source_is_pdf:
            # The unchanged PDF carrier requires a .pdf staging filename;
            # choosing it follows content validation, never the package suffix.
            pdf_plaintext_path = root / "source.pdf"
            if plaintext_path != pdf_plaintext_path:
                os.replace(plaintext_path, pdf_plaintext_path)
            plaintext_path = pdf_plaintext_path
            marked_path = root / "marked.pdf"
            config, _, codebook, codebook_manifest = _tardos_material(
                authority_secret, package["document_id"]
            )
            user_index = _next_tardos_index(
                ledger_root,
                package["document_id"],
                config.roster_size,
                state=ledger_state,
            )
            tardos_path = root / "tardos-overlay.pdf"
            carrier_metrics = tardos_carrier.embed_pdf(
                plaintext_path,
                tardos_path,
                codebook[user_index],
                authority_secret,
                f"document:{package['document_id']}",
                strength=4.0,
            )
            tag = layout_tag.tag_bits(
                authority_secret,
                package["document_id"],
                session_id,
                user_index,
            )
            encoded_tag = layout_tag.hamming74_encode(tag)
            layout_capacity = live_pdf.capacity(tardos_path)
            layout_metadata: dict[str, Any] = {
                "scheme": LAYOUT_TAG_SCHEME,
                "available": layout_capacity >= int(encoded_tag.size),
                "tag_bits": layout_tag.TAG_BITS,
                "encoded_bits": layout_tag.ENCODED_BITS,
                "codec": "Hamming(7,4), one-symbol correction per seven-symbol block",
                "supported_capacity_bits": layout_capacity,
                "tag_commitment_sha3_256": _tag_commitment(tag),
                "scope": (
                    "Exact digital-PDF text-layout channel; not collusion-secure and not claimed "
                    "robust to optimizer normalization, print/scan, OCR, or photography."
                ),
            }
            if layout_metadata["available"]:
                layout_result = live_pdf.embed(
                    tardos_path,
                    marked_path,
                    encoded_tag,
                    authority_secret,
                    _layout_context(package["document_id"], session_id, user_index),
                    adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
                )
                layout_metadata["embed_metrics"] = asdict(layout_result)
            else:
                os.replace(tardos_path, marked_path)

            final_metrics = asdict(
                tardos_carrier.measure_pdf_pair(plaintext_path, marked_path)
            )
            metrics = {
                **asdict(carrier_metrics),
                "psnr_db": final_metrics["psnr_db"],
                "text_preserved": final_metrics["text_preserved"],
                "source_text_sha3_256": final_metrics["source_text_sha3_256"],
                "marked_text_sha3_256": final_metrics["marked_text_sha3_256"],
                "visual_tardos_carrier": asdict(carrier_metrics),
                "layout_tag_carrier": layout_metadata,
            }
            fingerprint = {
                "scheme": TARDOS_SCHEME,
                "user_index": user_index,
                "parameters": asdict(config),
                "theorem_bounds": tardos.theorem_bounds(config),
                "codebook_sha3_256": codebook_manifest["codebook_sha3_256"],
                "biases_sha3_256": codebook_manifest["biases_sha3_256"],
                "generator": codebook_manifest["generator"],
                "generator_assurance": codebook_manifest["generator_assurance"],
                "carrier_scope": (
                    "The theorem is conditional on the decoded pirate word obeying the marking condition; "
                    "the carrier must be evaluated separately for each attack."
                ),
                "layout_tag": layout_metadata,
                "fusion_policy_version": "pdf-all-formats-corroboration/v1",
                "corroboration_required": True,
                "fusion_policy": (
                    "All PDF-source traces require visual/layout set-equality corroboration, "
                    "including rasterized suspects and releases with insufficient layout capacity. "
                    "Single-channel scores are research leads only; missing channels, inadequate "
                    "release capacity, disagreement or any unissued accusation cause abstention."
                ),
            }
            watermark_commitment_material = (
                str(codebook_manifest["codebook_sha3_256"])
                + "|"
                + str(user_index)
                + "|"
                + session_id
                + "|"
                + layout_metadata["tag_commitment_sha3_256"]
            ).encode("ascii")
        else:
            metrics = watermark.embed_document(
                plaintext_path,
                marked_path,
                authority_secret,
                session_id,
                strength=watermark_strength,
            )
            fingerprint = {
                "scheme": "nishan-spread-spectrum-session/v1",
                "formal_familywise_bound": False,
            }
            watermark_commitment_material = authority_secret + session_id.encode("ascii")
        output_hash = sha3_file(marked_path)
        watermark_commitment = hashlib.sha3_256(
            watermark_commitment_material
        ).hexdigest()
        event = {
            "version": "nishan-decryption-event/v1",
            "session_id": session_id,
            "document_id": package["document_id"],
            "source_sha3_256": package["source"]["sha3_256"],
            "recipient_id": recipient_id,
            "recipient_display_name": identity["profile"]["display_name"],
            "recipient_sign_public_key": b64e(identity["sign_public"].read_bytes()),
            "recipient_sign_public_key_sha3_256": identity["profile"]["sign_public_key_sha3_256"],
            "decrypted_at": datetime.now(timezone.utc).isoformat(),
            "watermark_commitment_sha3_256": watermark_commitment,
            "released_copy_sha3_256": output_hash,
            "watermark_metrics": metrics,
            "fingerprint": fingerprint,
            "release_assurance": assurance,
        }
        signature = pqc.sign(identity["sign_private"], canonical_json(event))
        record = {
            "event": event,
            "recipient_signature_algorithm": "ML-DSA-65 (FIPS 204)",
            "recipient_signature": b64e(signature),
        }
        if not _verify_event(record, ledger_state["identity_registry"]):
            raise RuntimeError("recipient signature self-check failed; plaintext not released")
        block = ledger.append(ledger_root, record, lock_held=True)
        committed_state = _require_healthy_signed_history(ledger_root)
        if (committed_state["canonical_length"] != ledger_state["canonical_length"] + 1
                or committed_state["canonical_head"] != block["block_hash"]):
            raise RuntimeError("committed ledger head does not match this authorized release")
        if witness_root is not None:
            extending = witness.require_extension(
                witness_root, committed_state, witness_public_key_sha3_256
            )
            if not hmac.compare_digest(
                extending["latest_checkpoint_hash"], checked_witness["latest_checkpoint_hash"]
            ):
                raise RuntimeError("witness anchor changed during release")
            # A failure leaves the signed authorization committed, with no new
            # output published. Explicit operator review/checkpoint is recovery.
            witness.checkpoint(witness_root, committed_state, lock_held=True)
            checked_witness = witness.require_consistent(
                witness_root, committed_state, witness_public_key_sha3_256
            )
        os.replace(marked_path, output_path)
    return {"event": event, "ledger_block_hash": block["block_hash"], "output": str(output_path),
            "release_assurance": {**assurance, "checkpoint": checked_witness}}


def _verify_event(
    record: dict[str, Any],
    identity_registry: dict[str, dict[str, str]],
) -> bool:
    try:
        event = record["event"]
        recipient_id = event["recipient_id"]
        enrollment = identity_registry.get(recipient_id)
        if enrollment is None:
            return False
        if (
            event["recipient_display_name"] != enrollment["display_name"]
            or event["recipient_sign_public_key_sha3_256"]
            != enrollment["sign_public_key_sha3_256"]
            or record["recipient_signature_algorithm"]
            != enrollment["signature_algorithm"]
        ):
            return False
        with tempfile.TemporaryDirectory(prefix="nishan-event-key-") as directory:
            public_key = Path(directory) / "public.pem"
            public_key.write_bytes(b64d(event["recipient_sign_public_key"]))
            if sha3_file(public_key) != event["recipient_sign_public_key_sha3_256"]:
                return False
            return pqc.verify(
                public_key,
                canonical_json(event),
                b64d(record["recipient_signature"]),
            )
    except (KeyError, OSError, TypeError, ValueError):
        return False


def _require_enrolled_identity(
    state: dict[str, Any],
    identity: dict[str, object],
) -> dict[str, str]:
    profile = identity["profile"]
    if not isinstance(profile, dict):
        raise RuntimeError("recipient identity profile is malformed")
    identity_id = profile.get("identity_id")
    registry = state.get("identity_registry")
    if not isinstance(registry, dict) or not isinstance(identity_id, str):
        raise RuntimeError("ledger identity registry is unavailable")
    enrollment = registry.get(identity_id)
    if not isinstance(enrollment, dict):
        raise PermissionError(f"{identity_id!r} is not in the ledger enrollment registry")
    sign_public = identity["sign_public"]
    kem_public = identity["kem_public"]
    if not isinstance(sign_public, Path) or not isinstance(kem_public, Path):
        raise RuntimeError("recipient public-key paths are malformed")
    comparisons = {
        "display_name": profile.get("display_name"),
        "signature_algorithm": profile.get("signature_algorithm"),
        "kem_algorithm": profile.get("kem_algorithm"),
        "sign_public_key_sha3_256": sha3_file(sign_public),
        "kem_public_key_sha3_256": sha3_file(kem_public),
    }
    mismatches = [
        name for name, observed in comparisons.items() if enrollment.get(name) != observed
    ]
    if mismatches:
        raise RuntimeError(
            "recipient identity does not match the signed enrollment root: "
            + ", ".join(mismatches)
        )
    return enrollment


def _require_healthy_signed_history(ledger_root: Path) -> dict[str, Any]:
    state = ledger.audit(ledger_root)
    if not state.get("trust_root_valid", False):
        raise RuntimeError(
            "ledger enrollment trust root is invalid: "
            + str(state.get("configuration_failure", "unknown failure"))
        )
    if not state["quorum_valid"] or state["divergent_replicas"]:
        raise RuntimeError("ledger replicas must be healthy before plaintext release")
    invalid_signature_blocks = [
        int(block["core"]["index"])
        for block in state["blocks"]
        if not _verify_event(
            block["core"]["record"], state["identity_registry"]
        )
    ]
    if invalid_signature_blocks:
        raise RuntimeError(
            "canonical ledger contains invalid recipient signatures in blocks: "
            + ", ".join(str(index) for index in invalid_signature_blocks)
        )
    seen_sessions: set[str] = set()
    seen_tardos_rows: set[tuple[str, int]] = set()
    duplicate_sessions: set[str] = set()
    duplicate_rows: set[tuple[str, int]] = set()
    for block in state["blocks"]:
        event = block["core"]["record"]["event"]
        session_id = str(event["session_id"])
        if session_id in seen_sessions:
            duplicate_sessions.add(session_id)
        seen_sessions.add(session_id)
        fingerprint = event.get("fingerprint", {})
        if fingerprint.get("scheme") == TARDOS_SCHEME:
            row = (str(event["document_id"]), int(fingerprint["user_index"]))
            if row in seen_tardos_rows:
                duplicate_rows.add(row)
            seen_tardos_rows.add(row)
    if duplicate_sessions or duplicate_rows:
        details: list[str] = []
        if duplicate_sessions:
            details.append(f"duplicate session ids={len(duplicate_sessions)}")
        if duplicate_rows:
            details.append(f"duplicate document-row assignments={len(duplicate_rows)}")
        raise RuntimeError("canonical ledger contains replayed receipts: " + "; ".join(details))
    return state


def _decoy_session_id(
    secret: bytes,
    reference_hash: str,
    suspect_hash: str,
    index: int,
) -> str:
    """Derive a reproducible never-issued session identifier for null scoring."""

    material = (
        f"NISHAN-DECOY/v1|{reference_hash}|{suspect_hash}|{index}"
    ).encode("ascii")
    digest = hmac.new(secret, material, hashlib.sha3_256).digest()
    return str(uuid.UUID(bytes=digest[:16]))


def _quantile(values: list[float], probability: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    position = (len(ordered) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] * (1.0 - fraction) + ordered[upper] * fraction


def _calibrate_screening_threshold(
    prepared: watermark.PreparedScore,
    secret: bytes,
    reference_hash: str,
    suspect_hash: str,
    issued_session_ids: set[str],
    roster_size: int,
    null_samples: int,
    familywise_alpha: float,
) -> tuple[float, dict[str, Any]]:
    """Estimate a per-query screening threshold from never-issued carriers.

    This deliberately does not label the result a formal false-accusation bound.
    The Gaussian tail is a model and a finite decoy sample cannot resolve rare
    probabilities such as 1e-6.  The evidence bundle records that limitation.
    """

    if null_samples < 20:
        raise ValueError("null_samples must be at least 20")
    if not 0.0 < familywise_alpha < 0.5:
        raise ValueError("familywise_alpha must be between 0 and 0.5")

    decoy_scores: list[float] = []
    index = 0
    while len(decoy_scores) < null_samples:
        session_id = _decoy_session_id(
            secret,
            reference_hash,
            suspect_hash,
            index,
        )
        index += 1
        if session_id in issued_session_ids:
            continue
        decoy_scores.append(watermark.score_prepared(prepared, secret, session_id))

    null_mean = fmean(decoy_scores)
    null_sd = pstdev(decoy_scores)
    tested_roster_size = max(roster_size, 1)
    per_candidate_alpha = familywise_alpha / tested_roster_size
    # Guard NormalDist against probabilities rounded to exactly 1.0.
    model_tail = min(max(per_candidate_alpha, 1e-12), 0.499999)
    gaussian_z = NormalDist().inv_cdf(1.0 - model_tail)
    gaussian_candidate = null_mean + gaussian_z * null_sd
    decoy_max = max(decoy_scores)
    threshold = max(gaussian_candidate, math.nextafter(decoy_max, math.inf))
    calibration = {
        "version": "nishan-empirical-null/v1",
        "decision_role": "screening threshold; not a formal accusation bound",
        "method": "maximum observed decoy score or Gaussian Bonferroni estimate, whichever is higher",
        "null_samples": null_samples,
        "roster_size": tested_roster_size,
        "requested_familywise_alpha": familywise_alpha,
        "per_candidate_alpha_for_gaussian_model": per_candidate_alpha,
        "gaussian_z": round(gaussian_z, 6),
        "null_mean": round(null_mean, 9),
        "null_sd": round(null_sd, 9),
        "null_max": round(decoy_max, 9),
        "null_q99": round(_quantile(decoy_scores, 0.99), 9),
        "gaussian_bonferroni_candidate": round(gaussian_candidate, 9),
        "selected_threshold": round(threshold, 9),
        "empirical_one_sided_p_resolution": round(1.0 / (null_samples + 1), 9),
        "formal_familywise_bound_established": False,
        "limitation": (
            "A finite decoy sample and an unverified Gaussian tail cannot certify rare false-accusation probabilities; "
            "a collusion-secure code with a declared proof model is required before an evidentiary accusation claim."
        ),
    }
    return threshold, calibration


def fuse_channel_indices(
    tardos_indices: set[int],
    layout_indices: set[int],
    unissued_tardos_indices: set[int],
    *,
    require_corroboration: bool = False,
) -> dict[str, Any]:
    """Apply the fail-closed dual-carrier decision policy."""

    if unissued_tardos_indices:
        return {
            "decision": "abstain_unissued_tardos_candidate",
            "selected_indices": [],
            "conflict": True,
            "reason": (
                "The Tardos decoder crossed threshold for at least one row with no signed "
                "release event; the carrier input is unsafe for attribution."
            ),
        }
    if require_corroboration and bool(tardos_indices) != bool(layout_indices):
        surviving = tardos_indices or layout_indices
        return {
            "decision": "abstain_single_channel_editable_pdf",
            "selected_indices": [],
            "screening_lead_indices": sorted(surviving),
            "conflict": True,
            "reason": (
                "This editable PDF was released with two carriers but only one survives. "
                "The remaining signal is an investigative lead, not corroborated attribution, "
                "because a remove-and-transplant attack can manufacture this state."
            ),
        }
    if tardos_indices and layout_indices:
        overlap = tardos_indices & layout_indices
        if tardos_indices == layout_indices:
            return {
                "decision": "corroborated_channels",
                "selected_indices": sorted(overlap),
                "conflict": False,
                "reason": "Both separately encoded, domain-separated carriers identify the same release event set.",
            }
        return {
            "decision": "abstain_channel_conflict",
            "selected_indices": [],
            "screening_lead_indices": sorted(overlap),
            "conflict": True,
            "reason": (
                "The visual Tardos and text-layout identity sets differ. Even an overlapping "
                "candidate is withheld because extra candidates are consistent with carrier "
                "transplantation or recombination."
            ),
        }
    if tardos_indices:
        return {
            "decision": "tardos_channel_only",
            "selected_indices": sorted(tardos_indices),
            "conflict": False,
            "reason": "Only the rendered visual carrier produced candidate rows.",
        }
    if layout_indices:
        return {
            "decision": "layout_channel_only",
            "selected_indices": sorted(layout_indices),
            "conflict": False,
            "reason": "Only the editable-PDF text-layout authenticator produced a candidate row.",
        }
    return {
        "decision": "no_attribution_signal",
        "selected_indices": [],
        "conflict": False,
        "reason": "Neither carrier produced a signed release candidate.",
    }


def _trace_tardos_pdf(
    reference: Path,
    suspect: Path,
    secret: bytes,
    source_hash: str,
    suspect_hash: str,
    state: dict[str, Any],
    candidate_records: list[tuple[dict[str, Any], dict[str, Any]]],
    evidence_path: Path | None,
) -> dict[str, Any]:
    """Trace a PDF carrier with the declared Tardos reference profile."""

    config, biases, codebook, codebook_manifest = _tardos_material(
        secret, source_hash
    )
    expected_codebook_hash = codebook_manifest["codebook_sha3_256"]
    expected_bias_hash = codebook_manifest["biases_sha3_256"]
    issued: dict[int, tuple[dict[str, Any], dict[str, Any]]] = {}
    for block, record in candidate_records:
        fingerprint = record["event"].get("fingerprint", {})
        if fingerprint.get("scheme") != TARDOS_SCHEME:
            raise RuntimeError("mixed fingerprint schemes for one document")
        if (
            fingerprint.get("codebook_sha3_256") != expected_codebook_hash
            or fingerprint.get("biases_sha3_256") != expected_bias_hash
        ):
            raise RuntimeError("ledger fingerprint commitment does not match derived codebook")
        user_index = int(fingerprint["user_index"])
        if user_index in issued:
            raise RuntimeError("duplicate Tardos user index in canonical ledger")
        issued[user_index] = (block, record)

    pirate_word, correlations, decoder_diagnostics = (
        tardos_carrier.decode_word_with_diagnostics(
        reference,
        suspect,
        config.code_length,
        secret,
        f"document:{source_hash}",
        )
    )
    scores = tardos.accusation_scores(biases, codebook, pirate_word)
    accused_indices = tardos.accuse(scores, config)
    accused_set = set(int(index) for index in accused_indices)
    suspect_is_pdf = watermark.is_pdf_document(suspect)
    layout_carrier: np.ndarray | None = None
    layout_read_error: str | None = None
    if suspect_is_pdf:
        try:
            layout_carrier = live_pdf.read_carrier(
                suspect, adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE
            )
        except Exception as error:  # malformed/unsupported suspect is evidence, not a crash
            layout_read_error = f"{type(error).__name__}: {error}"

    layout_expected = any(
        bool(record["event"].get("fingerprint", {}).get("layout_tag", {}).get("available", False))
        for _, record in issued.values()
    )
    candidates: list[dict[str, Any]] = []
    layout_matches: set[int] = set()
    for user_index, (block, record) in issued.items():
        event = record["event"]
        fingerprint = event["fingerprint"]
        tag_metadata = fingerprint.get("layout_tag", {})
        layout_available = bool(tag_metadata.get("available", False))
        layout_evidence: dict[str, Any] = {
            "release_channel_available": layout_available,
            "suspect_is_pdf": suspect_is_pdf,
            "suspect_carrier_symbols": (
                None if layout_carrier is None else int(layout_carrier.size)
            ),
            "match": False,
            "corrected_blocks": None,
            "status": "release had no supported layout capacity",
        }
        if layout_available:
            expected_tag = layout_tag.tag_bits(
                secret,
                source_hash,
                event["session_id"],
                user_index,
            )
            if tag_metadata.get("tag_commitment_sha3_256") != _tag_commitment(
                expected_tag
            ):
                raise RuntimeError("signed layout-tag commitment does not match derived tag")
            if layout_carrier is None:
                layout_evidence["status"] = (
                    "suspect is not a supported digital PDF"
                    if not suspect_is_pdf
                    else "layout carrier could not be read"
                )
            elif layout_carrier.size < layout_tag.ENCODED_BITS:
                layout_evidence["status"] = "too few signed layout symbols remain"
            else:
                encoded = live_pdf.decode_carrier(
                    layout_carrier,
                    layout_tag.ENCODED_BITS,
                    secret,
                    _layout_context(source_hash, event["session_id"], user_index),
                )
                decoded = layout_tag.hamming74_decode(encoded)
                matched = layout_tag.matches(
                    decoded.bits,
                    secret,
                    source_hash,
                    event["session_id"],
                    user_index,
                )
                layout_evidence.update(
                    {
                        "match": matched,
                        "corrected_blocks": decoded.corrected_blocks,
                        "hamming_blocks": decoded.blocks,
                        "status": "authenticated tag matched" if matched else "tag mismatch",
                    }
                )
                if matched:
                    layout_matches.add(user_index)
        candidates.append(
            {
                "recipient_id": event["recipient_id"],
                "recipient_display_name": event["recipient_display_name"],
                "session_id": event["session_id"],
                "fingerprint_user_index": user_index,
                "score": round(float(scores[user_index]), 6),
                "above_threshold": user_index in accused_set,
                "tardos_above_threshold": user_index in accused_set,
                "layout_tag": layout_evidence,
                "recipient_signature_valid": _verify_event(
                    record, state["identity_registry"]
                ),
                "ledger_block_index": block["core"]["index"],
                "ledger_block_hash": block["block_hash"],
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    issued_tardos_matches = accused_set & set(issued)
    unissued_accusations = accused_set - set(issued)
    fusion = fuse_channel_indices(
        issued_tardos_matches,
        layout_matches,
        unissued_accusations,
        require_corroboration=True,
    )
    if not layout_expected or not suspect_is_pdf:
        fusion = {
            **fusion,
            "selected_indices": [],
            "decision": ("abstain_inadequate_release_capacity" if not layout_expected
                         else "abstain_missing_layout_channel"),
            "reason": ("The signed release has inadequate layout capacity for corroborated attribution."
                       if not layout_expected else
                       "The raster suspect has no digital PDF layout channel; visual scores are research leads only."),
        }
    selected = set(fusion["selected_indices"])
    for candidate in candidates:
        candidate["selected_by_fusion"] = (
            candidate["fingerprint_user_index"] in selected
        )
    positives = [item for item in candidates if item["selected_by_fusion"]]
    reference_bounds = tardos.theorem_bounds(config)
    result = {
        "version": "nishan-evidence/v3-dual-carrier",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_sha3_256": source_hash,
        "suspect_sha3_256": suspect_hash,
        "fingerprint_scheme": "NISHAN dual carrier: Tardos visual code + HMAC layout tag",
        "detection_threshold": config.threshold,
        "threshold_calibration": {
            "version": "original-tardos-reference-profile/v1",
            "decision_role": "binary fingerprint accusation threshold",
            "roster_size": config.roster_size,
            "coalition_limit": config.coalition_limit,
            "familywise_epsilon_target": config.familywise_epsilon,
            "code_length": config.code_length,
            "threshold": config.threshold,
            "reference_theorem_bounds": reference_bounds,
            "formal_code_bound_available": True,
            "formal_familywise_bound_established_for_this_physical_attack": False,
            "formal_familywise_bound_established": False,
            "why_not_automatic": (
                "The theorem requires a coalition of at most c and a decoded pirate word that obeys "
                "the marking condition. Those facts cannot be established from an unknown leak alone; "
                "named attack fixtures test the carrier condition separately. The keyed generator also "
                "uses documented finite-precision discretization."
            ),
        },
        "attribution": positives,
        "ranking": candidates,
        "visual_only_research_leads": [item for item in candidates
                                       if item["tardos_above_threshold"] and not item["selected_by_fusion"]],
        "accused_codebook_rows": accused_indices.tolist(),
        "unissued_accused_codebook_rows": sorted(unissued_accusations),
        "channel_decision": {
            **fusion,
            "tardos_issued_indices": sorted(issued_tardos_matches),
            "layout_authenticated_indices": sorted(layout_matches),
            "unissued_tardos_indices": sorted(unissued_accusations),
            "editable_pdf_corroboration_required": suspect_is_pdf and layout_expected,
            "corroboration_required": True,
            "layout_observation": {
                "suspect_is_pdf": suspect_is_pdf,
                "carrier_symbols_read": (
                    None if layout_carrier is None else int(layout_carrier.size)
                ),
                "read_error": layout_read_error,
                "tag_bits": layout_tag.TAG_BITS,
                "encoded_bits": layout_tag.ENCODED_BITS,
                "nominal_wrong_candidate_match_probability": "2^-72 under the PRF/HMAC idealization",
                "scope": (
                    "The layout result authenticates an exact digital-PDF carrier. It is not a "
                    "Tardos accusation bound and is expected to disappear after normalization."
                ),
            },
        },
        "decoder": {
            "decoded_symbols": int(pirate_word.size),
            "decoded_one_fraction": float(pirate_word.mean()),
            "median_absolute_block_correlation": float(
                np.median(np.abs(correlations))
            ),
            "preprocessing": decoder_diagnostics,
        },
        "ledger": {
            "quorum_valid": state["quorum_valid"],
            "trust_root_valid": state["trust_root_valid"],
            "trust_root_hash": state["trust_root_hash"],
            "identity_registry_sha3_256": state[
                "identity_registry_sha3_256"
            ],
            "canonical_length": state["canonical_length"],
            "canonical_head": state["canonical_head"],
            "divergent_replicas": state["divergent_replicas"],
        },
        "interpretation": (
            "The engine returns a signed release candidate only under the recorded fail-closed "
            "channel policy. A visual/layout disagreement or an unissued Tardos threshold crossing "
            "causes abstention. The Tardos reference bound still requires its coalition and marking "
            "assumptions; it is not asserted automatically for a physical carrier input."
        ),
    }
    if evidence_path is not None:
        write_json(evidence_path, result)
    return result


def trace_leak(
    reference: Path,
    suspect: Path,
    authority_secret_path: Path,
    ledger_root: Path,
    evidence_path: Path | None = None,
    detection_threshold: float | None = None,
    null_samples: int = DEFAULT_NULL_SAMPLES,
    familywise_alpha: float = DEFAULT_FAMILYWISE_ALPHA,
    *,
    witness_root: Path | None = None,
    witness_public_key_sha3_256: str | None = None,
) -> dict[str, Any]:
    pin = _validate_witness_arguments(ledger_root, witness_root, witness_public_key_sha3_256)
    with ledger.exclusive(ledger_root):
        with witness.exclusive(witness_root) if witness_root is not None else nullcontext():
            state = _require_healthy_signed_history(ledger_root)
            checked_witness = ({"witness_enforced": False, "mode": "unwitnessed"}
                if witness_root is None else witness.require_consistent(witness_root, state, pin))
    # Extraction uses the captured, verified snapshot after releasing both locks.
    result = _trace_leak_snapshot(reference, suspect, authority_secret_path, state,
                                  detection_threshold, null_samples, familywise_alpha)
    result["ledger_witness"] = checked_witness
    if evidence_path is not None:
        write_json(evidence_path, result)
    return result


def _trace_leak_snapshot(
    reference: Path, suspect: Path, authority_secret_path: Path, state: dict[str, Any],
    detection_threshold: float | None, null_samples: int, familywise_alpha: float,
) -> dict[str, Any]:
    source_hash = sha3_file(reference)
    suspect_hash = sha3_file(suspect)
    secret = authority_secret_path.read_bytes()
    candidate_records: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for block in state["blocks"]:
        record = block["core"]["record"]
        event = record["event"]
        if event["source_sha3_256"] != source_hash:
            continue
        candidate_records.append((block, record))

    invalid_signature_blocks = [
        int(block["core"]["index"])
        for block, record in candidate_records
        if not _verify_event(record, state["identity_registry"])
    ]
    if invalid_signature_blocks:
        raise RuntimeError(
            "canonical ledger contains invalid recipient signatures in blocks: "
            + ", ".join(str(index) for index in invalid_signature_blocks)
        )

    candidate_session_ids = [
        str(record["event"]["session_id"]) for _, record in candidate_records
    ]
    if len(candidate_session_ids) != len(set(candidate_session_ids)):
        raise RuntimeError(
            "canonical ledger contains replayed receipts for this source"
        )

    schemes = {
        record["event"].get("fingerprint", {}).get("scheme")
        for _, record in candidate_records
    }
    if watermark.is_pdf_document(reference) and schemes != {TARDOS_SCHEME}:
        raise RuntimeError(
            "PDF references with legacy generic or absent receipts cannot use generic screening; "
            "a PDF-profile release with corroborating carriers is required"
        )
    if schemes == {TARDOS_SCHEME}:
        if detection_threshold is not None:
            raise ValueError("a caller threshold cannot override the declared Tardos profile")
        return _trace_tardos_pdf(
            reference,
            suspect,
            secret,
            source_hash,
            suspect_hash,
            state,
            candidate_records,
            None,
        )
    if TARDOS_SCHEME in schemes:
        raise RuntimeError("mixed legacy and Tardos fingerprints for one document")

    candidates: list[dict[str, Any]] = []
    prepared = watermark.prepare_score(reference, suspect)

    issued_session_ids = {
        record["event"]["session_id"] for _, record in candidate_records
    }
    if detection_threshold is None:
        selected_threshold, calibration = _calibrate_screening_threshold(
            prepared,
            secret,
            source_hash,
            suspect_hash,
            issued_session_ids,
            len(candidate_records),
            null_samples,
            familywise_alpha,
        )
    else:
        selected_threshold = float(detection_threshold)
        calibration = {
            "version": "nishan-threshold-override/v1",
            "decision_role": "caller-supplied screening threshold",
            "selected_threshold": selected_threshold,
            "formal_familywise_bound_established": False,
            "limitation": "No null calibration was run for this caller-supplied threshold.",
        }

    for block, record in candidate_records:
        event = record["event"]
        score = watermark.score_prepared(prepared, secret, event["session_id"])
        candidates.append(
            {
                "recipient_id": event["recipient_id"],
                "recipient_display_name": event["recipient_display_name"],
                "session_id": event["session_id"],
                "score": round(score, 6),
                "above_threshold": score >= selected_threshold,
                "recipient_signature_valid": _verify_event(
                    record, state["identity_registry"]
                ),
                "ledger_block_index": block["core"]["index"],
                "ledger_block_hash": block["block_hash"],
            }
        )
    candidates.sort(key=lambda item: item["score"], reverse=True)
    positives = [item for item in candidates if item["above_threshold"]]
    result = {
        "version": "nishan-evidence/v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "reference_sha3_256": source_hash,
        "suspect_sha3_256": suspect_hash,
        "detection_threshold": round(selected_threshold, 9),
        "threshold_calibration": calibration,
        "attribution": positives,
        "ranking": candidates,
        "ledger": {
            "quorum_valid": state["quorum_valid"],
            "trust_root_valid": state["trust_root_valid"],
            "trust_root_hash": state["trust_root_hash"],
            "identity_registry_sha3_256": state[
                "identity_registry_sha3_256"
            ],
            "canonical_length": state["canonical_length"],
            "canonical_head": state["canonical_head"],
            "divergent_replicas": state["divergent_replicas"],
        },
        "interpretation": (
            "one positive is a candidate single-copy attribution; multiple positives may indicate an averaged coalition. "
            "The current empirical threshold is suitable for prototype screening, not a formal evidentiary accusation."
        ),
    }
    return result
