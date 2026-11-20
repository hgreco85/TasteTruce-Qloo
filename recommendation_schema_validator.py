import math
from typing import Any, Dict, List, Optional, Tuple


class SchemaValidationError(Exception):
    """Raised when validation fails and fallback is disabled."""
    pass


# Expected schema definition for deterministic taste recommendations
TASTE_RECOMMENDATION_SPEC: Dict[str, type] = {
    "item_id": str,
    "title": str,
    "genre": str,
    "score": (int, float),
    "tags": list,
}


class TasteRecommendationValidator:
    """
    Deterministic schema validator for taste recommendation payloads.
    Supports negative fuzzing detection, type & value boundary validation,
    and fallback similarity scoring against reference schema/items.
    """

    def __init__(self, reference_item: Optional[Dict[str, Any]] = None):
        self.reference_item = reference_item or {
            "item_id": "ref_001",
            "title": "Standard Recommendation",
            "genre": "General",
            "score": 1.0,
            "tags": ["standard", "taste"]
        }

    def validate(self, payload: Any, raise_on_error: bool = True) -> Tuple[bool, List[str]]:
        """
        Validates a single recommendation item against the deterministic schema.
        Returns (is_valid, error_list).
        """
        errors: List[str] = []

        if not isinstance(payload, dict):
            errors.append(f"Payload must be a dict, got {type(payload).__name__}")
            if raise_on_error:
                raise SchemaValidationError("; ".join(errors))
            return False, errors

        # Check missing keys
        for key, expected_type in TASTE_RECOMMENDATION_SPEC.items():
            if key not in payload:
                errors.append(f"Missing required field: '{key}'")
                continue

            val = payload[key]
            if not isinstance(val, expected_type):
                exp_name = (
                    "/ ".join(t.__name__ for t in expected_type)
                    if isinstance(expected_type, tuple)
                    else expected_type.__name__
                )
                errors.append(
                    f"Field '{key}' expected type {exp_name}, got {type(val).__name__}"
                )
            else:
                # Specific semantic / deterministic boundary checks
                if key == "score":
                    if math.isnan(val) or math.isinf(val):
                        errors.append("Field 'score' must be a finite number")
                    elif val < 0.0 or val > 1.0:
                        errors.append(f"Field 'score' must be in range [0.0, 1.0], got {val}")
                elif key == "item_id":
                    if not val.strip():
                        errors.append("Field 'item_id' cannot be blank")
                elif key == "tags":
                    if not all(isinstance(t, str) and t.strip() for t in val):
                        errors.append("Field 'tags' must contain non-empty strings")

        is_valid = len(errors) == 0
        if not is_valid and raise_on_error:
            raise SchemaValidationError("; ".join(errors))

        return is_valid, errors

    def compute_similarity(self, candidate: Dict[str, Any], target: Optional[Dict[str, Any]] = None) -> float:
        """
        Deterministic fallback similarity scoring between a candidate payload
        and a target reference item (or default reference).
        Returns a normalized score between 0.0 and 1.0.
        """
        target = target or self.reference_item
        if not isinstance(candidate, dict) or not isinstance(target, dict):
            return 0.0

        # 1. Key overlap ratio (weight: 0.3)
        cand_keys = set(candidate.keys())
        target_keys = set(target.keys())
        key_overlap = len(cand_keys & target_keys) / max(len(cand_keys | target_keys), 1)

        # 2. Tag Jaccard similarity (weight: 0.35)
        cand_tags = set(candidate.get("tags", [])) if isinstance(candidate.get("tags"), list) else set()
        cand_tags = {str(t).lower() for t in cand_tags}
        target_tags = set(target.get("tags", [])) if isinstance(target.get("tags"), list) else set()
        target_tags = {str(t).lower() for t in target_tags}

        if cand_tags or target_tags:
            tag_sim = len(cand_tags & target_tags) / len(cand_tags | target_tags)
        else:
            tag_sim = 1.0 if "tags" in cand_keys and "tags" in target_keys else 0.0

        # 3. Genre matching (weight: 0.15)
        cand_genre = str(candidate.get("genre", "")).strip().lower()
        target_genre = str(target.get("genre", "")).strip().lower()
        genre_sim = 1.0 if cand_genre and cand_genre == target_genre else 0.0

        # 4. Score proximity (weight: 0.2)
        cand_score = candidate.get("score")
        target_score = target.get("score", 1.0)
        if isinstance(cand_score, (int, float)) and not (math.isnan(cand_score) or math.isinf(cand_score)):
            clamped_cand = max(0.0, min(1.0, float(cand_score)))
            clamped_target = max(0.0, min(1.0, float(target_score)))
            score_sim = 1.0 - abs(clamped_cand - clamped_target)
        else:
            score_sim = 0.0

        total_score = (0.30 * key_overlap) + (0.35 * tag_sim) + (0.15 * genre_sim) + (0.20 * score_sim)
        return round(total_score, 4)

    def validate_with_fallback(self, payload: Any) -> Dict[str, Any]:
        """
        Validates payload. If invalid, returns a fallback resolution dictionary
        with valid=False, error diagnostics, and a fallback similarity score.
        If valid, returns valid=True and identity similarity 1.0.
        """
        is_valid, errors = self.validate(payload, raise_on_error=False)
        if is_valid:
            return {
                "valid": True,
                "errors": [],
                "similarity_to_reference": 1.0,
                "sanitized_payload": payload,
            }

        cand_dict = payload if isinstance(payload, dict) else {}
        sim = self.compute_similarity(cand_dict, self.reference_item)
        return {
            "valid": False,
            "errors": errors,
            "similarity_to_reference": sim,
            "fallback_item": self.reference_item,
        }
