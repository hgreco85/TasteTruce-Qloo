from typing import List, Dict, Any, Optional
import hashlib


class PreferenceProfile:
    """Represents a party's preferences across multi-modal recommendation items."""

    def __init__(self, party_id: str, scores: Dict[str, float], weight: float = 1.0):
        self.party_id = party_id
        self.scores = {k: float(v) for k, v in scores.items()}
        self.weight = max(0.0, float(weight))


class PreferenceArbitrator:
    """Arbitrates between multiple parties' preferences over items deterministically."""

    def __init__(self, conflict_resolution: str = "borda", seed: Optional[str] = None):
        self.conflict_resolution = conflict_resolution
        self.seed = seed or "default-arbitration-seed"

    def _generate_tiebreaker_key(self, item_id: str) -> str:
        hasher = hashlib.sha256()
        hasher.update(self.seed.encode("utf-8"))
        hasher.update(item_id.encode("utf-8"))
        return hasher.hexdigest()

    def arbitrate(
        self,
        candidate_items: List[str],
        profiles: List[PreferenceProfile],
        top_k: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Deterministically combines preferences across parties.
        Returns a list of items sorted by aggregated score descending.
        Ties are broken deterministically using item hashing.
        """
        if not candidate_items:
            return []

        total_weight = sum(p.weight for p in profiles)
        aggregated_scores: Dict[str, float] = {item: 0.0 for item in candidate_items}

        if self.conflict_resolution == "weighted_average":
            if total_weight > 0:
                for profile in profiles:
                    for item in candidate_items:
                        score = profile.scores.get(item, 0.0)
                        aggregated_scores[item] += score * profile.weight
                for item in candidate_items:
                    aggregated_scores[item] /= total_weight
        elif self.conflict_resolution == "borda":
            # Weighted Borda Count
            for profile in profiles:
                ranked = sorted(
                    candidate_items,
                    key=lambda it: (profile.scores.get(it, 0.0), self._generate_tiebreaker_key(it)),
                    reverse=True
                )
                n = len(candidate_items)
                for rank_idx, item in enumerate(ranked):
                    borda_points = (n - 1 - rank_idx) * profile.weight
                    aggregated_scores[item] += borda_points
        elif self.conflict_resolution == "minimax":
            # Maximize the minimum satisfaction across parties
            for item in candidate_items:
                min_score = min(
                    (profile.scores.get(item, 0.0) * profile.weight for profile in profiles),
                    default=0.0
                )
                aggregated_scores[item] = min_score
        else:
            raise ValueError(f"Unsupported conflict resolution strategy: {self.conflict_resolution}")

        # Sort items: aggregated score desc, then deterministic tiebreaker key desc
        ranked_items = sorted(
            candidate_items,
            key=lambda item: (aggregated_scores[item], self._generate_tiebreaker_key(item)),
            reverse=True
        )

        results = [
            {"item_id": item, "score": round(aggregated_scores[item], 6)}
            for item in ranked_items
        ]

        if top_k is not None:
            results = results[:top_k]

        return results
