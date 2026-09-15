"""Evidence engine for the offline NISHAN interactive demonstration."""

from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any

import pymupdf as fitz
from PIL import Image, ImageOps, UnidentifiedImageError

from .public_fixture import build_material, decode_public


MAX_UPLOAD_BYTES = 25 * 1024 * 1024
MAX_IMAGE_PIXELS = 40_000_000
PUBLIC_LIMITATIONS = [
    "A photograph without a recovered carrier is inconclusive; it is not proof that a page was unmarked.",
    "The public fixture uses a published test key and synthetic row, not a signed real-person identity.",
    "This prototype does not establish physical robustness, mathematical certainty, or human guilt.",
]


class InputError(ValueError):
    """An unsupported or unsafe user input."""


class DemoEngine:
    def __init__(self, workspace: Path, state_dir: Path) -> None:
        self.workspace = Path(workspace).resolve()
        self.state_dir = Path(state_dir).resolve()
        self.state_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
        os.chmod(self.state_dir, 0o700)
        self.reference = self.workspace / "artifacts/nishan/synthetic-source.pdf"
        self.reference_hash = self._sha3(self.reference)
        self._public_material = build_material(self.reference)

    @staticmethod
    def _sha3(path: Path) -> str:
        digest = hashlib.sha3_256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _validate_input(self, path: Path, temporary: Path) -> tuple[str, Path]:
        try:
            size = path.stat().st_size
        except OSError as error:
            raise InputError(f"Input could not be read: {error}") from error
        if size > MAX_UPLOAD_BYTES:
            raise InputError("Input exceeds the 25 MiB upload limit.")
        try:
            document = fitz.open(path)
            try:
                if document.is_pdf:
                    if document.needs_pass:
                        raise InputError("Encrypted PDFs are not supported.")
                    if document.page_count != 1:
                        raise InputError("Only a one-page PDF is supported by this demonstration.")
                    document[0].rect
                    return "pdf", path
            finally:
                document.close()
        except InputError:
            raise
        except (fitz.FileDataError, RuntimeError, ValueError):
            pass

        try:
            with Image.open(path) as image:
                if image.format not in {"JPEG", "PNG", "WEBP"}:
                    raise InputError("Only JPEG, PNG, WebP and PDF inputs are supported; HEIC is not supported.")
                if getattr(image, "n_frames", 1) != 1:
                    raise InputError("Only a single still image is supported.")
                if image.width * image.height > MAX_IMAGE_PIXELS:
                    raise InputError("Decoded image exceeds the 40 million pixels limit.")
                oriented = ImageOps.exif_transpose(image).convert("RGB")
                normalized = temporary / "exif-oriented.png"
                oriented.save(normalized, format="PNG")
                return image.format.lower(), normalized
        except InputError:
            raise
        except (UnidentifiedImageError, OSError, ValueError) as error:
            raise InputError(
                "Unsupported or malformed input. Use a one-page PDF, JPEG, PNG or WebP file."
            ) from error

    def _base_result(self, path: Path, input_type: str, started: float) -> dict[str, Any]:
        return {
            "file_sha3_256": self._sha3(path),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "diagnostics": {"input_type": input_type, "original_bytes": path.stat().st_size},
            "limitations": list(PUBLIC_LIMITATIONS),
        }

    def analyze(self, path: Path, mode: str) -> dict[str, Any]:
        if mode not in {"public", "signed"}:
            raise InputError("Mode must be public or signed.")
        path = Path(path)
        started = time.perf_counter()
        with tempfile.TemporaryDirectory(prefix="analysis-", dir=self.state_dir) as directory:
            input_type, analysis_path = self._validate_input(path, Path(directory))
            digest = self._sha3(path)
            if digest == self.reference_hash:
                return {
                    "kind": "known_original",
                    "title": "Known original — no watermark",
                    "summary": "The uploaded bytes exactly match the published unmarked source.",
                    "assurance": "exact_file_identity",
                    "recipients": [],
                    "channels": {
                        "exact_file_identity": {"match": True, "algorithm": "SHA3-256"},
                        "visual": {"status": "not needed after exact source match"},
                        "layout": {"status": "not needed after exact source match"},
                        "signature": {"available": False},
                    },
                    **self._base_result(path, input_type, started),
                }
            if mode == "public":
                extracted = decode_public(
                    self.reference, analysis_path, input_type, self._public_material
                )
                return self._public_result(path, input_type, extracted, started)
            return self._signed_result(path, analysis_path, input_type, started)

    def _public_result(
        self, path: Path, input_type: str, evidence: dict[str, Any], started: float
    ) -> dict[str, Any]:
        kind = evidence["decision"]
        recipients = []
        if kind in {"fixture_match", "research_lead"}:
            recipients = [{
                "recipient_id": "public-fixture-row-0000",
                "display_name": "Demo recipient 0000",
                "session_id": "public-fixture-session-0000",
                "row": 0,
                "signed_identity": False,
                "score": evidence["visual"]["fixture_row_score"],
            }]
        labels = {
            "fixture_match": (
                "Public test fixture recovered",
                "Visual row 0 and the editable-PDF layout tag agree. This is an unsigned reproducibility fixture.",
                "corroborated_public_fixture",
            ),
            "research_lead": (
                "Research lead — public fixture signal",
                "The raster visual carrier crossed the threshold, but no digital layout or signed ledger proof is present.",
                "visual_only_research_lead",
            ),
            "inconclusive": (
                "Inconclusive — no reliable watermark recovered",
                "The available channels did not produce one registered, non-conflicting identity.",
                "inconclusive",
            ),
        }
        title, summary, assurance = labels[kind]
        return {
            "kind": kind,
            "title": title,
            "summary": summary,
            "assurance": assurance,
            "recipients": recipients,
            "channels": {
                "exact_file_identity": {"match": False, "algorithm": "SHA3-256"},
                "visual": evidence["visual"],
                "layout": evidence["layout"],
                "signature": {"available": False, "status": "Public fixture: no recipient-signed ledger record."},
            },
            **self._base_result(path, input_type, started),
            "diagnostics": {
                **self._base_result(path, input_type, started)["diagnostics"],
                "registration": evidence["preprocessing"],
                "channel_conflict": evidence["conflict"],
            },
        }

    def _signed_result(
        self, original: Path, analysis_path: Path, input_type: str, started: float
    ) -> dict[str, Any]:
        run, manifest = self._current_signed()
        from nishan import core

        evidence = core.trace_leak(
            run / "source.pdf",
            analysis_path,
            run / "authority-secret.bin",
            run / "ledger",
            witness_root=run / "witness",
            witness_public_key_sha3_256=manifest["witness_public_key_sha3_256"],
        )
        registration = evidence.get("decoder", {}).get("preprocessing", {})
        pages = registration.get("pages", [])
        registration_ok = bool(pages) and all(
            not page.get("rejection_reason")
            and float(page.get("registered_similarity", 0.0)) >= 0.08
            for page in pages
        )
        attribution = evidence.get("attribution", [])
        leads = evidence.get("visual_only_research_leads", []) if registration_ok else []
        if attribution:
            kind, title, assurance, selected = (
                "verified_session",
                "Verified signed release",
                "verified_signed_session",
                attribution,
            )
        elif input_type != "pdf" and leads:
            kind, title, assurance, selected = (
                "research_lead",
                "Research lead — signed visual carrier",
                "visual_only_research_lead",
                leads,
            )
        else:
            kind, title, assurance, selected = (
                "inconclusive",
                "Inconclusive — no reliable watermark recovered",
                "inconclusive",
                [],
            )
        recipients = [{
            "recipient_id": item["recipient_id"],
            "display_name": item["recipient_display_name"],
            "session_id": item["session_id"],
            "row": item["fingerprint_user_index"],
            "score": item["score"],
            "recipient_signature_valid": item["recipient_signature_valid"],
        } for item in selected]
        return {
            "kind": kind,
            "title": title,
            "summary": (
                "The visual and layout carriers agree with a recipient-signed, witnessed release."
                if kind == "verified_session"
                else "A raster can supply a visual lead only; the signed digital-PDF layout channel is absent."
                if kind == "research_lead"
                else "The signed channels did not produce one corroborated release identity."
            ),
            "assurance": assurance,
            "recipients": recipients,
            "channels": {
                "exact_file_identity": {"match": False, "algorithm": "SHA3-256"},
                "visual": {
                    "threshold": evidence["detection_threshold"],
                    "accused_rows": evidence.get("accused_codebook_rows", []),
                    "research_leads": len(evidence.get("visual_only_research_leads", [])),
                },
                "layout": evidence.get("channel_decision", {}),
                "signature": {
                    "available": True,
                    "valid": bool(recipients) and all(item.get("recipient_signature_valid") for item in recipients),
                },
                "witness": evidence.get("ledger_witness", {}),
            },
            **self._base_result(original, input_type, started),
            "diagnostics": {
                **self._base_result(original, input_type, started)["diagnostics"],
                "registration": registration,
            },
        }

    def _pqc_status(self) -> tuple[bool, str]:
        try:
            from nishan import pqc
            status = pqc.support()
            return status.ready, status.openssl_version
        except (ImportError, OSError, RuntimeError) as error:
            return False, str(error)

    def capabilities(self) -> dict[str, Any]:
        ready, detail = self._pqc_status()
        return {"public": True, "signed": ready, "signed_detail": detail}

    def prepare_signed(self) -> dict[str, Any]:
        try:
            _, manifest = self._current_signed()
            return self._public_manifest(manifest)
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass
        ready, detail = self._pqc_status()
        if not ready:
            raise RuntimeError(f"PQC support is unavailable: {detail}. Public fixture mode remains available.")

        from nishan import core, ledger, witness
        from nishan.identity import create_identity
        from nishan.util import write_private

        runs = self.state_dir / "runs"
        runs.mkdir(mode=0o700, exist_ok=True)
        run_id = f"run-{uuid.uuid4().hex}"
        run = runs / run_id
        run.mkdir(mode=0o700)
        source = run / "source.pdf"
        shutil.copyfile(self.reference, source)
        identities = run / "identities"
        create_identity(identities, "alice", "Alice")
        create_identity(identities, "bob", "Bob")
        ledger.initialize(run / "ledger", identities_root=identities)
        secret = run / "authority-secret.bin"
        write_private(secret, os.urandom(32))
        package = run / "package.json"
        core.encrypt_once(source, identities, ["alice", "bob"], package)
        witness_config = witness.initialize(run / "witness")
        witness.checkpoint(run / "witness", ledger.audit(run / "ledger"))
        copies = run / "copies"
        copies.mkdir(mode=0o700)
        fixtures = []
        for recipient in ("alice", "bob"):
            output = copies / f"{recipient}.pdf"
            release = core.decrypt_and_attribute(
                package,
                identities,
                recipient,
                secret,
                run / "ledger",
                output,
                witness_root=run / "witness",
                witness_public_key_sha3_256=witness_config["public_key_sha3_256"],
            )
            event = release["event"]
            fixtures.append({
                "id": f"signed-{recipient}",
                "label": f"Signed {event['recipient_display_name']} copy",
                "mode": "signed",
                "recipient_id": event["recipient_id"],
                "display_name": event["recipient_display_name"],
                "session_id": event["session_id"],
                "relative_path": f"copies/{recipient}.pdf",
            })
        manifest = {
            "version": "nishan-interactive-signed-run/v1",
            "run_id": run_id,
            "witness_public_key_sha3_256": witness_config["public_key_sha3_256"],
            "fixtures": fixtures,
        }
        self._write_private_json(run / "manifest.json", manifest)
        self._write_private_json(self.state_dir / "current-run.json", {"run_id": run_id})
        return self._public_manifest(manifest)

    @staticmethod
    def _write_private_json(path: Path, value: dict[str, Any]) -> None:
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(value, handle, indent=2, sort_keys=True)
            handle.write("\n")
        os.replace(temporary, path)

    def _current_signed(self) -> tuple[Path, dict[str, Any]]:
        pointer = json.loads((self.state_dir / "current-run.json").read_text())
        run_id = pointer.get("run_id")
        if not isinstance(run_id, str) or not re.fullmatch(r"run-[0-9a-f]{32}", run_id):
            raise ValueError("invalid current signed run pointer")
        runs = (self.state_dir / "runs").resolve()
        run = (runs / run_id).resolve()
        if run.parent != runs or not run.is_dir():
            raise ValueError("current signed run is outside local state")
        manifest = json.loads((run / "manifest.json").read_text())
        if manifest.get("run_id") != run_id:
            raise ValueError("signed run manifest does not match its directory")
        return run, manifest

    @staticmethod
    def _public_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
        return {
            "run_id": manifest["run_id"],
            "fixtures": [
                {key: value for key, value in item.items() if key != "relative_path"}
                for item in manifest["fixtures"]
            ],
        }

    def fixtures(self) -> list[dict[str, Any]]:
        fixtures = [
            {"id": "source", "label": "Try original", "mode": "public", "kind": "original"},
            {"id": "public-marked", "label": "Try marked", "mode": "public", "kind": "marked"},
            {"id": "public-screenshot", "label": "Try screenshot (digital transformation)", "mode": "public", "kind": "screenshot"},
        ]
        try:
            _, manifest = self._current_signed()
            fixtures.extend(self._public_manifest(manifest)["fixtures"])
        except (FileNotFoundError, ValueError, json.JSONDecodeError):
            pass
        return fixtures

    def fixture_path(self, fixture_id: str) -> Path:
        public = {
            "source": self.reference,
            "source-preview": self.workspace / "artifacts/nishan/source-page.png",
            "public-marked": self.workspace / "artifacts/nishan/dual-carrier-user-0000-live-text.pdf",
            "public-screenshot": self.workspace / "artifacts/nishan/dual-carrier-user-0000-screenshot.png",
        }
        if fixture_id in public:
            return public[fixture_id]
        run, manifest = self._current_signed()
        for item in manifest["fixtures"]:
            if item.get("id") != fixture_id:
                continue
            relative = Path(str(item.get("relative_path", "")))
            target = (run / relative).resolve()
            if relative.is_absolute() or target.parent != (run / "copies").resolve() or target.suffix.lower() != ".pdf":
                raise ValueError("invalid signed fixture path")
            if not target.is_file():
                raise FileNotFoundError(target)
            return target
        raise KeyError(fixture_id)
