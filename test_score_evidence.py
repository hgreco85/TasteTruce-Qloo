import unittest
from tastetruce import scoring, plan

class ScoreEvidenceTests(unittest.TestCase):
    def test_missing_invalid_nonfinite_out_of_range(self):
        for obj in ({}, {"score": None}, {"affinity": "NaN"},
                    {"affinity": "inf"}, {"affinity": -0.1},
                    {"affinity": 1.1}, {"affinity": True}, {"affinity": "invalid"}):
            with self.subTest(obj=obj):
                self.assertIsNone(scoring(obj))
    def test_valid_affinity(self):
        self.assertEqual(scoring({"affinity": 0.75}), .75)
    def test_ranked_shared_entity_without_affinity(self):
        class FakeClient:
            def search(self, term, kind, take=3):
                return [{"id": term}]
            def insights(self, ids, kind, location=None, take=15):
                return [{"id": "shared", "name": "Shared", "affinity": None}]
        result = plan([["A"], ["B"]], categories=("film",), client=FakeClient())
        self.assertEqual(result["choices"][0]["name"], "Shared")
        self.assertIsNone(result["choices"][0]["score"])
        self.assertEqual(result["choices"][0]["source"], "qloo_rank")
        self.assertEqual(result["choices"][0]["participant_ranks"], [1, 1])

if __name__ == "__main__":
    unittest.main()
