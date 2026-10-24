import unittest
from taste_recommender.validator import RecommendationSchemaValidator


class TestRecommendationSchemaValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RecommendationSchemaValidator(fallback_threshold=0.6)
        self.valid_payload = {
            "item_id": "item_001",
            "name": "Matcha Latte",
            "category": "beverage",
            "confidence": 0.95,
            "taste_profile": {
                "sweet": 0.4,
                "salty": 0.1,
                "sour": 0.05,
                "bitter": 0.6,
                "umami": 0.7,
            },
        }

    def test_valid_payload_passes_validation(self):
        is_valid, errors = self.validator.validate(self.valid_payload)
        self.assertTrue(is_valid)
        self.assertEqual(errors, [])

    def test_negative_fuzzing_suite(self):
        fuzzed_cases = RecommendationSchemaValidator.generate_negative_fuzz_cases(self.valid_payload)
        self.assertGreaterEqual(len(fuzzed_cases), 5)
        for idx, bad_case in enumerate(fuzzed_cases):
            is_valid, errors = self.validator.validate(bad_case)
            self.assertFalse(is_valid, f"Fuzzed case at index {idx} unexpectedly passed validation")
            self.assertGreater(len(errors), 0)

    def test_similarity_scoring_and_fallback_matching(self):
        target = {
            "taste_profile": {
                "sweet": 0.8,
                "salty": 0.1,
                "sour": 0.1,
                "bitter": 0.0,
                "umami": 0.0,
            }
        }

        corpus = [
            {
                "item_id": "b_candy",
                "name": "Caramel Candy",
                "category": "dessert",
                "confidence": 0.9,
                "taste_profile": {
                    "sweet": 0.9,
                    "salty": 0.1,
                    "sour": 0.05,
                    "bitter": 0.0,
                    "umami": 0.0,
                },
            },
            {
                "item_id": "a_syrup",
                "name": "Maple Syrup",
                "category": "dessert",
                "confidence": 0.85,
                "taste_profile": {
                    "sweet": 0.9,
                    "salty": 0.1,
                    "sour": 0.05,
                    "bitter": 0.0,
                    "umami": 0.0,
                },
            },
            {
                "item_id": "c_tea",
                "name": "Black Tea",
                "category": "beverage",
                "confidence": 0.8,
                "taste_profile": {
                    "sweet": 0.0,
                    "salty": 0.0,
                    "sour": 0.0,
                    "bitter": 0.9,
                    "umami": 0.3,
                },
            },
        ]

        best_match = self.validator.fallback_match(target, corpus)
        self.assertIsNotNone(best_match)
        # Due to identical highest similarity, tie-breaking chooses 'a_syrup' over 'b_candy'
        self.assertEqual(best_match["item_id"], "a_syrup")

        # Test similarity calculation directly
        sim = self.validator.calculate_similarity(
            {"sweet": 1.0, "salty": 0.0, "sour": 0.0, "bitter": 0.0, "umami": 0.0},
            {"sweet": 1.0, "salty": 0.0, "sour": 0.0, "bitter": 0.0, "umami": 0.0}
        )
        self.assertEqual(sim, 1.0)

    def test_fallback_match_returns_none_below_threshold(self):
        strict_validator = RecommendationSchemaValidator(fallback_threshold=0.999)
        target = {
            "taste_profile": {
                "sweet": 1.0,
                "salty": 0.0,
                "sour": 0.0,
                "bitter": 0.0,
                "umami": 0.0,
            }
        }
        corpus = [self.valid_payload]
        best_match = strict_validator.fallback_match(target, corpus)
        self.assertIsNone(best_match)


if __name__ == "__main__":
    unittest.main()
