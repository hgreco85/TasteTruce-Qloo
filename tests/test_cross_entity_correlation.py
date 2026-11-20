import unittest
from src.affinity_matrix import CulturalAffinityMatrix, compute_cosine_similarity, compute_jaccard_similarity


class TestCrossEntityCorrelation(unittest.TestCase):
    def setUp(self):
        self.entities = ["EntityA", "EntityB", "EntityC"]
        self.domains = ["music", "literature", "visual_arts"]
        self.matrix = CulturalAffinityMatrix(entities=self.entities, domains=self.domains)

        # Populate deterministic profiles
        self.matrix.set_domain_profile("EntityA", "music", {"classical": 0.8, "jazz": 0.6, "rock": 0.1})
        self.matrix.set_domain_profile("EntityA", "literature", {"sci-fi": 0.9, "philosophy": 0.7})
        self.matrix.set_domain_profile("EntityA", "visual_arts", {"minimalism": 0.8, "expressionism": 0.2})

        self.matrix.set_domain_profile("EntityB", "music", {"classical": 0.8, "jazz": 0.6, "rock": 0.1})
        self.matrix.set_domain_profile("EntityB", "literature", {"sci-fi": 0.9, "philosophy": 0.7})
        self.matrix.set_domain_profile("EntityB", "visual_arts", {"minimalism": 0.8, "expressionism": 0.2})

        self.matrix.set_domain_profile("EntityC", "music", {"pop": 0.9, "hip-hop": 0.8})
        self.matrix.set_domain_profile("EntityC", "literature", {"romance": 0.9})
        self.matrix.set_domain_profile("EntityC", "visual_arts", {"pop-art": 0.9})

    def test_deterministic_identical_affinity(self):
        """Verify that entities with identical profiles achieve an affinity score of 1.0 deterministically."""
        score_1 = self.matrix.calculate_cross_domain_affinity("EntityA", "EntityB")
        score_2 = self.matrix.calculate_cross_domain_affinity("EntityA", "EntityB")
        self.assertEqual(score_1, score_2)
        self.assertAlmostEqual(score_1, 1.0, places=6)

    def test_orthogonal_profiles_affinity(self):
        """Verify that entities with non-overlapping traits have 0 affinity across domains."""
        score = self.matrix.calculate_cross_domain_affinity("EntityA", "EntityC")
        self.assertAlmostEqual(score, 0.0, places=6)

    def test_affinity_matrix_symmetry_and_diagonal(self):
        """Verify that full affinity matrix is strictly symmetric and diagonal is 1.0."""
        mat = self.matrix.get_affinity_matrix()
        n = len(self.entities)
        self.assertEqual(len(mat), n)
        for i in range(n):
            self.assertEqual(len(mat[i]), n)
            self.assertAlmostEqual(mat[i][i], 1.0, places=6)
            for j in range(n):
                self.assertAlmostEqual(mat[i][j], mat[j][i], places=6)

    def test_weighted_domain_affinity(self):
        """Verify that custom domain weights appropriately modulate affinity calculation."""
        # Custom domain weight focusing only on music
        weights_music = {"music": 1.0, "literature": 0.0, "visual_arts": 0.0}
        score_music = self.matrix.calculate_cross_domain_affinity("EntityA", "EntityB", weights=weights_music)
        self.assertAlmostEqual(score_music, 1.0, places=6)

        # Modify B music traits to verify weighted sensitivity
        self.matrix.set_domain_profile("EntityB", "music", {"pop": 1.0})
        score_updated = self.matrix.calculate_cross_domain_affinity("EntityA", "EntityB", weights=weights_music)
        self.assertAlmostEqual(score_updated, 0.0, places=6)


if __name__ == "__main__":
    unittest.main()
