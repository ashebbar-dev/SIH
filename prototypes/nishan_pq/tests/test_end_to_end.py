from __future__ import annotations

import json
import os
import copy
import shutil
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

from nishan import ledger, pqc, watermark, witness
from nishan.core import decrypt_and_attribute, encrypt_once, trace_leak
from nishan.identity import create_identity, load_identity
from nishan.util import b64d, b64e, canonical_json, sha3_file, write_private


@unittest.skipUnless(pqc.support().ready, "OpenSSL PQC provider is unavailable")
class EndToEndTests(unittest.TestCase):
    def _source(self, path: Path) -> None:
        image = Image.new("RGB", (900, 1200), "#f5f2e9")
        draw = ImageDraw.Draw(image)
        draw.rectangle((45, 45, 855, 1155), outline="#1c2c4a", width=5)
        draw.text((90, 100), "RESTRICTED TEST DOCUMENT", fill="#781d24")
        for row in range(12):
            draw.line((90, 190 + row * 65, 810, 190 + row * 65), fill="#526078", width=2)
        image.save(path)

    def test_jpeg_attribution_collusion_scoring_and_quorum_tamper_detection(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.png"
            self._source(source)
            identities = root / "identities"
            create_identity(identities, "alice", "Alice")
            create_identity(identities, "bob", "Bob")
            create_identity(identities, "charlie", "Charlie")
            ledger_root = root / "ledger"
            ledger.initialize(
                ledger_root,
                validator_count=4,
                quorum=3,
                identities_root=identities,
            )
            secret = root / "authority-secret.bin"
            write_private(secret, os.urandom(32))
            package = root / "broadcast.json"
            encrypted = encrypt_once(source, identities, ["alice", "bob", "charlie"], package)
            self.assertEqual(encrypted["source"]["media_type"], "image")

            unauthorized_output = root / "mallory.png"
            with self.assertRaises(PermissionError):
                decrypt_and_attribute(
                    package,
                    identities,
                    "mallory",
                    secret,
                    ledger_root,
                    unauthorized_output,
                )
            self.assertFalse(unauthorized_output.exists())

            copies: dict[str, Path] = {}
            for recipient in ["alice", "bob", "charlie"]:
                copy_path = root / f"{recipient}.png"
                release = decrypt_and_attribute(
                    package, identities, recipient, secret, ledger_root, copy_path
                )
                self.assertEqual(release["event"]["fingerprint"]["scheme"],
                                 "nishan-spread-spectrum-session/v1")
                copies[recipient] = copy_path

            attacked = root / "bob-q45.jpg"
            watermark.jpeg_attack(copies["bob"], attacked, quality=45)
            evidence = trace_leak(
                source, attacked, secret, ledger_root, null_samples=32
            )
            self.assertEqual([item["recipient_id"] for item in evidence["attribution"]], ["bob"])
            self.assertTrue(evidence["attribution"][0]["recipient_signature_valid"])
            self.assertFalse(
                evidence["threshold_calibration"]["formal_familywise_bound_established"]
            )
            self.assertGreaterEqual(
                evidence["detection_threshold"],
                evidence["threshold_calibration"]["null_max"],
            )

            averaged = root / "alice-bob-average.png"
            watermark.average_collusion([copies["alice"], copies["bob"]], averaged)
            coalition = trace_leak(
                source, averaged, secret, ledger_root, null_samples=32
            )
            self.assertEqual(
                {item["recipient_id"] for item in coalition["attribution"]},
                {"alice", "bob"},
            )

            three_way = root / "alice-bob-charlie-average.png"
            watermark.average_collusion(list(copies.values()), three_way)
            three_way_evidence = trace_leak(
                source, three_way, secret, ledger_root, null_samples=32
            )
            self.assertEqual(
                {item["recipient_id"] for item in three_way_evidence["attribution"]},
                {"alice", "bob", "charlie"},
            )

            witness_root = root / "external-witness"
            witness.initialize(witness_root)
            healthy_state = ledger.audit(ledger_root)
            witness.checkpoint(witness_root, healthy_state)
            self.assertEqual(
                witness.audit(witness_root, healthy_state)["ledger_comparison"],
                "consistent",
            )
            rollback_ledger = root / "coordinated-rollback-ledger"
            shutil.copytree(ledger_root, rollback_ledger)
            for validator in (
                "validator-1",
                "validator-2",
                "validator-3",
                "validator-4",
            ):
                replica_path = (
                    rollback_ledger / "replicas" / validator / "ledger.jsonl"
                )
                replica_lines = replica_path.read_text().splitlines()
                replica_path.write_text("\n".join(replica_lines[:-1]) + "\n")
            rolled_back_state = ledger.audit(rollback_ledger)
            self.assertTrue(rolled_back_state["quorum_valid"])
            self.assertEqual(rolled_back_state["canonical_length"], 2)
            rollback_witness = witness.audit(witness_root, rolled_back_state)
            self.assertEqual(
                rollback_witness["ledger_comparison"], "rollback_detected"
            )

            valid_record = ledger.audit(ledger_root)["blocks"][0]["core"]["record"]

            replay_ledger = root / "replayed-receipt-ledger"
            shutil.copytree(ledger_root, replay_ledger)
            ledger.append(replay_ledger, copy.deepcopy(valid_record))
            with self.assertRaisesRegex(RuntimeError, "replayed receipts"):
                trace_leak(source, attacked, secret, replay_ledger, null_samples=32)
            replay_output = root / "must-not-release-replayed-history.png"
            with self.assertRaisesRegex(RuntimeError, "replayed receipts"):
                decrypt_and_attribute(
                    package,
                    identities,
                    "alice",
                    secret,
                    replay_ledger,
                    replay_output,
                )
            self.assertFalse(replay_output.exists())

            # A cryptographically valid self-asserted key must not be allowed to
            # claim an enrolled identity. The trust root binds Alice to the key
            # that existed when the ledger was initialized.
            substitution_ledger = root / "identity-substitution-ledger"
            shutil.copytree(ledger_root, substitution_ledger)
            rogue_identities = root / "rogue-identities"
            create_identity(rogue_identities, "alice", "Commander Alice Rao")
            rogue = load_identity(rogue_identities, "alice")
            substituted_record = copy.deepcopy(valid_record)
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
            ledger.append(substitution_ledger, substituted_record)
            with self.assertRaisesRegex(RuntimeError, "invalid recipient signature"):
                trace_leak(
                    source,
                    attacked,
                    secret,
                    substitution_ledger,
                    null_samples=32,
                )

            # The enrollment registry is part of a quorum-signed trust root, not
            # an editable label next to the chain.
            registry_tamper_ledger = root / "registry-tamper-ledger"
            shutil.copytree(ledger_root, registry_tamper_ledger)
            config_path = registry_tamper_ledger / "config.json"
            config = json.loads(config_path.read_text())
            config["identity_registry"]["alice"]["display_name"] = "Mallory"
            config_path.write_text(json.dumps(config, indent=2, sort_keys=True) + "\n")
            tampered_root = ledger.audit(registry_tamper_ledger)
            self.assertFalse(tampered_root["quorum_valid"])
            self.assertFalse(tampered_root["trust_root_valid"])
            self.assertEqual(
                tampered_root["configuration_failure"], "trust-root hash mismatch"
            )
            registry_tamper_output = root / "must-not-release-registry-tamper.png"
            with self.assertRaises(RuntimeError):
                decrypt_and_attribute(
                    package,
                    identities,
                    "alice",
                    secret,
                    registry_tamper_ledger,
                    registry_tamper_output,
                )
            self.assertFalse(registry_tamper_output.exists())

            # Validator endorsement is not a substitute for the recipient's
            # signature. Simulate validators accepting a corrupted receipt and
            # require both trace and future row assignment to fail closed.
            invalid_record = copy.deepcopy(valid_record)
            broken_signature = bytearray(b64d(invalid_record["recipient_signature"]))
            broken_signature[0] ^= 1
            invalid_record["recipient_signature"] = b64e(bytes(broken_signature))
            ledger.append(ledger_root, invalid_record)
            with self.assertRaisesRegex(RuntimeError, "invalid recipient signature"):
                trace_leak(source, attacked, secret, ledger_root, null_samples=32)
            invalid_history_output = root / "must-not-release-invalid-history.png"
            with self.assertRaisesRegex(RuntimeError, "invalid recipient signature"):
                decrypt_and_attribute(
                    package,
                    identities,
                    "alice",
                    secret,
                    ledger_root,
                    invalid_history_output,
                )
            self.assertFalse(invalid_history_output.exists())

            replica = ledger_root / "replicas" / "validator-1" / "ledger.jsonl"
            lines = replica.read_text().splitlines()
            changed = json.loads(lines[0])
            changed["core"]["record"]["event"]["recipient_id"] = "mallory"
            lines[0] = json.dumps(changed, sort_keys=True, separators=(",", ":"))
            replica.write_text("\n".join(lines) + "\n")
            state = ledger.audit(ledger_root)
            self.assertTrue(state["quorum_valid"])
            self.assertEqual(len(state["supporting_replicas"]), 3)
            self.assertEqual(state["divergent_replicas"], ["validator-1"])
            self.assertIn("block hash mismatch", state["replicas"]["validator-1"]["failure"])

            blocked_output = root / "must-not-be-released.png"
            with self.assertRaises(RuntimeError):
                decrypt_and_attribute(
                    package,
                    identities,
                    "alice",
                    secret,
                    ledger_root,
                    blocked_output,
                )
            self.assertFalse(blocked_output.exists())

            # A shared invalid prefix must not be misread as a healthy empty ledger.
            for validator in ("validator-2", "validator-3", "validator-4"):
                destination = ledger_root / "replicas" / validator / "ledger.jsonl"
                destination.write_text(replica.read_text())
            fully_corrupt = ledger.audit(ledger_root)
            self.assertFalse(fully_corrupt["quorum_valid"])
            self.assertEqual(fully_corrupt["supporting_replicas"], [])


if __name__ == "__main__":
    unittest.main()
