import unittest
from recommendation.arbitration import PreferenceProfile, PreferenceArbitrator


class TestMultiModalPreferenceArbitration(unittest.TestCase):

    def setUp(self):
        self.items = ["item_audio_1", "item_video_2", "item_text_3", "item_image_4"]
        self.profile_user = PreferenceProfile(
            party_id="user_alice",
            scores={
                "item_audio_1": 0.9,
                "item_video_2": 0.4,
                "item_text_3": 0.7,
                "item_image_4": 0.2,
            },
            weight=1.0
        )
        self.profile_agent = PreferenceProfile(
            party_id="assistant_bot",
            scores={
                "item_audio_1": 0.3,
                "item_video_2": 0.8,
                "item_text_3": 0.6,
                "item_image_4": 0.1,
            },
            weight=1.0
        )
        self.profile_moderator = PreferenceProfile(
            party_id="compliance_guard",
            scores={
                "item_audio_1": 0.5,
                "item_video_2": 0.5,
                "item_text_3": 0.9,
                "item_image_4": 0.8,
            },
            weight=2.0
        )

    def test_deterministic_weighted_borda_arbitration(self):
        arbitrator = PreferenceArbitrator(conflict_resolution="borda", seed="fixed-test-seed")
        profiles = [self.profile_user, self.profile_agent, self.profile_moderator]

        run_1 = arbitrator.arbitrate(self.items, profiles)
        run_2 = arbitrator.arbitrate(self.items, profiles)

        self.assertEqual(len(run_1), len(self.items))
        self.assertEqual(run_1, run_2, "Arbitration results must be strictly deterministic across runs.")
        self.assertEqual(run_1[0]["item_id"], "item_text_3", "Highest consensus item should be ranked first.")

    def test_weighted_average_arbitration_with_top_k(self):
        arbitrator = PreferenceArbitrator(conflict_resolution="weighted_average")
        profiles = [self.profile_user, self.profile_agent]

        results = arbitrator.arbitrate(self.items, profiles, top_k=2)
        self.assertEqual(len(results), 2)
        # Average for item_text_3: (0.7 + 0.6) / 2 = 0.65
        # Average for item_audio_1: (0.9 + 0.3) / 2 = 0.60
        self.assertEqual(results[0]["item_id"], "item_text_3")
        self.assertAlmostEqual(results[0]["score"], 0.65, places=5)
        self.assertEqual(results[1]["item_id"], "item_audio_1")
        self.assertAlmostEqual(results[1]["score"], 0.60, places=5)

    def test_deterministic_tie_breaking(self):
        arbitrator = PreferenceArbitrator(conflict_resolution="weighted_average", seed="tiebreaker-seed-42")
        profile_tie_1 = PreferenceProfile("party_1", {"item_A": 0.5, "item_B": 0.5})
        profile_tie_2 = PreferenceProfile("party_2", {"item_A": 0.5, "item_B": 0.5})

        res_1 = arbitrator.arbitrate(["item_A", "item_B"], [profile_tie_1, profile_tie_2])
        res_2 = arbitrator.arbitrate(["item_B", "item_A"], [profile_tie_1, profile_tie_2])

        self.assertEqual(res_1, res_2, "Candidate ordering in input must not alter deterministic tie-breaking.")
        self.assertEqual(res_1[0]["score"], res_1[1]["score"])
        self.assertTrue(res_1[0]["item_id"] in ["item_A", "item_B"])

    def test_minimax_arbitration(self):
        arbitrator = PreferenceArbitrator(conflict_resolution="minimax")
        profiles = [self.profile_user, self.profile_agent]

        results = arbitrator.arbitrate(self.items, profiles)
        # Min score across user and agent:
        # item_audio_1: min(0.9, 0.3) = 0.3
        # item_video_2: min(0.4, 0.8) = 0.4
        # item_text_3:  min(0.7, 0.6) = 0.6
        # item_image_4: min(0.2, 0.1) = 0.1
        self.assertEqual(results[0]["item_id"], "item_text_3")
        self.assertAlmostEqual(results[0]["score"], 0.6, places=5)
        self.assertEqual(results[1]["item_id"], "item_video_2")
        self.assertAlmostEqual(results[1]["score"], 0.4, places=5)


if __name__ == "__main__":
    unittest.main()
