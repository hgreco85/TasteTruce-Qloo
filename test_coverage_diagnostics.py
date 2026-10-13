import unittest
from tastetruce import plan

class CoverageDiagnostics(unittest.TestCase):
    class Client:
        def search(self, term, kind, take=3):
            return [{"id":term}]
        def insights(self, ids, kind, location=None, take=30):
            if ids[0]=="EMPTY": return []
            return [{"id":ids[0], "name":ids[0]}]
    def test_no_candidates_is_distinct(self):
        result=plan([["EMPTY"],["OTHER"]], categories=("film",), client=self.Client())
        choice=result["choices"][0]
        self.assertEqual(choice["candidate_counts"],[0,1])
        self.assertIn("No eligible results",choice["why"])
        self.assertIsNone(choice["name"])
    def test_disjoint_candidates_is_distinct(self):
        result=plan([["FIRST"],["SECOND"]], categories=("film",),client=self.Client())
        choice=result["choices"][0]
        self.assertEqual(choice["candidate_counts"],[1,1])
        self.assertIn("none share",choice["why"])
        self.assertIsNone(choice["score"])
    def test_shared_candidate_keeps_evidence(self):
        class Shared(self.Client):
            def insights(self, ids, kind, location=None, take=30):
                return [{"id":"one","name":"One"}]
        choice=plan([["FIRST"],["SECOND"]],categories=("film",),client=Shared())["choices"][0]
        self.assertEqual(choice["source"],"qloo_rank")
        self.assertEqual(choice["candidate_counts"],[1,1])
if __name__=="__main__": unittest.main()
