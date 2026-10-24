from typing import Dict, List, Mapping, Sequence, Tuple, Union
import math


def compute_cultural_affinity_matrix(
    domain_a_profiles: Mapping[str, Mapping[str, float]],
    domain_b_profiles: Mapping[str, Mapping[str, float]],
    metric: str = "cosine"
) -> Dict[Tuple[str, str], float]:
    """
    Computes a deterministic cross-domain cultural affinity matrix between entities
    in domain A and domain B.

    Each profile is a mapping of cultural feature names to numeric weights/scores.
    Supported metrics: 'cosine', 'dot_product', 'jaccard', 'euclidean_affinity'.
    """
    valid_metrics = ("cosine", "dot_product", "jaccard", "euclidean_affinity")
    if metric not in valid_metrics:
        raise ValueError(f"Unsupported metric '{metric}'. Expected one of {valid_metrics}.")

    matrix: Dict[Tuple[str, str], float] = {}

    # Sort keys to ensure deterministic processing order
    sorted_a = sorted(domain_a_profiles.keys())
    sorted_b = sorted(domain_b_profiles.keys())

    for entity_a in sorted_a:
        prof_a = domain_a_profiles[entity_a]
        for entity_b in sorted_b:
            prof_b = domain_b_profiles[entity_b]
            score = _calculate_affinity(prof_a, prof_b, metric)
            # Round to 6 decimal places for numerical stability
            matrix[(entity_a, entity_b)] = round(score, 6)

    return matrix


def _calculate_affinity(
    vec_a: Mapping[str, float],
    vec_b: Mapping[str, float],
    metric: str
) -> float:
    all_keys = set(vec_a.keys()).union(vec_b.keys())
    if not all_keys:
        return 1.0 if metric in ("cosine", "jaccard", "euclidean_affinity") else 0.0

    if metric == "dot_product":
        return sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in all_keys)

    elif metric == "cosine":
        dot = sum(vec_a.get(k, 0.0) * vec_b.get(k, 0.0) for k in all_keys)
        norm_a = math.sqrt(sum(v ** 2 for v in vec_a.values()))
        norm_b = math.sqrt(sum(v ** 2 for v in vec_b.values()))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    elif metric == "jaccard":
        intersection = sum(min(max(vec_a.get(k, 0.0), 0.0), max(vec_b.get(k, 0.0), 0.0)) for k in all_keys)
        union = sum(max(max(vec_a.get(k, 0.0), 0.0), max(vec_b.get(k, 0.0), 0.0)) for k in all_keys)
        if union == 0.0:
            return 1.0
        return intersection / union

    elif metric == "euclidean_affinity":
        dist_sq = sum((vec_a.get(k, 0.0) - vec_b.get(k, 0.0)) ** 2 for k in all_keys)
        return 1.0 / (1.0 + math.sqrt(dist_sq))

    raise ValueError(f"Unknown metric: {metric}")


def get_affinity_as_nested_dict(
    matrix: Dict[Tuple[str, str], float]
) -> Dict[str, Dict[str, float]]:
    """
    Converts flat tuple-keyed affinity matrix to a nested dictionary.
    """
    nested: Dict[str, Dict[str, float]] = {}
    for (entity_a, entity_b), score in matrix.items():
        if entity_a not in nested:
            nested[entity_a] = {}
        nested[entity_a][entity_b] = score
    return nested
