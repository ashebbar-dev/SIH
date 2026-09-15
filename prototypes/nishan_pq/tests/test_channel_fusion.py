from __future__ import annotations

import unittest

from nishan.core import fuse_channel_indices


class ChannelFusionTests(unittest.TestCase):
    def test_independent_survival_and_agreement(self) -> None:
        cases = [
            ({3}, set(), set(), "tardos_channel_only", [3]),
            (set(), {3}, set(), "layout_channel_only", [3]),
            ({3}, {3}, set(), "corroborated_channels", [3]),
            (set(), set(), set(), "no_attribution_signal", []),
        ]
        for tardos, layout, unissued, decision, selected in cases:
            with self.subTest(decision=decision):
                result = fuse_channel_indices(tardos, layout, unissued)
                self.assertEqual(result["decision"], decision)
                self.assertEqual(result["selected_indices"], selected)
                self.assertFalse(result["conflict"])

    def test_transplant_and_unissued_rows_force_abstention(self) -> None:
        transplant = fuse_channel_indices({1}, {2}, set())
        self.assertEqual(transplant["decision"], "abstain_channel_conflict")
        self.assertEqual(transplant["selected_indices"], [])
        self.assertTrue(transplant["conflict"])

        unissued = fuse_channel_indices({1}, {1}, {907})
        self.assertEqual(
            unissued["decision"], "abstain_unissued_tardos_candidate"
        )
        self.assertEqual(unissued["selected_indices"], [])
        self.assertTrue(unissued["conflict"])

    def test_partial_overlap_forces_abstention(self) -> None:
        result = fuse_channel_indices({1, 2}, {2, 3}, set())
        self.assertEqual(result["decision"], "abstain_channel_conflict")
        self.assertEqual(result["selected_indices"], [])
        self.assertEqual(result["screening_lead_indices"], [2])
        self.assertTrue(result["conflict"])

    def test_editable_pdf_requires_both_channels(self) -> None:
        for tardos, layout in [({4}, set()), (set(), {4})]:
            with self.subTest(tardos=tardos, layout=layout):
                result = fuse_channel_indices(
                    tardos,
                    layout,
                    set(),
                    require_corroboration=True,
                )
                self.assertEqual(
                    result["decision"], "abstain_single_channel_editable_pdf"
                )
                self.assertEqual(result["selected_indices"], [])
                self.assertEqual(result["screening_lead_indices"], [4])


if __name__ == "__main__":
    unittest.main()
