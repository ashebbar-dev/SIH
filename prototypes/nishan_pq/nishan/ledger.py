from __future__ import annotations

import json
import os
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
from pathlib import Path
from typing import Any

from . import pqc
from .identity import registry_snapshot
from .util import (
    b64d,
    b64e,
    canonical_json,
    read_json,
    sha3_bytes,
    sha3_file,
    write_json,
)


@contextmanager
def exclusive(root: Path):
    """Serialize local ledger transactions across processes and threads.

    The demonstrator stores all replicas on one filesystem, so one advisory
    lock can cover audit, row allocation, rendering, and commit. A distributed
    deployment replaces this with consensus-backed transactional allocation.
    """

    lock_path = root / ".transaction.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def initialize(
    root: Path,
    validator_count: int = 4,
    quorum: int = 3,
    identities_root: Path | None = None,
) -> dict[str, Any]:
    if validator_count < 1 or not (1 <= quorum <= validator_count):
        raise ValueError("quorum must be between one and validator count")
    if identities_root is None:
        raise ValueError("identities_root is required to bind enrolled recipient keys")
    if root.exists():
        raise FileExistsError(f"ledger already exists: {root}")
    identity_registry = registry_snapshot(identities_root)
    validators: list[dict[str, str]] = []
    for number in range(1, validator_count + 1):
        validator_id = f"validator-{number}"
        key_root = root / "validators" / validator_id
        private_key = key_root / "private.pem"
        public_key = key_root / "public.pem"
        pqc.generate_keypair("ML-DSA-65", private_key, public_key)
        (root / "replicas" / validator_id).mkdir(parents=True)
        (root / "replicas" / validator_id / "ledger.jsonl").touch()
        validators.append(
            {
                "validator_id": validator_id,
                "private_key": str(private_key.relative_to(root)),
                "public_key": str(public_key.relative_to(root)),
                "public_key_sha3_256": sha3_file(public_key),
            }
        )
    config_core = {
        "version": "nishan-quorum-ledger/v2-enrollment-root",
        "quorum": quorum,
        "validators": validators,
        "identity_registry": identity_registry,
        "identity_registry_sha3_256": sha3_bytes(canonical_json(identity_registry)),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    trust_root_hash = sha3_bytes(canonical_json(config_core))
    trust_root_endorsements = {
        validator["validator_id"]: b64e(
            pqc.sign(
                root / validator["private_key"],
                trust_root_hash.encode("ascii"),
            )
        )
        for validator in validators
    }
    config = {
        **config_core,
        "trust_root_hash": trust_root_hash,
        "trust_root_endorsements": trust_root_endorsements,
    }
    write_json(root / "config.json", config)
    return config


def _config(root: Path) -> dict[str, Any]:
    return read_json(root / "config.json")


def _read_replica(path: Path) -> list[dict[str, Any]]:
    blocks: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if line.strip():
            blocks.append(json.loads(line))
    return blocks


def _validate_trust_root(root: Path, config: dict[str, Any]) -> tuple[bool, str]:
    if config.get("version") != "nishan-quorum-ledger/v2-enrollment-root":
        return False, "unsupported or unsigned ledger configuration"
    config_core = {
        key: value
        for key, value in config.items()
        if key not in {"trust_root_hash", "trust_root_endorsements"}
    }
    calculated = sha3_bytes(canonical_json(config_core))
    if config.get("trust_root_hash") != calculated:
        return False, "trust-root hash mismatch"
    registry = config.get("identity_registry")
    if not isinstance(registry, dict) or not registry:
        return False, "identity registry is missing or empty"
    if config.get("identity_registry_sha3_256") != sha3_bytes(canonical_json(registry)):
        return False, "identity-registry commitment mismatch"
    validators = config.get("validators")
    if not isinstance(validators, list):
        return False, "validator registry is malformed"
    try:
        quorum = int(config["quorum"])
    except (KeyError, TypeError, ValueError):
        return False, "validator quorum is malformed"
    valid_signers: set[str] = set()
    endorsements = config.get("trust_root_endorsements", {})
    if not isinstance(endorsements, dict):
        return False, "trust-root endorsements are malformed"
    for validator in validators:
        try:
            validator_id = validator["validator_id"]
            public_key = root / validator["public_key"]
            if sha3_file(public_key) != validator["public_key_sha3_256"]:
                continue
            encoded_signature = endorsements.get(validator_id)
            if encoded_signature is not None and pqc.verify(
                public_key,
                calculated.encode("ascii"),
                b64d(encoded_signature),
            ):
                valid_signers.add(validator_id)
                if len(valid_signers) >= quorum:
                    break
        except (KeyError, OSError, TypeError, ValueError):
            continue
    if len(valid_signers) < quorum:
        return False, "trust-root endorsement quorum not met"
    return True, "valid"


def _validate_block(root: Path, config: dict[str, Any], block: dict[str, Any], previous: str) -> tuple[bool, str]:
    core = block.get("core")
    if not isinstance(core, dict):
        return False, "missing block core"
    if core.get("previous_hash") != previous:
        return False, "previous hash mismatch"
    if core.get("trust_root_hash") != config.get("trust_root_hash"):
        return False, "trust-root binding mismatch"
    calculated = sha3_bytes(canonical_json(core))
    if block.get("block_hash") != calculated:
        return False, "block hash mismatch"
    public_keys = {
        item["validator_id"]: root / item["public_key"] for item in config["validators"]
    }
    valid_signers: set[str] = set()
    quorum = int(config["quorum"])
    for validator_id, encoded_signature in block.get("endorsements", {}).items():
        public_key = public_keys.get(validator_id)
        if public_key is not None and pqc.verify(
            public_key, calculated.encode("ascii"), b64d(encoded_signature)
        ):
            valid_signers.add(validator_id)
            if len(valid_signers) >= quorum:
                break
    if len(valid_signers) < quorum:
        return False, "endorsement quorum not met"
    return True, "valid"


def audit(root: Path) -> dict[str, Any]:
    config = _config(root)
    trust_root_valid, trust_root_reason = _validate_trust_root(root, config)
    if not trust_root_valid:
        return {
            "quorum_valid": False,
            "trust_root_valid": False,
            "configuration_failure": trust_root_reason,
            "canonical_length": 0,
            "canonical_head": None,
            "supporting_replicas": [],
            "divergent_replicas": [],
            "replicas": {},
            "blocks": [],
            "identity_registry": config.get("identity_registry", {}),
            "identity_registry_sha3_256": config.get(
                "identity_registry_sha3_256"
            ),
        }
    replica_results: dict[str, dict[str, Any]] = {}
    valid_chains: dict[str, list[dict[str, Any]]] = {}
    # Every demonstrator replica stores the same endorsed block bytes. Verify
    # each unique (block, predecessor) once per audit, while still walking every
    # replica independently so truncation, insertion, or mutation is detected.
    block_validation_cache: dict[tuple[str, str], tuple[bool, str]] = {}
    for validator in config["validators"]:
        validator_id = validator["validator_id"]
        path = root / "replicas" / validator_id / "ledger.jsonl"
        previous = config["trust_root_hash"]
        valid: list[dict[str, Any]] = []
        failure: str | None = None
        blocks: list[dict[str, Any]] = []
        try:
            blocks = _read_replica(path)
            for expected_index, block in enumerate(blocks):
                if block.get("core", {}).get("index") != expected_index:
                    failure = f"unexpected block index at {expected_index}"
                    break
                serialized_hash = sha3_bytes(canonical_json(block))
                cache_key = (previous, serialized_hash)
                if cache_key not in block_validation_cache:
                    block_validation_cache[cache_key] = _validate_block(
                        root, config, block, previous
                    )
                okay, reason = block_validation_cache[cache_key]
                if not okay:
                    failure = f"block {expected_index}: {reason}"
                    break
                valid.append(block)
                previous = block["block_hash"]
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            failure = str(exc)
        valid_chains[validator_id] = valid
        replica_results[validator_id] = {
            "observed_blocks": len(blocks),
            "valid_blocks": len(valid),
            "failure": failure,
        }

    canonical: list[dict[str, Any]] = []
    index = 0
    while True:
        candidates = [
            chain[index] for chain in valid_chains.values() if len(chain) > index
        ]
        if not candidates:
            break
        counts = Counter(block["block_hash"] for block in candidates)
        block_hash, copies = counts.most_common(1)[0]
        if copies < int(config["quorum"]):
            break
        canonical.append(next(block for block in candidates if block["block_hash"] == block_hash))
        index += 1

    supporting_replicas = [
        validator_id
        for validator_id, chain in valid_chains.items()
        if replica_results[validator_id]["failure"] is None
        and len(chain) == len(canonical)
        and all(
            chain[position]["block_hash"] == canonical[position]["block_hash"]
            for position in range(len(canonical))
        )
    ]
    divergent = [
        validator_id
        for validator_id, chain in valid_chains.items()
        if validator_id not in supporting_replicas
        or len(chain) != len(canonical)
        or any(
            chain[position]["block_hash"] != canonical[position]["block_hash"]
            for position in range(min(len(chain), len(canonical)))
        )
    ]
    return {
        "quorum_valid": len(supporting_replicas) >= int(config["quorum"]),
        "trust_root_valid": True,
        "configuration_failure": None,
        "canonical_length": len(canonical),
        "canonical_head": (
            canonical[-1]["block_hash"]
            if canonical
            else config["trust_root_hash"]
        ),
        "supporting_replicas": supporting_replicas,
        "divergent_replicas": divergent,
        "replicas": replica_results,
        "blocks": canonical,
        "identity_registry": config["identity_registry"],
        "identity_registry_sha3_256": config["identity_registry_sha3_256"],
        "trust_root_hash": config["trust_root_hash"],
    }


def _atomic_append(path: Path, encoded: bytes) -> None:
    """Replace one replica with a fully written and fsynced successor file."""

    current = path.read_bytes()
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            dir=path.parent,
            prefix=".ledger-next-",
            delete=False,
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


def append(
    root: Path,
    record: dict[str, Any],
    *,
    lock_held: bool = False,
) -> dict[str, Any]:
    if not lock_held:
        with exclusive(root):
            return append(root, record, lock_held=True)
    config = _config(root)
    state = audit(root)
    if not state["quorum_valid"] or state["divergent_replicas"]:
        raise RuntimeError("ledger replicas must be healthy before a new commit")
    core = {
        "index": state["canonical_length"],
        "previous_hash": state["canonical_head"],
        "trust_root_hash": config["trust_root_hash"],
        "committed_at": datetime.now(timezone.utc).isoformat(),
        "record": record,
    }
    block_hash = sha3_bytes(canonical_json(core))
    endorsements: dict[str, str] = {}
    for validator in config["validators"]:
        validator_id = validator["validator_id"]
        signature = pqc.sign(root / validator["private_key"], block_hash.encode("ascii"))
        endorsements[validator_id] = b64e(signature)
    block = {"core": core, "block_hash": block_hash, "endorsements": endorsements}
    encoded = canonical_json(block) + b"\n"
    for validator in config["validators"]:
        path = root / "replicas" / validator["validator_id"] / "ledger.jsonl"
        _atomic_append(path, encoded)
    return block
