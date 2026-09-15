from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import numpy as np
import pymupdf as fitz

from nishan import live_pdf


class LivePdfCarrierTests(unittest.TestCase):
    def _source(self, path: Path) -> None:
        document = fitz.open()
        page = document.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(40, 40, 555, 802), color=(0.1, 0.2, 0.4), width=2)
        text = " ".join(["searchable operational document"] * 45)
        page.insert_textbox(
            fitz.Rect(60, 80, 535, 760),
            text,
            fontsize=11,
            fontname="helv",
        )
        document.save(path)
        document.close()

    def test_round_trip_preserves_text_and_vector_pdf(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            marked = root / "marked.pdf"
            self._source(source)
            bits = np.random.default_rng(123).integers(0, 2, size=96, dtype=np.uint8)
            result = live_pdf.embed(
                source,
                marked,
                bits,
                b"test-only-secret" * 2,
                "document-17/session-alice",
            )
            recovered = live_pdf.extract(
                marked,
                len(bits),
                b"test-only-secret" * 2,
                "document-17/session-alice",
            )

            self.assertTrue(result.text_preserved)
            self.assertGreaterEqual(result.capacity_bits, len(bits))
            np.testing.assert_array_equal(recovered, bits)
            with fitz.open(source) as original, fitz.open(marked) as output:
                self.assertEqual(original[0].get_text(), output[0].get_text())
                self.assertEqual(
                    [word[4] for word in original[0].get_text("words")],
                    [word[4] for word in output[0].get_text("words")],
                )
                self.assertTrue(output[0].search_for("operational document"))
                self.assertEqual(len(output[0].get_images(full=True)), 0)
                self.assertGreater(len(output[0].get_fonts(full=True)), 0)
                self.assertEqual(len(original[0].get_drawings()), len(output[0].get_drawings()))

    def test_capacity_failure_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            marked = Path(directory) / "marked.pdf"
            self._source(source)
            too_many = np.zeros(live_pdf.capacity(source) + 1, dtype=np.uint8)
            with self.assertRaisesRegex(ValueError, "supported capacity"):
                live_pdf.embed(source, marked, too_many, b"s" * 32, "context")

    def test_layout_normalization_attack_removes_channel_but_preserves_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            marked = root / "marked.pdf"
            normalized = root / "normalized.pdf"
            self._source(source)
            bits = np.random.default_rng(3).integers(0, 2, size=112, dtype=np.uint8)
            live_pdf.embed(source, marked, bits, b"k" * 32, "session")
            removed = live_pdf.strip_layout_adjustments(marked, normalized)

            self.assertGreaterEqual(removed, len(bits))
            with fitz.open(source) as original, fitz.open(normalized) as output:
                self.assertEqual(original[0].get_text(), output[0].get_text())
            with self.assertRaises(ValueError):
                live_pdf.extract(normalized, len(bits), b"k" * 32, "session")


if __name__ == "__main__":
    unittest.main()
