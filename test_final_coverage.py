import unittest
from tastetruce import plan

class CoverageWindowClient:
    def __init__(self):
        self.calls = []
    def search(self, term, kind, take=3):
        return [{"id":term}]
    def insights(self, ids, kind, location=None, take=30):
        self.calls.append((ids[0], take))
        assert take == 30
        # Shared entity appears only at the end of the extended candidate window.
        items = [{"id":ids[0]+"-"+str(i), "name":"Unshared"} for i in range(29)]
        items.append({"id":"common","name":"Cross-taste discovery"})
        return items[:take]

class FinalCoverageTests(unittest.TestCase):
    def test_30_results_recovers_deep_common_match_without_extra_calls(self):
        client=CoverageWindowClient()
        result=plan([["Radiohead"],["Daft Punk"]],categories=("film",),client=client)
        item=result["choices"][0]
        self.assertEqual(item["name"],"Cross-taste discovery")
        self.assertEqual(item["source"],"qloo_rank")
        self.assertEqual(item["participant_ranks"],[30,30])
        self.assertEqual(len(client.calls),2)
    def test_three_people_still_bounded(self):
        client=CoverageWindowClient()
        result=plan([["A"],["B"],["C"]],categories=("film",),client=client)
        self.assertEqual(result["choices"][0]["name"],"Cross-taste discovery")
        self.assertEqual(len(client.calls),3)

if __name__=="__main__":
    unittest.main()
