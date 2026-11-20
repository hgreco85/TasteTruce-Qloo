import math
from typing import List, Dict, Any, Tuple, Optional, Callable


def preference_distance(p1: Dict[str, float], p2: Dict[str, float], metric: str = "euclidean") -> float:
    """
    Computes a deterministic distance metric between two preference weight vectors / dictionaries.
    Missing keys default to weight 0.0.
    """
    keys = sorted(set(p1.keys()).union(set(p2.keys())))
    if metric == "euclidean":
        dist_sq = sum((p1.get(k, 0.0) - p2.get(k, 0.0)) ** 2 for k in keys)
        return math.sqrt(dist_sq)
    elif metric == "manhattan":
        return sum(abs(p1.get(k, 0.0) - p2.get(k, 0.0)) for k in keys)
    elif metric == "chebyshev":
        if not keys:
            return 0.0
        return max(abs(p1.get(k, 0.0) - p2.get(k, 0.0)) for k in keys)
    else:
        raise ValueError(f"Unsupported metric: {metric}")


def multi_party_dispersion(preferences: List[Dict[str, float]], metric: str = "euclidean") -> float:
    """
    Computes the deterministic pairwise average distance across a group of parties.
    """
    n = len(preferences)
    if n <= 1:
        return 0.0
    total_dist = 0.0
    count = 0
    for i in range(n):
        for j in range(i + 1, n):
            total_dist += preference_distance(preferences[i], preferences[j], metric=metric)
            count += 1
    return total_dist / count if count > 0 else 0.0


def evaluate_satisfaction(candidate_state: Dict[str, float], preference: Dict[str, float]) -> float:
    """
    Computes a scalar satisfaction score for a party given their preference vector.
    Higher is better. Computed as a normalized inner product / negative weighted distance.
    """
    keys = sorted(set(candidate_state.keys()).union(set(preference.keys())))
    # Inner product as utility
    return sum(candidate_state.get(k, 0.0) * preference.get(k, 0.0) for k in keys)


def is_pareto_dominated(candidate_utilities: List[float], other_utilities: List[float], tolerance: float = 1e-9) -> bool:
    """
    Returns True if candidate_utilities is strictly Pareto-dominated by other_utilities.
    `other` dominates `candidate` iff all elements of `other` are >= `candidate`
    and at least one element is strictly greater.
    """
    all_greater_or_equal = True
    at_least_one_strictly_greater = False
    for u_cand, u_oth in zip(candidate_utilities, other_utilities):
        if u_oth < u_cand - tolerance:
            all_greater_or_equal = False
            break
        if u_oth > u_cand + tolerance:
            at_least_one_strictly_greater = True
    return all_greater_or_equal and at_least_one_strictly_greater


def find_pareto_optimal_front(
    candidates: List[Dict[str, float]],
    party_preferences: List[Dict[str, float]]
) -> List[Tuple[Dict[str, float], List[float]]]:
    """
    Identifies candidates whose utility profiles across all parties are non-dominated.
    Returns list of (candidate, [utility_party_1, utility_party_2, ...]).
    """
    evaluated = []
    for cand in candidates:
        utils = [evaluate_satisfaction(cand, pref) for pref in party_preferences]
        evaluated.append((cand, utils))

    pareto_front = []
    for i, (cand_i, utils_i) in enumerate(evaluated):
        dominated = False
        for j, (cand_j, utils_j) in enumerate(evaluated):
            if i != j and is_pareto_dominated(utils_i, utils_j):
                dominated = True
                break
        if not dominated:
            pareto_front.append((cand_i, utils_i))
    return pareto_front


def arbitrate_pareto_convergence(
    candidates: List[Dict[str, float]],
    party_preferences: List[Dict[str, float]],
    social_welfare_func: Optional[Callable[[List[float]], float]] = None
) -> Tuple[Dict[str, float], List[float], float]:
    """
    Finds the optimal compromise candidate on the Pareto frontier.
    Defaults to maximizing egalitarian/Nash product welfare or utilitarian sum.
    Returns (best_candidate, utilities, welfare_score).
    """
    if not candidates:
        raise ValueError("No candidates provided for arbitration.")
    
    front = find_pareto_optimal_front(candidates, party_preferences)
    if not front:
        raise ValueError("No Pareto-optimal candidates found.")

    if social_welfare_func is None:
        # Default: Nash Bargaining Solution (product of positive utilities or sum if negative/zero)
        def default_welfare(utils: List[float]) -> float:
            min_u = min(utils)
            if min_u > 0:
                # Nash product
                return sum(math.log(u) for u in utils)
            # Fallback to utilitarian sum with egalitarian penalty
            return sum(utils) - (max(utils) - min(utils))
        social_welfare_func = default_welfare

    best_cand = None
    best_utils = None
    best_score = -float("inf")

    # Deterministic sorting to break ties cleanly
    for cand, utils in front:
        score = social_welfare_func(utils)
        if score > best_score:
            best_score = score
            best_cand = cand
            best_utils = utils

    return best_cand, best_utils, best_score
