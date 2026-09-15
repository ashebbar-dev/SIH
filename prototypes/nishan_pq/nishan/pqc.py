from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


class PQCError(RuntimeError):
    pass


@dataclass(frozen=True)
class PQCSupport:
    openssl_version: str
    ml_kem_768: bool
    ml_dsa_65: bool

    @property
    def ready(self) -> bool:
        return self.ml_kem_768 and self.ml_dsa_65


def _run(arguments: list[str]) -> subprocess.CompletedProcess[bytes]:
    try:
        return subprocess.run(
            arguments,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError as exc:
        raise PQCError("OpenSSL was not found on PATH") from exc
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise PQCError(f"OpenSSL command failed: {detail}") from exc


@lru_cache(maxsize=1)
def support() -> PQCSupport:
    binary = shutil.which("openssl")
    if binary is None:
        return PQCSupport("missing", False, False)
    version = _run([binary, "version"]).stdout.decode().strip()
    kem = _run([binary, "list", "-kem-algorithms"]).stdout.decode()
    signatures = _run([binary, "list", "-signature-algorithms"]).stdout.decode()
    return PQCSupport(
        openssl_version=version,
        ml_kem_768=bool(re.search(r"ML-?KEM-?768", kem, re.IGNORECASE)),
        ml_dsa_65=bool(re.search(r"ML-?DSA-?65", signatures, re.IGNORECASE)),
    )


def require_support() -> PQCSupport:
    result = support()
    if not result.ready:
        raise PQCError(
            "NISHAN requires OpenSSL with ML-KEM-768 and ML-DSA-65 enabled; "
            f"detected {result.openssl_version!r}"
        )
    return result


def generate_keypair(algorithm: str, private_key: Path, public_key: Path) -> None:
    require_support()
    private_key.parent.mkdir(parents=True, exist_ok=True)
    public_key.parent.mkdir(parents=True, exist_ok=True)
    _run(["openssl", "genpkey", "-algorithm", algorithm, "-out", str(private_key)])
    os.chmod(private_key, 0o600)
    _run(
        [
            "openssl",
            "pkey",
            "-in",
            str(private_key),
            "-pubout",
            "-out",
            str(public_key),
        ]
    )


def encapsulate(public_key: Path) -> tuple[bytes, bytes]:
    """Return (KEM ciphertext, shared secret)."""
    require_support()
    with tempfile.TemporaryDirectory(prefix="nishan-kem-") as directory:
        root = Path(directory)
        ciphertext = root / "ciphertext.bin"
        secret = root / "secret.bin"
        _run(
            [
                "openssl",
                "pkeyutl",
                "-encap",
                "-pubin",
                "-inkey",
                str(public_key),
                "-out",
                str(ciphertext),
                "-secret",
                str(secret),
            ]
        )
        return ciphertext.read_bytes(), secret.read_bytes()


def decapsulate(private_key: Path, ciphertext: bytes) -> bytes:
    require_support()
    with tempfile.TemporaryDirectory(prefix="nishan-kem-") as directory:
        root = Path(directory)
        ciphertext_path = root / "ciphertext.bin"
        secret = root / "secret.bin"
        ciphertext_path.write_bytes(ciphertext)
        _run(
            [
                "openssl",
                "pkeyutl",
                "-decap",
                "-inkey",
                str(private_key),
                "-in",
                str(ciphertext_path),
                "-secret",
                str(secret),
            ]
        )
        return secret.read_bytes()


def sign(private_key: Path, message: bytes) -> bytes:
    require_support()
    with tempfile.TemporaryDirectory(prefix="nishan-sign-") as directory:
        root = Path(directory)
        message_path = root / "message.bin"
        signature_path = root / "signature.bin"
        message_path.write_bytes(message)
        _run(
            [
                "openssl",
                "pkeyutl",
                "-sign",
                "-rawin",
                "-inkey",
                str(private_key),
                "-in",
                str(message_path),
                "-out",
                str(signature_path),
            ]
        )
        return signature_path.read_bytes()


def verify(public_key: Path, message: bytes, signature: bytes) -> bool:
    require_support()
    with tempfile.TemporaryDirectory(prefix="nishan-verify-") as directory:
        root = Path(directory)
        message_path = root / "message.bin"
        signature_path = root / "signature.bin"
        message_path.write_bytes(message)
        signature_path.write_bytes(signature)
        try:
            _run(
                [
                    "openssl",
                    "pkeyutl",
                    "-verify",
                    "-rawin",
                    "-pubin",
                    "-inkey",
                    str(public_key),
                    "-in",
                    str(message_path),
                    "-sigfile",
                    str(signature_path),
                ]
            )
            return True
        except PQCError:
            return False
