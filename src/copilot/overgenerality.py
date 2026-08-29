"""Over-generality gate (entropy) + question selection (max-entropy facet). See
implementation/04_SYSTEM_DESIGN.md for the two codex-review-driven corrections baked in here:
1. Actual numerically-stable softmax, not plain-sum normalization (round 1).
2. A calibrated `temperature` so RRF's tiny score gaps don't saturate entropy near 1.0 (round 2).
"""
from __future__ import annotations

import math
from collections import Counter

DEFAULT_TEMPERATURE = 0.02  # starting point sized to RRF's ~1/60 scale; calibrate in Phase 1.3


def score_entropy(top_k_scores: list[float], temperature: float = DEFAULT_TEMPERATURE) -> float:
    if not top_k_scores:
        return 0.0
    scaled = [s / temperature for s in top_k_scores]
    m = max(scaled)
    exps = [math.exp(s - m) for s in scaled]
    total = sum(exps) or 1e-9
    probs = [e / total for e in exps]
    k = len(probs)
    if k <= 1:
        return 0.0
    h = -sum(p * math.log(p + 1e-12) for p in probs)
    return h / math.log(k)


def should_clarify(entropy: float, pool_size: int, turns_remaining: int,
                    low: float = 0.3, high: float = 0.8,
                    min_pool_to_bother: int = 4, no_ask_after_turn: int = 7) -> bool:
    if turns_remaining <= (10 - no_ask_after_turn):
        return False
    if pool_size < min_pool_to_bother:
        return False
    return entropy >= low


# 'brand' is a valid ask_attribute enum value but has no matching branch in the simulator's
# classify_constraint() -- asking it can never surface a constraint (wiki/09_simulator_mechanics.md).
_UNPRODUCTIVE_ATTRIBUTES = {"other", "brand"}


def select_best_question(candidates: list[dict], filled_slots: set[str], attribute_enum: list[str]) -> str | None:
    best_attr, best_h = None, -1.0
    for attr in attribute_enum:
        if attr in filled_slots or attr in _UNPRODUCTIVE_ATTRIBUTES:
            continue
        h = _facet_value_entropy(candidates, attr)
        if h > best_h:
            best_attr, best_h = attr, h
    return best_attr if best_h > 0 else None


def _facet_value_entropy(candidates: list[dict], attribute: str) -> float:
    values = [c.get("attributes", {}).get(attribute) for c in candidates if c.get("attributes", {}).get(attribute)]
    if not values:
        return 0.0
    counts = Counter(values)
    total = len(values)
    return -sum((n / total) * math.log((n / total) + 1e-12) for n in counts.values())


def top_facet_values(candidates: list[dict], attribute: str, limit: int = 3) -> list[str]:
    """Concrete catalog-grounded values for phrasing a closed-choice question."""
    values = [c.get("attributes", {}).get(attribute) for c in candidates if c.get("attributes", {}).get(attribute)]
    return [v for v, _ in Counter(values).most_common(limit)]
