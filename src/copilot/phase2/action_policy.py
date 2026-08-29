"""Phase 2.2: within-session contextual bandit for facet selection, gated behind
ENABLE_ACTION_POLICY. implementation/06_DECISION_LOG.md D11: real cold-start risk (only ~3-6
clarification decisions per session) -- warm-started from a hand-set prior derived from ground
truth (wiki/09_simulator_mechanics.md: budget/brand are structurally weak reveal channels; category
is free; material/color are the simulator's most common early reveals), not learned from scratch.

LIVE reward is pool-size reduction only (entropy-adjacent, no ground truth) -- see D6/D7: never
condition this on the target rank, which the live agent never has access to.
"""
from __future__ import annotations

ENABLE_ACTION_POLICY = False  # Ablated on the 40-session validation split (wiki/08_evaluation_log.md):
# ON TechnicalScore=0.3693/HitRate@10=0.425/MRR=0.291 vs OFF (same commit) 0.4021/0.475/0.297 --
# OFF wins clearly on every metric. The warm-started prior + within-session updates appear to
# actively fight the already-calibrated entropy selector rather than complementing it, likely
# exactly the cold-start noise D11 flagged (only ~3-6 real decisions per session). DISABLED.
# RE-ABLATED after the Phase 2 codex review fixed two reward-tracking bugs (agent.py: the pool-size
# snapshot was capped at rerank_depth, usually pool-size-invariant; a consumed ask's outcome was
# never cleared and could replay against later unrelated pools) -- ON got WORSE, not better, once
# the reward signal was fixed (0.3595/0.425/0.2616/7.575 vs the buggy run's 0.3693/0.425/0.291), so
# the original "cut" verdict was not an artifact of broken measurement. Module kept for the
# writeup's "tried, measured (twice), cut" record.

# Warm-start prior: relative facet value, grounded in wiki/09's verified simulator mechanics
# (budget/brand rarely survive the intent card's candidate slicing; material/color are the most
# reliably productive reveal channels for the 40%/40% buying/browsing majority of sessions).
_PRIOR = {
    "material": 1.15, "color": 1.15, "size": 1.05, "style": 1.0,
    "use_case": 0.95, "feature": 0.9, "budget": 0.7, "category": 1.0,
}
_LEARNING_RATE = 0.3  # how fast within-session observations move the estimate away from the prior


def initial_utility(attribute: str) -> float:
    return _PRIOR.get(attribute, 1.0)


def record_outcome(state, attribute: str, pool_before: int, pool_after: int) -> None:
    """Called one turn after `attribute` was asked, once the resulting pool size is known.
    Reward = fractional pool reduction, a live-computable proxy -- never the target rank."""
    if not ENABLE_ACTION_POLICY or pool_before <= 0:
        return
    reduction = max(0.0, min(1.0, 1.0 - (pool_after / pool_before)))
    prior = initial_utility(attribute)
    current = state.facet_utility_history.get(attribute, prior)
    state.facet_utility_history[attribute] = (1 - _LEARNING_RATE) * current + _LEARNING_RATE * (0.5 + reduction)


def utility_multiplier(state, attribute: str) -> float:
    if not ENABLE_ACTION_POLICY:
        return 1.0
    return state.facet_utility_history.get(attribute, initial_utility(attribute))
