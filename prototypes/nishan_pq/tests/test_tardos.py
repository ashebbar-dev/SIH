from __future__ import annotations

import unittest

import numpy as np

from nishan import tardos


class TardosReferenceTests(unittest.TestCase):
    def test_paper_constants_and_familywise_bound(self) -> None:
        config = tardos.parameters(
            roster_size=1_000,
            coalition_limit=5,
            familywise_epsilon=1e-6,
        )

        self.assertAlmostEqual(config.per_user_epsilon, 1e-9)
        self.assertEqual(config.k, 21)
        self.assertEqual(config.code_length, 52_500)
        self.assertAlmostEqual(config.cutoff, 1 / 1_500)
        self.assertEqual(config.threshold, 2_100)
        self.assertLessEqual(
            tardos.theorem_bounds(config)["combined_error_upper"],
            config.familywise_epsilon,
        )

    def test_attacks_respect_marking_condition_and_fixture_accuses_colluders(self) -> None:
        config = tardos.parameters(32, 4, 0.01)
        rng = np.random.default_rng(20260910)
        biases, codebook = tardos.generate(config, rng)
        colluders = np.arange(config.coalition_limit)
        coalition = codebook[colluders]
        unanimous_zero = coalition.sum(axis=0) == 0
        unanimous_one = coalition.sum(axis=0) == config.coalition_limit

        for attack in ("interleaving", "majority", "minority", "coin_flip"):
            with self.subTest(attack=attack):
                pirate = tardos.simulate_attack(coalition, attack, rng)
                self.assertTrue(np.all(pirate[unanimous_zero] == 0))
                self.assertTrue(np.all(pirate[unanimous_one] == 1))
                scores = tardos.accusation_scores(biases, codebook, pirate)
                accused = tardos.accuse(scores, config)
                self.assertEqual(set(accused.tolist()), set(colluders.tolist()))

    def test_manifest_is_reproducible_without_exposing_codebook(self) -> None:
        config = tardos.parameters(12, 4, 0.1)
        first_rng = np.random.default_rng(7)
        second_rng = np.random.default_rng(7)
        first = tardos.generate(config, first_rng)
        second = tardos.generate(config, second_rng)
        first_manifest = tardos.manifest(config, *first)
        second_manifest = tardos.manifest(config, *second)

        self.assertEqual(first_manifest, second_manifest)
        self.assertNotIn("codebook", first_manifest)
        self.assertEqual(first_manifest["codebook_shape"], [12, config.code_length])
        self.assertEqual(
            tardos.canonical_manifest_bytes(first_manifest),
            tardos.canonical_manifest_bytes(second_manifest),
        )

    def test_keyed_generation_is_reproducible_and_context_separated(self) -> None:
        config = tardos.parameters(12, 4, 0.1)
        secret = b"x" * 32
        first = tardos.generate_keyed(config, secret, "document-a")
        second = tardos.generate_keyed(config, secret, "document-a")
        different = tardos.generate_keyed(config, secret, "document-b")

        np.testing.assert_array_equal(first[0], second[0])
        np.testing.assert_array_equal(first[1], second[1])
        self.assertFalse(np.array_equal(first[0], different[0]))
        self.assertFalse(np.array_equal(first[1], different[1]))

    def test_parameter_validation(self) -> None:
        for values in ((1, 4, 0.1), (10, 3, 0.1), (10, 11, 0.1), (10, 4, 1.0)):
            with self.subTest(values=values), self.assertRaises(ValueError):
                tardos.parameters(*values)


if __name__ == "__main__":
    unittest.main()
