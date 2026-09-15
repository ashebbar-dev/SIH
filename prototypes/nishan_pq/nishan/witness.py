"""External post-quantum checkpoints for detecting quorum-ledger rollback.

A hash-linked ledger cannot detect coordinated truncation to an older valid
prefix by itself. This module records the latest canonical head under a separate
ML-DSA-65 witness key. The demonstrator stores that key on the same machine; a
deployment must put it under a separately administered HSM or witness service.
"""

from __future__ import annotations

import json
import hmac
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from pathlib import Path
from typing import Any

from . import pqc
from .util import b64d, b64e, canonical_json, read_json, sha3_bytes, sha3_file, write_json


VERSION = "nishan-external-head-witness/v1"
GENESIS_CHECKPOINT = "0" * 64


def validate_pin(pin: str) -> str:
    """Normalize an explicitly provisioned SHA3-256 public-key pin."""
    if not isinstance(pin, str) or len(pin) != 64 or any(
        character not in "0123456789abcdefABCDEF" for character in pin
    ):
        raise ValueError("witness pin must be a 64-character hexadecimal SHA3-256 digest")
    return pin.lower()


def _pinned_audit(root: Path, state: dict[str, Any], pin: str) -> dict[str, Any]:
    pin = validate_pin(pin)
    try:
        config = read_json(root / "config.json")
        actual = sha3_file(root / config["public_key"])
        if not hmac.compare_digest(actual, pin):
            raise RuntimeError("witness public key does not match the provisioned pin")
        result = audit(root, state)
    except (KeyError, OSError, TypeError, ValueError) as error:
        raise RuntimeError(f"pinned witness is unavailable or malformed: {error}") from error
    if not result.get("valid") or not result.get("verified_checkpoints"):
        raise RuntimeError("pinned witness requires a valid, nonempty, explicitly bootstrapped checkpoint chain")
    return {"witness_enforced": True, "witness_public_key_sha3_256": pin, **result}


def require_consistent(root: Path, state: dict[str, Any], pin: str) -> dict[str, Any]:
    """Check the actual pinned key and a nonempty chain at exactly this head.

    Callers hold ledger then witness locks when comparing a live snapshot.
    This function never creates or repairs a checkpoint.
    """
    result = _pinned_audit(root, state, pin)
    if result.get("ledger_comparison") != "consistent":
        raise RuntimeError(f"pinned witness is not consistent: {result.get('ledger_comparison')}")
    return result


def require_extension(root: Path, state: dict[str, Any], pin: str) -> dict[str, Any]:
    """Validate the pinned anchor again after this locked transaction appended."""
    result = _pinned_audit(root, state, pin)
    if result.get("ledger_comparison") != "unwitnessed_extension":
        raise RuntimeError(f"pinned witness does not anchor the new release: {result.get('ledger_comparison')}")
    return result


@contextmanager
def exclusive(root: Path):
    """Serialize local checkpoint access; administration is a deployment boundary."""

    lock_path = root / ".transaction.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _atomic_append(path: Path, encoded: bytes) -> None:
    """Commit one checkpoint without exposing a partial trailing record."""

    current = path.read_bytes()
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb", dir=path.parent, prefix=".witness-next-", delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(current)
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
        temporary_name = None
        directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if temporary_name is not None:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass


def initialize(root: Path) -> dict[str, Any]:
    if root.exists():
        raise FileExistsError(f"witness already exists: {root}")
    private_key = root / "private.pem"
    public_key = root / "public.pem"
    pqc.generate_keypair("ML-DSA-65", private_key, public_key)
    (root / "checkpoints.jsonl").touch()
    config = {
        "version": VERSION,
        "algorithm": "ML-DSA-65 (FIPS 204)",
        "private_key": private_key.name,
        "public_key": public_key.name,
        "public_key_sha3_256": sha3_file(public_key),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "deployment_boundary": (
            "Demonstrator key is local. Production requires a separately administered "
            "HSM or witness node whose state cannot be rolled back with the ledger."
        ),
    }
    write_json(root / "config.json", config)
    return config


