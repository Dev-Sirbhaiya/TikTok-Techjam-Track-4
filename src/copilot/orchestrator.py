"""The adaptive layer (FR-8): a small explicit set of NAMED decision points, each gated by a cheap
signal already computed elsewhere in the pipeline. No LLM call ever decides control flow here --
see implementation/03_SYSTEM_ARCHITECTURE.md and research/07_adaptive_orchestration.md for why this
stays a rule-based state machine rather than a free-form controller. Phase 1.4 completion: these
branch points existed inline in agent.py/ranker.py before; this module makes them named, and every
decision is now logged (`decisions` list returned per turn), so "Adaptive Orchestration" is
demonstrable, not just implemented.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class OrchestrationTrace:
    decisions: list[dict] = field(default_factory=list)

    def record(self, point: str, choice: str, signal: str) -> None:
        self.decisions.append({"point": point, "choice": choice, "signal": signal})


def route_retrieval_breadth(buying_intent_score: float, trace: OrchestrationTrace) -> bool:
    """Decision point: apply-hard-filter. True = restrict fusion to the hard-filtered set
    (Buying-track precision); False = full breadth (Browsing-track diversity)."""
    apply_filter = buying_intent_score > 0.6
    trace.record(
        point="retrieval_breadth",
        choice="hard_filter" if apply_filter else "full_breadth",
        signal=f"buying_intent_score={buying_intent_score:.2f}",
    )
    return apply_filter


def decide_rerank_depth(pool_size: int, trace: OrchestrationTrace) -> int:
    """Decision point: rerank-shortlist-size. Bigger pools get a bigger (but still bounded)
    cross-encoder shortlist; tiny pools don't waste rerank budget on padding a short list.

    TESTED AND REVERTED (2026-08-30): raising this cap to match k_pool (50->60) looked like a pure
    bugfix on paper -- candidates ranked 51-60 were fetched into the pool but then dropped before
    ever reaching rerank()/hedge_slate(), never eligible for recommendation. But measured on the
    guaranteed-path training split, it REGRESSED (TechnicalScore 0.425645 -> 0.391078, browsing hit
    rate 0.634921 -> 0.52381) -- widening the reranked pool apparently dilutes signal for the
    cross-encoder, giving it more opportunity to misrank a genuinely weaker candidate above the true
    target, rather than simply recovering "wasted" recall. A reminder that "obviously correct"
    mechanical fixes still need empirical verification before shipping -- see
    wiki/08_evaluation_log.md for the full ablation. Left at 50, unchanged."""
    depth = 50 if pool_size > 20 else max(pool_size, 3)
    trace.record(
        point="rerank_depth",
        choice=str(depth),
        signal=f"pool_size={pool_size}",
    )
    return depth


def record_action(action: str, entropy: float, turns_remaining: int, trace: OrchestrationTrace) -> None:
    """Decision point: turn-action (ask/commit/both) -- the actual decision is made by
    turn_policy.decide_turn_action(); this just names it in the trace for demonstrability."""
    trace.record(
        point="turn_action",
        choice=action,
        signal=f"entropy={entropy:.3f} turns_remaining={turns_remaining}",
    )
