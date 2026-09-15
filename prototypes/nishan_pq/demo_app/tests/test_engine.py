from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf as fitz
from PIL import Image

from demo_app.engine import DemoEngine, InputError, MAX_UPLOAD_BYTES


ROOT = Path(__file__).resolve().parents[4]


class DemoEngineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.directory = tempfile.TemporaryDirectory()
        cls.state_dir = Path(cls.directory.name) / "state"
        cls.engine = DemoEngine(ROOT, cls.state_dir)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.directory.cleanup()

    def test_source_is_exact_known_original(self) -> None:
        result = self.engine.analyze(
            ROOT / "artifacts/nishan/synthetic-source.pdf", "public"
        )
        self.assertEqual(result["kind"], "known_original")
        self.assertEqual(result["recipients"], [])
        self.assertEqual(result["channels"]["exact_file_identity"]["match"], True)

    def test_public_fixture_is_not_a_signed_identity(self) -> None:
        result = self.engine.analyze(
            ROOT / "artifacts/nishan/dual-carrier-user-0000-live-text.pdf",
            "public",
        )
        self.assertEqual(result["kind"], "fixture_match")
        self.assertNotEqual(result["assurance"], "verified_signed_session")
        self.assertEqual(
            result["recipients"][0]["session_id"],
            "public-fixture-session-0000",
        )
        self.assertEqual(result["recipients"][0]["display_name"], "Demo recipient 0000")
        self.assertFalse(result["channels"]["signature"]["available"])

    def test_raster_marked_page_is_never_promoted_to_signed_verdict(self) -> None:
        marked = ROOT / "artifacts/nishan/dual-carrier-user-0000-live-text.pdf"
        output = self.state_dir / "rendered-marked.png"
        with fitz.open(marked) as document:
            pixmap = document[0].get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
            pixmap.save(output)
        result = self.engine.analyze(output, "public")
        self.assertIn(result["kind"], {"research_lead", "inconclusive"})
        self.assertNotEqual(result["kind"], "verified_session")
        self.assertNotEqual(result["assurance"], "verified_signed_session")
        if result["recipients"]:
            self.assertEqual(result["recipients"][0]["display_name"], "Demo recipient 0000")

    def test_blank_image_does_not_name_a_recipient(self) -> None:
        blank = self.state_dir / "blank.png"
        Image.new("RGB", (1200, 1600), "white").save(blank)
        result = self.engine.analyze(blank, "public")
        self.assertEqual(result["kind"], "inconclusive")
        self.assertEqual(result["recipients"], [])

    def test_content_type_not_filename_controls_pdf_policy(self) -> None:
        source = ROOT / "artifacts/nishan/dual-carrier-user-0000-live-text.pdf"
        renamed = self.state_dir / "marked.jpeg"
        renamed.write_bytes(source.read_bytes())
        result = self.engine.analyze(renamed, "public")
        self.assertEqual(result["kind"], "fixture_match")
        self.assertEqual(result["diagnostics"]["input_type"], "pdf")

    def test_malformed_and_multi_page_inputs_are_explicit_errors(self) -> None:
        malformed = self.state_dir / "malformed.jpg"
        malformed.write_bytes(b"not an image or PDF")
        with self.assertRaisesRegex(InputError, "Unsupported or malformed"):
            self.engine.analyze(malformed, "public")

        multiple = self.state_dir / "multiple.pdf"
        with fitz.open() as document:
            document.new_page()
            document.new_page()
            document.save(multiple)
        with self.assertRaisesRegex(InputError, "one-page"):
            self.engine.analyze(multiple, "public")

    def test_oversize_and_excessive_pixels_are_rejected(self) -> None:
        oversize = self.state_dir / "oversize.bin"
        with oversize.open("wb") as handle:
            handle.truncate(MAX_UPLOAD_BYTES + 1)
        with self.assertRaisesRegex(InputError, "25 MiB"):
            self.engine.analyze(oversize, "public")

        huge = self.state_dir / "huge.png"
        Image.new("1", (6500, 6500)).save(huge)
        with self.assertRaisesRegex(InputError, "40 million pixels"):
            self.engine.analyze(huge, "public")

    def test_signed_preparation_reports_missing_pqc_without_fallback(self) -> None:
        with patch.object(
            self.engine,
            "_pqc_status",
            return_value=(False, "compatible OpenSSL PQC support is unavailable"),
        ):
            with self.assertRaisesRegex(RuntimeError, "PQC support is unavailable"):
                self.engine.prepare_signed()


class SignedDemoIntegrationTests(unittest.TestCase):
    def test_signed_alice_bob_trace_and_restart_reuse(self) -> None:
        try:
            from nishan import pqc
        except (ImportError, OSError) as error:
            self.skipTest(f"PQC import unavailable: {error}")
        status = pqc.support()
        if not status.ready:
            self.skipTest(f"PQC unavailable: {status.detail}")

        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state"
            engine = DemoEngine(ROOT, state)
            prepared = engine.prepare_signed()
            self.assertEqual({item["recipient_id"] for item in prepared["fixtures"]}, {"alice", "bob"})
            for item in prepared["fixtures"]:
                result = engine.analyze(engine.fixture_path(item["id"]), "signed")
                self.assertEqual(result["kind"], "verified_session")
                self.assertEqual(result["assurance"], "verified_signed_session")
                self.assertEqual(result["recipients"][0]["recipient_id"], item["recipient_id"])
                self.assertEqual(result["recipients"][0]["session_id"], item["session_id"])

            restarted = DemoEngine(ROOT, state)
            reused = restarted.prepare_signed()
            self.assertEqual(reused["run_id"], prepared["run_id"])
            self.assertEqual(reused["fixtures"], prepared["fixtures"])


if __name__ == "__main__":
    unittest.main()
