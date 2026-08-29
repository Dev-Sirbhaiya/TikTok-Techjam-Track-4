"""Phase 3.1: the tunable strategy surface, in one place.

Before this module existed, the values 3.1 tunes were hardcoded literals scattered across
overgenerality.py, agent.py, and phase2/voi.py -- fine for Phase 0/1's hand-set, spot-checked
values (implementation/10_PRE_REGISTRATION.md exempts those), but exactly what the pre-registration
says needs a genuine train/validation split once a *systematic* search is doing the choosing.

Each constant reads an env-var override at import time, read fresh by every subprocess `tools/
tune_strategy.py` launches -- no monkeypatching, no stale bound-default footguns, and each rollout
is a real, independent process exercising the real code path end to end (the evaluator's own
harness), not a simulated re-scoring of cached candidates.
"""
from __future__ import annotations

import os


def _float(name: str, default: float) -> float:
    v = os.environ.get(name)
    return float(v) if v is not None else default


def _int(name: str, default: int) -> int:
    v = os.environ.get(name)
    return int(v) if v is not None else default


# overgenerality.should_clarify: the base entropy threshold above which a turn is a clarification
# candidate at all (before phase2/voi.py's disagreement-based adjustment). Phase 0's initial guess.
CLARIFY_BASE_LOW = _float("COPILOT_CLARIFY_BASE_LOW", 0.3)

# overgenerality.should_clarify: don't bother clarifying once the candidate pool is already this
# small -- committing is cheap and a facet question on a tiny pool rarely helps.
CLARIFY_MIN_POOL_TO_BOTHER = _int("COPILOT_CLARIFY_MIN_POOL_TO_BOTHER", 4)

# overgenerality.should_clarify: stop attempting clarification once fewer than
# (10 - CLARIFY_NO_ASK_AFTER_TURN) turns remain, reserving the tail of the session for commits.
CLARIFY_NO_ASK_AFTER_TURN = _int("COPILOT_CLARIFY_NO_ASK_AFTER_TURN", 7)

# phase2/voi.py adjusted_clarify_threshold: how strongly BM25/dense retriever disagreement lowers
# the clarify threshold (kept per Phase 2's ablation -- this tunes its strength, not whether it's on).
VOI_DISAGREEMENT_WEIGHT = _float("COPILOT_VOI_DISAGREEMENT_WEIGHT", 0.15)

# agent.py's per-candidate negative-preference penalty: score -= NEG_BOOST_WEIGHT * cosine(emb, neg_vec).
NEG_BOOST_WEIGHT = _float("COPILOT_NEG_BOOST_WEIGHT", 0.10)


def as_dict() -> dict:
    """For logging a run's exact effective config next to its evaluator result."""
    return {
        "CLARIFY_BASE_LOW": CLARIFY_BASE_LOW,
        "CLARIFY_MIN_POOL_TO_BOTHER": CLARIFY_MIN_POOL_TO_BOTHER,
        "CLARIFY_NO_ASK_AFTER_TURN": CLARIFY_NO_ASK_AFTER_TURN,
        "VOI_DISAGREEMENT_WEIGHT": VOI_DISAGREEMENT_WEIGHT,
        "NEG_BOOST_WEIGHT": NEG_BOOST_WEIGHT,
    }
