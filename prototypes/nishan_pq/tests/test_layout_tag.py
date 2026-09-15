from __future__ import annotations

import unittest

import numpy as np

from nishan import layout_tag


class LayoutTagTests(unittest.TestCase):
    def test_hamming_round_trip_and_every_single_bit_position(self) -> None:
        source = np.random.default_rng(42).integers(
            0, 2, size=layout_tag.TAG_BITS, dtype=np.uint8
        )
        encoded = layout_tag.hamming74_encode(source)
        self.assertEqual(encoded.size, layout_tag.ENCODED_BITS)
        np.testing.assert_array_equal(layout_tag.hamming74_decode(encoded).bits, source)

        for position in range(encoded.size):
            attacked = encoded.copy()
            attacked[position] ^= 1
            result = layout_tag.hamming74_decode(attacked)
            np.testing.assert_array_equal(result.bits, source)
            self.assertEqual(result.corrected_blocks, 1)

    def test_session_context_separation_and_match(self) -> None:
        secret = b"z" * 32
        expected = layout_tag.tag_bits(secret, "doc", "session-a", 7)
        self.assertTrue(layout_tag.matches(expected, secret, "doc", "session-a", 7))
        self.assertFalse(layout_tag.matches(expected, secret, "doc", "session-b", 7))
        self.assertFalse(layout_tag.matches(expected, secret, "doc", "session-a", 8))


if __name__ == "__main__":
    unittest.main()
