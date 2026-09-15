from __future__ import annotations

import multiprocessing as mp
import os
import queue
import tempfile
import traceback
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz

from nishan import core, ledger, pqc, witness
from nishan.demo import _sample_pdf, _transplant_first_image
from nishan.identity import create_identity, load_identity
from nishan.util import b64e, canonical_json, read_json, sha3_file, write_json, write_private


def issuance_worker(root_string, number, barrier, allocated, attempted, resume, results):
    """Hold the first allocation while the second independently enters release."""
    root = Path(root_string)
    original_allocate = core._next_tardos_index
    original_exclusive = ledger.exclusive

    def allocate(*args, **kwargs):
        value = original_allocate(*args, **kwargs)
        if number == 1:
            allocated.set()
            if not resume.wait(120):
                raise TimeoutError("allocation hold was not released")
        return value

    @contextmanager
    def exclusive(*args, **kwargs):
        if number == 2:
            attempted.set()
        with original_exclusive(*args, **kwargs):
            yield

    try:
        barrier.wait(timeout=120)
        if number == 2 and not allocated.wait(120):
            raise TimeoutError("first allocation was not observed")
        with patch.object(core, "_next_tardos_index", allocate), patch.object(ledger, "exclusive", exclusive):
            result = core.decrypt_and_attribute(root / "package.json", root / "identities",
                "alice", root / "secret.bin", root / "ledger", root / f"concurrent-{number}.pdf")
        results.put({"result": result})
    except BaseException:
        results.put({"error": traceback.format_exc()})


def concurrent_releases(root):
    context = mp.get_context("spawn")
    barrier = context.Barrier(2)
    allocated, attempted, resume = (context.Event() for _ in range(3))
    results = context.Queue()
    workers = [context.Process(target=issuance_worker, args=(str(root), number, barrier,
        allocated, attempted, resume, results)) for number in (1, 2)]
    try:
        for worker in workers:
            worker.start()
        if not allocated.wait(120) or not attempted.wait(120):
            raise AssertionError("deterministic allocation/lock overlap was not reached")
        resume.set()
        outputs = []
        for _ in workers:
            try:
                item = results.get(timeout=120)
            except queue.Empty as error:
                raise AssertionError("release worker produced no result") from error
            if "error" in item:
                raise AssertionError(item["error"])
            outputs.append(item["result"])
        for worker in workers:
            worker.join(120)
            if worker.is_alive() or worker.exitcode != 0:
                raise AssertionError(f"release worker failed: {worker.exitcode}")
        return outputs
    finally:
        resume.set()
        for worker in workers:
            if worker.is_alive():
                worker.terminate()
            worker.join(5)
        results.close()


