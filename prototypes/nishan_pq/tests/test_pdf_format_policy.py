from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import pymupdf as fitz
from PIL import Image, UnidentifiedImageError

from nishan import ledger, live_pdf, pqc, watermark
from nishan.core import decrypt_and_attribute, encrypt_once, trace_leak
from nishan.demo import _sample_pdf, _transplant_first_image
from nishan.identity import create_identity
from nishan.util import write_private


class RasterFormatPolicyTests(unittest.TestCase):
    def test_existing_pillow_raster_formats_remain_supported(self):
        with tempfile.TemporaryDirectory() as directory:
            for suffix in ("png", "jpg", "gif", "webp", "bmp", "tiff"):
                with self.subTest(suffix=suffix):
                    path = Path(directory) / ("image." + suffix)
                    Image.new("RGB", (32, 48), "white").save(path)
                    self.assertFalse(watermark.is_pdf_document(path))
                    pages, _ = watermark.load_pages(path)
                    self.assertEqual(pages[0].shape, (48, 32, 3))

    def test_unrecognized_input_is_not_accepted_as_raster(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.pdf"
            path.write_bytes(b"not a document or a raster image")
            with self.assertRaises((fitz.FileDataError, UnidentifiedImageError)):
                watermark.is_pdf_document(path)


@unittest.skipUnless(pqc.support().ready, "OpenSSL PQC provider is unavailable")
class PdfFormatPolicyTests(unittest.TestCase):
    def test_encrypt_classifies_pdf_source_content_without_suffix_trust(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            _sample_pdf(source)
            identities = root / "identities"
            create_identity(identities, "alice", "Alice")
            for prefix, suffix in ((b"", ".bin"), (b"\n", ".pdf"), (b"\n", ".bin")):
                with self.subTest(prefix=prefix, suffix=suffix):
                    renamed = root / ("renamed" + suffix)
                    renamed.write_bytes(prefix + source.read_bytes())
                    package = encrypt_once(renamed, identities, ["alice"], root / "package.json")
                    self.assertEqual(package["source"]["media_type"], "application/pdf")

    def test_parser_accepted_pdfs_always_require_channel_corroboration(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            _sample_pdf(source)
            identities = root / "identities"
            for name in ("alice", "bob"):
                create_identity(identities, name, name.title())
            ledger_root = root / "ledger"
            ledger.initialize(ledger_root, validator_count=4, quorum=3,
                              identities_root=identities)
            secret = root / "secret.bin"
            write_private(secret, os.urandom(32))
            package = root / "package.json"
            encrypt_once(source, identities, ["alice", "bob"], package)
            for name in ("alice", "bob"):
                decrypt_and_attribute(package, identities, name, secret,
                                      ledger_root, root / f"{name}.pdf")
            transplant = root / "transplant.pdf"
            _transplant_first_image(root / "alice.pdf", root / "bob.pdf", transplant)
            single = root / "single.pdf"
            live_pdf.strip_layout_adjustments(root / "alice.pdf", single,
                                               adjustment_magnitude=0.001)
            cases = (
                (root / "alice.pdf", "corroborated_channels", ["alice"]),
                (transplant, "abstain_channel_conflict", []),
                (single, "abstain_single_channel_editable_pdf", []),
            )
            for fixture, decision, recipients in cases:
                for prefix, suffix in ((b"", ".pdf"), (b"\n", ".pdf"),
                                       (b"\n", ".bin")):
                    with self.subTest(fixture=fixture.name, prefix=prefix, suffix=suffix):
                        suspect = root / ("variant" + suffix)
                        suspect.write_bytes(prefix + fixture.read_bytes())
                        with fitz.open(suspect) as parsed:
                            self.assertTrue(parsed.is_pdf)
                            self.assertGreater(len(parsed[0].get_text()), 0)
                        evidence = trace_leak(source, suspect, secret, ledger_root)
                        self.assertTrue(evidence["channel_decision"]["editable_pdf_corroboration_required"])
                        self.assertTrue(evidence["channel_decision"]["corroboration_required"])
                        self.assertEqual(evidence["channel_decision"]["decision"], decision)
                        self.assertEqual([row["recipient_id"] for row in evidence["attribution"]], recipients)


if __name__ == "__main__":
    unittest.main()
