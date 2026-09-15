from __future__ import annotations

from pathlib import Path

from . import pqc
from .util import read_json, sha3_file, write_json


def create_identity(root: Path, identity_id: str, display_name: str) -> dict[str, str]:
    identity = root / identity_id
    if identity.exists():
        raise FileExistsError(f"identity already exists: {identity}")
    identity.mkdir(parents=True)
    pqc.generate_keypair("ML-KEM-768", identity / "kem-private.pem", identity / "kem-public.pem")
    pqc.generate_keypair("ML-DSA-65", identity / "sign-private.pem", identity / "sign-public.pem")
    profile = {
        "identity_id": identity_id,
        "display_name": display_name,
        "kem_algorithm": "ML-KEM-768 (FIPS 203)",
        "signature_algorithm": "ML-DSA-65 (FIPS 204)",
        "kem_public_key_sha3_256": sha3_file(identity / "kem-public.pem"),
        "sign_public_key_sha3_256": sha3_file(identity / "sign-public.pem"),
    }
    write_json(identity / "profile.json", profile)
    return profile


def load_identity(root: Path, identity_id: str) -> dict[str, object]:
    identity = root / identity_id
    profile = read_json(identity / "profile.json")
    return {
        "root": identity,
        "profile": profile,
        "kem_private": identity / "kem-private.pem",
        "kem_public": identity / "kem-public.pem",
        "sign_private": identity / "sign-private.pem",
        "sign_public": identity / "sign-public.pem",
    }


def registry_snapshot(root: Path) -> dict[str, dict[str, str]]:
    """Build a validated public enrollment registry from local identities.

    The ledger trust root signs this snapshot. Private-key paths and key material
    are deliberately excluded.
    """

    if not root.is_dir():
        raise FileNotFoundError(f"identity root does not exist: {root}")
    registry: dict[str, dict[str, str]] = {}
    for identity_dir in sorted(path for path in root.iterdir() if path.is_dir()):
        profile_path = identity_dir / "profile.json"
        sign_public = identity_dir / "sign-public.pem"
        kem_public = identity_dir / "kem-public.pem"
        if not profile_path.is_file() or not sign_public.is_file() or not kem_public.is_file():
            raise ValueError(f"incomplete identity directory: {identity_dir}")
        profile = read_json(profile_path)
        identity_id = profile.get("identity_id")
        if not isinstance(identity_id, str) or identity_id != identity_dir.name:
            raise ValueError(f"identity id does not match directory: {identity_dir}")
        if identity_id in registry:
            raise ValueError(f"duplicate identity id: {identity_id}")
        actual_sign_hash = sha3_file(sign_public)
        actual_kem_hash = sha3_file(kem_public)
        if profile.get("sign_public_key_sha3_256") != actual_sign_hash:
            raise ValueError(f"signing public-key hash mismatch for {identity_id}")
        if profile.get("kem_public_key_sha3_256") != actual_kem_hash:
            raise ValueError(f"KEM public-key hash mismatch for {identity_id}")
        registry[identity_id] = {
            "identity_id": identity_id,
            "display_name": str(profile["display_name"]),
            "kem_algorithm": str(profile["kem_algorithm"]),
            "signature_algorithm": str(profile["signature_algorithm"]),
            "kem_public_key_sha3_256": actual_kem_hash,
            "sign_public_key_sha3_256": actual_sign_hash,
        }
    if not registry:
        raise ValueError("identity registry must contain at least one identity")
    return registry
