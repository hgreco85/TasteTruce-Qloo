import math
from typing import Dict, List, Tuple


def compute_jaccard_similarity(set_a: set, set_b: set) -> float:
    """Compute Jaccard similarity between two sets."""
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 0.0
    intersection = set_a & set_b
    return len(intersection) / len(union)


def compute_cosine_similarity(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    """Compute cosine similarity between two sparse vector representations."""
    all_keys = set(vec_a.keys()) | set(vec_b.keys())
    if not all_keys:
        return 1.0

    dot_product = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in all_keys)
    norm_a = math.sqrt(sum(v * v for v in vec_a.values()))
    norm_b = math.sqrt(sum(v * v for v in vec_b.values()))

    if norm_a == 0.0 and norm_b == 0.0:
        return 1.0
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot_product / (norm_a * norm_b)


class CulturalAffinityMatrix:
    """Calculates deterministic cross-domain cultural affinity between entities."""

    def __init__(self, entities: List[str], domains: List[str]):
        self.entities = sorted(list(set(entities)))
        self.domains = sorted(list(set(domains)))
        self._profiles: Dict[str, Dict[str, Dict[str, float]]] = {
            entity: {domain: {} for domain in self.domains} for entity in self.entities
        }

    def set_domain_profile(self, entity: str, domain: str, traits: Dict[str, float]) -> None:
        if entity not in self._profiles:
            raise ValueError(f"Unknown entity: {entity}")
        if domain not in self.domains:
            raise ValueError(f"Unknown domain: {domain}")
        self._profiles[entity][domain] = dict(traits)

    def calculate_cross_domain_affinity(
        self, entity_a: str, entity_b: str, weights: Dict[str, float] = None
    ) -> float:
        if entity_a not in self._profiles or entity_b not in self._profiles:
            raise ValueError("Entities must be registered in the matrix")

        if weights is None:
            weights = {domain: 1.0 / len(self.domains) for domain in self.domains} if self.domains else {}

        total_weight = sum(weights.get(d, 0.0) for d in self.domains)
        if total_weight == 0.0:
            return 0.0

        affinity_score = 0.0
        for domain in self.domains:
            weight = weights.get(domain, 0.0)
            if weight <= 0:
                continue
            prof_a = self._profiles[entity_a][domain]
            prof_b = self._profiles[entity_b][domain]
            domain_sim = compute_cosine_similarity(prof_a, prof_b)
            affinity_score += weight * domain_sim

        return affinity_score / total_weight

    def get_affinity_matrix(self, weights: Dict[str, float] = None) -> List[List[float]]:
        """Generate a full symmetric deterministic affinity matrix across all registered entities."""
        n = len(self.entities)
        matrix = [[0.0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(i, n):
                score = self.calculate_cross_domain_affinity(self.entities[i], self.entities[j], weights)
                matrix[i][j] = score
                matrix[j][i] = score
        return matrix
