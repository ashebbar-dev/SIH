from __future__ import annotations

import hashlib
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pymupdf as fitz

from nishan import tardos, tardos_carrier


class TardosPdfCarrierTests(unittest.TestCase):
    def _source(self, path: Path) -> None:
        document = fitz.open()
        page = document.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(40, 40, 555, 802), color=(0.1, 0.2, 0.4), width=2)
        page.insert_textbox(
            fitz.Rect(60, 80, 535, 760),
            " ".join(["searchable controlled document"] * 60),
            fontsize=11,
            fontname="helv",
        )
        document.save(path)
        document.close()

    def test_codeword_round_trip_preserves_pdf_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.pdf"
            marked = root / "marked.pdf"
            self._source(source)
            config = tardos.parameters(32, 4, 0.01)
            biases, codebook = tardos.generate(config, np.random.default_rng(19))
            secret = hashlib.sha3_256(b"test carrier key").digest()
            metrics = tardos_carrier.embed_pdf(
                source,
                marked,
                codebook[0],
                secret,
                "document/test",
                strength=4.0,
            )
            pirate, _ = tardos_carrier.decode_word(
                source,
                marked,
                config.code_length,
                secret,
                "document/test",
            )
            scores = tardos.accusation_scores(biases, codebook, pirate)

            self.assertTrue(metrics.text_preserved)
            self.assertGreater(metrics.capacity_symbols, config.code_length)
            self.assertEqual(tardos.accuse(scores, config).tolist(), [0])
            self.assertEqual(
                tardos_carrier.marking_condition_errors(pirate, codebook[[0]])[
                    "violations"
                ],
                0,
            )
            with fitz.open(source) as original, fitz.open(marked) as output:
                self.assertEqual(original[0].get_text(), output[0].get_text())
                self.assertEqual(len(output[0].get_images(full=True)), 1)
                self.assertEqual(len(original[0].get_drawings()), len(output[0].get_drawings()))

    def test_capacity_failure_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.pdf"
            output = Path(directory) / "marked.pdf"
            self._source(source)
            capacity = tardos_carrier.capacity(source)
            with self.assertRaisesRegex(ValueError, "rendered PDF capacity"):
                tardos_carrier.embed_pdf(
                    source,
                    output,
                    np.zeros(capacity + 1, dtype=np.uint8),
                    b"x" * 32,
                    "document/test",
                )


if __name__ == "__main__":
    unittest.main()
