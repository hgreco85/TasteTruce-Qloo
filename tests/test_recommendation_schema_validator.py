import math
import unittest
from recommendation_schema_validator import (
    TasteRecommendationValidator,
    SchemaValidationError,
)


class TestTasteRecommendationSchemaValidator(unittest.TestCase):

    def setUp(self):
        self.reference_item = {
            "item_id": "taste_ref_42",
            "title": "Spicy Ramen",
            "genre": "Japanese",
            "score": 0.95,
            "tags": ["savory", "spicy", "noodle"]
        }
        self.validator = TasteRecommendationValidator(reference_item=self.reference_item)
        self.valid_payload = {
            "item_id": "taste_101",
            "title": "Miso Ramen",
            "genre": "Japanese",
            "score": 0.90,
            "tags": ["savory", "broth", "noodle"]
        }

    def test_valid_payload_deterministic_success(self):
        """Verify valid payloads pass validation with full conformance."""
        is_valid, errors = self.validator.validate(self.valid_payload, raise_on_error=True)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

        res = self.validator.validate_with_fallback(self.valid_payload)
        self.assertTrue(res["valid"])
        self.assertEqual(res["similarity_to_reference"], 1.0)
        self.assertEqual(res["sanitized_payload"], self.valid_payload)

    def test_negative_fuzzing_mutation_cases(self):
        """Negative fuzzing with corruptions, out-of-bounds, wrong types, and NaN."""
        fuzz_cases = [
            ("Non-dict payload", "invalid_string", "Payload must be a dict"),
            ("Missing item_id", {"title": "A", "genre": "B", "score": 0.5, "tags": ["t"]}, "Missing required field: 'item_id'"),
            ("Blank item_id", {**self.valid_payload, "item_id": "   "}, "cannot be blank"),
            ("Score out of range (>1)", {**self.valid_payload, "score": 1.5}, "must be in range [0.0, 1.0]"),
            ("Score negative", {**self.valid_payload, "score": -0.1}, "must be in range [0.0, 1.0]"),
            ("Score NaN", {**self.valid_payload, "score": float("nan")}, "must be a finite number"),
            ("Score Inf", {**self.valid_payload, "score": float("inf")}, "must be a finite number"),
            ("Invalid tags type", {**self.valid_payload, "tags": "savory,spicy"}, "expected type list"),
            ("Tags containing non-strings", {**self.valid_payload, "tags": ["savory", 123]}, "must contain non-empty strings"),
            ("Tags containing empty strings", {**self.valid_payload, "tags": ["savory", ""]}, "must contain non-empty strings"),
        ]

        for desc, corrupted, expected_err in fuzz_cases:
            with self.subTest(case=desc):
                with self.assertRaises(SchemaValidationError):
                    self.validator.validate(corrupted, raise_on_error=True)

                is_valid, errors = self.validator.validate(corrupted, raise_on_error=False)
                self.assertFalse(is_valid)
                self.assertTrue(any(expected_err in err for err in errors), f"Expected '{expected_err}' in {errors}")

    def test_fallback_similarity_scoring(self):
        """Verify deterministic fallback similarity scoring degrades gracefully."""
        # Highly similar candidate (same genre, overlapping tags, close score)
        similar_candidate = {
            "item_id": "taste_close",
            "title": "Spicy Udon",
            "genre": "Japanese",
            "score": 0.85,
            "tags": ["spicy", "noodle"]
        }
        sim_high = self.validator.compute_similarity(similar_candidate)
        self.assertGreater(sim_high, 0.70)
        self.assertLessEqual(sim_high, 1.0)

        # Dissimilar candidate (different genre, zero tag overlap, distant score)
        dissimilar_candidate = {
            "item_id": "taste_far",
            "title": "Sweet Cake",
            "genre": "Dessert",
            "score": 0.10,
            "tags": ["sweet", "sugar"]
        }
        sim_low = self.validator.compute_similarity(dissimilar_candidate)
        self.assertLess(sim_low, sim_high)
        self.assertGreaterEqual(sim_low, 0.0)

        # Completely invalid non-dict or empty
        self.assertEqual(self.validator.compute_similarity({}), 0.0)
        self.assertEqual(self.validator.compute_similarity(None), 0.0)

        # End-to-end validate_with_fallback invocation
        corrupted_payload = {
            "item_id": "taste_err",
            "title": "Spicy Soup",
            "genre": "Japanese",
            "score": 2.0,  # Invalid score
            "tags": ["spicy", "noodle"]
        }
        res = self.validator.validate_with_fallback(corrupted_payload)
        self.assertFalse(res["valid"])
        self.assertIn("fallback_item", res)
        self.assertEqual(res["fallback_item"], self.reference_item)
        self.assertGreater(res["similarity_to_reference"], 0.0)
        self.assertTrue(len(res["errors"]) > 0)


if __name__ == "__main__":
    unittest.main()
