import unittest
from multimodal_arbitration.arbitrator import (
    DeterministicMultimodalArbitrator,
    PreferenceItem,
    PartyVote,
)


class TestMultimodalArbitration(unittest.TestCase):

    def setUp(self):
        self.arbitrator = DeterministicMultimodalArbitrator()

    def test_deterministic_tie_breaking(self):
        """Verify that exact ties yield deterministic identical order across runs."""
        item_a = PreferenceItem(item_id="candidate_alpha", score=0.5, modality="text")
        item_b = PreferenceItem(item_id="candidate_beta", score=0.5, modality="text")

        vote1 = PartyVote(party_id="party_1", weight=1.0, rankings=[item_a])
        vote2 = PartyVote(party_id="party_2", weight=1.0, rankings=[item_b])

        res1 = self.arbitrator.arbitrate([vote1, vote2], salt="seed_test_1")
        res2 = self.arbitrator.arbitrate([vote1, vote2], salt="seed_test_1")

        self.assertEqual(len(res1), 2)
        self.assertEqual(res1, res2)
        self.assertEqual(res1[0]["score"], res1[1]["score"])
        self.assertNotEqual(res1[0]["item_id"], res1[1]["item_id"])

    def test_weighted_parties_and_modalities(self):
        """Test party weight differentiation and modality multiplier scaling."""
        text_item = PreferenceItem(item_id="doc_recommendation", score=0.8, modality="text")
        visual_item = PreferenceItem(item_id="image_recommendation", score=0.8, modality="vision")

        vote_text = PartyVote(party_id="curator", weight=2.0, rankings=[text_item, visual_item])
        vote_vis = PartyVote(party_id="designer", weight=1.0, rankings=[visual_item, text_item])

        # With vision modality weighted higher
        results = self.arbitrator.arbitrate(
            [vote_text, vote_vis],
            modality_weights={"text": 1.0, "vision": 3.0}
        )

        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["item_id"], "image_recommendation")
        self.assertGreater(results[0]["score"], results[1]["score"])

    def test_empty_and_zero_weight_votes(self):
        """Check handling of empty votes and zero/negative weight parties."""
        self.assertEqual(self.arbitrator.arbitrate([]), [])

        item = PreferenceItem(item_id="lone_item", score=1.0, modality="audio")
        zero_vote = PartyVote(party_id="muted_party", weight=0.0, rankings=[item])
        neg_vote = PartyVote(party_id="invalid_party", weight=-1.0, rankings=[item])
        pos_vote = PartyVote(party_id="active_party", weight=1.0, rankings=[item])

        zero_results = self.arbitrator.arbitrate([zero_vote, neg_vote])
        self.assertEqual(zero_results, [])

        active_results = self.arbitrator.arbitrate([zero_vote, pos_vote], top_k=1)
        self.assertEqual(len(active_results), 1)
        self.assertEqual(active_results[0]["item_id"], "lone_item")
        self.assertEqual(active_results[0]["rank"], 1)

    def test_top_k_truncation(self):
        """Ensure top_k limits the returned results correctly."""
        items = [
            PreferenceItem(item_id=f"item_{i}", score=float(i), modality="general")
            for i in range(5)
        ]
        vote = PartyVote(party_id="evaluator", weight=1.0, rankings=list(reversed(items)))
        results = self.arbitrator.arbitrate([vote], top_k=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["rank"], 1)
        self.assertEqual(results[1]["rank"], 2)


if __name__ == "__main__":
    unittest.main()
