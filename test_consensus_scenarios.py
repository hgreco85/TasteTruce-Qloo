import unittest
from tastetruce import plan

class ScenarioClient:
    def search(self, term, kind, take=3):
        return [{"id": term}]
    def insights(self, ids, kind, location=None, take=15):
        if kind == "urn:entity:place":
            return [{"id": "bridge", "name": "Brooklyn Bridge", "tags":[{"name":"Landmark"}]},
                    {"id": "bistro", "name": "Shared Bistro", "tags":[{"name":"Restaurant"}]}]
        if ids[0] == "A":
            return [{"id": "soloA", "name": "A only"},
                    {"id": "shared", "name": "Shared movie"}]
        return [{"id": "shared", "name": "Shared movie"},
                {"id": "soloB", "name": "B only"}]

class CoverageTests(unittest.TestCase):
    def test_rank_only_common_movie_and_no_invented_score(self):
        result = plan([["A"], ["B"]], categories=("film",), client=ScenarioClient())
        item = result["choices"][0]
        self.assertEqual(item["name"], "Shared movie")
        self.assertEqual(item["participant_ranks"], [2,1])
        self.assertEqual(item["source"], "qloo_rank")
        self.assertIsNone(item["score"])

    def test_dining_rejects_landmark(self):
        result = plan([["A"], ["B"]], categories=("dining",), location="New York", client=ScenarioClient())
        self.assertEqual(result["choices"][0]["name"], "Shared Bistro")

    def test_genuinely_disjoint_results(self):
        class Disjoint(ScenarioClient):
            def insights(self, ids, kind, location=None, take=15):
                return [{"id": ids[0], "name": ids[0]}]
        result = plan([["A"], ["B"]], categories=("film",), client=Disjoint())
        self.assertIsNone(result["choices"][0]["name"])

if __name__ == "__main__":
    unittest.main()