@unittest.skipUnless(pqc.support().ready, "OpenSSL PQC provider is unavailable")
class ReleaseSafeguardsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.source = self.root / "source.pdf"
        _sample_pdf(self.source)
        self.identities = self.root / "identities"
        for name in ("alice", "bob"):
            create_identity(self.identities, name, name.title())
        self.ledger = self.root / "ledger"
        ledger.initialize(self.ledger, validator_count=4, quorum=3, identities_root=self.identities)
        self.secret = self.root / "secret.bin"
        write_private(self.secret, os.urandom(32))
        self.package = self.root / "package.json"
        core.encrypt_once(self.source, self.identities, ["alice", "bob"], self.package)
        self.witness = self.root / "witness"
        self.pin = witness.initialize(self.witness)["public_key_sha3_256"]
        witness.checkpoint(self.witness, ledger.audit(self.ledger))

    def release(self, output=None, **kwargs):
        return core.decrypt_and_attribute(self.package, self.identities, "alice", self.secret,
            self.ledger, output or self.root / "out.pdf", **kwargs)

    def strict(self):
        return {"witness_root": self.witness, "witness_public_key_sha3_256": self.pin}

    def trace(self, suspect=None, **kwargs):
        return core.trace_leak(self.source, suspect or self.root / "out.pdf", self.secret,
                               self.ledger, **kwargs)

    def test_pinned_happy_path_and_read_only_trace(self):
        result = self.release(**self.strict())
        assurance = result["release_assurance"]
        self.assertTrue(assurance["witness_enforced"])
        self.assertEqual(result["event"]["release_assurance"]["witness_public_key_sha3_256"], self.pin)
        self.assertEqual(result["event"]["released_copy_sha3_256"], sha3_file(self.root / "out.pdf"))
        before = (self.witness / "checkpoints.jsonl").read_bytes()
        with patch.object(witness, "checkpoint", side_effect=AssertionError("trace must not checkpoint")):
            evidence = self.trace(**self.strict())
        self.assertEqual(evidence["ledger_witness"]["ledger_comparison"], "consistent")
        self.assertEqual(evidence["ledger_witness"]["observed_ledger_head"], evidence["ledger"]["canonical_head"])
        self.assertEqual(evidence["channel_decision"]["decision"], "corroborated_channels")
        self.assertEqual([item["recipient_id"] for item in evidence["attribution"]], ["alice"])
        self.assertEqual(before, (self.witness / "checkpoints.jsonl").read_bytes())

    def test_workspace_destination_can_be_on_another_filesystem(self):
        # /tmp and the workspace are different mounts in the demonstration
        # environment. This also exercises destination staging on single-mount hosts.
        with tempfile.TemporaryDirectory(dir=Path(__file__).resolve().parents[3],
                                         prefix=".release-destination-test-") as directory:
            output = Path(directory) / "released.pdf"
            result = self.release(output, **self.strict())
            self.assertEqual(result["event"]["released_copy_sha3_256"], sha3_file(output))

    def test_pdf_source_label_tampering_before_first_strict_release_rejected(self):
        package = read_json(self.package)
        package["source"]["media_type"] = "image"
        write_json(self.package, package)
        before_checkpoint = (self.witness / "checkpoints.jsonl").read_bytes()
        with self.assertRaisesRegex(RuntimeError, "media type"):
            self.release(**self.strict())
        self.assertFalse((self.root / "out.pdf").exists())
        self.assertEqual(ledger.audit(self.ledger)["canonical_length"], 0)
        self.assertEqual((self.witness / "checkpoints.jsonl").read_bytes(), before_checkpoint)

    def test_renamed_prefixed_pdf_source_uses_strict_pdf_policy(self):
        renamed = self.root / "prefixed-source.bin"
        renamed.write_bytes(b"\n" + self.source.read_bytes())
        self.source = renamed
        package = core.encrypt_once(renamed, self.identities, ["alice"], self.package)
        self.assertEqual(package["source"]["media_type"], "application/pdf")
        result = self.release(**self.strict())
        self.assertEqual(result["event"]["fingerprint"]["scheme"], core.TARDOS_SCHEME)
        evidence = self.trace(**self.strict())
        self.assertEqual(evidence["channel_decision"]["decision"], "corroborated_channels")
        self.assertEqual([row["recipient_id"] for row in evidence["attribution"]], ["alice"])

    def test_legacy_generic_pdf_receipt_rejected_before_screening(self):
        # Reconstruct a genuine generic-carrier PDF and valid legacy-style
        # receipt with the synthetic recipient key. Production release must no
        # longer create this profile for actual PDF bytes.
        event = self.release()["event"]
        generic = self.root / "legacy-generic.pdf"
        metrics = core.watermark.embed_document(self.source, generic, self.secret.read_bytes(),
                                               event["session_id"])
        event["fingerprint"] = {"scheme": "nishan-spread-spectrum-session/v1",
                                "formal_familywise_bound": False}
        event["watermark_metrics"] = metrics
        event["released_copy_sha3_256"] = sha3_file(generic)
        identity = load_identity(self.identities, "alice")
        record = {"event": event, "recipient_signature_algorithm": "ML-DSA-65 (FIPS 204)",
                  "recipient_signature": b64e(pqc.sign(identity["sign_private"], canonical_json(event)))}
        legacy = self.root / "legacy-ledger"
        ledger.initialize(legacy, validator_count=4, quorum=3, identities_root=self.identities)
        ledger.append(legacy, record)
        legacy_witness = self.root / "legacy-witness"
        pin = witness.initialize(legacy_witness)["public_key_sha3_256"]
        witness.checkpoint(legacy_witness, ledger.audit(legacy))
        for prefix, suffix in ((b"", ".pdf"), (b"\n", ".bin")):
            reference = self.root / ("legacy-reference" + suffix)
            reference.write_bytes(prefix + self.source.read_bytes())
            # A changed prefix changes the source commitment; use that same
            # actual PDF source hash in a separately signed legacy receipt.
            if prefix:
                event["source_sha3_256"] = sha3_file(reference)
                event["document_id"] = sha3_file(reference)
                event["session_id"] = "legacy-prefixed-session"
                record["recipient_signature"] = b64e(pqc.sign(identity["sign_private"], canonical_json(event)))
                ledger.append(legacy, record)
                witness.checkpoint(legacy_witness, ledger.audit(legacy))
            with self.subTest(prefix=prefix, suffix=suffix), patch.object(core.watermark, "prepare_score",
                    side_effect=AssertionError("legacy PDF reached generic screening")):
                with self.assertRaisesRegex(RuntimeError, "legacy generic"):
                    core.trace_leak(reference, generic, self.secret, legacy,
                        witness_root=legacy_witness, witness_public_key_sha3_256=pin)

    def test_bad_arguments_fail_before_decryption_and_locks_are_released(self):
        cases = ({"witness_root": self.witness}, {"witness_public_key_sha3_256": self.pin},
                 {**self.strict(), "witness_public_key_sha3_256": "0" * 64},
                 {**self.strict(), "witness_public_key_sha3_256": "z" * 64},
                 {**self.strict(), "witness_public_key_sha3_256": "abcd"},
                 {**self.strict(), "witness_root": self.ledger},
                 {**self.strict(), "witness_root": self.root / "absent"})
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), patch.object(pqc, "decapsulate", side_effect=AssertionError("plaintext path reached")):
                with self.assertRaises((RuntimeError, ValueError, OSError)):
                    self.release(**kwargs)
                self.assertFalse((self.root / "out.pdf").exists())
                with self.assertRaises((RuntimeError, ValueError, OSError)):
                    self.trace(**kwargs)
        # A separate process must be able to acquire both locks after errors.
        import subprocess
        check = subprocess.run([os.sys.executable, "-c",
            "from pathlib import Path; from nishan import ledger,witness; import sys; "
            "exec('with ledger.exclusive(Path(sys.argv[1])):\\n with witness.exclusive(Path(sys.argv[2])):\\n  pass')",
            str(self.ledger), str(self.witness)], capture_output=True, text=True, timeout=15)
        self.assertEqual(check.returncode, 0, check.stderr)
        self.release(**self.strict())

    def test_empty_missing_and_replaced_witness_rejected(self):
        checkpoint = self.witness / "checkpoints.jsonl"
        original = checkpoint.read_bytes()
        for missing in (False, True):
            if missing:
                checkpoint.unlink()
            else:
                checkpoint.write_bytes(b"")
            with self.assertRaises((RuntimeError, OSError)):
                self.release(**self.strict())
            self.assertFalse((self.root / "out.pdf").exists())
            checkpoint.write_bytes(original)
        replacement = self.root / "replacement"
        witness.initialize(replacement)
        witness.checkpoint(replacement, ledger.audit(self.ledger))
        with self.assertRaises(RuntimeError):
            self.release(**{**self.strict(), "witness_root": replacement})

    def test_coordinated_rollback_rejected_by_release_and_trace(self):
        self.release(**self.strict())
        for replica in (self.ledger / "replicas").glob("*/ledger.jsonl"):
            replica.write_bytes(b"")
        self.assertTrue(ledger.audit(self.ledger)["quorum_valid"])
        output = self.root / "rollback.pdf"
        with self.assertRaises(RuntimeError):
            self.release(output, **self.strict())
        self.assertFalse(output.exists())
        with self.assertRaises(RuntimeError):
            self.trace(**self.strict())

    def test_checkpoint_failure_commits_but_never_publishes_and_requires_recovery(self):
        for preexisting in (False, True):
            with self.subTest(preexisting=preexisting):
                output = self.root / f"failure-{preexisting}.pdf"
                if preexisting:
                    output.write_bytes(b"existing destination")
                length = ledger.audit(self.ledger)["canonical_length"]
                with patch.object(witness, "checkpoint", side_effect=RuntimeError("injected checkpoint failure")):
                    with self.assertRaisesRegex(RuntimeError, "injected"):
                        self.release(output, **self.strict())
                self.assertEqual(ledger.audit(self.ledger)["canonical_length"], length + 1)
                self.assertEqual(output.read_bytes() if output.exists() else None,
                                 b"existing destination" if preexisting else None)
                with self.assertRaises(RuntimeError):
                    self.release(**self.strict())
                with self.assertRaises(RuntimeError):
                    self.trace(output, **self.strict())
                witness.checkpoint(self.witness, ledger.audit(self.ledger))
        self.release(**self.strict())

    def test_concurrent_issuance_has_distinct_rows_and_third_release_succeeds(self):
        results = concurrent_releases(self.root)
        self.assertEqual(sorted(item["event"]["fingerprint"]["user_index"] for item in results), [0, 1])
        self.assertEqual(len({item["event"]["session_id"] for item in results}), 2)
        third = self.release()
        self.assertEqual(third["event"]["fingerprint"]["user_index"], 2)
        self.assertFalse(third["release_assurance"]["witness_enforced"])

    def test_noop_or_corrupt_checkpoint_never_publishes(self):
        original_checkpoint = witness.checkpoint
        for corrupt in (False, True):
            with self.subTest(corrupt=corrupt):
                checkpoint_path = self.witness / "checkpoints.jsonl"
                before = checkpoint_path.read_bytes()

                def checkpoint(*args, **kwargs):
                    result = original_checkpoint(*args, **kwargs) if corrupt else None
                    if corrupt:
                        import json
                        lines = checkpoint_path.read_text().splitlines()
                        last = json.loads(lines[-1])
                        last["signature"] = "AAAA"
                        lines[-1] = json.dumps(last)
                        checkpoint_path.write_text("\n".join(lines) + "\n")
                    return result

                with patch.object(witness, "checkpoint", checkpoint):
                    with self.assertRaises(RuntimeError):
                        self.release(**self.strict())
                self.assertFalse((self.root / "out.pdf").exists())
                checkpoint_path.write_bytes(before)
                original_checkpoint(self.witness, ledger.audit(self.ledger))

    def test_actual_pin_rechecked_after_append_before_checkpoint(self):
        replacement = self.root / "replacement"
        witness.initialize(replacement)
        original_append = ledger.append

        def append(*args, **kwargs):
            result = original_append(*args, **kwargs)
            (self.witness / "public.pem").write_bytes((replacement / "public.pem").read_bytes())
            return result

        with patch.object(ledger, "append", append), patch.object(witness, "checkpoint") as checkpoint:
            with self.assertRaisesRegex(RuntimeError, "provisioned pin"):
                self.release(**self.strict())
            checkpoint.assert_not_called()
        self.assertFalse((self.root / "out.pdf").exists())
        self.assertEqual(ledger.audit(self.ledger)["canonical_length"], 1)

    def test_foreign_ledger_root_and_invalid_witness_signature_rejected(self):
        foreign = self.root / "foreign-ledger"
        ledger.initialize(foreign, validator_count=4, quorum=3, identities_root=self.identities)
        with self.assertRaisesRegex(RuntimeError, "foreign_or_replaced_trust_root"):
            core.decrypt_and_attribute(self.package, self.identities, "alice", self.secret,
                                       foreign, self.root / "foreign.pdf", **self.strict())
        self.assertFalse((self.root / "foreign.pdf").exists())
        import json
        checkpoint = self.witness / "checkpoints.jsonl"
        record = json.loads(checkpoint.read_text())
        record["signature"] = "AAAA"
        checkpoint.write_text(json.dumps(record) + "\n")
        with self.assertRaises(RuntimeError):
            self.release(**self.strict())
        with self.assertRaises(RuntimeError):
            self.trace(**self.strict())
        self.assertFalse((self.root / "out.pdf").exists())

    def test_rendered_transplant_retains_leads_without_attribution(self):
        self.release()
        core.decrypt_and_attribute(self.package, self.identities, "bob", self.secret,
                                   self.ledger, self.root / "bob.pdf")
        transplant = self.root / "transplant.pdf"
        _transplant_first_image(self.root / "out.pdf", self.root / "bob.pdf", transplant)
        raster = self.root / "transplant.png"
        with fitz.open(transplant) as document:
            document[0].get_pixmap(dpi=144).save(raster)
        evidence = self.trace(raster)
        self.assertEqual(evidence["attribution"], [])
        self.assertTrue(evidence["channel_decision"]["corroboration_required"])
        self.assertEqual(evidence["channel_decision"]["decision"], "abstain_missing_layout_channel")
        self.assertTrue(evidence["visual_only_research_leads"])

    def test_short_pdf_abstains_with_signed_capacity_limitation(self):
        with fitz.open() as document:
            page = document.new_page(width=595, height=842)
            page.insert_text((60, 90), "Short synthetic fixture")
            document.save(self.root / "short.pdf", no_new_id=True, reproducible=True)
        self.source = self.root / "short.pdf"
        core.encrypt_once(self.source, self.identities, ["alice"], self.package)
        result = self.release()
        self.assertFalse(result["event"]["fingerprint"]["layout_tag"]["available"])
        self.assertEqual(result["event"]["fingerprint"]["fusion_policy_version"], "pdf-all-formats-corroboration/v1")
        evidence = self.trace()
        self.assertEqual(evidence["attribution"], [])
        self.assertEqual(evidence["channel_decision"]["decision"], "abstain_inadequate_release_capacity")
        self.assertTrue(evidence["visual_only_research_leads"])


if __name__ == "__main__":
    unittest.main()
