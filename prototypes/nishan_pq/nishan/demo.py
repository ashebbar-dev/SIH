from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

import pymupdf as fitz

from . import ledger, live_pdf, pqc, watermark, witness
from .core import (
    LAYOUT_ADJUSTMENT_MAGNITUDE,
    decrypt_and_attribute,
    encrypt_once,
    trace_leak,
)
from .identity import create_identity, load_identity
from .util import (
    b64d,
    b64e,
    canonical_json,
    read_json,
    sha3_file,
    write_json,
    write_private,
)


def _sample_pdf(path: Path) -> None:
    document = fitz.open()
    page = document.new_page(width=595, height=842)
    page.draw_rect(fitz.Rect(42, 42, 553, 800), color=(0.12, 0.18, 0.30), width=2)
    page.insert_text((64, 92), "RESTRICTED // EXERCISE", fontsize=17, color=(0.65, 0.08, 0.08))
    page.insert_text((64, 132), "Operations Readiness Note 17-A", fontsize=24, color=(0.05, 0.12, 0.22))
    page.insert_text((64, 172), "Distribution: ALPHA CELL", fontsize=11)
    body = (
        "This synthetic document is generated only for the NISHAN-PQ demonstration. "
        "The sender encrypts it once. Each authorized reader receives the same visible "
        "content, while the trusted offline viewer creates a session-specific forensic "
        "fingerprint and a signed decryption receipt before release."
    )
    page.insert_textbox(fitz.Rect(64, 215, 520, 350), body, fontsize=13, lineheight=1.5)
    rows = [
        ("Section", "Status", "Owner"),
        ("Communications", "READY", "A. Rao"),
        ("Logistics", "REVIEW", "B. Singh"),
        ("Navigation", "READY", "C. Devi"),
    ]
    y = 400
    for row in rows:
        page.insert_text((70, y), f"{row[0]:<22} {row[1]:<12} {row[2]}", fontsize=12)
        y += 28
    page.insert_text((64, 720), "Synthetic data — no operational information", fontsize=10)
    document.save(path, no_new_id=True, reproducible=True)
    document.close()


def _remove_first_image(source: Path, destination: Path) -> None:
    document = fitz.open(source)
    try:
        images = document[0].get_images(full=True)
        if not images:
            raise RuntimeError("marked fixture has no visual carrier image")
        document[0].delete_image(images[0][0])
        document.save(destination, garbage=4, deflate=True)
    finally:
        document.close()


def _transplant_first_image(
    donor: Path,
    recipient: Path,
    destination: Path,
) -> None:
    donor_document = fitz.open(donor)
    try:
        images = donor_document[0].get_images(full=True)
        if not images:
            raise RuntimeError("donor fixture has no visual carrier image")
        carrier_image = donor_document.extract_image(images[0][0])["image"]
    finally:
        donor_document.close()

    recipient_document = fitz.open(recipient)
    try:
        images = recipient_document[0].get_images(full=True)
        if not images:
            raise RuntimeError("recipient fixture has no visual carrier image")
        recipient_document[0].delete_image(images[0][0])
        recipient_document[0].insert_image(
            recipient_document[0].rect,
            stream=carrier_image,
            overlay=True,
            keep_proportion=False,
        )
        recipient_document.save(destination, garbage=4, deflate=True)
    finally:
        recipient_document.close()


