"""Ask / commit / both decision. NFR-1: turns_remaining <= 1 structurally forces a commit -- this
must never be bypassable, since exceeding 10 turns is a hard zero score.

Self-caught fix before this ever ran: an earlier draft mixed a `top_score` confidence threshold
(sized for RRF's ~0.01-0.05 scale) into the same decision as `should_clarify()`'s entropy gate --
but by the time a real cross-encoder is in play, "top_score" could mean the RRF-fused score OR the
cross-encoder's raw (unbounded, differently-scaled) logit depending on call order, and conflating
the two thresholds risks a threshold tuned for one scale silently misfiring against the other.
Simplified: the entropy gate (already scale-normalized to [0,1] by score_entropy()) is the single
source of truth for ask-vs-commit; `should_clarify()`'s own low/high/turn-ceiling parameters are
what Phase 1.3 calibrates, not a second independent threshold here.
"""
from __future__ import annotations

from .overgenerality import should_clarify


def decide_turn_action(state, entropy: float, pool_size: int, low: float = 0.3) -> str:
    """`low` defaults to should_clarify()'s own default but can be overridden -- Phase 2.3/2.5
    (phase2/voi.py) adjusts it down when BM25/dense retrieval disagree, a live-computable ambiguity
    signal independent of the fused score distribution's own entropy."""
    turns_left = state.turns_remaining
    if turns_left <= 1:
        return "commit"  # NFR-1, non-negotiable
    if pool_size == 0:
        return "commit"  # nothing to ask about either -- attach a (possibly empty) best-effort response
    if not should_clarify(entropy, pool_size, turns_left, low=low):
        return "commit"
    if pool_size <= 10:
        return "both"  # confident enough to show candidates AND still narrow further
    return "ask"
