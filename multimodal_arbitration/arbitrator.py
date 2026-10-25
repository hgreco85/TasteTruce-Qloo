from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import hashlib


@dataclass(frozen=True)
class PreferenceItem:
    item_id: str
    score: float
    modality: str = "general"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PartyVote:
    party_id: str
    weight: float
    rankings: List[PreferenceItem]


class DeterministicMultimodalArbitrator:
    """
    Arbitrates preference recommendations across multiple parties and modalities
    deterministically using weighted Borda count scoring and cryptographic tie-breaking.
    """

    def __init__(self, party_weight_overrides: Optional[Dict[str, float]] = None):
        self.party_weight_overrides = party_weight_overrides or {}

    def arbitrate(
        self,
        votes: List[PartyVote],
        top_k: Optional[int] = None,
        modality_weights: Optional[Dict[str, float]] = None,
        salt: str = "arbitration_v1"
    ) -> List[Dict[str, Any]]:
        """
        Deterministically combines preferences from all parties.
        Returns a list of arbitrated items ranked by aggregate score.
        """
        if not votes:
            return []

        modality_weights = modality_weights or {}
        scores: Dict[str, float] = {}
        items_by_id: Dict[str, PreferenceItem] = {}

        # Aggregate scores via weighted positional Borda count with modality adjustments
        for vote in votes:
            weight = self.party_weight_overrides.get(vote.party_id, vote.weight)
            if weight <= 0.0:
                continue

            n = len(vote.rankings)
            for rank_idx, item in enumerate(vote.rankings):
                items_by_id[item.item_id] = item
                # Standard positional points: n - rank_idx
                position_points = float(n - rank_idx)
                mod_multiplier = modality_weights.get(item.modality, 1.0)
                score_contrib = position_points * weight * mod_multiplier * (1.0 + max(item.score, 0.0))
                scores[item.item_id] = scores.get(item.item_id, 0.0) + score_contrib

        def tie_breaker_key(item_id: str) -> str:
            hasher = hashlib.sha256()
            hasher.update(salt.encode("utf-8"))
            hasher.update(b":")
            hasher.update(item_id.encode("utf-8"))
            return hasher.hexdigest()

        # Sort descending by score, tie-break by deterministic hash
        sorted_item_ids = sorted(
            scores.keys(),
            key=lambda iid: (-scores[iid], tie_breaker_key(iid))
        )

        if top_k is not None:
            sorted_item_ids = sorted_item_ids[:top_k]

        results = []
        for rank, iid in enumerate(sorted_item_ids, start=1):
            item = items_by_id[iid]
            results.append({
                "rank": rank,
                "item_id": iid,
                "score": round(scores[iid], 6),
                "modality": item.modality,
                "tie_breaker_hash": tie_breaker_key(iid)
            })

        return results