def run(work_root: Path, null_samples: int = 400) -> dict[str, object]:
    if work_root.exists() and any(work_root.iterdir()):
        raise FileExistsError(f"demo directory is not empty: {work_root}")
    work_root.mkdir(parents=True, exist_ok=True)
    support = pqc.require_support()
    identities = work_root / "identities"
    for identity_id, display_name in [
        ("alice", "Commander Alice Rao"),
        ("bob", "Lieutenant Bob Singh"),
        ("charlie", "Analyst Charlie Devi"),
    ]:
        create_identity(identities, identity_id, display_name)

    ledger_root = work_root / "ledger"
    ledger.initialize(
        ledger_root,
        validator_count=4,
        quorum=3,
        identities_root=identities,
    )
    authority_secret = work_root / "authority" / "watermark-secret.bin"
    write_private(authority_secret, os.urandom(32))
    source = work_root / "source.pdf"
    _sample_pdf(source)
    package = work_root / "broadcast.nishan.json"
    encrypt_once(source, identities, ["alice", "bob", "charlie"], package)

    releases: dict[str, Path] = {}
    events: dict[str, object] = {}
    for recipient_id in ["alice", "bob", "charlie"]:
        output = work_root / "released" / f"{recipient_id}.pdf"
        events[recipient_id] = decrypt_and_attribute(
            package,
            identities,
            recipient_id,
            authority_secret,
            ledger_root,
            output,
        )
        releases[recipient_id] = output

    bob_leak = work_root / "attacks" / "bob-jpeg-q55.jpg"
    bob_leak.parent.mkdir(parents=True)
    watermark.jpeg_attack(releases["bob"], bob_leak, quality=55)
    bob_evidence = trace_leak(
        source,
        bob_leak,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "bob-jpeg.json",
        null_samples=null_samples,
    )

    coalition = work_root / "attacks" / "alice-bob-average.png"
    watermark.average_collusion([releases["alice"], releases["bob"]], coalition)
    coalition_evidence = trace_leak(
        source,
        coalition,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "alice-bob-coalition.json",
        null_samples=null_samples,
    )

    three_copy_coalition = work_root / "attacks" / "alice-bob-charlie-average.png"
    watermark.average_collusion(
        [releases["alice"], releases["bob"], releases["charlie"]],
        three_copy_coalition,
    )
    three_copy_evidence = trace_leak(
        source,
        three_copy_coalition,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "alice-bob-charlie-coalition.json",
        null_samples=null_samples,
    )

    direct_pdf_evidence = trace_leak(
        source,
        releases["alice"],
        authority_secret,
        ledger_root,
        work_root / "evidence" / "alice-direct-pdf.json",
    )
    overlay_removed = work_root / "attacks" / "alice-overlay-removed.pdf"
    _remove_first_image(releases["alice"], overlay_removed)
    overlay_removed_evidence = trace_leak(
        source,
        overlay_removed,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "alice-overlay-removed.json",
    )
    layout_normalized = work_root / "attacks" / "alice-layout-normalized.pdf"
    live_pdf.strip_layout_adjustments(
        releases["alice"],
        layout_normalized,
        adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
    )
    layout_normalized_evidence = trace_leak(
        source,
        layout_normalized,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "alice-layout-normalized.json",
    )
    both_removed = work_root / "attacks" / "alice-both-carriers-removed.pdf"
    live_pdf.strip_layout_adjustments(
        overlay_removed,
        both_removed,
        adjustment_magnitude=LAYOUT_ADJUSTMENT_MAGNITUDE,
    )
    both_removed_evidence = trace_leak(
        source,
        both_removed,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "alice-both-carriers-removed.json",
    )
    transplanted = work_root / "attacks" / "alice-visual-on-bob-layout.pdf"
    _transplant_first_image(releases["alice"], releases["bob"], transplanted)
    transplanted_evidence = trace_leak(
        source,
        transplanted,
        authority_secret,
        ledger_root,
        work_root / "evidence" / "visual-transplant-conflict.json",
    )

    pristine_audit = ledger.audit(ledger_root)

    witness_root = work_root / "external-head-witness"
    witness.initialize(witness_root)
    witness_checkpoint = witness.checkpoint(witness_root, pristine_audit)
    witness_consistent = witness.audit(witness_root, pristine_audit)
    rollback_ledger = work_root / "coordinated-rollback-ledger"
    shutil.copytree(ledger_root, rollback_ledger)
    for validator in ("validator-1", "validator-2", "validator-3", "validator-4"):
        rollback_replica = rollback_ledger / "replicas" / validator / "ledger.jsonl"
        rollback_lines = rollback_replica.read_text().splitlines()
        rollback_replica.write_text("\n".join(rollback_lines[:-1]) + "\n")
    rollback_ledger_audit = ledger.audit(rollback_ledger)
    rollback_witness_audit = witness.audit(witness_root, rollback_ledger_audit)

    replay_ledger = work_root / "replayed-receipt-ledger"
    shutil.copytree(ledger_root, replay_ledger)
    ledger.append(
        replay_ledger,
        json.loads(json.dumps(pristine_audit["blocks"][0]["core"]["record"])),
    )
    replay_trace_error: str | None = None
    try:
        trace_leak(
            source,
            bob_leak,
            authority_secret,
            replay_ledger,
            null_samples=32,
        )
    except RuntimeError as error:
        replay_trace_error = str(error)
    replay_release = work_root / "must-not-release-replayed-history.pdf"
    replay_release_error: str | None = None
    try:
        decrypt_and_attribute(
            package,
            identities,
            "alice",
            authority_secret,
            replay_ledger,
            replay_release,
        )
    except RuntimeError as error:
        replay_release_error = str(error)

    # A quorum signature is not a substitute for the recipient's ML-DSA
    # signature. Deliberately let the generic replica layer endorse a corrupted
    # receipt in an isolated ledger copy, then verify that both tracing and the
    # next plaintext release stop at the application trust boundary.
    invalid_receipt_ledger = work_root / "invalid-receipt-ledger"
    shutil.copytree(ledger_root, invalid_receipt_ledger)
    invalid_record = json.loads(
        json.dumps(pristine_audit["blocks"][0]["core"]["record"])
    )
    invalid_signature = bytearray(b64d(invalid_record["recipient_signature"]))
    invalid_signature[0] ^= 1
    invalid_record["recipient_signature"] = b64e(bytes(invalid_signature))
    ledger.append(invalid_receipt_ledger, invalid_record)
    invalid_receipt_audit = ledger.audit(invalid_receipt_ledger)

    invalid_trace_error: str | None = None
    try:
        trace_leak(
            source,
            bob_leak,
            authority_secret,
            invalid_receipt_ledger,
            null_samples=32,
        )
    except RuntimeError as error:
        invalid_trace_error = str(error)

    invalid_release = work_root / "must-not-release-invalid-history.pdf"
    invalid_release_error: str | None = None
    try:
        decrypt_and_attribute(
            package,
            identities,
            "alice",
            authority_secret,
            invalid_receipt_ledger,
            invalid_release,
        )
    except RuntimeError as error:
        invalid_release_error = str(error)

    # A self-asserted key can create a valid signature while falsely claiming an
    # enrolled name. The quorum-signed enrollment root must make that record
    # unusable even if the generic replica layer endorsed it.
    substitution_ledger = work_root / "identity-substitution-ledger"
    shutil.copytree(ledger_root, substitution_ledger)
    rogue_identities = work_root / "rogue-identities"
    create_identity(rogue_identities, "alice", "Commander Alice Rao")
    rogue = load_identity(rogue_identities, "alice")
    substituted_record = json.loads(
        json.dumps(pristine_audit["blocks"][0]["core"]["record"])
    )
    substituted_event = substituted_record["event"]
    substituted_event["recipient_sign_public_key"] = b64e(
        rogue["sign_public"].read_bytes()
    )
    substituted_event["recipient_sign_public_key_sha3_256"] = sha3_file(
        rogue["sign_public"]
    )
    substituted_record["recipient_signature"] = b64e(
        pqc.sign(rogue["sign_private"], canonical_json(substituted_event))
    )
    substituted_signature_valid_for_rogue_key = pqc.verify(
        rogue["sign_public"],
        canonical_json(substituted_event),
        b64d(substituted_record["recipient_signature"]),
    )
    ledger.append(substitution_ledger, substituted_record)
    substitution_trace_error: str | None = None
    try:
        trace_leak(
            source,
            bob_leak,
            authority_secret,
            substitution_ledger,
            null_samples=32,
        )
    except RuntimeError as error:
        substitution_trace_error = str(error)
    substitution_release = work_root / "must-not-release-key-substitution.pdf"
    substitution_release_error: str | None = None
    try:
        decrypt_and_attribute(
            package,
            identities,
            "alice",
            authority_secret,
            substitution_ledger,
            substitution_release,
        )
    except RuntimeError as error:
        substitution_release_error = str(error)

    # Editing the identity map itself must invalidate the validator-signed trust
    # root before any chain or release is accepted.
    registry_tamper_ledger = work_root / "registry-tamper-ledger"
    shutil.copytree(ledger_root, registry_tamper_ledger)
    registry_config_path = registry_tamper_ledger / "config.json"
    registry_config = read_json(registry_config_path)
    registry_config["identity_registry"]["alice"]["display_name"] = "Mallory"
    write_json(registry_config_path, registry_config)
    registry_tamper_audit = ledger.audit(registry_tamper_ledger)
    registry_tamper_release = work_root / "must-not-release-registry-tamper.pdf"
    registry_tamper_release_error: str | None = None
    try:
        decrypt_and_attribute(
            package,
            identities,
            "alice",
            authority_secret,
            registry_tamper_ledger,
            registry_tamper_release,
        )
    except RuntimeError as error:
        registry_tamper_release_error = str(error)

    attacked_replica = ledger_root / "replicas" / "validator-1" / "ledger.jsonl"
    lines = attacked_replica.read_text().splitlines()
    tampered = json.loads(lines[1])
    tampered["core"]["record"]["event"]["recipient_id"] = "mallory"
    lines[1] = json.dumps(tampered, sort_keys=True, separators=(",", ":"))
    attacked_replica.write_text("\n".join(lines) + "\n")
    attacked_audit = ledger.audit(ledger_root)

    summary = {
        "openssl": support.openssl_version,
        "algorithms": ["ML-KEM-768", "ML-DSA-65", "AES-256-GCM", "SHA3-256"],
        "decryption_events": {
            identity: {
                "session_id": value["event"]["session_id"],
                "watermark_psnr_db": value["event"]["watermark_metrics"]["psnr_db"],
                "ledger_block_hash": value["ledger_block_hash"],
            }
            for identity, value in events.items()
        },
        "jpeg_attack_attribution": bob_evidence["attribution"],
        "two_copy_average_attribution": coalition_evidence["attribution"],
        "three_copy_average_attribution": three_copy_evidence["attribution"],
        "dual_carrier_attack_decisions": {
            "direct_pdf": direct_pdf_evidence["channel_decision"],
            "visual_overlay_removed": overlay_removed_evidence["channel_decision"],
            "layout_tag_normalized": layout_normalized_evidence["channel_decision"],
            "both_channels_removed": both_removed_evidence["channel_decision"],
            "alice_visual_transplanted_onto_bob_layout": transplanted_evidence[
                "channel_decision"
            ],
        },
        "threshold_calibration": {
            "jpeg_q55": bob_evidence["threshold_calibration"],
            "two_copy_average": coalition_evidence["threshold_calibration"],
            "three_copy_average": three_copy_evidence["threshold_calibration"],
        },
        "ledger_before_attack": {
            "quorum_valid": pristine_audit["quorum_valid"],
            "divergent_replicas": pristine_audit["divergent_replicas"],
        },
        "ledger_after_single_replica_attack": {
            "quorum_valid": attacked_audit["quorum_valid"],
            "divergent_replicas": attacked_audit["divergent_replicas"],
            "failure": attacked_audit["replicas"]["validator-1"]["failure"],
        },
        "invalid_recipient_signature_attack": {
            "invalid_record_received_quorum_endorsement": invalid_receipt_audit[
                "quorum_valid"
            ],
            "trace_blocked": invalid_trace_error is not None,
            "future_plaintext_release_blocked": invalid_release_error is not None,
            "plaintext_output_created": invalid_release.exists(),
            "trace_error": invalid_trace_error,
            "release_error": invalid_release_error,
            "boundary": (
                "The portable replica layer signs arbitrary records; the application "
                "verifies every recipient ML-DSA receipt before tracing or release. "
                "Production endorsement policy must enforce the same validation."
            ),
        },
        "self_asserted_identity_key_attack": {
            "substituted_signature_valid_under_attacker_key": substituted_signature_valid_for_rogue_key,
            "invalid_record_received_quorum_endorsement": ledger.audit(
                substitution_ledger
            )["quorum_valid"],
            "trace_blocked": substitution_trace_error is not None,
            "future_plaintext_release_blocked": substitution_release_error is not None,
            "plaintext_output_created": substitution_release.exists(),
            "trace_error": substitution_trace_error,
            "release_error": substitution_release_error,
            "boundary": (
                "A valid signature under an attacker key cannot claim Alice because "
                "the event key hash must equal Alice's quorum-signed enrollment entry."
            ),
        },
        "enrollment_registry_tamper_attack": {
            "trust_root_valid": registry_tamper_audit["trust_root_valid"],
            "quorum_valid": registry_tamper_audit["quorum_valid"],
            "configuration_failure": registry_tamper_audit[
                "configuration_failure"
            ],
            "future_plaintext_release_blocked": registry_tamper_release_error
            is not None,
            "plaintext_output_created": registry_tamper_release.exists(),
            "release_error": registry_tamper_release_error,
        },
        "enrollment_trust_root": {
            "trust_root_valid": pristine_audit["trust_root_valid"],
            "trust_root_hash": pristine_audit["trust_root_hash"],
            "identity_registry_sha3_256": pristine_audit[
                "identity_registry_sha3_256"
            ],
            "enrolled_identity_ids": sorted(pristine_audit["identity_registry"]),
        },
        "valid_receipt_replay_attack": {
            "replayed_record_received_quorum_endorsement": ledger.audit(
                replay_ledger
            )["quorum_valid"],
            "trace_blocked": replay_trace_error is not None,
            "future_plaintext_release_blocked": replay_release_error is not None,
            "plaintext_output_created": replay_release.exists(),
            "trace_error": replay_trace_error,
            "release_error": replay_release_error,
        },
        "coordinated_valid_prefix_rollback_attack": {
            "checkpoint_hash": witness_checkpoint["checkpoint_hash"],
            "baseline_witness_comparison": witness_consistent[
                "ledger_comparison"
            ],
            "rolled_back_ledger_quorum_valid": rollback_ledger_audit[
                "quorum_valid"
            ],
            "witnessed_length": pristine_audit["canonical_length"],
            "rolled_back_length": rollback_ledger_audit["canonical_length"],
            "external_witness_comparison": rollback_witness_audit[
                "ledger_comparison"
            ],
            "boundary": (
                "The ledger alone accepts a coordinated truncation to a valid prefix. "
                "A separately retained ML-DSA head checkpoint detects it. The demo "
                "witness key is local; production requires separate administration."
            ),
        },
    }
    write_json(work_root / "demo-summary.json", summary)
    return summary
