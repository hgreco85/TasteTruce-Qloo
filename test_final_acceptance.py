"""Final bounded offline acceptance matrix. No paid API calls or secrets."""
import unittest
from tastetruce import plan

class BoundedQloo:
    def __init__(self): self.calls=[]
    def search(self, term, kind, take=3):
        self.calls.append(("search",term,take))
        return [{"id":term}]
    def insights(self, ids, kind, location=None, take=30):
        self.calls.append(("insights",kind,take))
        assert take == 30
        if kind=="urn:entity:place":
            return [{"id":"landmark","name":"Brooklyn Bridge","tags":[{"name":"Landmark"}]},
                    {"id":"restaurant","name":"Shared Restaurant","tags":[{"name":"Restaurant"}]}]
        if kind=="urn:entity:artist":
            return [{"id":"shared_artist","name":"Shared Music"}]
        return [{"id":"shared_movie","name":"Shared Movie"}]

class FinalAcceptance(unittest.TestCase):
    def test_three_distinct_profiles_bounded(self):
        client=BoundedQloo()
        result=plan([["Radiohead"],["Daft Punk"],["Björk"]],
                    categories=("film","music","dining"),location="New York",client=client)
        self.assertEqual(result["mode"],"LIVE_QLOO")
        self.assertEqual([x["name"] for x in result["choices"]],
                         ["Shared Movie","Shared Music","Shared Restaurant"])
        self.assertEqual(len(client.calls),12)  # 3 search + 3*3 insights, no retry
        self.assertTrue(all(x["score"] is None for x in result["choices"]))
        self.assertTrue(all(x["source"]=="qloo_rank" for x in result["choices"]))
    def test_empty_interest_refused_before_calls(self):
        client=BoundedQloo()
        with self.assertRaises(ValueError):
            plan([["Radiohead"],[]],client=client)
        self.assertEqual(client.calls,[])
if __name__=="__main__": unittest.main()
