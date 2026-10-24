import unittest
from cultural_analytics.affinity import (
    compute_cultural_affinity_matrix,
    get_affinity_as_nested_dict,
)


class TestCrossEntityCorrelation(unittest.TestCase):
    def setUp(self):
        self.domain_arts = {
            "renaissance": {"humanism": 0.9, "symmetry": 0.8, "secularism": 0.4},
            "baroque": {"ornamentation": 0.9, "emotionalism": 0.85, "symmetry": 0.3},
            "modernism": {"abstraction": 0.95, "experimentation": 0.8, "humanism": 0.2},
        }

        self.domain_architecture = {
            "classical": {"symmetry": 0.9, "humanism": 0.7, "monumentality": 0.6},
            "rococo": {"ornamentation": 0.95, "emotionalism": 0.75, "asymmetry": 0.5},
            "brutalism": {"abstraction": 0.7, "functionality": 0.9, "monumentality": 0.8},
        }

    def test_affinity_matrix_determinism_and_dimensions(self):
        """Verify that matrix generation is fully deterministic across multiple executions."""
        run_1 = compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="cosine")
        run_2 = compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="cosine")

        self.assertEqual(run_1, run_2)
        self.assertEqual(len(run_1), len(self.domain_arts) * len(self.domain_architecture))

        keys = list(run_1.keys())
        expected_keys = [
            ("baroque", "brutalism"),
            ("baroque", "classical"),
            ("baroque", "rococo"),
            ("modernism", "brutalism"),
            ("modernism", "classical"),
            ("modernism", "rococo"),
            ("renaissance", "brutalism"),
            ("renaissance", "classical"),
            ("renaissance", "rococo"),
        ]
        self.assertEqual(keys, expected_keys)

    def test_expected_cultural_correlation_pairings(self):
        """Ensure high affinity between historically corresponding cultural movements."""
        matrix = compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="cosine")

        # Renaissance should have higher affinity to Classical than to Rococo
        self.assertGreater(
            matrix[("renaissance", "classical")],
            matrix[("renaissance", "rococo")]
        )

        # Baroque should correlate strongly with Rococo
        self.assertGreater(
            matrix[("baroque", "rococo")],
            matrix[("baroque", "brutalism")]
        )

        # Modernism should correlate more with Brutalism than with Classical
        self.assertGreater(
            matrix[("modernism", "brutalism")],
            matrix[("modernism", "classical")]
        )

    def test_nested_dict_conversion(self):
        """Test conversion of affinity matrix into nested 2D dictionary."""
        matrix = compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="cosine")
        nested = get_affinity_as_nested_dict(matrix)

        self.assertEqual(set(nested.keys()), set(self.domain_arts.keys()))
        for k in nested:
            self.assertEqual(set(nested[k].keys()), set(self.domain_architecture.keys()))
            for target_k in nested[k]:
                self.assertEqual(nested[k][target_k], matrix[(k, target_k)])

    def test_multiple_affinity_metrics(self):
        """Test alternative affinity metric computations like euclidean and dot product."""
        dot_matrix = compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="dot_product")
        euc_matrix = compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="euclidean_affinity")

        self.assertIn(("renaissance", "classical"), dot_matrix)
        self.assertGreater(dot_matrix[("renaissance", "classical")], 0.0)

        for val in euc_matrix.values():
            self.assertGreater(val, 0.0)
            self.assertLessEqual(val, 1.0)

    def test_invalid_metric_raises(self):
        """Ensure invalid metric identifier raises ValueError."""
        with self.assertRaises(ValueError):
            compute_cultural_affinity_matrix(self.domain_arts, self.domain_architecture, metric="invalid_metric")


if __name__ == "__main__":
    unittest.main()
