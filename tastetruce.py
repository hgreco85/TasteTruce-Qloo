"""TasteTruce: deterministic cross-domain group taste agent, using Qloo (stdlib-only)."""
from __future__ import annotations
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from collections import defaultdict

BASE = "https://hackathon.api.qloo.com"
CATEGORIES = {"film": "urn:entity:movie", "music": "urn:entity:artist", "dining": "urn:entity:place", "books": "urn:entity:book"}
FIXTURES = {
    "film": [{"name": "Shared Cinema Night", "id": "demo-film", "affinity": .81}],
    "music": [{"name": "Shared Music Session", "id": "demo-music", "affinity": .76}],
    "dining": [{"name": "Shared Dinner", "id": "demo-dining", "affinity": .79}],
    "books": [{"name": "Shared Reading", "id": "demo-books", "affinity": .72}],
}

class QlooError(Exception):
    pass

class Qloo:
    def __init__(self, key=None, base=BASE, transport=None):
        self.key = key if key is not None else os.environ.get("QLOO_API_KEY", "")
        self.base = base.rstrip("/")
        if urllib.parse.urlsplit(self.base).scheme != "https":
            raise ValueError("HTTPS required")
        self.transport = transport or urllib.request.urlopen

    def get(self, path, params):
        if not self.key:
            raise QlooError("QLOO_API_KEY missing")
        url = self.base + path + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"X-Api-Key": self.key, "Accept": "application/json"})
        try:
            with self.transport(req, timeout=8) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            raise QlooError("Qloo HTTP " + str(exc.code)) from None
        except Exception as exc:
            raise QlooError("Qloo request unsuccessful: " + type(exc).__name__) from None

    def search(self, term, kind, take=5):
        return entities(self.get("/search", {"query": term, "types": kind, "take": take}))

    def insights(self, ids, kind, location=None, take=15):
        params = {"filter.type": kind, "signal.interests.entities": ",".join(ids), "take": take}
        if location and kind == "urn:entity:place":
            params["filter.location.query"] = location
        return entities(self.get("/v2/insights", params))

def entities(payload):
    """Normalize documented results.entities plus list-shaped API responses."""
    if not isinstance(payload, dict):
        return []
    value = payload.get("results", payload.get("entities", []))
    if isinstance(value, dict):
        value = value.get("entities", value.get("results", []))
    return [x for x in value if isinstance(x, dict)] if isinstance(value, list) else []

def entity_id(obj):
    return str(obj.get("id") or obj.get("entity_id") or obj.get("entityId") or "").strip()

def entity_name(obj):
    return str(obj.get("name") or obj.get("title") or obj.get("properties", {}).get("name", "")).strip()

def scoring(obj):
    raw = obj.get("affinity", obj.get("score", 0))
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.

def plan(profiles, categories=("film", "music", "dining"), location=None, client=None, offline=False):
    """Bounded multi-agent workflow: resolve -> discover -> rank -> justify."""
    if not 2 <= len(profiles) <= 5:
        raise ValueError("2-5 participants required")
    if len(categories) > 4 or not categories or any(x not in CATEGORIES for x in categories):
        raise ValueError("Invalid categories")
    if any(not isinstance(p, list) or not 1 <= len(p) <= 4 or any(not isinstance(t, str) or len(t) > 100 for t in p) for p in profiles):
        raise ValueError("Each person needs 1-4 short interests")
    if location and len(location) > 100:
        raise ValueError("Location too long")
    if offline:
        return {"mode": "OFFLINE_FIXTURE_NOT_REAL_QLOO", "choices": [
            {"category": c, "name": FIXTURES[c][0]["name"], "score": FIXTURES[c][0]["affinity"],
             "why": "Demonstration fixture; not a real recommendation", "source": "fixture"}
            for c in categories], "unresolved": []}
    client = client or Qloo()
    resolved, unresolved = [], []
    for person, interests in enumerate(profiles):
        ids = []
        for term in interests:
            matches = client.search(term.strip(), "urn:entity:artist", take=3)
            if matches and entity_id(matches[0]):
                ids.append(entity_id(matches[0]))
            else:
                unresolved.append({"person": person + 1, "interest": term})
        resolved.append(list(dict.fromkeys(ids)))
    if any(not p for p in resolved):
        return {"mode": "LIVE_QLOO", "choices": [], "unresolved": unresolved, "error": "At least one participant has no resolved tastes"}
    choices = []
    for cat in categories:
        # Per-person evidence, not pooled popularity: consensus is minimum support.
        per_person = []
        for ids in resolved:
            results = client.insights(ids, CATEGORIES[cat], location=location, take=15)
            per_person.append({entity_id(x): x for x in results if entity_id(x)})
        shared = set.intersection(*(set(x) for x in per_person))
        scores = []
        for id_ in shared:
            objs = [group[id_] for group in per_person]
            vals = [scoring(x) for x in objs]
            score = round(min(vals) * .7 + sum(vals) / len(vals) * .3, 4)
            scores.append((score, entity_name(objs[0]), id_, vals))
        scores.sort(key=lambda x: (-x[0], x[1], x[2]))
        if scores:
            score, name, id_, affinities = scores[0]
            choices.append({"category": cat, "name": name or id_, "qloo_id": id_, "score": score,
                            "participant_affinities": affinities,
                            "why": "Shared Qloo entity: 70% weakest-member affinity + 30% mean affinity",
                            "source": "qloo"})
        else:
            choices.append({"category": cat, "name": None, "score": None, "why": "No verified common entity in returned candidates; no invented recommendation", "source": "qloo"})
    return {"mode": "LIVE_QLOO", "choices": choices, "unresolved": unresolved}

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--location", default=None)
    parser.add_argument("--profiles", default='[["Radiohead"],["Daft Punk"]]')
    args = parser.parse_args()
    print(json.dumps(plan(json.loads(args.profiles), location=args.location, offline=args.offline), indent=2))
