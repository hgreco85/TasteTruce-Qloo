import math
from typing import Any, Dict, List, Optional, Set, Tuple


class ValidationError(Exception):
    """Raised when schema validation fails."""
    pass


class RecommendationSchemaValidator:
    """
    Deterministic taste recommendation schema validator with negative fuzzing
    and fallback similarity scoring.
    """

    REQUIRED_FIELDS: Set[str] = {
        "item_id",
        "name",
        "category",
        "taste_profile",
        "confidence",
    }

    VALID_CATEGORIES: Set[str] = {
        "beverage",
        "food",
        "dessert",
        "snack",
    }

    TASTE_ATTRIBUTES: Set[str] = {
        "sweet",
        "salty",
        "sour",
        "bitter",
        "umami",
    }

    def __init__(self, fallback_threshold: float = 0.5):
        self.fallback_threshold = fallback_threshold

    def validate(self, payload: Any) -> Tuple[bool, List[str]]:
        """
        Deterministically validates a taste recommendation record.
        Returns (is_valid, list_of_error_reasons).
        """
        errors: List[str] = []

        if not isinstance(payload, dict):
            return False, ["Payload must be a dictionary"]

        for field in sorted(self.REQUIRED_FIELDS):
            if field not in payload:
                errors.append(f"Missing required field: '{field}'")

        if errors:
            return False, errors

        # item_id validation
        if not isinstance(payload["item_id"], (int, str)) or str(payload["item_id"]).strip() == "":
            errors.append("Field 'item_id' must be a non-empty string or integer")

        # name validation
        if not isinstance(payload["name"], str) or not payload["name"].strip():
            errors.append("Field 'name' must be a non-empty string")

        # category validation
        if not isinstance(payload["category"], str) or payload["category"].lower() not in self.VALID_CATEGORIES:
            errors.append(f"Field 'category' must be one of {sorted(self.VALID_CATEGORIES)}")

        # confidence validation (deterministic float in [0.0, 1.0])
        confidence = payload["confidence"]
        if not isinstance(confidence, (int, float)) or isinstance(confidence, bool):
            errors.append("Field 'confidence' must be a numeric float between 0.0 and 1.0")
        elif not (0.0 <= float(confidence) <= 1.0):
            errors.append("Field 'confidence' must be within [0.0, 1.0]")

        # taste_profile validation
        taste_profile = payload["taste_profile"]
        if not isinstance(taste_profile, dict):
            errors.append("Field 'taste_profile' must be a dictionary of taste dimensions")
        else:
            for attr in sorted(self.TASTE_ATTRIBUTES):
                if attr not in taste_profile:
                    errors.append(f"taste_profile missing dimension '{attr}'")
                else:
                    val = taste_profile[attr]
                    if not isinstance(val, (int, float)) or isinstance(val, bool) or not (0.0 <= float(val) <= 1.0):
                        errors.append(f"taste_profile dimension '{attr}' must be a float between 0.0 and 1.0")

        return len(errors) == 0, errors

    def calculate_similarity(self, profile_a: Dict[str, float], profile_b: Dict[str, float]) -> float:
        """
        Calculates cosine similarity between two taste profiles deterministically.
        Returns a float between 0.0 and 1.0.
        """
        dot_product = 0.0
        norm_a = 0.0
        norm_b = 0.0

        for dim in sorted(self.TASTE_ATTRIBUTES):
            val_a = float(profile_a.get(dim, 0.0))
            val_b = float(profile_b.get(dim, 0.0))
            dot_product += val_a * val_b
            norm_a += val_a * val_a
            norm_b += val_b * val_b

        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0

        similarity = dot_product / (math.sqrt(norm_a) * math.sqrt(norm_b))
        return round(max(0.0, min(1.0, similarity)), 4)

    def fallback_match(
        self,
        candidate: Dict[str, Any],
        corpus: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Deterministic fallback scoring when primary matching or validation needs nearest alternative.
        Selects the candidate with the highest similarity score above the fallback_threshold.
        Ties are broken deterministically by item_id.
        """
        valid_corpus = [item for item in corpus if self.validate(item)[0]]
        if not valid_corpus:
            return None

        candidate_profile = candidate.get("taste_profile", {})
        scored: List[Tuple[float, str, Dict[str, Any]]] = []

        for item in valid_corpus:
            sim = self.calculate_similarity(candidate_profile, item["taste_profile"])
            if sim >= self.fallback_threshold:
                scored.append((sim, str(item["item_id"]), item))

        if not scored:
            return None

        # Sort descending by similarity, ascending by item_id for deterministic tie-breaking
        scored.sort(key=lambda x: (-x[0], x[1]))
        return scored[0][2]

    @staticmethod
    def generate_negative_fuzz_cases(base_valid_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Generates deterministic fuzzed variations that violate different validation constraints.
        """
        fuzz_cases = []

        # 1. Missing item_id
        c1 = dict(base_valid_payload)
        c1.pop("item_id", None)
        fuzz_cases.append(c1)

        # 2. Empty string name
        c2 = dict(base_valid_payload)
        c2["name"] = "   "
        fuzz_cases.append(c2)

        # 3. Invalid category
        c3 = dict(base_valid_payload)
        c3["category"] = "invalid_category_xyz"
        fuzz_cases.append(c3)

        # 4. Confidence out of bounds (> 1.0)
        c4 = dict(base_valid_payload)
        c4["confidence"] = 1.5
        fuzz_cases.append(c4)

        # 5. Confidence negative
        c5 = dict(base_valid_payload)
        c5["confidence"] = -0.1
        fuzz_cases.append(c5)

        # 6. taste_profile dimension out of bounds
        c6 = dict(base_valid_payload)
        c6["taste_profile"] = dict(base_valid_payload.get("taste_profile", {}))
        c6["taste_profile"]["sweet"] = 2.0
        fuzz_cases.append(c6)

        # 7. taste_profile missing attribute
        c7 = dict(base_valid_payload)
        c7["taste_profile"] = dict(base_valid_payload.get("taste_profile", {}))
        c7["taste_profile"].pop("bitter", None)
        fuzz_cases.append(c7)

        # 8. Non-dict payload
        fuzz_cases.append("not_a_dictionary")

        return fuzz_cases