def _read(root: Path) -> list[dict[str, Any]]:
    path = root / "checkpoints.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def audit(root: Path, ledger_state: dict[str, Any] | None = None) -> dict[str, Any]:
    config = read_json(root / "config.json")
    public_key = root / config["public_key"]
    if config.get("version") != VERSION:
        return {"valid": False, "failure": "unsupported witness version"}
    configured_hash = config.get("public_key_sha3_256")
    if not isinstance(configured_hash, str) or not hmac.compare_digest(sha3_file(public_key), configured_hash):
        return {"valid": False, "failure": "witness public-key hash mismatch"}

    previous = GENESIS_CHECKPOINT
    verified: list[dict[str, Any]] = []
    failure: str | None = None
    try:
        for expected_index, checkpoint in enumerate(_read(root)):
            payload = checkpoint.get("payload")
            if not isinstance(payload, dict):
                failure = f"checkpoint {expected_index}: missing payload"
                break
            if payload.get("index") != expected_index:
                failure = f"checkpoint {expected_index}: index mismatch"
                break
            if payload.get("previous_checkpoint_hash") != previous:
                failure = f"checkpoint {expected_index}: previous hash mismatch"
                break
            calculated = sha3_bytes(canonical_json(payload))
            if checkpoint.get("checkpoint_hash") != calculated:
                failure = f"checkpoint {expected_index}: hash mismatch"
                break
            if not pqc.verify(
                public_key,
                calculated.encode("ascii"),
                b64d(checkpoint["signature"]),
            ):
                failure = f"checkpoint {expected_index}: signature invalid"
                break
            verified.append(checkpoint)
            previous = calculated
    except (KeyError, OSError, TypeError, ValueError, json.JSONDecodeError) as error:
        failure = str(error)

    result: dict[str, Any] = {
        "valid": failure is None,
        "failure": failure,
        "verified_checkpoints": len(verified),
        "latest_checkpoint_hash": previous,
        "latest": verified[-1]["payload"] if verified else None,
    }
    if ledger_state is None or failure is not None or not verified:
        result["ledger_comparison"] = "not_compared"
        return result

    latest = verified[-1]["payload"]
    observed_length = int(ledger_state.get("canonical_length", -1))
    witnessed_length = int(latest["canonical_length"])
    if ledger_state.get("trust_root_hash") != latest["ledger_trust_root_hash"]:
        comparison = "foreign_or_replaced_trust_root"
    elif observed_length < witnessed_length:
        comparison = "rollback_detected"
    elif observed_length == witnessed_length:
        comparison = (
            "consistent"
            if ledger_state.get("canonical_head") == latest["canonical_head"]
            else "same_length_fork_detected"
        )
    else:
        blocks = ledger_state.get("blocks", [])
        anchored = (
            witnessed_length == 0
            or len(blocks) >= witnessed_length
            and blocks[witnessed_length - 1].get("block_hash")
            == latest["canonical_head"]
        )
        comparison = "unwitnessed_extension" if anchored else "fork_after_checkpoint"
    result["ledger_comparison"] = comparison
    result["observed_ledger_length"] = observed_length
    result["witnessed_ledger_length"] = witnessed_length
    result["observed_ledger_head"] = ledger_state.get("canonical_head")
    result["witnessed_ledger_head"] = latest["canonical_head"]
    return result


def checkpoint(
    root: Path,
    ledger_state: dict[str, Any],
    *,
    lock_held: bool = False,
) -> dict[str, Any]:
    if not lock_held:
        with exclusive(root):
            return checkpoint(root, ledger_state, lock_held=True)
    if not ledger_state.get("quorum_valid") or not ledger_state.get("trust_root_valid"):
        raise RuntimeError("cannot witness a ledger without a valid quorum and trust root")
    if ledger_state.get("divergent_replicas"):
        raise RuntimeError("cannot witness a ledger while replicas diverge")
    current = audit(root)
    if not current["valid"]:
        raise RuntimeError(f"witness history is invalid: {current['failure']}")
    latest = current["latest"]
    observed_length = int(ledger_state["canonical_length"])
    if latest is not None:
        if latest["ledger_trust_root_hash"] != ledger_state["trust_root_hash"]:
            raise RuntimeError("refusing to checkpoint a replaced ledger trust root")
        previous_length = int(latest["canonical_length"])
        if observed_length < previous_length:
            raise RuntimeError("refusing to checkpoint a rolled-back ledger")
        if observed_length == previous_length:
            if ledger_state["canonical_head"] != latest["canonical_head"]:
                raise RuntimeError("refusing to checkpoint a same-length fork")
            return {
                "idempotent": True,
                "checkpoint_hash": current["latest_checkpoint_hash"],
                "payload": latest,
            }
        blocks = ledger_state["blocks"]
        if previous_length and (
            len(blocks) < previous_length
            or blocks[previous_length - 1]["block_hash"] != latest["canonical_head"]
        ):
            raise RuntimeError("refusing to checkpoint a fork after the witnessed head")

    config = read_json(root / "config.json")
    records = _read(root)
    payload = {
        "version": VERSION,
        "index": len(records),
        "previous_checkpoint_hash": current["latest_checkpoint_hash"],
        "ledger_trust_root_hash": ledger_state["trust_root_hash"],
        "identity_registry_sha3_256": ledger_state[
            "identity_registry_sha3_256"
        ],
        "canonical_length": observed_length,
        "canonical_head": ledger_state["canonical_head"],
        "witnessed_at": datetime.now(timezone.utc).isoformat(),
    }
    checkpoint_hash = sha3_bytes(canonical_json(payload))
    signature = pqc.sign(
        root / config["private_key"], checkpoint_hash.encode("ascii")
    )
    record = {
        "payload": payload,
        "checkpoint_hash": checkpoint_hash,
        "signature_algorithm": config["algorithm"],
        "signature": b64e(signature),
    }
    _atomic_append(root / "checkpoints.jsonl", canonical_json(record) + b"\n")
    return {"idempotent": False, **record}
