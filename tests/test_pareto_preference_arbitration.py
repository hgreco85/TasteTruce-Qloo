"""Unit tests for deterministic multi-party preference distance and Pareto-optimal group satisfaction convergence."""

import unittest
from pareto_preference_arbitration import (
    preference_distance,
    group_preference_distance,
    compute_satisfactions,
    is_pareto_dominated,
    filter_pareto_optimal,
    arbitrate_group_consensus,
)


class TestParetoPreferenceArbitration(unittest.TestCase):

    def test_preference_distance_metrics(self):
        """Verify deterministic distance calculations for Manhattan, Euclidean, and Chebyshev metrics."""
        p1 = [0.0, 0.0, 1.0]
        p2 = [1.0, 2.0, 3.0]

        manhattan_dist = preference_distance(p1, p2, metric="manhattan")
        self.assertAlmostEqual(manhattan_dist, 1.0 + 2.0 + 2.0, places=6)

        euclidean_dist = preference_distance(p1, p2, metric="euclidean")
        expected_euclidean = (1.0**2 + 2.0**2 + 2.0**2) ** 0.5  # 3.0
        self.assertAlmostEqual(euclidean_dist, expected_euclidean, places=6)

        chebyshev_dist = preference_distance(p1, p2, metric="chebyshev")
        self.assertAlmostEqual(chebyshev_dist, 2.0, places=6)

        # Mismatched dimensions
        with self.assertRaises(ValueError):
            preference_distance([0.0], [0.0, 1.0])

        # Group preference aggregate
        group = [[0.0, 0.0], [1.0, 1.0]]
        target = [0.5, 0.5]
        grp_dist = group_preference_distance(group, target, metric="manhattan")
        self.assertAlmostEqual(grp_dist, 1.0, places=6)

    def test_pareto_dominance_and_optimal_filtering(self):
        """Test non-dominated front identification and Pareto-optimal group satisfaction filtering."""
        party_ideals = [
            [0.0, 0.0],  # Party A preference
            [1.0, 1.0],  # Party B preference
        ]
        # Candidates along trade-off
        candidates = [
            [0.0, 0.0],  # Candidate 1: Max A satisfaction, low B
            [1.0, 1.0],  # Candidate 2: Max B satisfaction, low A
            [0.5, 0.5],  # Candidate 3: Balanced compromise
            [-0.5, -0.5], # Candidate 4: Dominated by Candidate 1
            [1.5, 1.5],  # Candidate 5: Dominated by Candidate 2
        ]

        pareto_front = filter_pareto_optimal(
            candidates,
            party_ideals,
            max_possible_distance=2.0,
            metric="euclidean"
        )

        pareto_candidates = [cand for cand, _ in pareto_front]
        # Candidates 1, 2, and 3 should belong to the Pareto set
        self.assertIn([0.0, 0.0], pareto_candidates)
        self.assertIn([1.0, 1.0], pareto_candidates)
        self.assertIn([0.5, 0.5], pareto_candidates)
        # Strictly dominated candidates should be filtered out
        self.assertNotIn([-0.5, -0.5], pareto_candidates)
        self.assertNotIn([1.5, 1.5], pareto_candidates)

    def test_group_satisfaction_convergence(self):
        """Verify convergence towards Pareto-optimal consensus and group satisfaction guarantee."""
        party_ideals = [
            [0.2, 0.8],
            [0.8, 0.2],
            [0.5, 0.5]
        ]
        weights = [0.3, 0.3, 0.4]

        consensus, satisfactions, iters = arbitrate_group_consensus(
            party_ideals=party_ideals,
            weights=weights,
            metric="euclidean",
            bounds=[(0.0, 1.0), (0.0, 1.0)],
            convergence_tol=1e-7,
            max_iterations=100
        )

        # Expected analytic centroid: 0.3*0.2 + 0.3*0.8 + 0.4*0.5 = 0.5
        self.assertAlmostEqual(consensus[0], 0.5, places=4)
        self.assertAlmostEqual(consensus[1], 0.5, places=4)
        self.assertTrue(iters >= 1)

        # Verify that all parties achieve positive non-zero satisfaction at consensus
        for score in satisfactions:
            self.assertGreater(score, 0.0)
            self.assertLessEqual(score, 1.0)

        # Consensus should not be Pareto-dominated by extreme outliers
        other_evals = [compute_satisfactions([1.0, 0.0], party_ideals, max_possible_distance=1.0)]
        self.assertFalse(is_pareto_dominated(satisfactions, other_evals))


if __name__ == "__main__":
    unittest.main()
