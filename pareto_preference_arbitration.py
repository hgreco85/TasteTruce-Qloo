"""Multi-party preference distance metric and Pareto-optimal group satisfaction arbitration."""

import math
from typing import Dict, List, Sequence, Tuple, Union


def preference_distance(
    profile_a: Sequence[float],
    profile_b: Sequence[float],
    metric: str = "manhattan"
) -> float:
    """Compute deterministic distance between two preference profiles.

    Supported metrics:
    - 'manhattan': L1 norm
    - 'euclidean': L2 norm
    - 'chebyshev': L-infinity norm
    """
    if len(profile_a) != len(profile_b):
        raise ValueError("Preference profiles must have identical dimensions.")
    if not profile_a:
        return 0.0

    if metric == "manhattan":
        return float(sum(abs(a - b) for a, b in zip(profile_a, profile_b)))
    elif metric == "euclidean":
        return float(math.sqrt(sum((a - b) ** 2 for a, b in zip(profile_a, profile_b))))
    elif metric == "chebyshev":
        return float(max(abs(a - b) for a, b in zip(profile_a, profile_b)))
    else:
        raise ValueError(f"Unsupported metric: {metric}")


def group_preference_distance(
    group_profiles: Sequence[Sequence[float]],
    target_profile: Sequence[float],
    weights: Sequence[float] = None,
    metric: str = "manhattan"
) -> float:
    """Compute weighted aggregate distance from a group of party preferences to a candidate profile."""
    if not group_profiles:
        return 0.0
    num_parties = len(group_profiles)
    if weights is None:
        weights = [1.0 / num_parties] * num_parties
    elif len(weights) != num_parties:
        raise ValueError("Length of weights must match number of parties in group.")

    total_dist = 0.0
    for party_profile, w in zip(group_profiles, weights):
        dist = preference_distance(party_profile, target_profile, metric=metric)
        total_dist += w * dist
    return total_dist


def compute_satisfactions(
    candidate: Sequence[float],
    party_ideals: Sequence[Sequence[float]],
    max_possible_distance: float = 1.0,
    metric: str = "euclidean"
) -> List[float]:
    """Compute party satisfaction scores in [0.0, 1.0] based on distance from party ideals.

    satisfaction = max(0.0, 1.0 - (distance / max_possible_distance))
    """
    satisfactions = []
    for ideal in party_ideals:
        d = preference_distance(candidate, ideal, metric=metric)
        score = max(0.0, 1.0 - (d / max_possible_distance))
        satisfactions.append(score)
    return satisfactions


def is_pareto_dominated(
    candidate_eval: Sequence[float],
    other_evals: Sequence[Sequence[float]],
    tolerance: float = 1e-9
) -> bool:
    """Check if candidate_eval is Pareto-dominated by any other evaluation.

    A candidate y dominates x if y_i >= x_i for all i, and y_j > x_j for at least one j.
    """
    for other in other_evals:
        all_geq = True
        strictly_greater = False
        for o, c in zip(other, candidate_eval):
            if o < c - tolerance:
                all_geq = False
                break
            if o > c + tolerance:
                strictly_greater = True
        if all_geq and strictly_greater:
            return True
    return False


def filter_pareto_optimal(
    candidates: Sequence[Sequence[float]],
    party_ideals: Sequence[Sequence[float]],
    max_possible_distance: float = 1.0,
    metric: str = "euclidean"
) -> List[Tuple[Sequence[float], List[float]]]:
    """Return list of (candidate, satisfactions) that are Pareto-optimal among given candidates."""
    evaluations = [
        compute_satisfactions(cand, party_ideals, max_possible_distance, metric)
        for cand in candidates
    ]
    pareto_set = []
    for idx, (cand, ev) in enumerate(zip(candidates, evaluations)):
        other_evals = [evaluations[j] for j in range(len(evaluations)) if j != idx]
        if not is_pareto_dominated(ev, other_evals):
            pareto_set.append((cand, ev))
    return pareto_set


def arbitrate_group_consensus(
    party_ideals: Sequence[Sequence[float]],
    weights: Sequence[float] = None,
    metric: str = "euclidean",
    bounds: Sequence[Tuple[float, float]] = None,
    learning_rate: float = 0.05,
    max_iterations: int = 200,
    convergence_tol: float = 1e-6
) -> Tuple[List[float], List[float], int]:
    """Iteratively converge to a consensus profile maximizing weighted party satisfaction.

    Returns:
        (consensus_profile, final_satisfactions, iterations_taken)
    """
    if not party_ideals:
        raise ValueError("At least one party ideal must be provided.")
    n_dim = len(party_ideals[0])
    n_parties = len(party_ideals)

    for ideal in party_ideals:
        if len(ideal) != n_dim:
            raise ValueError("All party ideals must have identical dimensions.")

    if weights is None:
        weights = [1.0 / n_parties] * n_parties
    else:
        s = sum(weights)
        if s <= 0:
            raise ValueError("Sum of weights must be positive.")
        weights = [w / s for w in weights]

    # Analytical starting consensus: weighted average of ideals
    current = [0.0] * n_dim
    for d in range(n_dim):
        current[d] = sum(weights[i] * party_ideals[i][d] for i in range(n_parties))

    # Refine if bounds are specified or iterate for verification
    iterations = 0
    for it in range(max_iterations):
        iterations += 1
        # Gradient descent step towards minimizing weighted squared Euclidean distance
        new_pos = [0.0] * n_dim
        for d in range(n_dim):
            target_d = sum(weights[i] * party_ideals[i][d] for i in range(n_parties))
            # Update step
            grad = current[d] - target_d
            val = current[d] - learning_rate * grad
            if bounds and len(bounds) == n_dim:
                val = max(bounds[d][0], min(bounds[d][1], val))
            new_pos[d] = val

        shift = preference_distance(current, new_pos, metric="euclidean")
        current = new_pos
        if shift < convergence_tol:
            break

    final_satisfactions = compute_satisfactions(current, party_ideals, max_possible_distance=1.0, metric=metric)
    return current, final_satisfactions, iterations
