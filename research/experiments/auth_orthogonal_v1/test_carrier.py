from __future__ import annotations

import dataclasses
import io
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pymupdf as fitz

from carrier import (
    BLOCK_SIZE,
    REPEATS,
    SYMBOLS,
    TAG_ENCODED_BITS,
    auth_bits,
    canonical_context,
    copy_observed_overlays,
    decode,
    make_plan,
)
from nishan import tardos_carrier


def _one_page_pdf(path: Path, text: str) -> None:
    document = fitz.open()
    page = document.new_page(width=300, height=300)
    page.insert_text((36, 50), text, fontsize=12)
    document.save(path)
    document.close()


class CarrierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.secret = b"x" * 32
        self.context = canonical_context("a" * 64, "b" * 64, "session-0", 0)
        self.order = np.arange(SYMBOLS, dtype=np.int64)
        self.tardos_orientation = np.arange(SYMBOLS, dtype=np.uint8) % 2

    def test_context_is_canonical_and_each_field_binds(self) -> None:
        original = self.context
        self.assertEqual(
            original, canonical_context("a" * 64, "b" * 64, "session-0", 0)
        )
        altered_contexts = [
            canonical_context("c" * 64, "b" * 64, "session-0", 0),
            canonical_context("a" * 64, "c" * 64, "session-0", 0),
            canonical_context("a" * 64, "b" * 64, "session-1", 0),
            canonical_context("a" * 64, "b" * 64, "session-0", 1),
        ]
        for altered in altered_contexts:
            self.assertNotEqual(original, altered)
            self.assertFalse(
                np.array_equal(auth_bits(self.secret, original), auth_bits(self.secret, altered))
            )

    def test_context_and_secret_validation(self) -> None:
        with self.assertRaises(ValueError):
            canonical_context("not-a-hash", "b" * 64, "session-0", 0)
        with self.assertRaises(ValueError):
            canonical_context("a" * 64, "b" * 64, "session-0", -1)
        with self.assertRaises(ValueError):
            auth_bits(b"short", self.context)
        with self.assertRaises(ValueError):
            auth_bits(self.secret, "non-ascii-€")

    def test_plan_rejects_wrong_profile_capacity(self) -> None:
        with self.assertRaises(ValueError):
            make_plan(
                self.secret,
                self.context,
                self.order[:-1],
                self.tardos_orientation[:-1],
            )
        bad_order = self.order.copy()
        bad_order[-1] = 0
        with self.assertRaises(ValueError):
            make_plan(self.secret, self.context, bad_order, self.tardos_orientation)

    def test_plan_has_unique_placements_and_orthogonal_orientations(self) -> None:
        plan = make_plan(self.secret, self.context, self.order, self.tardos_orientation)
        self.assertEqual(plan.raw_bits.shape, (72,))
        self.assertEqual(plan.encoded_bits.shape, (TAG_ENCODED_BITS,))
        self.assertEqual(plan.positions.shape, (TAG_ENCODED_BITS * REPEATS,))
        self.assertEqual(np.unique(plan.positions).size, plan.positions.size)
        np.testing.assert_array_equal(
            plan.orientations, 1 - self.tardos_orientation[plan.positions]
        )
        self.assertTrue(np.all(np.isin(plan.polarities, (-1, 1))))

    def test_exact_decode_and_intentional_expected_tag_mismatch(self) -> None:
        plan = make_plan(self.secret, self.context, self.order, self.tardos_orientation)
        templates = tardos_carrier._templates(BLOCK_SIZE)
        blocks = np.zeros((SYMBOLS, BLOCK_SIZE, BLOCK_SIZE), dtype=np.float32)
        payload = np.tile(plan.encoded_bits, REPEATS)
        blocks[plan.positions] = (
            (2 * payload.astype(np.int8) - 1)[:, None, None]
            * plan.polarities[:, None, None]
            * templates[plan.orientations]
        )
        observation = decode(blocks, plan)
        self.assertTrue(observation["exact_match"])
        self.assertEqual(observation["decoded_bit_distance"], 0)
        self.assertEqual(observation["encoded_bit_distance"], 0)
        self.assertEqual(len(observation["raw_sums"]), TAG_ENCODED_BITS)

        mismatch = dataclasses.replace(plan, raw_bits=1 - plan.raw_bits)
        rejected = decode(blocks, mismatch)
        self.assertFalse(rejected["exact_match"])
        self.assertEqual(rejected["decoded_bit_distance"], 72)

    def test_copy_observed_overlays_preserves_changed_target_text_and_masks(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            base = root / "base.pdf"
            target = root / "target.pdf"
            donor = root / "donor.pdf"
            copied = root / "copied.pdf"
            _one_page_pdf(base, "quantity 120")
            _one_page_pdf(target, "quantity 920")

            document = fitz.open(base)
            page = document[0]
            for sign in (1.0, -1.0):
                pattern = np.zeros((600, 600), dtype=np.float32)
                pattern[:, :300] = sign
                page.insert_image(
                    page.rect,
                    stream=tardos_carrier._transparent_overlay(pattern, 4.0),
                    overlay=True,
                    keep_proportion=False,
                )
            document.save(donor, deflate=True)
            document.close()

            copy_observed_overlays(donor, target, copied)
            with fitz.open(donor) as donor_doc, fitz.open(copied) as copied_doc:
                donor_images = donor_doc[0].get_images(full=True)
                copied_images = copied_doc[0].get_images(full=True)
                self.assertEqual(len(donor_images), 2)
                self.assertEqual(len(copied_images), 2)
                self.assertTrue(all(image[1] > 0 for image in donor_images))
                self.assertTrue(all(image[1] > 0 for image in copied_images))
                self.assertIn("quantity 920", copied_doc[0].get_text())
                self.assertNotIn("quantity 120", copied_doc[0].get_text())

    def test_copy_rejects_page_geometry_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            donor = root / "donor.pdf"
            target = root / "target.pdf"
            destination = root / "copied.pdf"
            _one_page_pdf(donor, "donor")
            document = fitz.open()
            document.new_page(width=301, height=300)
            document.save(target)
            document.close()
            with self.assertRaises(ValueError):
                copy_observed_overlays(donor, target, destination)

    def test_cli_refuses_existing_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            command = [
                sys.executable,
                str(Path(__file__).with_name("run_study.py")),
                "--output",
                directory,
            ]
            completed = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(completed.returncode, 0)
            self.assertIn("refus", (completed.stdout + completed.stderr).lower())


if __name__ == "__main__":
    unittest.main()
