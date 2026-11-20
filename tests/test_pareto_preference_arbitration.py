import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.pareto_preference_arbitration import (
    preference_distance,
    multi_party_dispersion,
    evaluate_satisfaction,
    is_pareto_dominated,
    find_pareto_optimal_front,
    arbitrate_pareto_convergence,
)


class TestParetoPreferenceArbitration(unittest.TestCase):

    def test_deterministic_preference_distance_metrics(self):
        p1 = {"security": 0.8, "efficiency": 0.4, "usability": 0.2}
        p2 = {"security": 0.5, "efficiency": 0.8, "usability": 0.2}

        # Euclidean: sqrt((0.8-0.5)^2 + (0.4-0.8)^2 + 0) = sqrt(0.09 + 0.16) = 0.5
        euclid = preference_distance(p1, p2, metric="euclidean")
        self.assertAlmostEqual(euclid, 0.5, places=6)

        # Manhattan: |0.3| + |-0.4| + 0 = 0.7
        manhattan = preference_distance(p1, p2, metric="manhattan")
        self.assertAlmostEqual(manhattan, 0.7, places=6)

        # Chebyshev: max(0.3, 0.4, 0) = 0.4
        chebyshev = preference_distance(p1, p2, metric="chebyshev")
        self.assertAlmostEqual(chebyshev, 0.4, places=6)

        # Multi-party dispersion
        p3 = {"security": 0.5, "efficiency": 0.4, "usability": 0.2}
        # dist(p1, p2) = 0.5
        # dist(p1, p3) = 0.3
        # dist(p2, p3) = 0.4
        # average = (0.5 + 0.3 + 0.4) / 3 = 0.4
        dispersion = multi_party_dispersion([p1, p2, p3], metric="euclidean")
        self.assertAlmostEqual(dispersion, 0.4, places=6)

    def test_pareto_frontier_identification(self):
        # 2 parties
        party_prefs = [
            {"x": 1.0, "y": 0.0},
            {"x": 0.0, "y": 1.0}
        ]

        candidates = [
            {"name": "c1", "x": 10.0, "y": 0.0},  # utils: [10, 0]
            {"name": "c2", "x": 0.0, "y": 10.0},  # utils: [0, 10]
            {"name": "c3", "x": 5.0, "y": 5.0},    # utils: [5, 5]
            {"name": "dominated", "x": 2.0, "y": 2.0}  # utils: [2, 2] -> dominated by c3
        ]

        front = find_pareto_optimal_front(candidates, party_prefs)
        front_names = {cand["name"] for cand, _ in front}
        self.assertIn("c1", front_names)
        self.assertIn("c2", front_names)
        self.assertIn("c3", front_names)
        self.assertNotIn("dominated", front_names)

        # Test dominance helper explicitly
        self.assertTrue(is_pareto_dominated([2.0, 2.0], [5.0, 5.0]))
        self.assertFalse(is_pareto_dominated([5.0, 5.0], [2.0, 2.0]))
        self.assertFalse(is_pareto_dominated([10.0, 0.0], [0.0, 10.0]))

    def test_group_satisfaction_convergence_arbitration(self):
        party_prefs = [
            {"a": 0.7, "b": 0.3},
            {"a": 0.3, "b": 0.7}
        ]

        # Candidates presenting trade-offs
        candidates = [
            {"id": "extreme_a", "a": 10.0, "b": 0.0},
            {"id": "extreme_b", "a": 0.0, "b": 10.0},
            {"id": "balanced", "a": 5.0, "b": 5.0},
            {"id": "suboptimal", "a": 3.0, "b": 3.0}
        ]

        best_cand, best_utils, welfare = arbitrate_pareto_convergence(candidates, party_prefs)
        # Balanced candidate yields equal utilities: 5.0*0.7 + 5.0*0.3 = 5.0 for both
        # Extreme candidates yield 7.0 for one, 3.0 for the other
        # Nash welfare: log(5) + log(5) = 2*log(5) ≈ 3.2188
        # versus log(7) + log(3) = log(21) ≈ 3.0445
        # Balanced should be selected as optimal compromise convergence
        self.assertEqual(best_cand["id"], "balanced")
        self.assertEqual(best_utils, [5.0, 5.0])
        self.assertGreater(welfare, 0.0)


if __name__ == "__main__":
    unittest.main()
